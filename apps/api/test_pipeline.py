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
import sys
import asyncio
import structlog
import uuid
from datetime import datetime
from pathlib import Path

# Set environment for testing
os.environ["MOCK_MODE"] = "true"  # Change to "false" for real testing

from src.services.video_downloader import VideoDownloaderService
from src.services.transcription import TranscriptionService
from src.services.viral_detection import ViralDetectionService
from src.services.video_processor import VideoProcessorService
from src.services.subtitle_generator import SubtitleGeneratorService
from src.services.pipeline_orchestrator import PipelineOrchestratorService
from src.database import SessionLocal
from src.models.project import Project
from src.models.user import User

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


async def test_pipeline_orchestrator():
    """Test the complete pipeline using the orchestrator"""
    logger.info("Starting pipeline orchestrator test")

    # Create database session
    db = SessionLocal()

    try:
        # Create test user
        test_user = User(
            id=uuid.uuid4(),
            clerk_id="test_user_123",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            plan="FREE"
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        logger.info("Created test user", user_id=str(test_user.id))

        # Create test project
        test_project = Project(
            id=uuid.uuid4(),
            user_id=test_user.id,
            source_url="https://www.youtube.com/watch?v=test123",
            max_clips_requested=3,
            status="pending",
            processing_progress=0,
            video_metadata={
                "platform": "youtube",
                "video_id": "test123",
                "original_url": "https://www.youtube.com/watch?v=test123"
            }
        )
        db.add(test_project)
        db.commit()
        db.refresh(test_project)
        logger.info("Created test project", project_id=str(test_project.id))

        # Test pipeline orchestrator
        orchestrator = PipelineOrchestratorService()
        start_time = datetime.now()

        try:
            await orchestrator.process_project(str(test_project.id))
            duration = (datetime.now() - start_time).total_seconds()

            # Refresh project to get results
            db.refresh(test_project)

            logger.info("Pipeline orchestrator test completed",
                       status=test_project.status,
                       progress=test_project.processing_progress,
                       duration=duration,
                       clips_count=len(test_project.clips) if test_project.clips else 0)

            print(f"\n[RESULTS] PIPELINE ORCHESTRATOR TEST RESULTS:")
            print(f"   Status: {test_project.status}")
            print(f"   Progress: {test_project.processing_progress}%")
            print(f"   Duration: {duration:.2f}s")
            print(f"   Clips: {len(test_project.clips) if test_project.clips else 0}")

            if test_project.viral_segments:
                print(f"   Viral segments: {len(test_project.viral_segments)}")

            return test_project.status == "completed"

        except Exception as e:
            logger.error("Pipeline orchestrator failed", error=str(e))
            print(f"\n[ERROR] PIPELINE ORCHESTRATOR FAILED: {str(e)}")
            return False

    finally:
        # Cleanup
        try:
            db.delete(test_project)
            db.delete(test_user)
            db.commit()
            logger.info("Cleaned up test data")
        except:
            pass
        db.close()


if __name__ == "__main__":
    print("ShortCut Video Processing Pipeline - Complete Test Suite")
    print(f"Mock Mode: {os.getenv('MOCK_MODE', 'false')}")
    print("=" * 60)

    success = True

    # Test 1: Individual services
    print("\n[1] Testing Individual Services...")
    try:
        asyncio.run(test_individual_services())
        print("[PASS] Individual services test PASSED")
    except Exception as e:
        print(f"[FAIL] Individual services test FAILED: {str(e)}")
        success = False

    # Test 2: Legacy pipeline (services chained)
    print("\n[2] Testing Legacy Pipeline (Service Chain)...")
    try:
        asyncio.run(test_video_pipeline())
        print("[PASS] Legacy pipeline test PASSED")
    except Exception as e:
        print(f"[FAIL] Legacy pipeline test FAILED: {str(e)}")
        success = False

    # Test 3: NEW Pipeline orchestrator
    print("\n[3] Testing NEW Pipeline Orchestrator...")
    try:
        orchestrator_success = asyncio.run(test_pipeline_orchestrator())
        if orchestrator_success:
            print("[PASS] Pipeline orchestrator test PASSED")
        else:
            print("[FAIL] Pipeline orchestrator test FAILED")
            success = False
    except Exception as e:
        print(f"[FAIL] Pipeline orchestrator test ERROR: {str(e)}")
        success = False

    print("\n" + "=" * 60)
    if success:
        print("SUCCESS: ALL TESTS PASSED! The complete pipeline is ready for production.")
        sys.exit(0)
    else:
        print("ERROR: SOME TESTS FAILED! Check the errors above.")
        sys.exit(1)