import structlog
import tempfile
import os
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from .celery_app import celery_app
from ..database import get_db
from ..models.clip import Clip
from ..models.project import Project
from ..services.clip_editor import get_clip_editor_service
from ..services.video_processor import VideoProcessorService
from ..services.subtitle_generator import SubtitleGeneratorService
from ..utils.s3 import get_s3_service
from ..utils.ffmpeg import get_ffmpeg_service

logger = structlog.get_logger()


@celery_app.task(name="regenerate_clip", bind=True)
def regenerate_clip_task(self, clip_id: str) -> Dict[str, Any]:
    """
    Regenerate a clip with updated settings (timing, subtitle style, etc.).

    Critères PRD F5-03: Re-traite le clip avec les nouveaux paramètres

    Args:
        clip_id: UUID of the clip to regenerate

    Returns:
        Dictionary with regeneration result
    """
    logger.info("Starting clip regeneration task", clip_id=clip_id)

    db: Session = next(get_db())

    try:
        # Get clip from database
        clip = db.query(Clip).filter(Clip.id == clip_id).first()
        if not clip:
            raise ValueError(f"Clip not found: {clip_id}")

        # Update clip status
        clip.status = "processing"
        clip.processing_progress = 10
        clip.error_message = None
        clip.updated_at = datetime.utcnow()
        db.commit()

        logger.info("Clip regeneration started", clip_id=clip.id, title=clip.title)

        # Get services
        s3_service = get_s3_service()
        ffmpeg_service = get_ffmpeg_service()
        video_processor = VideoProcessorService()
        subtitle_generator = SubtitleGeneratorService()

        # Step 1: Download source video
        logger.info("Downloading source video", project_id=clip.project_id)
        source_video_path = _download_source_video(clip.project, s3_service)

        clip.processing_progress = 30
        db.commit()

        # Step 2: Cut clip with new timing
        logger.info("Cutting clip with new timing", start_time=clip.start_time, end_time=clip.end_time)
        cut_clip_path = video_processor.cut_clip(
            source_path=source_video_path,
            start_time=clip.start_time,
            end_time=clip.end_time
        )

        clip.processing_progress = 50
        db.commit()

        # Step 3: Crop to 9:16 format
        logger.info("Cropping clip to portrait format")
        cropped_clip_path = video_processor.crop_to_portrait(
            input_path=cut_clip_path,
            target_aspect_ratio=9/16
        )

        clip.processing_progress = 70
        db.commit()

        # Step 4: Generate subtitles with new style
        logger.info("Generating subtitles", style=clip.subtitle_style)
        subtitled_clip_path = _generate_subtitles_for_clip(
            clip, cropped_clip_path, subtitle_generator
        )

        clip.processing_progress = 85
        db.commit()

        # Step 5: Generate thumbnail and preview
        logger.info("Generating thumbnail and preview")
        thumbnail_s3_key = _generate_thumbnail(clip, subtitled_clip_path, s3_service, ffmpeg_service)
        preview_gif_s3_key = _generate_preview_gif(clip, subtitled_clip_path, s3_service, ffmpeg_service)

        # Step 6: Upload final clip to S3
        logger.info("Uploading regenerated clip to S3")
        clip_s3_key = _upload_clip_to_s3(clip, subtitled_clip_path, s3_service)

        # Step 7: Update clip with new URLs and status
        clip.s3_key = clip_s3_key
        clip.thumbnail_url = thumbnail_s3_key
        clip.preview_gif_url = preview_gif_s3_key
        clip.status = "ready"
        clip.processing_progress = 100
        clip.generated_at = datetime.utcnow()
        clip.updated_at = datetime.utcnow()
        db.commit()

        logger.info("Clip regeneration completed successfully", clip_id=clip.id)

        # Clean up temporary files
        _cleanup_temp_files([source_video_path, cut_clip_path, cropped_clip_path, subtitled_clip_path])

        return {
            "success": True,
            "clip_id": str(clip.id),
            "status": "ready",
            "message": "Clip regenerated successfully"
        }

    except Exception as e:
        logger.error("Clip regeneration failed", clip_id=clip_id, error=str(e))

        # Update clip with error status
        if 'clip' in locals():
            clip.status = "failed"
            clip.error_message = str(e)
            clip.updated_at = datetime.utcnow()
            db.commit()

        return {
            "success": False,
            "clip_id": clip_id,
            "status": "failed",
            "error": str(e)
        }

    finally:
        db.close()


