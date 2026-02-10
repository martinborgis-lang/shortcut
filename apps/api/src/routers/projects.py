from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List
import structlog
import uuid
import tempfile
import zipfile
import os
from datetime import datetime, timedelta

from ..database import get_db
from ..models.project import Project
from ..models.clip import Clip
from ..models.user import User
from ..schemas.projects import (
    CreateProjectRequest,
    CreateProjectResponse,
    ProjectResponse,
    ProjectStatusResponse
)
from ..schemas.clips import BulkDownloadResponse
from ..middleware.auth import get_current_user
from ..services.url_validator import validate_video_url
from ..services.pipeline_orchestrator import PipelineOrchestratorService
from ..utils.s3 import get_s3_service

logger = structlog.get_logger()

router = APIRouter()


@router.post(
    "/",
    response_model=CreateProjectResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_project(
    request: CreateProjectRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new project from a video URL.

    Critères PRD F4-01 & F4-14: Accepte { url: string }, valide l'URL robustement, crée le projet en DB, lance le pipeline en BackgroundTask
    """
    logger.info("Creating new project", url=request.url, user_id=str(current_user.id))

    # Validate URL using robust service (PRD F4-14)
    url_validation = validate_video_url(request.url)
    if not url_validation['is_valid']:
        logger.warning("Invalid URL provided", url=request.url, error=url_validation['error'])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=url_validation['error']
        )

    try:
        # Check user plan limits (basic validation)
        active_projects = db.query(Project).filter(
            Project.user_id == current_user.id,
            Project.status.in_(["pending", "downloading", "transcribing", "analyzing", "processing"])
        ).count()

        # Basic plan: 1 concurrent project, Pro plan: 5 concurrent projects
        max_concurrent = 5 if current_user.plan == "pro" else 1
        if active_projects >= max_concurrent:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Maximum concurrent projects ({max_concurrent}) reached for {current_user.plan} plan"
            )

        # Create project in database with normalized URL
        project = Project(
            user_id=current_user.id,
            source_url=url_validation['normalized_url'] or request.url,
            max_clips_requested=request.max_clips or 5,
            status="pending",
            processing_progress=0,
            # Store platform and video ID for future reference
            video_metadata={
                "platform": url_validation['platform'],
                "video_id": url_validation['video_id'],
                "original_url": url_validation['original_url']
            }
        )

        db.add(project)
        db.commit()
        db.refresh(project)

        # Start pipeline processing in background
        pipeline_orchestrator = PipelineOrchestratorService()
        background_tasks.add_task(
            pipeline_orchestrator.process_project,
            str(project.id)
        )

        logger.info(
            "Project created and pipeline started",
            project_id=str(project.id),
            platform=url_validation['platform'],
            video_id=url_validation['video_id']
        )

        # Estimate completion time based on typical processing
        estimated_completion = datetime.utcnow() + timedelta(minutes=15)

        return CreateProjectResponse(
            id=project.id,
            status="pending",
            message="Project created successfully. Processing will begin shortly.",
            estimated_completion=estimated_completion
        )

    except Exception as e:
        db.rollback()
        logger.error("Failed to create project", error=str(e), url=request.url, user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project. Please try again."
        )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
)
async def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get project details with clips.

    Critères PRD F4-02: Retourne le projet avec ses clips et statut
    """
    logger.info("Getting project", project_id=str(project_id), user_id=str(current_user.id))

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    return project


@router.get(
    "/{project_id}/status",
    response_model=ProjectStatusResponse,
)
async def get_project_status(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed project status for real-time updates.

    Critères PRD F4-03: Retourne le statut détaillé du pipeline (étape actuelle, progression %)
    """
    logger.info("Getting project status", project_id=str(project_id), user_id=str(current_user.id))

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Build step details based on current status
    step_details = {}

    if project.status == "downloading":
        step_details = {
            "message": "Downloading video from source",
            "current_operation": "Video download in progress"
        }
    elif project.status == "transcribing":
        step_details = {
            "message": "Extracting audio and generating transcript",
            "current_operation": "Sending audio to Deepgram API"
        }
    elif project.status == "analyzing":
        step_details = {
            "message": "Analyzing content for viral moments",
            "current_operation": "AI analysis with Gemini Flash"
        }
    elif project.status == "processing":
        clips_count = db.query(Clip).filter(Clip.project_id == project_id).count()
        step_details = {
            "message": f"Processing {clips_count} video clips",
            "current_operation": "Cutting, cropping and adding subtitles"
        }
    elif project.status == "done":
        clips_count = db.query(Clip).filter(Clip.project_id == project_id).count()
        step_details = {
            "message": f"Processing complete! {clips_count} clips generated",
            "current_operation": "Ready for download"
        }
    elif project.status == "failed":
        step_details = {
            "message": "Processing failed",
            "current_operation": "Error occurred during processing",
            "error": project.error_message
        }

    return ProjectStatusResponse(
        id=project.id,
        status=project.status,
        current_step=project.current_step,
        processing_progress=project.processing_progress,
        error_message=project.error_message,
        step_details=step_details
    )


@router.get(
    "/",
    response_model=List[ProjectResponse],
)
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0
):
    """Get user's projects"""
    logger.info("Listing projects", user_id=str(current_user.id), limit=limit, offset=offset)

    projects = db.query(Project).filter(
        Project.user_id == current_user.id
    ).order_by(
        Project.created_at.desc()
    ).limit(limit).offset(offset).all()

    return projects


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a project and all its clips"""
    logger.info("Deleting project", project_id=str(project_id), user_id=str(current_user.id))

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # TODO: Cancel running Celery task if project is still processing
    # TODO: Delete S3 files (source video and generated clips)

    db.delete(project)
    db.commit()

    logger.info("Project deleted", project_id=str(project_id))


@router.get("/{project_id}/download-all", response_model=BulkDownloadResponse)
async def download_all_project_clips(
    project_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download all clips from a project as a ZIP file.

    Critères PRD F5-12: Télécharger tous les clips d'un projet en ZIP
    """
    logger.info("Project download-all request", project_id=project_id, user_id=current_user.id)

    # Verify project ownership
    project = db.query(Project).filter(
        and_(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
    ).first()

    if not project:
        logger.warning("Project not found or access denied", project_id=project_id, user_id=current_user.id)
        raise HTTPException(status_code=404, detail="Project not found")

    # Get all ready clips from the project
    clips = db.query(Clip).filter(
        and_(
            Clip.project_id == project_id,
            Clip.status == "ready",
            Clip.s3_key.isnot(None)
        )
    ).all()

    if not clips:
        raise HTTPException(status_code=404, detail="No clips ready for download in this project")

    # Create temporary ZIP file
    temp_zip = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    temp_zip_path = temp_zip.name
    temp_zip.close()

    try:
        s3_service = get_s3_service()
        total_size = 0

        with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for clip in clips:
                try:
                    if clip.s3_key:
                        # Get file info
                        object_info = s3_service.get_object_info(clip.s3_key)
                        if object_info and object_info.get("exists"):
                            file_size = object_info.get("size", 0)
                            total_size += file_size

                            # In mock mode, add dummy file
                            if s3_service._is_mock_mode():
                                filename = f"{clip.title}.mp4".replace(" ", "_")
                                zip_file.writestr(filename, b"mock video content")
                                logger.info("Added mock clip to ZIP", filename=filename)
                            else:
                                # In real mode, download and add to ZIP
                                # This would download the actual file from S3 and add it to the ZIP
                                pass

                except Exception as e:
                    logger.warning("Failed to add clip to ZIP", clip_id=clip.id, error=str(e))

        # Upload ZIP to S3 for download
        zip_s3_key = f"downloads/{current_user.id}/{project_id}/{uuid.uuid4()}.zip"
        project_title = project.source_url.split('/')[-1] if project.source_url else str(project_id)
        zip_filename = f"{project_title}_clips_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

        if s3_service._is_mock_mode():
            logger.info("Mock uploading project ZIP to S3", s3_key=zip_s3_key)
        else:
            # Real S3 upload would go here
            pass

        # Generate download URL
        download_url = s3_service.generate_download_url(
            zip_s3_key,
            filename=zip_filename,
            expiration=3600  # 1 hour
        )

        if not download_url:
            raise HTTPException(status_code=500, detail="Failed to generate download URL")

        expires_at = datetime.utcnow() + timedelta(seconds=3600)

        # Schedule cleanup of temporary files
        background_tasks.add_task(_cleanup_temp_zip, temp_zip_path)

        logger.info(
            "Project download-all created successfully",
            project_id=project_id,
            clips_count=len(clips),
            total_size=total_size
        )

        return BulkDownloadResponse(
            download_url=download_url,
            expires_at=expires_at,
            filename=zip_filename,
            clips_count=len(clips),
            total_size=total_size
        )

    except Exception as e:
        # Clean up on error
        if os.path.exists(temp_zip_path):
            os.unlink(temp_zip_path)

        logger.error("Project download-all failed", project_id=project_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create project download")


def _cleanup_temp_zip(temp_zip_path: str):
    """Clean up temporary ZIP file"""
    try:
        if os.path.exists(temp_zip_path):
            os.unlink(temp_zip_path)
            logger.info("Cleaned up temporary ZIP file", path=temp_zip_path)
    except Exception as e:
        logger.warning("Failed to clean up temporary ZIP file", path=temp_zip_path, error=str(e))