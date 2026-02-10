import os
import shutil
import subprocess
import structlog
from typing import Dict, Any, Tuple, Optional
from pathlib import Path
import json
import re
import uuid
from datetime import datetime

from ..config import settings

logger = structlog.get_logger()


class VideoDownloaderService:
    """
    Service for downloading videos from YouTube and Twitch using yt-dlp.

    Critères PRD F4-04: Télécharge la vidéo YouTube via yt-dlp (max 1080p, MP4), stockage local pour MVP
    """

    def __init__(self):
        # Create uploads directory for local storage
        self.uploads_dir = Path("uploads/videos")
        self.uploads_dir.mkdir(parents=True, exist_ok=True)

    def _is_mock_mode(self) -> bool:
        """Check if running in mock mode for development"""
        return os.getenv("MOCK_MODE", "false").lower() == "true"

    def download(self, url: str) -> Tuple[str, Dict[str, Any]]:
        """
        Download video from URL and store locally.

        Args:
            url: YouTube or Twitch video URL

        Returns:
            Tuple of (local_path, metadata)
        """
        logger.info("Starting video download", url=url, mock_mode=self._is_mock_mode())

        if self._is_mock_mode():
            return self._mock_download(url)

        try:
            # Download to final destination
            output_path = self._download_video(url)
            metadata = self._extract_metadata(output_path)

            logger.info("Video download completed", url=url, local_path=output_path)
            return output_path, metadata

        except subprocess.CalledProcessError as e:
            logger.error("yt-dlp download failed", url=url, error=str(e))
            raise Exception(f"Failed to download video: {str(e)}")
        except Exception as e:
            logger.error("Unexpected error during download", url=url, error=str(e))
            raise Exception(f"Download error: {str(e)}")

    def _download_video(self, url: str) -> str:
        """Download video using yt-dlp to local uploads directory"""
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = f"video_{timestamp}_{unique_id}.%(ext)s"

        output_template = str(self.uploads_dir / safe_filename)

        # yt-dlp command with quality restrictions
        cmd = [
            "yt-dlp",
            "--format", "best[height<=1080][ext=mp4]/best[height<=1080]/best",
            "--output", output_template,
            "--no-playlist",
            "--embed-thumbnail",
            "--add-metadata",
            url
        ]

        logger.info("Running yt-dlp", cmd=" ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Find the downloaded file
        downloaded_files = list(self.uploads_dir.glob(f"video_{timestamp}_{unique_id}.*"))
        if not downloaded_files:
            raise Exception("No file was downloaded")

        return str(downloaded_files[0])

    def _extract_metadata(self, video_path: str) -> Dict[str, Any]:
        """Extract video metadata using ffprobe"""
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                video_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            probe_data = json.loads(result.stdout)

            # Extract relevant metadata
            video_stream = None
            audio_stream = None

            for stream in probe_data.get("streams", []):
                if stream.get("codec_type") == "video" and not video_stream:
                    video_stream = stream
                elif stream.get("codec_type") == "audio" and not audio_stream:
                    audio_stream = stream

            format_info = probe_data.get("format", {})

            metadata = {
                "filename": Path(video_path).name,
                "duration": float(format_info.get("duration", 0)),
                "size": int(format_info.get("size", 0)),
                "format": format_info.get("format_name"),
                "bitrate": int(format_info.get("bit_rate", 0)) if format_info.get("bit_rate") else None
            }

            if video_stream:
                metadata.update({
                    "width": int(video_stream.get("width", 0)),
                    "height": int(video_stream.get("height", 0)),
                    "video_codec": video_stream.get("codec_name"),
                    "fps": self._parse_fps(video_stream.get("r_frame_rate", "0/0"))
                })

            if audio_stream:
                metadata.update({
                    "audio_codec": audio_stream.get("codec_name"),
                    "audio_bitrate": int(audio_stream.get("bit_rate", 0)) if audio_stream.get("bit_rate") else None,
                    "sample_rate": int(audio_stream.get("sample_rate", 0)) if audio_stream.get("sample_rate") else None
                })

            return metadata

        except subprocess.CalledProcessError as e:
            logger.warning("Failed to extract metadata", error=str(e))
            return {
                "filename": Path(video_path).name,
                "duration": 0,
                "size": os.path.getsize(video_path)
            }

    def _parse_fps(self, fps_str: str) -> float:
        """Parse fps from fraction string like '30/1'"""
        try:
            if '/' in fps_str:
                num, den = fps_str.split('/')
                return float(num) / float(den)
            return float(fps_str)
        except:
            return 0.0

    def get_video_url(self, local_path: str) -> str:
        """Generate a URL for serving the video file"""
        # For MVP: serve from local filesystem via API endpoint
        filename = Path(local_path).name
        return f"/api/videos/{filename}"

    def _mock_download(self, url: str) -> Tuple[str, Dict[str, Any]]:
        """Mock download for development"""
        logger.info("Using mock download", url=url)

        # Return mock data
        mock_metadata = {
            "filename": "test_video.mp4",
            "duration": 300.0,  # 5 minutes
            "size": 50 * 1024 * 1024,  # 50MB
            "width": 1920,
            "height": 1080,
            "fps": 30.0,
            "video_codec": "h264",
            "audio_codec": "aac",
            "format": "mp4"
        }

        mock_local_path = str(self.uploads_dir / "mock_test_video.mp4")

        return mock_local_path, mock_metadata

    def delete_video(self, local_path: str) -> None:
        """Delete video file from local storage"""
        try:
            if os.path.exists(local_path):
                os.remove(local_path)
                logger.info("Video file deleted", local_path=local_path)
        except Exception as e:
            logger.error("Failed to delete video file", local_path=local_path, error=str(e))

    def validate_duration_limit(self, duration: float, user_plan: str) -> None:
        """
        Validate video duration against user plan limits.

        Critères PRD F4-15: Vérification de la durée de la source vs le plan user avant processing
        """
        # Basic plan: 10 minutes max, Pro plan: 60 minutes max
        max_duration = 3600 if user_plan == "pro" else 600  # seconds

        if duration > max_duration:
            max_minutes = max_duration // 60
            raise Exception(
                f"Video duration ({duration/60:.1f} minutes) exceeds "
                f"{user_plan} plan limit ({max_minutes} minutes)"
            )