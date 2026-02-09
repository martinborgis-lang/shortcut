import os
import tempfile
import structlog
import boto3
from celery import Task
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import asyncio
from datetime import datetime
import traceback
import time

from .celery_app import celery_app
from ..database import get_db, SessionLocal
from ..models.project import Project
from ..models.clip import Clip
from ..models.user import User
from ..services.video_downloader import VideoDownloaderService
from ..services.transcription import TranscriptionService
from ..services.viral_detection import ViralDetectionService
from ..services.video_processor import VideoProcessorService
from ..services.subtitle_generator import SubtitleGeneratorService
from ..config import settings

logger = structlog.get_logger()


class VideoProcessingTask(Task):
    """
    Base task for video processing with retry logic and error handling
    """
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 60}
    retry_backoff = True
    retry_jitter = True


@celery_app.task(bind=True, base=VideoProcessingTask, name="video_pipeline.process_video")
def process_video(self, project_id: str):
    """
    Main video processing pipeline task.

    Critères PRD F4-09: Task Celery qui orchestre les 5 étapes séquentiellement avec gestion d'erreurs
    Critères PRD F4-10: 3 tentatives par étape avec backoff exponentiel
    Critères PRD F4-11: Le worker met à jour le statut du projet en DB à chaque étape
    """
    logger.info("Starting video processing pipeline", project_id=project_id, task_id=self.request.id)

    db = SessionLocal()
    try:
        # Get project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise Exception(f"Project {project_id} not found")

        # Get user for plan validation
        user = db.query(User).filter(User.id == project.user_id).first()
        if not user:
            raise Exception(f"User {project.user_id} not found")

        # Initialize services
        downloader = VideoDownloaderService()
        transcription = TranscriptionService()
        viral_detection = ViralDetectionService()
        video_processor = VideoProcessorService()
        subtitle_generator = SubtitleGeneratorService()

        # Pipeline stages
        stages = [
            ("downloading", "Downloading video from source", 10),
            ("transcribing", "Extracting audio and transcribing", 30),
            ("analyzing", "Analyzing content for viral moments", 50),
            ("processing", "Processing video clips", 90),
            ("done", "Processing complete", 100)
        ]

        # Stage 1: Download Video
        logger.info("Stage 1: Downloading video", project_id=project_id)
        _update_project_status(db, project, "downloading", "Downloading video from source", 10)

        try:
            s3_key, metadata = downloader.download(project.source_url)

            # Validate duration against user plan
            duration = metadata.get("duration", 0)
            downloader.validate_duration_limit(duration, user.plan)

            # Update project with download results
            project.source_s3_key = s3_key
            project.source_filename = metadata.get("filename")
            project.source_size = metadata.get("size")
            project.source_duration = duration
            project.video_metadata = metadata
            project.name = project.name or metadata.get("filename", "Untitled Video")
            db.commit()

            logger.info("Video downloaded successfully", project_id=project_id, s3_key=s3_key, duration=duration)

        except Exception as e:
            _handle_stage_error(db, project, "downloading", str(e))
            raise

        # Get local video file for processing
        if downloader._is_mock_mode():
            # In mock mode, create a dummy file
            source_video_path = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
            with open(source_video_path, "w") as f:
                f.write("mock video content")
        else:
            # Download from S3 for processing
            source_video_path = _download_from_s3(s3_key)

        try:
            # Stage 2: Transcription
            logger.info("Stage 2: Transcribing audio", project_id=project_id)
            _update_project_status(db, project, "transcribing", "Extracting audio and transcribing", 30)

            try:
                transcript = _run_async_transcription(transcription, source_video_path)
                project.transcript_json = transcript
                db.commit()

                logger.info("Transcription completed", project_id=project_id)

            except Exception as e:
                _handle_stage_error(db, project, "transcribing", str(e))
                raise

            # Stage 3: Viral Detection
            logger.info("Stage 3: Detecting viral moments", project_id=project_id)
            _update_project_status(db, project, "analyzing", "Analyzing content for viral moments", 50)

            try:
                viral_segments = viral_detection.detect_viral_segments(
                    transcript,
                    project.source_duration,
                    project.max_clips_requested
                )

                project.viral_segments = viral_segments
                db.commit()

                logger.info("Viral detection completed", project_id=project_id, segments_count=len(viral_segments))

            except Exception as e:
                _handle_stage_error(db, project, "analyzing", str(e))
                raise

            # Stage 4: Process Clips
            logger.info("Stage 4: Processing video clips", project_id=project_id)
            _update_project_status(db, project, "processing", "Processing video clips", 70)

            try:
                processed_clips = []

                for i, segment in enumerate(viral_segments):
                    logger.info(
                        "Processing clip",
                        project_id=project_id,
                        clip_index=i + 1,
                        total_clips=len(viral_segments),
                        segment=segment
                    )

                    # Update progress
                    progress = 70 + (20 * i / len(viral_segments))
                    _update_project_status(db, project, "processing", f"Processing clip {i+1}/{len(viral_segments)}", int(progress))

                    # Process individual clip
                    clip = _process_single_clip(
                        db, project, segment, source_video_path, transcript,
                        video_processor, subtitle_generator, i + 1
                    )

                    if clip:
                        processed_clips.append(clip)

                logger.info("All clips processed", project_id=project_id, clips_generated=len(processed_clips))

            except Exception as e:
                _handle_stage_error(db, project, "processing", str(e))
                raise

            # Stage 5: Completion
            logger.info("Stage 5: Completing processing", project_id=project_id)
            _update_project_status(db, project, "done", "Processing complete", 100)

            project.completed_at = datetime.utcnow()
            db.commit()

            logger.info("Video processing pipeline completed successfully", project_id=project_id)

            return {
                "status": "success",
                "project_id": project_id,
                "clips_generated": len(processed_clips),
                "processing_time": (datetime.utcnow() - project.created_at).total_seconds()
            }

        finally:
            # Cleanup: Remove temporary files (Critères PRD F4-13)
            _cleanup_temp_files([source_video_path])

    except Exception as e:
        logger.error("Video processing pipeline failed", project_id=project_id, error=str(e), traceback=traceback.format_exc())

        # Update project status to failed
        try:
            if 'project' in locals():
                _handle_stage_error(db, project, project.status or "failed", str(e))
        except:
            pass  # Don't fail the cleanup

        raise

    finally:
        db.close()


