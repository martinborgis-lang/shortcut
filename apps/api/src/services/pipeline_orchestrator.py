import asyncio
import structlog
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from ..models.project import Project
from ..models.clip import Clip
from ..database import SessionLocal
from .video_downloader import VideoDownloaderService
from .transcription import TranscriptionService
from .viral_detection import ViralDetectionService
from .video_processor import VideoProcessorService
from .subtitle_generator import SubtitleGeneratorService

logger = structlog.get_logger()


class PipelineOrchestratorService:
    """
    Service orchestrating the complete video processing pipeline.

    Pipeline steps:
    1. Download video from URL
    2. Extract audio and transcribe with Deepgram
    3. Detect viral segments with Gemini Flash
    4. Cut and process clips with FFmpeg
    5. Generate subtitles for each clip

    MVP: Uses BackgroundTasks instead of Celery for simplicity
    """

    def __init__(self):
        self.video_downloader = VideoDownloaderService()
        self.transcription = TranscriptionService()
        self.viral_detection = ViralDetectionService()
        self.video_processor = VideoProcessorService()
        self.subtitle_generator = SubtitleGeneratorService()

    async def process_project(self, project_id: str) -> None:
        """
        Process a complete project through the pipeline.

        Args:
            project_id: UUID of the project to process
        """
        db = SessionLocal()
        project = None

        try:
            # Get project from database
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise Exception(f"Project {project_id} not found")

            logger.info(
                "Starting pipeline processing",
                project_id=project_id,
                source_url=project.source_url
            )

            # Step 1: Download video
            await self._step_1_download(db, project)

            # Step 2: Transcribe audio
            await self._step_2_transcribe(db, project)

            # Step 3: Detect viral segments
            await self._step_3_viral_detection(db, project)

            # Step 4: Process clips
            await self._step_4_process_clips(db, project)

            # Mark project as completed
            project.status = "completed"
            project.current_step = "completed"
            project.processing_progress = 100
            project.completed_at = datetime.utcnow()
            db.commit()

            logger.info(
                "Pipeline processing completed successfully",
                project_id=project_id,
                clips_generated=len(project.clips)
            )

        except Exception as e:
            logger.error(
                "Pipeline processing failed",
                project_id=project_id,
                error=str(e)
            )

            if project:
                project.status = "failed"
                project.error_message = str(e)
                db.commit()

            raise e

        finally:
            db.close()

    async def _step_1_download(self, db, project: Project) -> None:
        """Step 1: Download video from URL"""
        logger.info("Step 1: Downloading video", project_id=project.id)

        project.status = "processing"
        project.current_step = "downloading"
        project.processing_progress = 10
        db.commit()

        try:
            # Download video
            local_path, metadata = self.video_downloader.download(project.source_url)

            # Validate duration limits
            duration = metadata.get('duration', 0)
            self.video_downloader.validate_duration_limit(duration, project.user.plan)

            # Update project with video info
            project.source_filename = Path(local_path).name
            project.source_size = metadata.get('size', 0)
            project.source_duration = duration
            project.video_metadata = metadata
            project.source_s3_key = local_path  # Store local path in s3_key field for now
            project.processing_progress = 20
            db.commit()

            logger.info(
                "Video download completed",
                project_id=project.id,
                local_path=local_path,
                duration=duration
            )

        except Exception as e:
            logger.error("Video download failed", project_id=project.id, error=str(e))
            raise Exception(f"Download failed: {str(e)}")

    async def _step_2_transcribe(self, db, project: Project) -> None:
        """Step 2: Transcribe audio with Deepgram"""
        logger.info("Step 2: Transcribing audio", project_id=project.id)

        project.current_step = "transcribing"
        project.processing_progress = 30
        db.commit()

        try:
            # Transcribe video
            transcript = await self.transcription.transcribe(project.source_s3_key)

            # Store transcript in project
            project.transcript_json = transcript
            project.processing_progress = 50
            db.commit()

            logger.info(
                "Transcription completed",
                project_id=project.id,
                confidence=self.transcription._get_average_confidence(transcript)
            )

        except Exception as e:
            logger.error("Transcription failed", project_id=project.id, error=str(e))
            raise Exception(f"Transcription failed: {str(e)}")

    async def _step_3_viral_detection(self, db, project: Project) -> None:
        """Step 3: Detect viral segments with Gemini Flash"""
        logger.info("Step 3: Detecting viral segments", project_id=project.id)

        project.current_step = "analyzing"
        project.processing_progress = 60
        db.commit()

        try:
            # Detect viral segments
            viral_segments = self.viral_detection.detect_viral_segments(
                project.transcript_json,
                project.source_duration,
                project.max_clips_requested or 5
            )

            # Store viral segments
            project.viral_segments = viral_segments
            project.processing_progress = 70
            db.commit()

            logger.info(
                "Viral detection completed",
                project_id=project.id,
                segments_found=len(viral_segments)
            )

        except Exception as e:
            logger.error("Viral detection failed", project_id=project.id, error=str(e))
            raise Exception(f"Viral detection failed: {str(e)}")

    async def _step_4_process_clips(self, db, project: Project) -> None:
        """Step 4: Process all clips (cut video + generate subtitles)"""
        logger.info("Step 4: Processing clips", project_id=project.id)

        project.current_step = "generating_clips"
        project.processing_progress = 80
        db.commit()

        try:
            clips_created = 0
            viral_segments = project.viral_segments or []

            for i, segment in enumerate(viral_segments):
                logger.info(
                    "Processing clip",
                    project_id=project.id,
                    clip_index=i + 1,
                    total_clips=len(viral_segments)
                )

                # Create clip in database
                clip = Clip(
                    project_id=project.id,
                    title=segment.get('title', f'Clip {i + 1}'),
                    description=segment.get('reason', ''),
                    start_time=segment['start_time'],
                    end_time=segment['end_time'],
                    duration=segment['end_time'] - segment['start_time'],
                    viral_score=segment.get('virality_score', 0),
                    reason=segment.get('reason', ''),
                    hook=segment.get('hook', ''),
                    status="processing"
                )
                db.add(clip)
                db.flush()  # Get clip ID

                try:
                    # Cut video clip
                    clip_path = self.video_processor.cut_clip(
                        project.source_s3_key,  # local path
                        segment['start_time'],
                        segment['end_time']
                    )

                    # Generate subtitles
                    subtitle_path = self.subtitle_generator.generate_subtitles(
                        project.transcript_json,
                        segment,
                        style="hormozi"  # Default style
                    )

                    # Burn subtitles into video
                    final_clip_path = self.subtitle_generator.burn_subtitles(
                        clip_path,
                        subtitle_path
                    )

                    # Update clip with paths
                    clip.video_url = self.video_downloader.get_video_url(final_clip_path)
                    clip.s3_key = final_clip_path  # Store local path
                    clip.status = "ready"
                    clips_created += 1

                    # Clean up temporary files
                    if clip_path != final_clip_path and Path(clip_path).exists():
                        Path(clip_path).unlink()
                    if Path(subtitle_path).exists():
                        Path(subtitle_path).unlink()

                    logger.info(
                        "Clip processed successfully",
                        project_id=project.id,
                        clip_id=clip.id,
                        clip_path=final_clip_path
                    )

                except Exception as clip_error:
                    logger.error(
                        "Clip processing failed",
                        project_id=project.id,
                        clip_index=i + 1,
                        error=str(clip_error)
                    )
                    clip.status = "failed"
                    clip.error_message = str(clip_error)

                # Update progress
                progress = 80 + (10 * (i + 1) / len(viral_segments))
                project.processing_progress = min(95, int(progress))
                db.commit()

            logger.info(
                "All clips processed",
                project_id=project.id,
                clips_created=clips_created,
                total_clips=len(viral_segments)
            )

        except Exception as e:
            logger.error("Clip processing failed", project_id=project.id, error=str(e))
            raise Exception(f"Clip processing failed: {str(e)}")

    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get current status of project processing"""
        db = SessionLocal()
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"error": "Project not found"}

            return {
                "project_id": project_id,
                "status": project.status,
                "current_step": project.current_step,
                "progress": project.processing_progress,
                "error_message": project.error_message,
                "clips_count": len(project.clips) if project.clips else 0
            }
        finally:
            db.close()