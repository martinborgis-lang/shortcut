import structlog
import tempfile
import os
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from ..utils.s3 import get_s3_service
from ..utils.ffmpeg import get_ffmpeg_service
from ..models.clip import Clip

logger = structlog.get_logger()


class ThumbnailGeneratorService:
    """
    Service for generating thumbnails from video clips.

    Critères PRD F5-13: Extraction automatique d'une frame représentative comme thumbnail
    """

    def __init__(self):
        self.s3_service = get_s3_service()
        self.ffmpeg_service = get_ffmpeg_service()

    def generate_thumbnail_from_video(
        self,
        video_path: str,
        timestamp: float = None,
        width: int = 480,
        height: int = 854
    ) -> Optional[str]:
        """
        Extract thumbnail from video at specified timestamp.

        Args:
            video_path: Path to the video file
            timestamp: Time in seconds to extract frame (default: 30% of video duration)
            width: Thumbnail width in pixels
            height: Thumbnail height in pixels (9:16 aspect ratio by default)

        Returns:
            Path to generated thumbnail or None if failed
        """
        try:
            logger.info("Generating thumbnail from video", video_path=video_path, timestamp=timestamp)

            # Get video duration if timestamp not provided
            if timestamp is None:
                duration = self.ffmpeg_service.get_video_duration(video_path)
                timestamp = duration * 0.3  # 30% into the video for best frame

            # Extract thumbnail using FFmpeg
            thumbnail_path = self.ffmpeg_service.extract_thumbnail(
                video_path=video_path,
                timestamp=timestamp,
                width=width,
                height=height
            )

            if not thumbnail_path:
                logger.warning("FFmpeg failed to extract thumbnail")
                return None

            logger.info("Thumbnail generated successfully", path=thumbnail_path)
            return thumbnail_path

        except Exception as e:
            logger.error("Failed to generate thumbnail from video", error=str(e))
            return None

    def generate_thumbnail_for_clip(self, clip: Clip) -> Optional[str]:
        """
        Generate and upload thumbnail for a clip.

        Args:
            clip: Clip model instance

        Returns:
            S3 key for uploaded thumbnail or None if failed
        """
        try:
            if not clip.s3_key:
                logger.warning("Cannot generate thumbnail - clip video not available", clip_id=clip.id)
                return None

            logger.info("Generating thumbnail for clip", clip_id=clip.id)

            # Download video temporarily
            temp_video_path = self._download_video_temp(clip.s3_key)
            if not temp_video_path:
                logger.error("Failed to download video for thumbnail generation", clip_id=clip.id)
                return None

            try:
                # Calculate optimal timestamp (avoid first/last 10% of video)
                clip_duration = clip.end_time - clip.start_time
                if clip_duration > 6:
                    # For longer clips, use multiple candidate timestamps and pick best
                    candidate_timestamps = [
                        clip_duration * 0.2,  # 20% into clip
                        clip_duration * 0.3,  # 30% into clip
                        clip_duration * 0.5,  # 50% into clip
                    ]
                    timestamp = self._select_best_thumbnail_timestamp(
                        temp_video_path,
                        candidate_timestamps
                    )
                else:
                    # For short clips, just use middle
                    timestamp = clip_duration * 0.5

                # Generate thumbnail
                thumbnail_path = self.generate_thumbnail_from_video(
                    video_path=temp_video_path,
                    timestamp=timestamp,
                    width=480,
                    height=854
                )

                if not thumbnail_path:
                    logger.error("Failed to generate thumbnail", clip_id=clip.id)
                    return None

                # Upload to S3
                s3_key = f"clips/{clip.id}/thumbnail.jpg"
                upload_success = self._upload_thumbnail_to_s3(thumbnail_path, s3_key)

                if not upload_success:
                    logger.error("Failed to upload thumbnail to S3", clip_id=clip.id)
                    return None

                logger.info("Thumbnail generated and uploaded successfully",
                          clip_id=clip.id, s3_key=s3_key)
                return s3_key

            finally:
                # Clean up temporary files
                if os.path.exists(temp_video_path):
                    os.unlink(temp_video_path)
                if thumbnail_path and os.path.exists(thumbnail_path):
                    os.unlink(thumbnail_path)

        except Exception as e:
            logger.error("Failed to generate thumbnail for clip", error=str(e), clip_id=clip.id)
            return None

    def generate_animated_thumbnail(self, clip: Clip, duration: float = 3.0) -> Optional[str]:
        """
        Generate animated GIF thumbnail for clip preview.

        Args:
            clip: Clip model instance
            duration: Duration of animated thumbnail in seconds

        Returns:
            S3 key for uploaded animated thumbnail or None if failed
        """
        try:
            if not clip.s3_key:
                logger.warning("Cannot generate animated thumbnail - clip video not available", clip_id=clip.id)
                return None

            logger.info("Generating animated thumbnail for clip", clip_id=clip.id, duration=duration)

            # Download video temporarily
            temp_video_path = self._download_video_temp(clip.s3_key)
            if not temp_video_path:
                return None

            try:
                # Use first few seconds of clip for animation
                clip_duration = clip.end_time - clip.start_time
                anim_duration = min(duration, clip_duration, 3.0)  # Max 3 seconds

                # Create animated GIF
                gif_path = self.ffmpeg_service.create_preview_gif(
                    video_path=temp_video_path,
                    start_time=0,
                    duration=anim_duration,
                    width=240,
                    height=427,  # Smaller 9:16 for animation
                    fps=10
                )

                if not gif_path:
                    logger.error("Failed to generate animated thumbnail", clip_id=clip.id)
                    return None

                # Upload to S3
                s3_key = f"clips/{clip.id}/animated_thumbnail.gif"
                upload_success = self._upload_thumbnail_to_s3(gif_path, s3_key)

                if not upload_success:
                    logger.error("Failed to upload animated thumbnail to S3", clip_id=clip.id)
                    return None

                logger.info("Animated thumbnail generated successfully",
                          clip_id=clip.id, s3_key=s3_key)
                return s3_key

            finally:
                # Clean up temporary files
                if os.path.exists(temp_video_path):
                    os.unlink(temp_video_path)
                if gif_path and os.path.exists(gif_path):
                    os.unlink(gif_path)

        except Exception as e:
            logger.error("Failed to generate animated thumbnail", error=str(e), clip_id=clip.id)
            return None

    def batch_generate_thumbnails(self, clip_ids: list[str]) -> Dict[str, Any]:
        """
        Generate thumbnails for multiple clips in batch.

        Args:
            clip_ids: List of clip UUIDs

        Returns:
            Dictionary with batch generation results
        """
        logger.info("Starting batch thumbnail generation", clip_count=len(clip_ids))

        results = {
            "total": len(clip_ids),
            "successful": 0,
            "failed": 0,
            "results": {}
        }

        from ..database import get_db
        from sqlalchemy.orm import Session

        db: Session = next(get_db())

        try:
            for clip_id in clip_ids:
                try:
                    # Get clip from database
                    from ..models.clip import Clip
                    clip = db.query(Clip).filter(Clip.id == clip_id).first()

                    if not clip:
                        results["failed"] += 1
                        results["results"][clip_id] = {"success": False, "error": "Clip not found"}
                        continue

                    # Generate thumbnail
                    thumbnail_s3_key = self.generate_thumbnail_for_clip(clip)

                    if thumbnail_s3_key:
                        # Update clip with thumbnail URL
                        clip.thumbnail_url = thumbnail_s3_key
                        db.commit()

                        results["successful"] += 1
                        results["results"][clip_id] = {
                            "success": True,
                            "thumbnail_url": thumbnail_s3_key
                        }
                    else:
                        results["failed"] += 1
                        results["results"][clip_id] = {
                            "success": False,
                            "error": "Failed to generate thumbnail"
                        }

                except Exception as e:
                    logger.error("Failed to generate thumbnail in batch", clip_id=clip_id, error=str(e))
                    results["failed"] += 1
                    results["results"][clip_id] = {"success": False, "error": str(e)}

        finally:
            db.close()

        logger.info(
            "Batch thumbnail generation completed",
            total=results["total"],
            successful=results["successful"],
            failed=results["failed"]
        )

        return results

    def _download_video_temp(self, s3_key: str) -> Optional[str]:
        """Download video from S3 to temporary file"""
        try:
            temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
            temp_path = temp_file.name
            temp_file.close()

            if self.s3_service._is_mock_mode():
                # In mock mode, create dummy video file
                with open(temp_path, 'wb') as f:
                    f.write(b"mock video content for thumbnail generation")
                logger.info("Mock downloaded video for thumbnail", path=temp_path)
            else:
                # In real mode, download from S3
                success = self.s3_service.download_file(s3_key, temp_path)
                if not success:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                    return None

            return temp_path

        except Exception as e:
            logger.error("Failed to download video temporarily", error=str(e))
            return None

    def _upload_thumbnail_to_s3(self, thumbnail_path: str, s3_key: str) -> bool:
        """Upload thumbnail to S3"""
        try:
            if self.s3_service._is_mock_mode():
                logger.info("Mock uploading thumbnail to S3", s3_key=s3_key)
                return True
            else:
                # In real mode, upload to S3
                return self.s3_service.upload_file(
                    file_path=thumbnail_path,
                    s3_key=s3_key,
                    content_type="image/jpeg"
                )

        except Exception as e:
            logger.error("Failed to upload thumbnail to S3", error=str(e))
            return False

    def _select_best_thumbnail_timestamp(
        self,
        video_path: str,
        candidate_timestamps: list[float]
    ) -> float:
        """
        Select best timestamp for thumbnail by analyzing frame quality.
        For now, just return the middle candidate.
        In production, could analyze frame brightness, contrast, etc.
        """
        # Simple implementation: return middle timestamp
        return candidate_timestamps[len(candidate_timestamps) // 2]

    def clean_up_orphaned_thumbnails(self) -> Dict[str, Any]:
        """
        Clean up thumbnail files in S3 that don't have corresponding clips.

        Returns:
            Dictionary with cleanup results
        """
        logger.info("Starting orphaned thumbnails cleanup")

        results = {
            "scanned": 0,
            "orphaned": 0,
            "deleted": 0,
            "errors": 0
        }

        try:
            # This would scan S3 for thumbnail files and check against database
            # For now, just return mock results
            logger.info("Orphaned thumbnails cleanup completed (mock mode)")

        except Exception as e:
            logger.error("Orphaned thumbnails cleanup failed", error=str(e))
            results["errors"] += 1

        return results


def get_thumbnail_generator_service() -> ThumbnailGeneratorService:
    """Get the global thumbnail generator service instance"""
    return ThumbnailGeneratorService()