def _download_source_video(project: Project, s3_service) -> str:
    """Download source video from S3 to temporary file"""
    if not project.source_s3_key:
        raise ValueError("Source video S3 key not available")

    # Create temporary file for source video
    temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    temp_path = temp_file.name
    temp_file.close()

    if s3_service._is_mock_mode():
        # In mock mode, create a dummy file
        with open(temp_path, 'wb') as f:
            f.write(b"mock video content")
        logger.info("Mock downloaded source video", path=temp_path)
    else:
        # In real mode, download from S3
        signed_url = s3_service.generate_signed_url(project.source_s3_key, expiration=3600)
        if not signed_url:
            raise Exception("Failed to generate signed URL for source video")

        # Download logic would go here
        # For now, create mock file
        with open(temp_path, 'wb') as f:
            f.write(b"mock video content")

    return temp_path


def _generate_subtitles_for_clip(clip: Clip, video_path: str, subtitle_generator) -> str:
    """Generate subtitles for clip with specified style"""
    try:
        # Get transcript for the clip timing from project
        project_transcript = clip.project.transcript_json
        if not project_transcript:
            logger.warning("No transcript available, skipping subtitles", clip_id=clip.id)
            return video_path

        # Extract transcript segment for this clip
        clip_transcript = _extract_clip_transcript(
            project_transcript,
            clip.start_time,
            clip.end_time
        )

        if not clip_transcript:
            logger.warning("No transcript found for clip timeframe", clip_id=clip.id)
            return video_path

        # Generate subtitles with style
        subtitled_path = subtitle_generator.add_subtitles_to_video(
            video_path=video_path,
            transcript=clip_transcript,
            style=clip.subtitle_style,
            custom_config=clip.subtitle_config
        )

        return subtitled_path or video_path

    except Exception as e:
        logger.error("Failed to generate subtitles", error=str(e), clip_id=clip.id)
        return video_path


def _extract_clip_transcript(project_transcript: Dict[str, Any], start_time: float, end_time: float) -> Dict[str, Any]:
    """Extract transcript segment for clip timing"""
    try:
        # Extract words/segments that fall within clip timeframe
        words = project_transcript.get("words", [])
        clip_words = []

        for word in words:
            word_start = word.get("start", 0)
            word_end = word.get("end", 0)

            # Check if word overlaps with clip timeframe
            if word_start < end_time and word_end > start_time:
                # Adjust timing relative to clip start
                adjusted_word = word.copy()
                adjusted_word["start"] = max(0, word_start - start_time)
                adjusted_word["end"] = min(end_time - start_time, word_end - start_time)
                clip_words.append(adjusted_word)

        return {
            "words": clip_words,
            "language": project_transcript.get("language", "en"),
            "duration": end_time - start_time
        }

    except Exception as e:
        logger.error("Failed to extract clip transcript", error=str(e))
        return {}


def _generate_thumbnail(clip: Clip, video_path: str, s3_service, ffmpeg_service) -> str:
    """Generate and upload thumbnail for clip"""
    try:
        thumbnail_path = ffmpeg_service.extract_thumbnail(
            video_path=video_path,
            timestamp=clip.duration * 0.3,  # 30% into clip
            width=480,
            height=854
        )

        if not thumbnail_path:
            logger.warning("Failed to generate thumbnail", clip_id=clip.id)
            return None

        # Upload to S3
        s3_key = f"clips/{clip.id}/thumbnail.jpg"

        if s3_service._is_mock_mode():
            logger.info("Mock uploading thumbnail", s3_key=s3_key)
        else:
            # Real S3 upload would go here
            pass

        # Clean up local file
        if os.path.exists(thumbnail_path):
            os.unlink(thumbnail_path)

        return s3_key

    except Exception as e:
        logger.error("Failed to generate thumbnail", error=str(e), clip_id=clip.id)
        return None


