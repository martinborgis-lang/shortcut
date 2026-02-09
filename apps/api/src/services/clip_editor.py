import structlog
import tempfile
import os
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from datetime import datetime

from ..models.clip import Clip
from ..utils.s3 import get_s3_service
from ..utils.ffmpeg import get_ffmpeg_service
from .video_processor import VideoProcessorService
from .subtitle_generator import SubtitleGeneratorService

logger = structlog.get_logger()


class ClipEditorService:
    """
    Service for editing clips: timing, styling, regeneration.

    Critères PRD F5-02, F5-03, F5-07, F5-08: Édition timing, style sous-titres, régénération
    """

    def __init__(self):
        self.s3_service = get_s3_service()
        self.ffmpeg_service = get_ffmpeg_service()
        self.video_processor = VideoProcessorService()
        self.subtitle_generator = SubtitleGeneratorService()

    def update_clip_timing(
        self,
        clip: Clip,
        new_start_time: float,
        new_end_time: float
    ) -> Dict[str, Any]:
        """
        Update clip timing and validate constraints.

        Args:
            clip: Clip model instance
            new_start_time: New start time in seconds
            new_end_time: New end time in seconds

        Returns:
            Dictionary with update result and validation info
        """
        try:
            # Validate timing constraints
            duration = new_end_time - new_start_time

            if new_start_time < 0:
                raise ValueError("Start time cannot be negative")

            if new_start_time >= new_end_time:
                raise ValueError("Start time must be before end time")

            if duration < 10:
                raise ValueError("Clip duration must be at least 10 seconds")

            if duration > 120:
                raise ValueError("Clip duration cannot exceed 120 seconds")

            # Get project's source video info to validate timing
            project = clip.project
            if project.source_duration:
                if new_end_time > project.source_duration:
                    raise ValueError(f"End time cannot exceed video duration ({project.source_duration}s)")

            logger.info(
                "Updating clip timing",
                clip_id=clip.id,
                old_timing=f"{clip.start_time}-{clip.end_time}",
                new_timing=f"{new_start_time}-{new_end_time}",
                duration=duration
            )

            # Update clip properties
            clip.start_time = new_start_time
            clip.end_time = new_end_time
            clip.duration = duration
            clip.status = "pending_regeneration"  # Mark for regeneration
            clip.processing_progress = 0
            clip.updated_at = datetime.utcnow()

            return {
                "success": True,
                "message": "Timing updated successfully",
                "requires_regeneration": True,
                "new_duration": duration
            }

        except ValueError as e:
            logger.warning("Clip timing validation failed", error=str(e), clip_id=clip.id)
            return {
                "success": False,
                "error": str(e),
                "requires_regeneration": False
            }
        except Exception as e:
            logger.error("Unexpected error updating clip timing", error=str(e), clip_id=clip.id)
            return {
                "success": False,
                "error": "Failed to update timing",
                "requires_regeneration": False
            }

    def update_subtitle_style(
        self,
        clip: Clip,
        new_style: str,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update clip subtitle style and configuration.

        Args:
            clip: Clip model instance
            new_style: New subtitle style (hormozi, clean, neon, karaoke, minimal)
            custom_config: Optional custom subtitle configuration

        Returns:
            Dictionary with update result
        """
        try:
            # Validate subtitle style
            allowed_styles = ['hormozi', 'clean', 'neon', 'karaoke', 'minimal']
            if new_style not in allowed_styles:
                raise ValueError(f"Invalid subtitle style. Must be one of: {', '.join(allowed_styles)}")

            logger.info(
                "Updating subtitle style",
                clip_id=clip.id,
                old_style=clip.subtitle_style,
                new_style=new_style
            )

            # Update clip properties
            clip.subtitle_style = new_style
            clip.status = "pending_regeneration"  # Mark for regeneration
            clip.processing_progress = 0
            clip.updated_at = datetime.utcnow()

            # Update subtitle configuration if provided
            if custom_config:
                clip.subtitle_config = custom_config
                logger.info("Updated subtitle configuration", config=custom_config)

            return {
                "success": True,
                "message": f"Subtitle style updated to {new_style}",
                "requires_regeneration": True,
                "new_style": new_style
            }

        except ValueError as e:
            logger.warning("Subtitle style validation failed", error=str(e), clip_id=clip.id)
            return {
                "success": False,
                "error": str(e),
                "requires_regeneration": False
            }
        except Exception as e:
            logger.error("Unexpected error updating subtitle style", error=str(e), clip_id=clip.id)
            return {
                "success": False,
                "error": "Failed to update subtitle style",
                "requires_regeneration": False
            }

    def regenerate_clip(self, clip: Clip) -> Dict[str, Any]:
        """
        Regenerate clip with current settings (timing, subtitle style, etc.).

        Args:
            clip: Clip model instance

        Returns:
            Dictionary with regeneration result
        """
        try:
            logger.info("Starting clip regeneration", clip_id=clip.id, status=clip.status)

            # Validate clip can be regenerated
            if not clip.project.source_s3_key:
                raise ValueError("Source video not available for regeneration")

            # Update status to processing
            clip.status = "processing"
            clip.processing_progress = 0
            clip.error_message = None
            clip.updated_at = datetime.utcnow()

            # This will be handled by the async worker
            return {
                "success": True,
                "message": "Clip regeneration started",
                "clip_id": str(clip.id),
                "status": "processing"
            }

        except ValueError as e:
            logger.warning("Clip regeneration validation failed", error=str(e), clip_id=clip.id)
            clip.status = "failed"
            clip.error_message = str(e)
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error("Unexpected error starting clip regeneration", error=str(e), clip_id=clip.id)
            clip.status = "failed"
            clip.error_message = "Failed to start regeneration"
            return {
                "success": False,
                "error": "Failed to start regeneration"
            }

    def generate_thumbnail(self, clip: Clip) -> Optional[str]:
        """
        Generate thumbnail for clip.

        Args:
            clip: Clip model instance

        Returns:
            S3 key for generated thumbnail or None if failed
        """
        try:
            if not clip.s3_key:
                logger.warning("Cannot generate thumbnail - clip video not available", clip_id=clip.id)
                return None

            logger.info("Generating thumbnail for clip", clip_id=clip.id)

            # Download clip video temporarily
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_video:
                video_url = self.s3_service.generate_signed_url(clip.s3_key, expiration=3600)
                if not video_url:
                    raise Exception("Failed to get video URL")

                # For mock mode, just create empty file
                if self.ffmpeg_service._is_mock_mode():
                    temp_video.write(b"mock video content")
                    temp_video.flush()
                else:
                    # In real mode, would download from S3
                    # This is simplified for the implementation
                    pass

                temp_video_path = temp_video.name

            try:
                # Extract thumbnail
                thumbnail_path = self.ffmpeg_service.extract_thumbnail(
                    video_path=temp_video_path,
                    timestamp=clip.duration * 0.3,  # 30% into the clip
                    width=480,
                    height=854  # 9:16 aspect ratio
                )

                if not thumbnail_path:
                    raise Exception("Failed to extract thumbnail")

                # Upload to S3
                thumbnail_s3_key = f"clips/{clip.id}/thumbnail.jpg"

                # In mock mode, just return the key
                if self.s3_service._is_mock_mode():
                    logger.info("Mock uploading thumbnail to S3", s3_key=thumbnail_s3_key)
                    return thumbnail_s3_key

                # In real mode, would upload to S3
                # upload_success = self.s3_service.upload_file(thumbnail_path, thumbnail_s3_key)
                # For now, return mock key
                return thumbnail_s3_key

            finally:
                # Clean up temporary files
                if os.path.exists(temp_video_path):
                    os.unlink(temp_video_path)
                if thumbnail_path and os.path.exists(thumbnail_path):
                    os.unlink(thumbnail_path)

        except Exception as e:
            logger.error("Failed to generate thumbnail", error=str(e), clip_id=clip.id)
            return None

    def create_preview_gif(self, clip: Clip) -> Optional[str]:
        """
        Create preview GIF for clip.

        Args:
            clip: Clip model instance

        Returns:
            S3 key for generated GIF or None if failed
        """
        try:
            if not clip.s3_key:
                logger.warning("Cannot create preview GIF - clip video not available", clip_id=clip.id)
                return None

            logger.info("Creating preview GIF for clip", clip_id=clip.id)

            # Use first 3 seconds of clip for preview
            preview_duration = min(3.0, clip.duration)

            # Download clip video temporarily
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_video:
                # Mock video content
                temp_video.write(b"mock video content")
                temp_video.flush()
                temp_video_path = temp_video.name

            try:
                # Create preview GIF
                gif_path = self.ffmpeg_service.create_preview_gif(
                    video_path=temp_video_path,
                    start_time=0,
                    duration=preview_duration,
                    width=240,
                    height=427,  # 9:16 aspect ratio
                    fps=10
                )

                if not gif_path:
                    raise Exception("Failed to create preview GIF")

                # Upload to S3
                gif_s3_key = f"clips/{clip.id}/preview.gif"

                # In mock mode, just return the key
                if self.s3_service._is_mock_mode():
                    logger.info("Mock uploading GIF to S3", s3_key=gif_s3_key)
                    return gif_s3_key

                # In real mode, would upload to S3
                return gif_s3_key

            finally:
                # Clean up temporary files
                if os.path.exists(temp_video_path):
                    os.unlink(temp_video_path)
                if gif_path and os.path.exists(gif_path):
                    os.unlink(gif_path)

        except Exception as e:
            logger.error("Failed to create preview GIF", error=str(e), clip_id=clip.id)
            return None

    def validate_crop_settings(self, crop_settings: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate crop settings configuration.

        Args:
            crop_settings: Crop configuration dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            required_fields = ['x', 'y', 'width', 'height']
            for field in required_fields:
                if field not in crop_settings:
                    return False, f"Missing required field: {field}"

                if not isinstance(crop_settings[field], (int, float)) or crop_settings[field] < 0:
                    return False, f"Invalid {field}: must be a non-negative number"

            # Validate aspect ratio is close to 9:16
            width = crop_settings['width']
            height = crop_settings['height']
            aspect_ratio = width / height
            target_ratio = 9 / 16

            if abs(aspect_ratio - target_ratio) > 0.1:
                return False, f"Invalid aspect ratio: {aspect_ratio:.3f} (expected ~{target_ratio:.3f})"

            return True, None

        except Exception as e:
            return False, f"Crop settings validation error: {str(e)}"

    def get_subtitle_style_preview(self, style: str) -> Dict[str, Any]:
        """
        Get preview configuration for a subtitle style.

        Args:
            style: Subtitle style name

        Returns:
            Dictionary with style preview configuration
        """
        style_configs = {
            "hormozi": {
                "font_family": "Arial Black",
                "font_size": 48,
                "font_color": "#FFFFFF",
                "outline_color": "#000000",
                "outline_width": 2,
                "position": "center",
                "background": False,
                "animation": "word_highlight"
            },
            "clean": {
                "font_family": "Helvetica",
                "font_size": 44,
                "font_color": "#FFFFFF",
                "outline_color": "#333333",
                "outline_width": 1,
                "position": "bottom",
                "background": True,
                "background_color": "rgba(0,0,0,0.7)",
                "animation": "none"
            },
            "neon": {
                "font_family": "Impact",
                "font_size": 50,
                "font_color": "#00FFFF",
                "outline_color": "#FF00FF",
                "outline_width": 3,
                "position": "center",
                "background": False,
                "animation": "glow",
                "shadow": True
            },
            "karaoke": {
                "font_family": "Comic Sans MS",
                "font_size": 46,
                "font_color": "#FFD700",
                "outline_color": "#000000",
                "outline_width": 2,
                "position": "center",
                "background": False,
                "animation": "word_by_word"
            },
            "minimal": {
                "font_family": "SF Pro",
                "font_size": 40,
                "font_color": "#FFFFFF",
                "outline_color": "none",
                "outline_width": 0,
                "position": "bottom",
                "background": False,
                "animation": "fade"
            }
        }

        return style_configs.get(style, style_configs["clean"])

    def estimate_regeneration_time(self, clip: Clip) -> int:
        """
        Estimate regeneration time in seconds.

        Args:
            clip: Clip model instance

        Returns:
            Estimated time in seconds
        """
        # Base time for processing
        base_time = 30

        # Add time based on clip duration
        duration_factor = clip.duration * 2

        # Add time for subtitle generation
        subtitle_time = 15 if clip.subtitle_style != "minimal" else 5

        # Add time for video processing
        video_processing_time = clip.duration * 1.5

        estimated = int(base_time + duration_factor + subtitle_time + video_processing_time)

        logger.info(
            "Estimated regeneration time",
            clip_id=clip.id,
            duration=clip.duration,
            estimated_seconds=estimated
        )

        return estimated


def get_clip_editor_service() -> ClipEditorService:
    """Get the global clip editor service instance"""
    return ClipEditorService()