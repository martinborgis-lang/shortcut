import subprocess
import tempfile
import structlog
import os
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
import json

logger = structlog.get_logger()


class FFmpegService:
    """
    Service for FFmpeg operations: thumbnail extraction, GIF generation, video info.

    Critères PRD F5-13: Extraction automatique d'une frame représentative comme thumbnail
    """

    def __init__(self):
        self.ffmpeg_path = self._find_ffmpeg()
        self.ffprobe_path = self._find_ffprobe()

    def _is_mock_mode(self) -> bool:
        """Check if running in mock mode for development"""
        return os.getenv("MOCK_MODE", "false").lower() == "true"

    def _find_ffmpeg(self) -> str:
        """Find FFmpeg executable path"""
        try:
            result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass

        # Try common paths
        common_paths = [
            'ffmpeg',
            '/usr/bin/ffmpeg',
            '/usr/local/bin/ffmpeg',
            '/opt/homebrew/bin/ffmpeg'
        ]

        for path in common_paths:
            try:
                subprocess.run([path, '-version'], capture_output=True, check=True)
                return path
            except:
                continue

        logger.warning("FFmpeg not found, operations will be mocked")
        return 'ffmpeg'  # Fallback

    def _find_ffprobe(self) -> str:
        """Find FFprobe executable path"""
        try:
            result = subprocess.run(['which', 'ffprobe'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass

        # Try common paths
        common_paths = [
            'ffprobe',
            '/usr/bin/ffprobe',
            '/usr/local/bin/ffprobe',
            '/opt/homebrew/bin/ffprobe'
        ]

        for path in common_paths:
            try:
                subprocess.run([path, '-version'], capture_output=True, check=True)
                return path
            except:
                continue

        logger.warning("FFprobe not found, operations will be mocked")
        return 'ffprobe'  # Fallback

    def extract_thumbnail(
        self,
        video_path: str,
        timestamp: Optional[float] = None,
        output_path: Optional[str] = None,
        width: int = 480,
        height: int = 854  # 9:16 aspect ratio for portrait
    ) -> Optional[str]:
        """
        Extract a thumbnail from video at specified timestamp.

        Args:
            video_path: Path to source video
            timestamp: Time in seconds to extract thumbnail (None for auto-detect)
            output_path: Optional output path for thumbnail
            width: Thumbnail width
            height: Thumbnail height

        Returns:
            Path to extracted thumbnail or None if failed
        """
        if self._is_mock_mode():
            return self._mock_extract_thumbnail(video_path, timestamp, output_path)

        if output_path is None:
            output_path = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False).name

        try:
            # If no timestamp specified, find optimal frame
            if timestamp is None:
                timestamp = self._find_optimal_thumbnail_time(video_path)

            # Extract thumbnail with FFmpeg
            cmd = [
                self.ffmpeg_path,
                "-ss", str(timestamp),  # Seek to timestamp
                "-i", video_path,  # Input video
                "-vf", f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}",
                "-vframes", "1",  # Extract only one frame
                "-q:v", "2",  # High quality JPEG
                "-y",  # Overwrite output
                output_path
            ]

            logger.info(
                "Extracting thumbnail",
                video_path=video_path,
                timestamp=timestamp,
                size=f"{width}x{height}",
                cmd=" ".join(cmd)
            )

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Verify thumbnail was created
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info("Thumbnail extracted successfully", output_path=output_path)
                return output_path
            else:
                logger.error("Thumbnail extraction failed - no output file created")
                return None

        except subprocess.CalledProcessError as e:
            logger.error("FFmpeg thumbnail extraction failed", error=str(e), stderr=e.stderr)
            return None
        except Exception as e:
            logger.error("Unexpected error during thumbnail extraction", error=str(e))
            return None

    def _find_optimal_thumbnail_time(self, video_path: str) -> float:
        """
        Find optimal time for thumbnail extraction using scene detection.

        Args:
            video_path: Path to source video

        Returns:
            Optimal timestamp in seconds
        """
        try:
            # Get video duration
            video_info = self.get_video_info(video_path)
            duration = video_info.get('duration', 30.0)

            # Use FFmpeg to detect scene changes and find a good frame
            cmd = [
                self.ffprobe_path,
                "-f", "lavfi",
                "-i", f"movie={video_path},select=gt(scene\\,0.3)",
                "-show_entries", "frame=best_effort_timestamp_time",
                "-of", "csv=p=0",
                "-v", "quiet"
            ]

            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and result.stdout.strip():
                    # Get first scene change after 10% of video
                    scene_times = [float(line.strip()) for line in result.stdout.strip().split('\n') if line.strip()]
                    min_time = duration * 0.1  # Skip first 10%
                    max_time = duration * 0.8  # Skip last 20%

                    for time in scene_times:
                        if min_time <= time <= max_time:
                            logger.info("Found optimal thumbnail time via scene detection", time=time)
                            return time
            except:
                pass

            # Fallback: use 30% of video duration
            optimal_time = duration * 0.3
            logger.info("Using fallback thumbnail time", time=optimal_time, duration=duration)
            return optimal_time

        except Exception as e:
            logger.warning("Failed to find optimal thumbnail time, using default", error=str(e))
            return 10.0  # Default to 10 seconds

    def create_preview_gif(
        self,
        video_path: str,
        start_time: float,
        duration: float = 3.0,
        output_path: Optional[str] = None,
        width: int = 240,
        height: int = 427,  # 9:16 aspect ratio
        fps: int = 10
    ) -> Optional[str]:
        """
        Create a preview GIF from video segment.

        Args:
            video_path: Path to source video
            start_time: Start time in seconds
            duration: GIF duration in seconds
            output_path: Optional output path for GIF
            width: GIF width
            height: GIF height
            fps: Frames per second for GIF

        Returns:
            Path to created GIF or None if failed
        """
        if self._is_mock_mode():
            return self._mock_create_preview_gif(video_path, start_time, duration, output_path)

        if output_path is None:
            output_path = tempfile.NamedTemporaryFile(suffix=".gif", delete=False).name

        try:
            # Create GIF with optimized settings
            cmd = [
                self.ffmpeg_path,
                "-ss", str(start_time),
                "-t", str(duration),
                "-i", video_path,
                "-vf", f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},fps={fps}",
                "-c:v", "gif",
                "-f", "gif",
                "-y",
                output_path
            ]

            logger.info(
                "Creating preview GIF",
                video_path=video_path,
                start_time=start_time,
                duration=duration,
                size=f"{width}x{height}"
            )

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info("Preview GIF created successfully", output_path=output_path)
                return output_path
            else:
                logger.error("GIF creation failed - no output file created")
                return None

        except subprocess.CalledProcessError as e:
            logger.error("FFmpeg GIF creation failed", error=str(e), stderr=e.stderr)
            return None
        except Exception as e:
            logger.error("Unexpected error during GIF creation", error=str(e))
            return None

    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        Get detailed video information using ffprobe.

        Args:
            video_path: Path to video file

        Returns:
            Dictionary with video metadata
        """
        if self._is_mock_mode():
            return self._mock_video_info(video_path)

        try:
            cmd = [
                self.ffprobe_path,
                "-v", "quiet",
                "-print_format", "json",
                "-show_streams",
                "-show_format",
                video_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)

            # Find video stream
            video_stream = None
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "video":
                    video_stream = stream
                    break

            if not video_stream:
                raise Exception("No video stream found")

            # Extract relevant information
            format_info = data.get("format", {})

            return {
                "width": int(video_stream.get("width", 0)),
                "height": int(video_stream.get("height", 0)),
                "duration": float(format_info.get("duration", 0)),
                "fps": self._parse_fps(video_stream.get("r_frame_rate", "30/1")),
                "codec": video_stream.get("codec_name"),
                "bitrate": int(format_info.get("bit_rate", 0)),
                "size": int(format_info.get("size", 0)),
                "format": format_info.get("format_name")
            }

        except subprocess.CalledProcessError as e:
            logger.error("FFprobe failed", error=str(e), stderr=e.stderr)
            return {}
        except json.JSONDecodeError as e:
            logger.error("Failed to parse ffprobe output", error=str(e))
            return {}
        except Exception as e:
            logger.error("Unexpected error getting video info", error=str(e))
            return {}

    def _parse_fps(self, fps_str: str) -> float:
        """Parse fps from fraction string"""
        try:
            if '/' in fps_str:
                num, den = fps_str.split('/')
                return float(num) / float(den)
            return float(fps_str)
        except:
            return 30.0

    def get_video_thumbnail_grid(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        tile_count: int = 9,
        width: int = 480,
        height: int = 854
    ) -> Optional[str]:
        """
        Create a thumbnail grid showing multiple frames from video.

        Args:
            video_path: Path to source video
            output_path: Optional output path
            tile_count: Number of thumbnails in grid (3x3 = 9)
            width: Output width
            height: Output height

        Returns:
            Path to thumbnail grid or None if failed
        """
        if self._is_mock_mode():
            return self._mock_thumbnail_grid(video_path, output_path)

        if output_path is None:
            output_path = tempfile.NamedTemporaryFile(suffix="_grid.jpg", delete=False).name

        try:
            # Calculate grid dimensions (e.g., 3x3 for 9 tiles)
            grid_size = int(tile_count ** 0.5)
            tile_width = width // grid_size
            tile_height = height // grid_size

            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-vf", f"fps=1/10,scale={tile_width}:{tile_height},tile={grid_size}x{grid_size}",
                "-vframes", "1",
                "-q:v", "2",
                "-y",
                output_path
            ]

            logger.info("Creating thumbnail grid", video_path=video_path, tiles=tile_count)

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info("Thumbnail grid created successfully", output_path=output_path)
                return output_path
            else:
                logger.error("Thumbnail grid creation failed")
                return None

        except subprocess.CalledProcessError as e:
            logger.error("FFmpeg thumbnail grid failed", error=str(e), stderr=e.stderr)
            return None

    # Mock methods for development
    def _mock_extract_thumbnail(self, video_path: str, timestamp: Optional[float], output_path: Optional[str]) -> str:
        """Mock thumbnail extraction for development"""
        if output_path is None:
            output_path = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False).name

        logger.info("Mock extracting thumbnail", video_path=video_path, timestamp=timestamp)
        Path(output_path).touch()
        return output_path

    def _mock_create_preview_gif(self, video_path: str, start_time: float, duration: float, output_path: Optional[str]) -> str:
        """Mock GIF creation for development"""
        if output_path is None:
            output_path = tempfile.NamedTemporaryFile(suffix=".gif", delete=False).name

        logger.info("Mock creating preview GIF", video_path=video_path, start_time=start_time, duration=duration)
        Path(output_path).touch()
        return output_path

    def _mock_video_info(self, video_path: str) -> Dict[str, Any]:
        """Mock video info for development"""
        return {
            "width": 1920,
            "height": 1080,
            "duration": 60.0,
            "fps": 30.0,
            "codec": "h264",
            "bitrate": 5000000,
            "size": 10 * 1024 * 1024,  # 10MB
            "format": "mp4"
        }

    def _mock_thumbnail_grid(self, video_path: str, output_path: Optional[str]) -> str:
        """Mock thumbnail grid for development"""
        if output_path is None:
            output_path = tempfile.NamedTemporaryFile(suffix="_grid.jpg", delete=False).name

        logger.info("Mock creating thumbnail grid", video_path=video_path)
        Path(output_path).touch()
        return output_path


# Global FFmpeg service instance
ffmpeg_service = FFmpegService()


def get_ffmpeg_service() -> FFmpegService:
    """Get the global FFmpeg service instance"""
    return ffmpeg_service