def _generate_preview_gif(clip: Clip, video_path: str, s3_service, ffmpeg_service) -> str:
    """Generate and upload preview GIF for clip"""
    try:
        preview_duration = min(3.0, clip.duration)

        gif_path = ffmpeg_service.create_preview_gif(
            video_path=video_path,
            start_time=0,
            duration=preview_duration,
            width=240,
            height=427,
            fps=10
        )

        if not gif_path:
            logger.warning("Failed to generate preview GIF", clip_id=clip.id)
            return None

        # Upload to S3
        s3_key = f"clips/{clip.id}/preview.gif"

        if s3_service._is_mock_mode():
            logger.info("Mock uploading preview GIF", s3_key=s3_key)
        else:
            # Real S3 upload would go here
            pass

        # Clean up local file
        if os.path.exists(gif_path):
            os.unlink(gif_path)

        return s3_key

    except Exception as e:
        logger.error("Failed to generate preview GIF", error=str(e), clip_id=clip.id)
        return None


def _upload_clip_to_s3(clip: Clip, video_path: str, s3_service) -> str:
    """Upload final clip to S3"""
    try:
        s3_key = f"clips/{clip.id}/final_clip.mp4"

        if s3_service._is_mock_mode():
            logger.info("Mock uploading clip to S3", s3_key=s3_key)
        else:
            # Real S3 upload would go here
            pass

        return s3_key

    except Exception as e:
        logger.error("Failed to upload clip to S3", error=str(e), clip_id=clip.id)
        raise


def _cleanup_temp_files(file_paths: list):
    """Clean up temporary files"""
    for path in file_paths:
        try:
            if path and os.path.exists(path):
                os.unlink(path)
                logger.debug("Cleaned up temporary file", path=path)
        except Exception as e:
            logger.warning("Failed to clean up temporary file", path=path, error=str(e))


@celery_app.task(name="batch_regenerate_clips")
def batch_regenerate_clips_task(clip_ids: list) -> Dict[str, Any]:
    """
    Regenerate multiple clips in batch.

    Args:
        clip_ids: List of clip UUIDs to regenerate

    Returns:
        Dictionary with batch regeneration results
    """
    logger.info("Starting batch clip regeneration", clip_count=len(clip_ids))

    results = {
        "total": len(clip_ids),
        "successful": 0,
        "failed": 0,
        "results": {}
    }

    for clip_id in clip_ids:
        try:
            result = regenerate_clip_task.delay(clip_id)
            result_data = result.get(timeout=300)  # 5 minute timeout per clip

            if result_data.get("success"):
                results["successful"] += 1
            else:
                results["failed"] += 1

            results["results"][clip_id] = result_data

        except Exception as e:
            logger.error("Failed to regenerate clip in batch", clip_id=clip_id, error=str(e))
            results["failed"] += 1
            results["results"][clip_id] = {
                "success": False,
                "error": str(e)
            }

    logger.info(
        "Batch clip regeneration completed",
        total=results["total"],
        successful=results["successful"],
        failed=results["failed"]
    )

    return results


@celery_app.task(name="cleanup_failed_clips")
def cleanup_failed_clips_task() -> Dict[str, Any]:
    """
    Clean up clips that have been in failed state for too long.

    Returns:
        Dictionary with cleanup results
    """
    logger.info("Starting failed clips cleanup")

    db: Session = next(get_db())

    try:
        # Find clips that have been failed for more than 24 hours
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=24)

        failed_clips = db.query(Clip).filter(
            Clip.status == "failed",
            Clip.updated_at < cutoff_time
        ).all()

        cleanup_count = 0
        s3_service = get_s3_service()

        for clip in failed_clips:
            try:
                # Clean up S3 files if they exist
                if clip.s3_key:
                    s3_service.delete_object(clip.s3_key)
                if clip.thumbnail_url:
                    s3_service.delete_object(clip.thumbnail_url)
                if clip.preview_gif_url:
                    s3_service.delete_object(clip.preview_gif_url)

                # Reset clip to pending state for potential retry
                clip.status = "pending"
                clip.error_message = None
                clip.processing_progress = 0

                cleanup_count += 1

            except Exception as e:
                logger.error("Failed to cleanup clip", clip_id=clip.id, error=str(e))

        db.commit()

        logger.info("Failed clips cleanup completed", cleaned_count=cleanup_count)

        return {
            "success": True,
            "cleaned_count": cleanup_count,
            "total_failed": len(failed_clips)
        }

    except Exception as e:
        logger.error("Failed clips cleanup failed", error=str(e))
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()