import os
import tempfile
import subprocess
import structlog
import cv2
import numpy as np
from typing import Dict, Any, Tuple, Optional
from pathlib import Path
import mediapipe as mp

from ..config import settings

logger = structlog.get_logger()


class VideoProcessorService:
    """
    Service for video processing: cutting clips and cropping to 9:16 with face detection.

    Critères PRD F4-07: Pour chaque segment : découpe avec FFmpeg (timestamps précis), recadrage 9:16 avec détection faciale MediaPipe
    """

    def _is_mock_mode(self) -> bool:
        """Check if running in mock mode for development"""
        return os.getenv("MOCK_MODE", "false").lower() == "true"

    def __init__(self):
        if not self._is_mock_mode():
            try:
                self.mp_face_detection = mp.solutions.face_detection
                self.mp_drawing = mp.solutions.drawing_utils
            except:
                logger.warning("MediaPipe face detection not available, falling back to mock mode")
                self.mp_face_detection = None
                self.mp_drawing = None
        else:
            self.mp_face_detection = None
            self.mp_drawing = None

    def cut_clip(
        self,
        source_path: str,
        start_time: float,
        end_time: float,
        output_path: str = None
    ) -> str:
        """
        Cut a video clip from source video.

        Args:
            source_path: Path to source video
            start_time: Start time in seconds
            end_time: End time in seconds
            output_path: Optional output path

        Returns:
            Path to cut clip
        """
        if self._is_mock_mode():
            return self._mock_cut_clip(source_path, start_time, end_time, output_path)

        if output_path is None:
            output_path = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name

        try:
            duration = end_time - start_time

            # FFmpeg command for precise cutting
            cmd = [
                "ffmpeg",
                "-ss", str(start_time),  # Seek to start time
                "-i", source_path,  # Input file
                "-t", str(duration),  # Duration
                "-c", "copy",  # Copy streams without re-encoding (faster)
                "-avoid_negative_ts", "make_zero",  # Handle timestamp issues
                "-y",  # Overwrite output
                output_path
            ]

            logger.info(
                "Cutting video clip",
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                cmd=" ".join(cmd)
            )

            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)

            logger.info("Video clip cut successfully", output_path=output_path)
            return output_path

        except subprocess.CalledProcessError as e:
            logger.error("Video cutting failed", error=str(e), stderr=e.stderr)
            raise Exception(f"Failed to cut video clip: {str(e)}")

    def crop_to_portrait(
        self,
        input_path: str,
        output_path: str = None,
        target_aspect_ratio: float = 9/16
    ) -> str:
        """
        Crop video to portrait format (9:16) with smart face detection.

        Args:
            input_path: Path to input video
            output_path: Optional output path
            target_aspect_ratio: Target aspect ratio (default 9:16)

        Returns:
            Path to cropped video
        """
        if self._is_mock_mode():
            return self._mock_crop_to_portrait(input_path, output_path)

        if output_path is None:
            output_path = tempfile.NamedTemporaryFile(suffix="_cropped.mp4", delete=False).name

        try:
            # Get video dimensions
            video_info = self._get_video_info(input_path)
            width = video_info["width"]
            height = video_info["height"]
            current_aspect = width / height

            logger.info(
                "Starting portrait crop",
                input_path=input_path,
                current_size=f"{width}x{height}",
                current_aspect=current_aspect,
                target_aspect=target_aspect_ratio
            )

            # If already portrait or close to target, minimal cropping needed
            if abs(current_aspect - target_aspect_ratio) < 0.1:
                logger.info("Video already close to target aspect ratio")
                return self._simple_crop(input_path, output_path, width, height, target_aspect_ratio)

            # For landscape videos, use smart face detection
            if current_aspect > 1:  # Landscape
                crop_region = self._detect_optimal_crop_region(input_path, target_aspect_ratio)
            else:  # Portrait but wrong ratio
                crop_region = self._center_crop_region(width, height, target_aspect_ratio)

            # Apply crop using FFmpeg
            return self._apply_crop(input_path, output_path, crop_region)

        except Exception as e:
            logger.error("Portrait cropping failed", error=str(e))
            raise Exception(f"Failed to crop video: {str(e)}")

    def _get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get video information using ffprobe"""
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_streams",
                "-select_streams", "v:0",
                video_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
            import json
            data = json.loads(result.stdout)

            if not data.get("streams"):
                raise Exception("No video stream found")

            stream = data["streams"][0]

            return {
                "width": int(stream["width"]),
                "height": int(stream["height"]),
                "duration": float(stream.get("duration", 0)),
                "fps": self._parse_fps(stream.get("r_frame_rate", "30/1"))
            }

        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error("Failed to get video info", error=str(e))
            raise Exception(f"Could not read video info: {str(e)}")

    def _parse_fps(self, fps_str: str) -> float:
        """Parse fps from fraction string"""
        try:
            if '/' in fps_str:
                num, den = fps_str.split('/')
                return float(num) / float(den)
            return float(fps_str)
        except:
            return 30.0

    def _detect_optimal_crop_region(
        self,
        video_path: str,
        target_aspect_ratio: float
    ) -> Dict[str, int]:
        """
        Detect optimal crop region using face detection.
        Samples multiple frames to find best crop area.
        """
        try:
            cap = cv2.VideoCapture(video_path)

            if not cap.isOpened():
                raise Exception("Could not open video file")

            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            logger.info("Analyzing video for face detection", width=width, height=height, frames=frame_count)

            # Calculate target crop dimensions
            target_width = int(height * target_aspect_ratio)
            if target_width > width:
                # Video is too narrow, crop height instead
                target_height = int(width / target_aspect_ratio)
                target_width = width
            else:
                target_height = height

            # Sample frames for face detection
            face_regions = []
            sample_count = min(10, frame_count // 10)  # Sample up to 10 frames

            with self.mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5) as face_detection:
                for i in range(sample_count):
                    frame_pos = (i * frame_count) // sample_count
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)

                    ret, frame = cap.read()
                    if not ret:
                        continue

                    # Convert BGR to RGB for MediaPipe
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = face_detection.process(rgb_frame)

                    if results.detections:
                        for detection in results.detections:
                            # Get face bounding box
                            bbox = detection.location_data.relative_bounding_box
                            x = int(bbox.xmin * width)
                            y = int(bbox.ymin * height)
                            w = int(bbox.width * width)
                            h = int(bbox.height * height)

                            # Calculate face center
                            face_center_x = x + w // 2
                            face_center_y = y + h // 2

                            face_regions.append({
                                "center_x": face_center_x,
                                "center_y": face_center_y,
                                "confidence": detection.score[0]
                            })

            cap.release()

            if face_regions:
                # Calculate weighted center of all detected faces
                total_weight = sum(face["confidence"] for face in face_regions)

                weighted_center_x = sum(
                    face["center_x"] * face["confidence"] for face in face_regions
                ) / total_weight

                weighted_center_y = sum(
                    face["center_y"] * face["confidence"] for face in face_regions
                ) / total_weight

                # Calculate crop region centered around face(s)
                crop_x = max(0, int(weighted_center_x - target_width // 2))
                crop_y = max(0, int(weighted_center_y - target_height // 2))

                # Ensure crop region stays within bounds
                if crop_x + target_width > width:
                    crop_x = width - target_width
                if crop_y + target_height > height:
                    crop_y = height - target_height

                logger.info(
                    "Face-based crop region calculated",
                    faces_detected=len(face_regions),
                    crop_region=f"{crop_x},{crop_y},{target_width}x{target_height}"
                )

            else:
                # No faces detected, use center crop
                logger.info("No faces detected, using center crop")
                crop_x = (width - target_width) // 2
                crop_y = (height - target_height) // 2

            return {
                "x": crop_x,
                "y": crop_y,
                "width": target_width,
                "height": target_height
            }

        except Exception as e:
            logger.error("Face detection failed, falling back to center crop", error=str(e))
            return self._center_crop_region(width, height, target_aspect_ratio)

    def _center_crop_region(self, width: int, height: int, target_aspect_ratio: float) -> Dict[str, int]:
        """Calculate center crop region"""
        # Calculate target dimensions
        target_width = int(height * target_aspect_ratio)
        if target_width > width:
            target_height = int(width / target_aspect_ratio)
            target_width = width
        else:
            target_height = height

        crop_x = (width - target_width) // 2
        crop_y = (height - target_height) // 2

        return {
            "x": crop_x,
            "y": crop_y,
            "width": target_width,
            "height": target_height
        }

    def _simple_crop(self, input_path: str, output_path: str, width: int, height: int, target_aspect_ratio: float) -> str:
        """Apply simple center crop for videos already close to target ratio"""
        crop_region = self._center_crop_region(width, height, target_aspect_ratio)
        return self._apply_crop(input_path, output_path, crop_region)

    def _apply_crop(self, input_path: str, output_path: str, crop_region: Dict[str, int]) -> str:
        """Apply crop using FFmpeg"""
        try:
            cmd = [
                "ffmpeg",
                "-i", input_path,
                "-filter:v", f"crop={crop_region['width']}:{crop_region['height']}:{crop_region['x']}:{crop_region['y']}",
                "-c:a", "copy",  # Copy audio without re-encoding
                "-y",
                output_path
            ]

            logger.info(
                "Applying crop",
                crop_filter=f"crop={crop_region['width']}:{crop_region['height']}:{crop_region['x']}:{crop_region['y']}",
                cmd=" ".join(cmd)
            )

            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)

            logger.info("Video cropped successfully", output_path=output_path)
            return output_path

        except subprocess.CalledProcessError as e:
            logger.error("FFmpeg crop failed", error=str(e), stderr=e.stderr)
            raise Exception(f"Failed to apply crop: {str(e)}")

    def _mock_cut_clip(self, source_path: str, start_time: float, end_time: float, output_path: str = None) -> str:
        """Mock clip cutting for development"""
        if output_path is None:
            output_path = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name

        logger.info(
            "Mock cutting clip",
            start_time=start_time,
            end_time=end_time,
            output_path=output_path
        )

        # In mock mode, just create an empty file
        Path(output_path).touch()
        return output_path

    def _mock_crop_to_portrait(self, input_path: str, output_path: str = None) -> str:
        """Mock portrait cropping for development"""
        if output_path is None:
            output_path = tempfile.NamedTemporaryFile(suffix="_cropped.mp4", delete=False).name

        logger.info("Mock cropping to portrait", input_path=input_path, output_path=output_path)

        # In mock mode, just create an empty file
        Path(output_path).touch()
        return output_path