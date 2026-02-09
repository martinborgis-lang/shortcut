"""
Scheduled post management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc
from datetime import datetime, timedelta
from typing import List, Optional
import structlog
from uuid import UUID

from ..database import get_db
from ..middleware.auth import get_current_user
from ..models.user import User
from ..models.scheduled_post import ScheduledPost
from ..models.social_account import SocialAccount
from ..models.clip import Clip
from ..schemas.schedule import (
    CreateScheduledPostRequest,
    ScheduledPostResponse,
    UpdateScheduledPostRequest,
    ScheduledPostsListResponse,
    ScheduledPostFilters,
    CancelScheduledPostRequest,
    CancelScheduledPostResponse,
    ScheduledPostStats,
    PostPerformanceMetrics,
    BulkScheduleRequest,
    BulkScheduleResponse,
    PostStatus
)

logger = structlog.get_logger()
router = APIRouter()


@router.post("/", response_model=ScheduledPostResponse)
async def create_scheduled_post(
    request: CreateScheduledPostRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new scheduled post

    F6-08: Endpoint POST `/api/schedule`
    Crée une publication programmée : `{ clip_id, platform, scheduled_at, caption, hashtags }`
    """
    try:
        # Validate clip ownership
        clip = db.query(Clip).filter(
            and_(
                Clip.id == request.clip_id,
                Clip.user_id == current_user.id
            )
        ).first()

        if not clip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Clip not found or access denied"
            )

        # Validate social account ownership
        social_account = db.query(SocialAccount).filter(
            and_(
                SocialAccount.id == request.social_account_id,
                SocialAccount.user_id == current_user.id,
                SocialAccount.is_active == True
            )
        ).first()

        if not social_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Social account not found or inactive"
            )

        # Validate scheduled time (must be in the future)
        if request.scheduled_time <= datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scheduled time must be in the future"
            )

        # Check for duplicate scheduling (same clip, same account, similar time)
        existing_post = db.query(ScheduledPost).filter(
            and_(
                ScheduledPost.clip_id == request.clip_id,
                ScheduledPost.social_account_id == request.social_account_id,
                ScheduledPost.status.in_(["scheduled", "publishing"]),
                ScheduledPost.scheduled_time.between(
                    request.scheduled_time - timedelta(minutes=30),
                    request.scheduled_time + timedelta(minutes=30)
                )
            )
        ).first()

        if existing_post:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A similar post is already scheduled for this time period"
            )

        # Create scheduled post
        scheduled_post = ScheduledPost(
            clip_id=request.clip_id,
            social_account_id=request.social_account_id,
            scheduled_time=request.scheduled_time,
            time_zone=request.time_zone,
            caption=request.caption,
            hashtags=request.hashtags,
            mentions=request.mentions,
            platform_settings=request.platform_settings,
            status="scheduled"
        )

        db.add(scheduled_post)
        db.commit()
        db.refresh(scheduled_post)

        logger.info("Created scheduled post",
                   user_id=current_user.id, post_id=scheduled_post.id,
                   clip_id=request.clip_id, platform=social_account.platform,
                   scheduled_time=request.scheduled_time)

        return ScheduledPostResponse.from_orm(scheduled_post)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Failed to create scheduled post",
                    user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create scheduled post: {str(e)}"
        )


