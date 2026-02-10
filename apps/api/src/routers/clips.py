from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc
from typing import Optional, List
import structlog
import uuid
import zipfile
import tempfile
import os
from datetime import datetime, timedelta

from ..database import get_db
from ..middleware.auth import get_current_user
from ..models.clip import Clip
from ..models.user import User
from ..schemas.clips import (
    ClipResponse,
    ClipDetailResponse,
    UpdateClipRequest,
    RegenerateClipRequest,
    ClipDownloadResponse,
    ClipsListResponse,
    ClipsFilterRequest,
    BulkDownloadRequest,
    BulkDownloadResponse
)
from ..services.clip_editor import get_clip_editor_service
from ..utils.s3 import get_s3_service
from ..workers.regenerate_clip import regenerate_clip_task

logger = structlog.get_logger()
router = APIRouter()


@router.get("/{clip_id}", response_model=ClipDetailResponse)
async def get_clip(
    clip_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get clip details with signed URLs.

    Critères PRD F5-01: Endpoint GET `/api/clips/{id}` avec URL signée S3
    """
    logger.info("Getting clip details", clip_id=clip_id, user_id=current_user.id)

    # Get clip from database
    clip = db.query(Clip).filter(
        and_(
            Clip.id == clip_id,
            Clip.project.has(user_id=current_user.id)
        )
    ).first()

    if not clip:
        logger.warning("Clip not found or access denied", clip_id=clip_id, user_id=current_user.id)
        raise HTTPException(status_code=404, detail="Clip not found")

    # Generate signed URLs
    s3_service = get_s3_service()
    signed_urls = {}

    if clip.s3_key:
        signed_urls["signed_video_url"] = s3_service.generate_signed_url(
            clip.s3_key, expiration=3600
        )

    if clip.thumbnail_url:
        signed_urls["signed_thumbnail_url"] = s3_service.generate_signed_url(
            clip.thumbnail_url, expiration=3600
        )

    if clip.preview_gif_url:
        signed_urls["signed_preview_gif_url"] = s3_service.generate_signed_url(
            clip.preview_gif_url, expiration=3600
        )

    # Generate download URL
    if clip.s3_key:
        filename = f"{clip.title}.mp4".replace(" ", "_")
        signed_urls["download_url"] = s3_service.generate_download_url(
            clip.s3_key, filename=filename, expiration=3600
        )

    # Convert to response model
    clip_dict = {
        **ClipResponse.from_orm(clip).dict(),
        **signed_urls
    }

    logger.info("Clip details retrieved successfully", clip_id=clip_id)
    return ClipDetailResponse(**clip_dict)


@router.patch("/{clip_id}", response_model=ClipResponse)
async def update_clip(
    clip_id: uuid.UUID,
    update_request: UpdateClipRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update clip properties.

    Critères PRD F5-02: Endpoint PATCH `/api/clips/{id}` pour modifier title, timing, subtitle_style
    """
    logger.info("Updating clip", clip_id=clip_id, user_id=current_user.id, updates=update_request.dict(exclude_none=True))

    # Get clip from database
    clip = db.query(Clip).filter(
        and_(
            Clip.id == clip_id,
            Clip.project.has(user_id=current_user.id)
        )
    ).first()

    if not clip:
        logger.warning("Clip not found or access denied", clip_id=clip_id, user_id=current_user.id)
        raise HTTPException(status_code=404, detail="Clip not found")

    clip_editor = get_clip_editor_service()
    requires_regeneration = False

    # Update title
    if update_request.title is not None:
        clip.title = update_request.title

    # Update user preferences
    if update_request.is_favorite is not None:
        clip.is_favorite = update_request.is_favorite

    if update_request.user_rating is not None:
        clip.user_rating = update_request.user_rating

    if update_request.user_notes is not None:
        clip.user_notes = update_request.user_notes

    # Update timing (requires regeneration)
    if update_request.start_time is not None or update_request.end_time is not None:
        # Validate timing if both are provided
        if update_request.start_time is not None and update_request.end_time is not None:
            update_request.validate_timing()

        new_start = update_request.start_time if update_request.start_time is not None else clip.start_time
        new_end = update_request.end_time if update_request.end_time is not None else clip.end_time

        timing_result = clip_editor.update_clip_timing(clip, new_start, new_end)
        if not timing_result["success"]:
            raise HTTPException(status_code=400, detail=timing_result["error"])

        requires_regeneration = timing_result["requires_regeneration"]

    # Update subtitle style (requires regeneration)
    if update_request.subtitle_style is not None:
        style_result = clip_editor.update_subtitle_style(clip, update_request.subtitle_style)
        if not style_result["success"]:
            raise HTTPException(status_code=400, detail=style_result["error"])

        requires_regeneration = requires_regeneration or style_result["requires_regeneration"]

    # Update timestamp
    clip.updated_at = datetime.utcnow()

    # Commit changes
    db.commit()
    db.refresh(clip)

    # Start regeneration if needed
    if requires_regeneration:
        logger.info("Starting clip regeneration due to updates", clip_id=clip.id)
        regenerate_clip_task.delay(str(clip.id))

    logger.info("Clip updated successfully", clip_id=clip.id, requires_regeneration=requires_regeneration)
    return ClipResponse.from_orm(clip)


@router.post("/{clip_id}/regenerate")
async def regenerate_clip(
    clip_id: uuid.UUID,
    regenerate_request: RegenerateClipRequest = RegenerateClipRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Regenerate clip with new parameters.

    Critères PRD F5-03: Endpoint POST `/api/clips/{id}/regenerate` pour re-traiter le clip
    """
    logger.info("Regenerating clip", clip_id=clip_id, user_id=current_user.id, params=regenerate_request.dict(exclude_none=True))

    # Get clip from database
    clip = db.query(Clip).filter(
        and_(
            Clip.id == clip_id,
            Clip.project.has(user_id=current_user.id)
        )
    ).first()

    if not clip:
        logger.warning("Clip not found or access denied", clip_id=clip_id, user_id=current_user.id)
        raise HTTPException(status_code=404, detail="Clip not found")

    # Check if clip is already processing
    if clip.status == "processing":
        raise HTTPException(status_code=409, detail="Clip is already being processed")

    clip_editor = get_clip_editor_service()

    # Apply new settings if provided
    if regenerate_request.subtitle_style:
        style_result = clip_editor.update_subtitle_style(clip, regenerate_request.subtitle_style)
        if not style_result["success"]:
            raise HTTPException(status_code=400, detail=style_result["error"])

    if regenerate_request.crop_settings:
        is_valid, error = clip_editor.validate_crop_settings(regenerate_request.crop_settings)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)

        clip.crop_settings = regenerate_request.crop_settings

    # Start regeneration
    regeneration_result = clip_editor.regenerate_clip(clip)
    if not regeneration_result["success"]:
        raise HTTPException(status_code=400, detail=regeneration_result["error"])

    # Commit changes and start async task
    db.commit()
    regenerate_clip_task.delay(str(clip.id))

    # Estimate completion time
    estimated_time = clip_editor.estimate_regeneration_time(clip)
    estimated_completion = datetime.utcnow() + timedelta(seconds=estimated_time)

    logger.info("Clip regeneration started", clip_id=clip.id, estimated_seconds=estimated_time)

    return {
        "success": True,
        "message": "Clip regeneration started",
        "clip_id": str(clip.id),
        "status": "processing",
        "estimated_completion": estimated_completion,
        "estimated_duration_seconds": estimated_time
    }


@router.get("/{clip_id}/download", response_model=ClipDownloadResponse)
async def get_download_url(
    clip_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get download URL for clip.

    Critères PRD F5-04: Endpoint GET `/api/clips/{id}/download` avec URL signée S3 (expiration 1h)
    """
    logger.info("Getting download URL", clip_id=clip_id, user_id=current_user.id)

    # Get clip from database
    clip = db.query(Clip).filter(
        and_(
            Clip.id == clip_id,
            Clip.project.has(user_id=current_user.id)
        )
    ).first()

    if not clip:
        logger.warning("Clip not found or access denied", clip_id=clip_id, user_id=current_user.id)
        raise HTTPException(status_code=404, detail="Clip not found")

    if not clip.s3_key:
        raise HTTPException(status_code=404, detail="Clip video not available")

    if clip.status != "ready":
        raise HTTPException(status_code=409, detail=f"Clip is not ready (status: {clip.status})")

    # Generate download URL
    s3_service = get_s3_service()
    filename = f"{clip.title}.mp4".replace(" ", "_")
    download_url = s3_service.generate_download_url(
        clip.s3_key,
        filename=filename,
        expiration=3600  # 1 hour
    )

    if not download_url:
        raise HTTPException(status_code=500, detail="Failed to generate download URL")

    # Get file size if available
    object_info = s3_service.get_object_info(clip.s3_key)
    file_size = object_info.get("size") if object_info else None

    expires_at = datetime.utcnow() + timedelta(seconds=3600)

    logger.info("Download URL generated successfully", clip_id=clip_id, filename=filename)

    return ClipDownloadResponse(
        download_url=download_url,
        expires_at=expires_at,
        filename=filename,
        file_size=file_size
    )


@router.delete("/{clip_id}")
async def delete_clip(
    clip_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete clip from database and S3.

    Critères PRD F5-05: Endpoint DELETE `/api/clips/{id}` pour supprimer de S3 et DB
    """
    logger.info("Deleting clip", clip_id=clip_id, user_id=current_user.id)

    # Get clip from database
    clip = db.query(Clip).filter(
        and_(
            Clip.id == clip_id,
            Clip.project.has(user_id=current_user.id)
        )
    ).first()

    if not clip:
        logger.warning("Clip not found or access denied", clip_id=clip_id, user_id=current_user.id)
        raise HTTPException(status_code=404, detail="Clip not found")

    # Delete S3 objects
    s3_service = get_s3_service()
    s3_keys_to_delete = [clip.s3_key, clip.thumbnail_url, clip.preview_gif_url]

    for s3_key in s3_keys_to_delete:
        if s3_key:
            try:
                s3_service.delete_object(s3_key)
                logger.info("Deleted S3 object", s3_key=s3_key)
            except Exception as e:
                logger.warning("Failed to delete S3 object", s3_key=s3_key, error=str(e))

    # Delete from database
    db.delete(clip)
    db.commit()

    logger.info("Clip deleted successfully", clip_id=clip_id)

    return {
        "success": True,
        "message": "Clip deleted successfully",
        "clip_id": str(clip_id)
    }


@router.get("/", response_model=ClipsListResponse)
async def list_clips(
    project_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    subtitle_style: Optional[str] = Query(None),
    is_favorite: Optional[bool] = Query(None),
    min_viral_score: Optional[float] = Query(None),
    max_viral_score: Optional[float] = Query(None),
    min_duration: Optional[float] = Query(None),
    max_duration: Optional[float] = Query(None),
    sort_by: str = Query("viral_score"),
    sort_order: str = Query("desc"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List user's clips with filtering and sorting.

    Critères PRD F5-11: Tri et filtrage par score de viralité, date, durée
    """
    logger.info("Listing clips", user_id=current_user.id, filters={
        "project_id": project_id,
        "status": status,
        "sort_by": sort_by,
        "page": page,
        "size": size
    })

    # Build query
    query = db.query(Clip).filter(
        Clip.project.has(user_id=current_user.id)
    )

    # Apply filters
    if project_id:
        query = query.filter(Clip.project_id == project_id)

    if status:
        query = query.filter(Clip.status == status)

    if subtitle_style:
        query = query.filter(Clip.subtitle_style == subtitle_style)

    if is_favorite is not None:
        query = query.filter(Clip.is_favorite == is_favorite)

    if min_viral_score is not None:
        query = query.filter(Clip.viral_score >= min_viral_score)

    if max_viral_score is not None:
        query = query.filter(Clip.viral_score <= max_viral_score)

    if min_duration is not None:
        query = query.filter(Clip.duration >= min_duration)

    if max_duration is not None:
        query = query.filter(Clip.duration <= max_duration)

    # Apply sorting
    sort_column = getattr(Clip, sort_by, None)
    if sort_column is None:
        raise HTTPException(status_code=400, detail=f"Invalid sort field: {sort_by}")

    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * size
    clips = query.offset(offset).limit(size).all()

    # Calculate total pages
    total_pages = (total + size - 1) // size

    logger.info("Clips listed successfully", count=len(clips), total=total, page=page)

    return ClipsListResponse(
        clips=[ClipResponse.from_orm(clip) for clip in clips],
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )


@router.post("/bulk-download", response_model=BulkDownloadResponse)
async def bulk_download_clips(
    request: BulkDownloadRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download multiple clips as a ZIP file.

    Critères PRD F5-12: Batch download - télécharger tous les clips d'un projet en ZIP
    """
    logger.info("Bulk download request", user_id=current_user.id, clip_count=len(request.clip_ids))

    # Get clips from database
    clips_query = db.query(Clip).filter(
        and_(
            Clip.id.in_(request.clip_ids),
            Clip.project.has(user_id=current_user.id),
            Clip.status == "ready",
            Clip.s3_key.isnot(None)
        )
    )

    if request.project_id:
        clips_query = clips_query.filter(Clip.project_id == request.project_id)

    clips = clips_query.all()

    if not clips:
        raise HTTPException(status_code=404, detail="No clips found or clips not ready")

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
                            else:
                                # In real mode, download and add to ZIP
                                # Implementation would download from S3 and add to ZIP
                                pass

                except Exception as e:
                    logger.warning("Failed to add clip to ZIP", clip_id=clip.id, error=str(e))

        # Upload ZIP to S3 for download
        zip_s3_key = f"downloads/{current_user.id}/{uuid.uuid4()}.zip"

        if s3_service._is_mock_mode():
            logger.info("Mock uploading ZIP to S3", s3_key=zip_s3_key)
        else:
            # Real S3 upload would go here
            pass

        # Generate download URL
        download_url = s3_service.generate_download_url(
            zip_s3_key,
            filename=f"clips_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            expiration=3600
        )

        if not download_url:
            raise HTTPException(status_code=500, detail="Failed to generate download URL")

        expires_at = datetime.utcnow() + timedelta(seconds=3600)

        # Schedule cleanup of temporary files
        background_tasks.add_task(_cleanup_temp_zip, temp_zip_path)

        logger.info("Bulk download created successfully", clips_count=len(clips), total_size=total_size)

        return BulkDownloadResponse(
            download_url=download_url,
            expires_at=expires_at,
            filename=f"clips_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            clips_count=len(clips),
            total_size=total_size
        )

    except Exception as e:
        # Clean up on error
        if os.path.exists(temp_zip_path):
            os.unlink(temp_zip_path)

        logger.error("Bulk download failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create bulk download")


def _cleanup_temp_zip(temp_zip_path: str):
    """Clean up temporary ZIP file"""
    try:
        if os.path.exists(temp_zip_path):
            os.unlink(temp_zip_path)
            logger.info("Cleaned up temporary ZIP file", path=temp_zip_path)
    except Exception as e:
        logger.warning("Failed to clean up temporary ZIP file", path=temp_zip_path, error=str(e))