"""
User management endpoints
"""
import structlog
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..models.user import User, PlanType
from ..middleware.auth import get_current_user
from ..middleware.rate_limiting import check_rate_limit
from ..utils.logging import safe_log_user_data

logger = structlog.get_logger()

router = APIRouter()


class UserResponse(BaseModel):
    """User response model"""
    id: str
    clerk_id: str
    email: str
    name: str
    first_name: str | None
    last_name: str | None
    profile_image_url: str | None
    plan: PlanType
    monthly_minutes_used: int
    monthly_minutes_limit: int
    created_at: str

    class Config:
        from_attributes = True


class UsageStats(BaseModel):
    """User usage statistics"""
    monthly_minutes_used: int
    monthly_minutes_limit: int
    monthly_minutes_remaining: int
    clips_generated: int
    clips_limit: int
    plan: PlanType


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(check_rate_limit)
) -> UserResponse:
    """
    Get current user information

    Returns authenticated user's profile and subscription details
    """
    try:
        # Log user info request with masked data in production
        log_data = safe_log_user_data(str(current_user.id), clerk_id=current_user.clerk_id, email=current_user.email)
        logger.info("User info requested", **log_data)

        return UserResponse(
            id=str(current_user.id),
            clerk_id=current_user.clerk_id,
            email=current_user.email,
            name=current_user.name,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            profile_image_url=current_user.profile_image_url,
            plan=current_user.plan,
            monthly_minutes_used=current_user.monthly_minutes_used,
            monthly_minutes_limit=current_user.monthly_minutes_limit,
            created_at=current_user.created_at.isoformat() if current_user.created_at else ""
        )

    except Exception as e:
        logger.error("Failed to get user info", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )


@router.get("/me/usage", response_model=UsageStats)
async def get_user_usage(
    current_user: User = Depends(check_rate_limit)
) -> UsageStats:
    """
    Get current user usage statistics

    Returns detailed usage information for the current user
    """
    try:
        log_data = safe_log_user_data(str(current_user.id))
        log_data["plan"] = current_user.plan.value
        logger.info("User usage requested", **log_data)

        monthly_minutes_remaining = max(
            0,
            current_user.monthly_minutes_limit - current_user.monthly_minutes_used
        )

        return UsageStats(
            monthly_minutes_used=current_user.monthly_minutes_used,
            monthly_minutes_limit=current_user.monthly_minutes_limit,
            monthly_minutes_remaining=monthly_minutes_remaining,
            clips_generated=current_user.clips_generated,
            clips_limit=current_user.clips_limit,
            plan=current_user.plan
        )

    except Exception as e:
        logger.error("Failed to get user usage", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage statistics"
        )


@router.post("/me/reset-usage")
async def reset_monthly_usage(
    current_user: User = Depends(check_rate_limit),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Reset monthly usage (admin/development endpoint)

    This endpoint is for testing purposes and should be removed or secured in production
    """
    try:
        log_data = safe_log_user_data(str(current_user.id))
        log_data["old_usage"] = current_user.monthly_minutes_used
        logger.info("Resetting monthly usage", **log_data)

        current_user.reset_monthly_usage()
        db.commit()

        return {
            "status": "success",
            "message": "Monthly usage reset successfully",
            "monthly_minutes_used": current_user.monthly_minutes_used
        }

    except Exception as e:
        logger.error("Failed to reset usage", user_id=str(current_user.id), error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset usage"
        )