def _process_single_clip(
    db: Session,
    project: Project,
    segment: Dict[str, Any],
    source_video_path: str,
    transcript: Dict[str, Any],
    video_processor: VideoProcessorService,
    subtitle_generator: SubtitleGeneratorService,
    clip_number: int
) -> Clip:
    """
    Process a single clip: cut, crop, subtitle, upload.

    Critères PRD F4-07: Pour chaque segment : découpe avec FFmpeg (timestamps précis), recadrage 9:16 avec détection faciale MediaPipe
    Critères PRD F4-08: Génère un fichier ASS avec le style sélectionné, incrustation via FFmpeg
    Critères PRD F4-12: Chaque clip final est uploadé sur S3, URL signée générée pour le téléchargement
    """
    temp_files = []

    try:
        # Create clip record
        clip = Clip(
            project_id=project.id,
            title=segment.get("title", f"Clip {clip_number}"),
            start_time=segment["start_time"],
            end_time=segment["end_time"],
            duration=segment["end_time"] - segment["start_time"],
            viral_score=segment.get("virality_score"),
            reason=segment.get("reason"),
            hook=segment.get("hook"),
            subtitle_style="hormozi",  # Default style
            status="processing",
            processing_progress=0
        )

        db.add(clip)
        db.commit()
        db.refresh(clip)

        logger.info("Processing clip", clip_id=str(clip.id), title=clip.title)

        # Step 1: Cut video segment
        clip.status = "processing"
        clip.processing_progress = 25
        db.commit()

        cut_path = video_processor.cut_clip(
            source_video_path,
            segment["start_time"],
            segment["end_time"]
        )
        temp_files.append(cut_path)

        logger.info("Clip cut completed", clip_id=str(clip.id), cut_path=cut_path)

        # Step 2: Crop to 9:16 portrait
        clip.processing_progress = 50
        db.commit()

        cropped_path = video_processor.crop_to_portrait(cut_path)
        temp_files.append(cropped_path)

        logger.info("Clip cropped to portrait", clip_id=str(clip.id), cropped_path=cropped_path)

        # Step 3: Generate subtitles
        clip.processing_progress = 75
        db.commit()

        subtitle_path = subtitle_generator.generate_subtitles(
            transcript,
            segment,
            clip.subtitle_style
        )
        temp_files.append(subtitle_path)

        logger.info("Subtitles generated", clip_id=str(clip.id), subtitle_path=subtitle_path)

        # Step 4: Burn subtitles into video
        final_path = subtitle_generator.burn_subtitles(cropped_path, subtitle_path)
        temp_files.append(final_path)

        logger.info("Subtitles burned", clip_id=str(clip.id), final_path=final_path)

        # Step 5: Upload to S3
        clip.processing_progress = 90
        db.commit()

        s3_key = _upload_clip_to_s3(final_path, f"clip_{clip.id}.mp4")
        signed_url = _generate_signed_url(s3_key)

        # Update clip with final results
        clip.s3_key = s3_key
        clip.video_url = signed_url
        clip.status = "ready"
        clip.processing_progress = 100
        clip.generated_at = datetime.utcnow()

        db.commit()

        logger.info("Clip processing completed", clip_id=str(clip.id), s3_key=s3_key)

        return clip

    except Exception as e:
        logger.error("Single clip processing failed", error=str(e), clip_id=str(clip.id) if 'clip' in locals() else None)

        # Update clip status to failed
        if 'clip' in locals():
            try:
                clip.status = "failed"
                clip.error_message = str(e)
                db.commit()
            except:
                pass

        raise

    finally:
        # Cleanup temporary files for this clip
        _cleanup_temp_files(temp_files)


