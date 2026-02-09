"""Quota service for managing plan limits and usage tracking"""

import structlog
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..models.user import User, PlanType
from ..schemas.billing import QuotaCheckResponse, PlanLimits

logger = structlog.get_logger()

# Plan limits configuration as per PRD F7
PLAN_LIMITS = {
    PlanType.FREE: PlanLimits(
        monthly_upload_minutes=30,
        monthly_clips=5,
        max_source_duration=600,  # 10 min
        scheduling_enabled=False,
        platforms=["tiktok"],
        subtitle_styles=["clean", "minimal"],
        watermark=True,
    ),
    PlanType.STARTER: PlanLimits(
        monthly_upload_minutes=120,
        monthly_clips=30,
        max_source_duration=3600,  # 1h
        scheduling_enabled=True,
        max_scheduled_per_week=5,
        platforms=["tiktok", "youtube"],
        subtitle_styles=["clean", "minimal", "hormozi", "neon", "karaoke"],
        watermark=False,
    ),
    PlanType.PRO: PlanLimits(
        monthly_upload_minutes=600,
        monthly_clips=150,
        max_source_duration=14400,  # 4h
        scheduling_enabled=True,
        max_scheduled_per_week=None,  # unlimited
        platforms=["tiktok", "youtube", "instagram"],
        subtitle_styles="all",
        watermark=False,
    ),
    PlanType.ENTERPRISE: PlanLimits(
        monthly_upload_minutes=None,  # unlimited
        monthly_clips=None,
        max_source_duration=None,
        scheduling_enabled=True,
        max_scheduled_per_week=None,
        platforms="all",
        subtitle_styles="all",
        watermark=False,
    ),
}