@router.get("/", response_model=ScheduledPostsListResponse)
async def get_scheduled_posts(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[PostStatus] = Query(None, description="Filter by status"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    clip_id: Optional[UUID] = Query(None, description="Filter by clip ID"),
    social_account_id: Optional[UUID] = Query(None, description="Filter by social account"),
    scheduled_after: Optional[datetime] = Query(None, description="Posts scheduled after this time"),
    scheduled_before: Optional[datetime] = Query(None, description="Posts scheduled before this time"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of scheduled posts with filtering and pagination

    F6-09: Endpoint GET `/api/schedule`
    Liste les publications programmées avec statut
    """
    try:
        # Build base query with joins for efficient loading
        query = db.query(ScheduledPost).options(
            joinedload(ScheduledPost.clip),
            joinedload(ScheduledPost.social_account)
        ).join(SocialAccount).filter(
            SocialAccount.user_id == current_user.id
        )

        # Apply filters
        if status:
            query = query.filter(ScheduledPost.status == status)

        if platform:
            query = query.filter(SocialAccount.platform == platform)

        if clip_id:
            query = query.filter(ScheduledPost.clip_id == clip_id)

        if social_account_id:
            query = query.filter(ScheduledPost.social_account_id == social_account_id)

        if scheduled_after:
            query = query.filter(ScheduledPost.scheduled_time >= scheduled_after)

        if scheduled_before:
            query = query.filter(ScheduledPost.scheduled_time <= scheduled_before)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        posts = query.order_by(desc(ScheduledPost.scheduled_time)).offset(
            (page - 1) * per_page
        ).limit(per_page).all()

        total_pages = (total + per_page - 1) // per_page

        logger.info("Retrieved scheduled posts",
                   user_id=current_user.id, total=total, page=page)

        return ScheduledPostsListResponse(
            posts=[ScheduledPostResponse.from_orm(post) for post in posts],
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )

    except Exception as e:
        logger.error("Failed to retrieve scheduled posts",
                    user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve scheduled posts: {str(e)}"
        )


@router.get("/{post_id}", response_model=ScheduledPostResponse)
async def get_scheduled_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific scheduled post"""
    try:
        post = db.query(ScheduledPost).options(
            joinedload(ScheduledPost.clip),
            joinedload(ScheduledPost.social_account)
        ).join(SocialAccount).filter(
            and_(
                ScheduledPost.id == post_id,
                SocialAccount.user_id == current_user.id
            )
        ).first()

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheduled post not found"
            )

        logger.info("Retrieved scheduled post details",
                   user_id=current_user.id, post_id=post_id)

        return ScheduledPostResponse.from_orm(post)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve scheduled post",
                    user_id=current_user.id, post_id=post_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve scheduled post: {str(e)}"
        )


@router.patch("/{post_id}", response_model=ScheduledPostResponse)
async def update_scheduled_post(
    post_id: str,
    update_data: UpdateScheduledPostRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a scheduled post (only if not yet published)"""
    try:
        post = db.query(ScheduledPost).options(
            joinedload(ScheduledPost.social_account)
        ).join(SocialAccount).filter(
            and_(
                ScheduledPost.id == post_id,
                SocialAccount.user_id == current_user.id
            )
        ).first()

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheduled post not found"
            )

        # Check if post can be updated
        if post.status in ["published", "publishing"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update post that is already published or being published"
            )

        # Validate new scheduled time if provided
        if update_data.scheduled_time and update_data.scheduled_time <= datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scheduled time must be in the future"
            )

        # Update fields
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(post, field, value)

        db.commit()
        db.refresh(post)

        logger.info("Updated scheduled post",
                   user_id=current_user.id, post_id=post_id)

        return ScheduledPostResponse.from_orm(post)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Failed to update scheduled post",
                    user_id=current_user.id, post_id=post_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update scheduled post: {str(e)}"
        )


@router.delete("/{post_id}", response_model=CancelScheduledPostResponse)
async def cancel_scheduled_post(
    post_id: str,
    request: Optional[CancelScheduledPostRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel a scheduled post

    F6-10: Endpoint DELETE `/api/schedule/{id}`
    Annule une publication programmée
    """
    try:
        post = db.query(ScheduledPost).options(
            joinedload(ScheduledPost.social_account)
        ).join(SocialAccount).filter(
            and_(
                ScheduledPost.id == post_id,
                SocialAccount.user_id == current_user.id
            )
        ).first()

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheduled post not found"
            )

        # Check if post can be cancelled
        if post.status in ["published", "publishing"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel post that is already published or being published"
            )

        post_response = ScheduledPostResponse.from_orm(post)

        # Update status to cancelled
        post.status = "cancelled"
        post.error_message = request.reason if request else "Cancelled by user"
        post.failed_at = datetime.utcnow()

        db.commit()

        logger.info("Cancelled scheduled post",
                   user_id=current_user.id, post_id=post_id,
                   reason=request.reason if request else "No reason provided")

        return CancelScheduledPostResponse(
            message="Scheduled post cancelled successfully",
            cancelled_post=post_response
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Failed to cancel scheduled post",
                    user_id=current_user.id, post_id=post_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel scheduled post: {str(e)}"
        )


@router.get("/stats/summary", response_model=ScheduledPostStats)
async def get_scheduled_posts_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to include in stats"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get statistics for scheduled posts"""
    try:
        # Date range for stats
        start_date = datetime.utcnow() - timedelta(days=days)

        # Get posts in date range
        posts = db.query(ScheduledPost).join(SocialAccount).filter(
            and_(
                SocialAccount.user_id == current_user.id,
                ScheduledPost.created_at >= start_date
            )
        ).all()

        # Calculate stats
        total_scheduled = len([p for p in posts if p.status == "scheduled"])
        total_published = len([p for p in posts if p.status == "published"])
        total_failed = len([p for p in posts if p.status == "failed"])
        total_cancelled = len([p for p in posts if p.status == "cancelled"])

        total_completed = total_published + total_failed + total_cancelled
        success_rate = (total_published / total_completed * 100) if total_completed > 0 else 0

        # Calculate average engagement rate
        published_posts_with_engagement = [
            p for p in posts
            if p.status == "published" and p.engagement_rate is not None
        ]
        avg_engagement_rate = None
        if published_posts_with_engagement:
            avg_engagement_rate = sum(p.engagement_rate for p in published_posts_with_engagement) / len(published_posts_with_engagement)

        logger.info("Retrieved scheduled posts stats",
                   user_id=current_user.id, days=days,
                   total_scheduled=total_scheduled, total_published=total_published)

        return ScheduledPostStats(
            total_scheduled=total_scheduled,
            total_published=total_published,
            total_failed=total_failed,
            total_cancelled=total_cancelled,
            success_rate=round(success_rate, 2),
            avg_engagement_rate=round(avg_engagement_rate, 2) if avg_engagement_rate else None
        )

    except Exception as e:
        logger.error("Failed to retrieve scheduled posts stats",
                    user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve stats: {str(e)}"
        )


@router.post("/bulk", response_model=BulkScheduleResponse)
async def bulk_schedule_posts(
    request: BulkScheduleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Schedule multiple posts with automatic time distribution"""
    try:
        # Validate clips ownership
        clips = db.query(Clip).filter(
            and_(
                Clip.id.in_(request.clip_ids),
                Clip.user_id == current_user.id
            )
        ).all()

        if len(clips) != len(request.clip_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more clips not found or access denied"
            )

        # Validate social accounts
        social_accounts = db.query(SocialAccount).filter(
            and_(
                SocialAccount.id.in_(request.social_account_ids),
                SocialAccount.user_id == current_user.id,
                SocialAccount.is_active == True
            )
        ).all()

        if len(social_accounts) != len(request.social_account_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more social accounts not found or inactive"
            )

        scheduled_posts = []
        failed_posts = []
        current_time = request.base_scheduled_time

        # Create posts for each clip-account combination
        for clip in clips:
            for account in social_accounts:
                try:
                    # Build caption from template if provided
                    caption = request.caption_template
                    if caption:
                        caption = caption.replace("{clip_title}", clip.title or "")
                        caption = caption.replace("{clip_description}", clip.description or "")

                    # Create scheduled post
                    scheduled_post = ScheduledPost(
                        clip_id=clip.id,
                        social_account_id=account.id,
                        scheduled_time=current_time,
                        time_zone="UTC",
                        caption=caption,
                        hashtags=request.hashtags,
                        platform_settings=request.platform_settings,
                        status="scheduled"
                    )

                    db.add(scheduled_post)
                    scheduled_posts.append(scheduled_post)

                    # Increment time for next post
                    current_time += timedelta(minutes=request.time_interval_minutes)

                except Exception as e:
                    failed_posts.append({
                        "clip_id": str(clip.id),
                        "social_account_id": str(account.id),
                        "error": str(e)
                    })

        db.commit()

        # Refresh all scheduled posts
        for post in scheduled_posts:
            db.refresh(post)

        summary = {
            "total_requested": len(request.clip_ids) * len(request.social_account_ids),
            "successfully_scheduled": len(scheduled_posts),
            "failed": len(failed_posts)
        }

        logger.info("Bulk scheduled posts",
                   user_id=current_user.id, summary=summary)

        return BulkScheduleResponse(
            scheduled_posts=[ScheduledPostResponse.from_orm(post) for post in scheduled_posts],
            failed_posts=failed_posts,
            summary=summary
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Failed to bulk schedule posts",
                    user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk schedule posts: {str(e)}"
        )