def _update_project_status(db: Session, project: Project, status: str, current_step: str, progress: int):
    """Update project status in database"""
    project.status = status
    project.current_step = current_step
    project.processing_progress = progress
    project.updated_at = datetime.utcnow()
    db.commit()

    logger.info(
        "Project status updated",
        project_id=str(project.id),
        status=status,
        progress=progress,
        step=current_step
    )


def _handle_stage_error(db: Session, project: Project, stage: str, error: str):
    """Handle stage error and update project"""
    project.status = "failed"
    project.current_step = f"Failed at {stage}"
    project.error_message = error
    project.updated_at = datetime.utcnow()
    db.commit()

    logger.error("Pipeline stage failed", project_id=str(project.id), stage=stage, error=error)


def _download_from_s3(s3_key: str) -> str:
    """Download file from S3 to local temporary file"""
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )

        temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        temp_file.close()

        s3_client.download_file(settings.S3_BUCKET_NAME, s3_key, temp_file.name)

        logger.info("File downloaded from S3", s3_key=s3_key, local_path=temp_file.name)
        return temp_file.name

    except Exception as e:
        logger.error("S3 download failed", s3_key=s3_key, error=str(e))
        raise Exception(f"Failed to download from S3: {str(e)}")


def _upload_clip_to_s3(file_path: str, filename: str) -> str:
    """Upload processed clip to S3"""
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )

        s3_key = f"clips/{filename}"

        s3_client.upload_file(
            file_path,
            settings.S3_BUCKET_NAME,
            s3_key,
            ExtraArgs={
                'ContentType': 'video/mp4',
                'Metadata': {
                    'generated_at': datetime.utcnow().isoformat()
                }
            }
        )

        logger.info("Clip uploaded to S3", s3_key=s3_key, file_path=file_path)
        return s3_key

    except Exception as e:
        logger.error("S3 upload failed", file_path=file_path, error=str(e))
        raise Exception(f"Failed to upload clip to S3: {str(e)}")


def _generate_signed_url(s3_key: str, expiration: int = 86400) -> str:
    """Generate signed URL for S3 object (24 hours expiration)"""
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )

        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': settings.S3_BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=expiration
        )

        return url

    except Exception as e:
        logger.error("Failed to generate signed URL", s3_key=s3_key, error=str(e))
        return ""


def _cleanup_temp_files(file_paths: List[str]):
    """
    Cleanup temporary files.

    Critères PRD F4-13: Les fichiers temporaires locaux sont supprimés après upload S3
    """
    for file_path in file_paths:
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.debug("Temporary file removed", file_path=file_path)
        except Exception as e:
            logger.warning("Failed to remove temporary file", file_path=file_path, error=str(e))


@celery_app.task(name="video_pipeline.cleanup_expired_tasks")
def cleanup_expired_tasks():
    """Cleanup expired/failed tasks and old temporary files"""
    logger.info("Running cleanup task")

    db = SessionLocal()
    try:
        # Find projects stuck in processing for more than 2 hours
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=2)

        stuck_projects = db.query(Project).filter(
            Project.status.in_(["pending", "downloading", "transcribing", "analyzing", "processing"]),
            Project.updated_at < cutoff_time
        ).all()

        for project in stuck_projects:
            logger.warning("Found stuck project", project_id=str(project.id), status=project.status)
            project.status = "failed"
            project.error_message = "Processing timed out"
            project.updated_at = datetime.utcnow()

        db.commit()

        logger.info("Cleanup completed", stuck_projects_count=len(stuck_projects))

    except Exception as e:
        logger.error("Cleanup task failed", error=str(e))
        db.rollback()

    finally:
        db.close()


# Helper function to run async transcription in sync context
def _run_async_transcription(transcription_service: TranscriptionService, video_path: str) -> Dict[str, Any]:
    """Helper to run async transcription in sync Celery task"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(transcription_service.transcribe(video_path))
    finally:
        loop.close()


# Legacy functions for backwards compatibility (kept for existing celery_app.py references)
def process_video_pipeline(project_id: str) -> Dict[str, Any]:
    """Legacy wrapper for the new Celery task"""
    logger.warning("Using legacy process_video_pipeline, consider using the new Celery task")
    return process_video.delay(project_id).get()


def generate_clips_pipeline(project_id: str, viral_moments: List[Dict]) -> Dict[str, Any]:
    """Legacy function - now integrated into main pipeline"""
    logger.warning("generate_clips_pipeline is deprecated, clips are now generated in main pipeline")
    return {"status": "deprecated", "message": "Use process_video instead"}


def cleanup_expired_tasks_legacy():
    """Legacy wrapper for cleanup task"""
    return cleanup_expired_tasks.delay().get()