class QuotaService:
    """Service for checking and managing user quotas based on subscription plans"""

    def __init__(self, db: Session):
        self.db = db
        self.limits = PLAN_LIMITS

    def get_plan_limits(self, plan: PlanType) -> PlanLimits:
        """Get limits for a specific plan"""
        return self.limits.get(plan, self.limits[PlanType.FREE])

    def check_upload_quota(self, user: User, video_duration_minutes: float) -> QuotaCheckResponse:
        """
        Check if user can upload video of given duration

        Args:
            user: User object
            video_duration_minutes: Duration of video in minutes

        Returns:
            QuotaCheckResponse with quota check result
        """
        limits = self.get_plan_limits(user.plan)

        # Enterprise plan has unlimited upload minutes
        if limits.monthly_upload_minutes is None:
            return QuotaCheckResponse(
                allowed=True,
                remaining=None,
                limit=None,
                reset_date=self._get_next_reset_date()
            )

        # Calculate remaining quota
        used_minutes = user.monthly_minutes_used or 0
        remaining_minutes = limits.monthly_upload_minutes - used_minutes

        # Check if upload would exceed quota
        if video_duration_minutes > remaining_minutes:
            return QuotaCheckResponse(
                allowed=False,
                reason=f"Upload would exceed monthly limit of {limits.monthly_upload_minutes} minutes. "
                       f"You have {remaining_minutes:.1f} minutes remaining.",
                remaining=int(remaining_minutes),
                limit=limits.monthly_upload_minutes,
                reset_date=self._get_next_reset_date()
            )

        return QuotaCheckResponse(
            allowed=True,
            remaining=int(remaining_minutes - video_duration_minutes),
            limit=limits.monthly_upload_minutes,
            reset_date=self._get_next_reset_date()
        )

    def check_clip_quota(self, user: User, clips_count: int = 1) -> QuotaCheckResponse:
        """
        Check if user can generate more clips this month

        Args:
            user: User object
            clips_count: Number of clips to generate

        Returns:
            QuotaCheckResponse with quota check result
        """
        limits = self.get_plan_limits(user.plan)

        # Enterprise plan has unlimited clips
        if limits.monthly_clips is None:
            return QuotaCheckResponse(
                allowed=True,
                remaining=None,
                limit=None,
                reset_date=self._get_next_reset_date()
            )

        # Get current clips generated (you'll need to track this in User model)
        clips_generated = getattr(user, 'monthly_clips_generated', 0)
        remaining_clips = limits.monthly_clips - clips_generated

        # Check if clip generation would exceed quota
        if clips_count > remaining_clips:
            return QuotaCheckResponse(
                allowed=False,
                reason=f"Would exceed monthly limit of {limits.monthly_clips} clips. "
                       f"You have {remaining_clips} clips remaining.",
                remaining=remaining_clips,
                limit=limits.monthly_clips,
                reset_date=self._get_next_reset_date()
            )

        return QuotaCheckResponse(
            allowed=True,
            remaining=remaining_clips - clips_count,
            limit=limits.monthly_clips,
            reset_date=self._get_next_reset_date()
        )

    def check_scheduling_quota(self, user: User) -> QuotaCheckResponse:
        """
        Check if user can schedule more posts this week

        Args:
            user: User object

        Returns:
            QuotaCheckResponse with quota check result
        """
        limits = self.get_plan_limits(user.plan)

        # Check if scheduling is enabled for plan
        if not limits.scheduling_enabled:
            return QuotaCheckResponse(
                allowed=False,
                reason="Scheduling is not available on your current plan. Upgrade to enable scheduling.",
                remaining=0,
                limit=0,
                reset_date=self._get_next_week_reset_date()
            )

        # Enterprise and Pro plans have unlimited scheduling
        if limits.max_scheduled_per_week is None:
            return QuotaCheckResponse(
                allowed=True,
                remaining=None,
                limit=None,
                reset_date=self._get_next_week_reset_date()
            )

        # Get current scheduled posts this week (you'll need to implement this)
        scheduled_this_week = self._get_scheduled_posts_this_week(user)
        remaining = limits.max_scheduled_per_week - scheduled_this_week

        if remaining <= 0:
            return QuotaCheckResponse(
                allowed=False,
                reason=f"Weekly scheduling limit of {limits.max_scheduled_per_week} posts reached.",
                remaining=0,
                limit=limits.max_scheduled_per_week,
                reset_date=self._get_next_week_reset_date()
            )

        return QuotaCheckResponse(
            allowed=True,
            remaining=remaining,
            limit=limits.max_scheduled_per_week,
            reset_date=self._get_next_week_reset_date()
        )

    def check_video_duration_limit(self, user: User, video_duration_seconds: int) -> QuotaCheckResponse:
        """
        Check if video duration is within plan limits

        Args:
            user: User object
            video_duration_seconds: Duration of video in seconds

        Returns:
            QuotaCheckResponse with quota check result
        """
        limits = self.get_plan_limits(user.plan)

        # Enterprise plan has no duration limit
        if limits.max_source_duration is None:
            return QuotaCheckResponse(allowed=True)

        if video_duration_seconds > limits.max_source_duration:
            max_minutes = limits.max_source_duration // 60
            return QuotaCheckResponse(
                allowed=False,
                reason=f"Video duration exceeds the {max_minutes}-minute limit for your plan.",
                limit=limits.max_source_duration
            )

        return QuotaCheckResponse(allowed=True, limit=limits.max_source_duration)

    def check_platform_access(self, user: User, platform: str) -> bool:
        """
        Check if user has access to specific platform

        Args:
            user: User object
            platform: Platform name (e.g., "tiktok", "youtube", "instagram")

        Returns:
            bool: True if user has access to platform
        """
        limits = self.get_plan_limits(user.plan)

        if limits.platforms == "all":
            return True

        if isinstance(limits.platforms, list):
            return platform.lower() in [p.lower() for p in limits.platforms]

        return False

    def check_subtitle_style_access(self, user: User, style: str) -> bool:
        """
        Check if user has access to specific subtitle style

        Args:
            user: User object
            style: Subtitle style name

        Returns:
            bool: True if user has access to style
        """
        limits = self.get_plan_limits(user.plan)

        if limits.subtitle_styles == "all":
            return True

        if isinstance(limits.subtitle_styles, list):
            return style.lower() in [s.lower() for s in limits.subtitle_styles]

        return False

    def should_apply_watermark(self, user: User) -> bool:
        """
        Check if watermark should be applied for user's plan

        Args:
            user: User object

        Returns:
            bool: True if watermark should be applied
        """
        limits = self.get_plan_limits(user.plan)
        return limits.watermark

    def _get_next_reset_date(self) -> datetime:
        """Get next monthly reset date (first day of next month)"""
        now = datetime.utcnow()
        if now.month == 12:
            return datetime(now.year + 1, 1, 1)
        else:
            return datetime(now.year, now.month + 1, 1)

    def _get_next_week_reset_date(self) -> datetime:
        """Get next weekly reset date (next Monday)"""
        now = datetime.utcnow()
        days_ahead = 7 - now.weekday()  # Monday is 0
        if days_ahead <= 0:  # Today is Monday
            days_ahead += 7
        return (now + timedelta(days=days_ahead)).replace(hour=0, minute=0, second=0, microsecond=0)

    def _get_scheduled_posts_this_week(self, user: User) -> int:
        """
        Get number of posts scheduled this week for user

        This would query the scheduled_posts table to count posts
        scheduled for the current week.
        """
        # Implementation would depend on your ScheduledPost model
        # For now, return 0 as placeholder
        from ..models.scheduled_post import ScheduledPost
        from datetime import datetime, timedelta

        # Get start of current week (Monday)
        now = datetime.utcnow()
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_week = start_of_week + timedelta(days=7)

        try:
            count = self.db.query(ScheduledPost).filter(
                ScheduledPost.user_id == user.id,
                ScheduledPost.scheduled_time >= start_of_week,
                ScheduledPost.scheduled_time < end_of_week,
                ScheduledPost.status != "cancelled"
            ).count()
            return count
        except Exception as e:
            logger.error("Failed to get scheduled posts count", error=str(e), user_id=str(user.id))
            return 0