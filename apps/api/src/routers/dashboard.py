"""
Dashboard endpoints for analytics and overview data
"""
import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta, timezone

from ..database import get_db
from ..models.user import User
from ..models.project import Project
from ..models.clip import Clip
from ..middleware.auth import get_current_user
from ..utils.logging import safe_log_user_data

logger = structlog.get_logger()

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get dashboard statistics for the current user

    Returns:
    - Total projects
    - Total clips
    - Minutes processed this month
    - Recent activity
    """
    try:
        log_data = safe_log_user_data(str(current_user.id))
        logger.info("Dashboard stats requested", **log_data)

        # Get total projects for user
        total_projects = db.query(Project).filter(Project.user_id == current_user.id).count()

        # Get total clips for user's projects
        total_clips = (
            db.query(Clip)
            .join(Project)
            .filter(Project.user_id == current_user.id)
            .count()
        )

        # Get completed projects
        completed_projects = (
            db.query(Project)
            .filter(
                and_(
                    Project.user_id == current_user.id,
                    Project.status == 'completed'
                )
            )
            .count()
        )

        # Get processing projects
        processing_projects = (
            db.query(Project)
            .filter(
                and_(
                    Project.user_id == current_user.id,
                    Project.status == 'processing'
                )
            )
            .count()
        )

        # Get recent projects (last 7 days)
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        recent_projects = (
            db.query(Project)
            .filter(
                and_(
                    Project.user_id == current_user.id,
                    Project.created_at >= seven_days_ago
                )
            )
            .count()
        )

        # Get clips generated this month
        start_of_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        clips_this_month = (
            db.query(Clip)
            .join(Project)
            .filter(
                and_(
                    Project.user_id == current_user.id,
                    Clip.created_at >= start_of_month
                )
            )
            .count()
        )

        return {
            "total_projects": total_projects,
            "total_clips": total_clips,
            "completed_projects": completed_projects,
            "processing_projects": processing_projects,
            "recent_projects": recent_projects,
            "clips_this_month": clips_this_month,
            "monthly_minutes_used": current_user.monthly_minutes_used,
            "monthly_minutes_limit": current_user.monthly_minutes_limit,
            "monthly_minutes_remaining": max(0, current_user.monthly_minutes_limit - current_user.monthly_minutes_used),
            "plan": current_user.plan.value,
            "clips_generated": current_user.clips_generated,
            "clips_limit": current_user.clips_limit,
        }

    except Exception as e:
        logger.error("Failed to get dashboard stats", user_id=str(current_user.id), error=str(e))
        # Return default empty stats instead of raising error
        return {
            "total_projects": 0,
            "total_clips": 0,
            "completed_projects": 0,
            "processing_projects": 0,
            "recent_projects": 0,
            "clips_this_month": 0,
            "monthly_minutes_used": current_user.monthly_minutes_used if current_user else 0,
            "monthly_minutes_limit": current_user.monthly_minutes_limit if current_user else 30,
            "monthly_minutes_remaining": current_user.monthly_minutes_limit - current_user.monthly_minutes_used if current_user else 30,
            "plan": current_user.plan.value if current_user else "FREE",
            "clips_generated": current_user.clips_generated if current_user else 0,
            "clips_limit": current_user.clips_limit if current_user else 10,
        }