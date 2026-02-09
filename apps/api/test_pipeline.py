"""
Simple test script for the video processing pipeline.

Set MOCK_MODE=true to test without external services.

Usage:
    # In mock mode
    export MOCK_MODE=true
    python test_pipeline.py

    # With real services (requires API keys)
    export MOCK_MODE=false
    export DEEPGRAM_API_KEY=your_key
    export ANTHROPIC_API_KEY=your_key
    export AWS_ACCESS_KEY_ID=your_key
    export AWS_SECRET_ACCESS_KEY=your_key
    python test_pipeline.py
"""

import os
import asyncio
import structlog
from datetime import datetime

# Set environment for testing
os.environ["MOCK_MODE"] = "true"  # Change to "false" for real testing

from src.services.video_downloader import VideoDownloaderService
from src.services.transcription import TranscriptionService
from src.services.viral_detection import ViralDetectionService
from src.services.video_processor import VideoProcessorService
from src.services.subtitle_generator import SubtitleGeneratorService

# Configure logging for testing
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


async def test_video_pipeline():
    """Test the complete video processing pipeline"""
    logger.info("Starting video pipeline test", mock_mode=os.getenv("MOCK_MODE"))

    # Test URL
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll for testing

    try:
        # Stage 1: Download
        logger.info("Testing video download")
        downloader = VideoDownloaderService()
        s3_key, metadata = downloader.download(test_url)
        logger.info("Download completed", s3_key=s3_key, metadata=metadata)

        # Stage 2: Transcription
        logger.info("Testing transcription")
        transcription = TranscriptionService()

        # Create a dummy video file for transcription test
        import tempfile
        dummy_video = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        dummy_video.write(b"dummy video content")
        dummy_video.close()

        transcript = await transcription.transcribe(dummy_video.name)
        logger.info("Transcription completed", word_count=len(transcript.get("results", {}).get("channels", [{}])[0].get("alternatives", [{}])[0].get("words", [])))

        # Stage 3: Viral Detection
        logger.info("Testing viral detection")
        viral_detection = ViralDetectionService()
        viral_segments = viral_detection.detect_viral_segments(
            transcript,
            metadata.get("duration", 300),
            max_clips=3
        )
        logger.info("Viral detection completed", segments_count=len(viral_segments))

        # Stage 4: Video Processing
        logger.info("Testing video processing")
        video_processor = VideoProcessorService()

        for i, segment in enumerate(viral_segments[:1]):  # Test only first segment
            logger.info("Processing test segment", segment=segment)

            # Cut clip
            cut_path = video_processor.cut_clip(
                dummy_video.name,
                segment["start_time"],
                segment["end_time"]
            )
            logger.info("Clip cut", cut_path=cut_path)

            # Crop to portrait
            cropped_path = video_processor.crop_to_portrait(cut_path)
            logger.info("Clip cropped", cropped_path=cropped_path)

            # Stage 5: Subtitle Generation
            logger.info("Testing subtitle generation")
            subtitle_generator = SubtitleGeneratorService()

            # Generate subtitles
            subtitle_path = subtitle_generator.generate_subtitles(
                transcript,
                segment,
                style="hormozi"
            )
            logger.info("Subtitles generated", subtitle_path=subtitle_path)

            # Burn subtitles
            final_path = subtitle_generator.burn_subtitles(cropped_path, subtitle_path)
            logger.info("Subtitles burned", final_path=final_path)

            # Cleanup test files
            for path in [cut_path, cropped_path, subtitle_path, final_path]:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except:
                    pass

        # Cleanup
        os.remove(dummy_video.name)

        logger.info("Pipeline test completed successfully")

    except Exception as e:
        logger.error("Pipeline test failed", error=str(e))
        raise


async def test_individual_services():
    """Test each service individually"""
    logger.info("Testing individual services")

    # Test Video Downloader
    logger.info("Testing VideoDownloaderService")
    downloader = VideoDownloaderService()
    styles = downloader._is_mock_mode()
    logger.info("VideoDownloader mock mode", is_mock=styles)

    # Test Transcription Service
    logger.info("Testing TranscriptionService")
    transcription = TranscriptionService()
    is_mock = transcription._is_mock_mode()
    logger.info("Transcription mock mode", is_mock=is_mock)

    # Test Viral Detection
    logger.info("Testing ViralDetectionService")
    viral_detection = ViralDetectionService()
    is_mock = viral_detection._is_mock_mode()
    logger.info("ViralDetection mock mode", is_mock=is_mock)

    # Test Video Processor
    logger.info("Testing VideoProcessorService")
    video_processor = VideoProcessorService()
    is_mock = video_processor._is_mock_mode()
    logger.info("VideoProcessor mock mode", is_mock=is_mock)

    # Test Subtitle Generator
    logger.info("Testing SubtitleGeneratorService")
    subtitle_generator = SubtitleGeneratorService()
    styles = subtitle_generator.get_available_styles()
    logger.info("Available subtitle styles", styles=list(styles.keys()))


if __name__ == "__main__":
    print("Testing Video Processing Pipeline")
    print(f"Mock Mode: {os.getenv('MOCK_MODE', 'false')}")
    print("=" * 50)

    # Test individual services first
    asyncio.run(test_individual_services())

    print("\n" + "=" * 50)
    print("Testing complete pipeline")

    # Test complete pipeline
    asyncio.run(test_video_pipeline())

    print("All tests completed!")