"""Tests for QuotaService"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch

from src.services.quota_service import QuotaService
from src.models.user import User, PlanType
from src.schemas.billing import QuotaCheckResponse


@pytest.fixture
def mock_db():
    """Mock database session"""
    return Mock()


@pytest.fixture
def quota_service(mock_db):
    """Create QuotaService instance with mock db"""
    return QuotaService(mock_db)


@pytest.fixture
def free_user():
    """Create a free plan user"""
    user = Mock(spec=User)
    user.id = "user-123"
    user.plan = PlanType.FREE
    user.monthly_minutes_used = 15
    user.monthly_clips_generated = 2
    return user


@pytest.fixture
def starter_user():
    """Create a starter plan user"""
    user = Mock(spec=User)
    user.id = "user-456"
    user.plan = PlanType.STARTER
    user.monthly_minutes_used = 60
    user.monthly_clips_generated = 10
    return user


@pytest.fixture
def enterprise_user():
    """Create an enterprise plan user"""
    user = Mock(spec=User)
    user.id = "user-789"
    user.plan = PlanType.ENTERPRISE
    user.monthly_minutes_used = 500
    user.monthly_clips_generated = 100
    return user


class TestQuotaService:
    """Test cases for QuotaService"""

    def test_get_plan_limits_free(self, quota_service):
        """Test getting limits for free plan"""
        limits = quota_service.get_plan_limits(PlanType.FREE)

        assert limits.monthly_upload_minutes == 30
        assert limits.monthly_clips == 5
        assert limits.max_source_duration == 600
        assert limits.scheduling_enabled is False
        assert limits.watermark is True
        assert "tiktok" in limits.platforms

    def test_get_plan_limits_starter(self, quota_service):
        """Test getting limits for starter plan"""
        limits = quota_service.get_plan_limits(PlanType.STARTER)

        assert limits.monthly_upload_minutes == 120
        assert limits.monthly_clips == 30
        assert limits.max_source_duration == 3600
        assert limits.scheduling_enabled is True
        assert limits.max_scheduled_per_week == 5
        assert limits.watermark is False
        assert "youtube" in limits.platforms

    def test_get_plan_limits_enterprise(self, quota_service):
        """Test getting limits for enterprise plan"""
        limits = quota_service.get_plan_limits(PlanType.ENTERPRISE)

        assert limits.monthly_upload_minutes is None  # unlimited
        assert limits.monthly_clips is None  # unlimited
        assert limits.max_source_duration is None  # unlimited
        assert limits.scheduling_enabled is True
        assert limits.max_scheduled_per_week is None  # unlimited
        assert limits.watermark is False
        assert limits.platforms == "all"

    def test_check_upload_quota_free_user_within_limit(self, quota_service, free_user):
        """Test upload quota check for free user within limits"""
        result = quota_service.check_upload_quota(free_user, 10.0)

        assert result.allowed is True
        assert result.remaining == 5  # 30 - 15 - 10
        assert result.limit == 30

    def test_check_upload_quota_free_user_exceeds_limit(self, quota_service, free_user):
        """Test upload quota check for free user exceeding limits"""
        result = quota_service.check_upload_quota(free_user, 20.0)

        assert result.allowed is False
        assert "exceed monthly limit" in result.reason
        assert result.remaining == 15  # 30 - 15
        assert result.limit == 30

    def test_check_upload_quota_enterprise_unlimited(self, quota_service, enterprise_user):
        """Test upload quota check for enterprise user (unlimited)"""
        result = quota_service.check_upload_quota(enterprise_user, 1000.0)

        assert result.allowed is True
        assert result.remaining is None
        assert result.limit is None

    def test_check_clip_quota_starter_user_within_limit(self, quota_service, starter_user):
        """Test clip quota check for starter user within limits"""
        result = quota_service.check_clip_quota(starter_user, 5)

        assert result.allowed is True
        assert result.remaining == 15  # 30 - 10 - 5
        assert result.limit == 30

    def test_check_clip_quota_starter_user_exceeds_limit(self, quota_service, starter_user):
        """Test clip quota check for starter user exceeding limits"""
        result = quota_service.check_clip_quota(starter_user, 25)

        assert result.allowed is False
        assert "exceed monthly limit" in result.reason
        assert result.remaining == 20  # 30 - 10
        assert result.limit == 30

    @patch('src.services.quota_service.QuotaService._get_scheduled_posts_this_week')
    def test_check_scheduling_quota_free_user_disabled(self, mock_scheduled, quota_service, free_user):
        """Test scheduling quota check for free user (disabled)"""
        mock_scheduled.return_value = 0

        result = quota_service.check_scheduling_quota(free_user)

        assert result.allowed is False
        assert "not available on your current plan" in result.reason

    @patch('src.services.quota_service.QuotaService._get_scheduled_posts_this_week')
    def test_check_scheduling_quota_starter_user_within_limit(self, mock_scheduled, quota_service, starter_user):
        """Test scheduling quota check for starter user within limits"""
        mock_scheduled.return_value = 2

        result = quota_service.check_scheduling_quota(starter_user)

        assert result.allowed is True
        assert result.remaining == 3  # 5 - 2
        assert result.limit == 5

    @patch('src.services.quota_service.QuotaService._get_scheduled_posts_this_week')
    def test_check_scheduling_quota_starter_user_exceeds_limit(self, mock_scheduled, quota_service, starter_user):
        """Test scheduling quota check for starter user exceeding limits"""
        mock_scheduled.return_value = 5

        result = quota_service.check_scheduling_quota(starter_user)

        assert result.allowed is False
        assert "Weekly scheduling limit" in result.reason
        assert result.remaining == 0

    def test_check_video_duration_limit_free_user_within_limit(self, quota_service, free_user):
        """Test video duration check for free user within limits"""
        result = quota_service.check_video_duration_limit(free_user, 300)  # 5 minutes

        assert result.allowed is True

    def test_check_video_duration_limit_free_user_exceeds_limit(self, quota_service, free_user):
        """Test video duration check for free user exceeding limits"""
        result = quota_service.check_video_duration_limit(free_user, 900)  # 15 minutes

        assert result.allowed is False
        assert "duration exceeds" in result.reason
        assert result.limit == 600

    def test_check_video_duration_limit_enterprise_unlimited(self, quota_service, enterprise_user):
        """Test video duration check for enterprise user (unlimited)"""
        result = quota_service.check_video_duration_limit(enterprise_user, 10800)  # 3 hours

        assert result.allowed is True

    def test_check_platform_access_free_user(self, quota_service, free_user):
        """Test platform access for free user"""
        assert quota_service.check_platform_access(free_user, "tiktok") is True
        assert quota_service.check_platform_access(free_user, "youtube") is False
        assert quota_service.check_platform_access(free_user, "instagram") is False

    def test_check_platform_access_starter_user(self, quota_service, starter_user):
        """Test platform access for starter user"""
        assert quota_service.check_platform_access(starter_user, "tiktok") is True
        assert quota_service.check_platform_access(starter_user, "youtube") is True
        assert quota_service.check_platform_access(starter_user, "instagram") is False

    def test_check_platform_access_enterprise_user(self, quota_service, enterprise_user):
        """Test platform access for enterprise user"""
        assert quota_service.check_platform_access(enterprise_user, "tiktok") is True
        assert quota_service.check_platform_access(enterprise_user, "youtube") is True
        assert quota_service.check_platform_access(enterprise_user, "instagram") is True

    def test_check_subtitle_style_access_free_user(self, quota_service, free_user):
        """Test subtitle style access for free user"""
        assert quota_service.check_subtitle_style_access(free_user, "clean") is True
        assert quota_service.check_subtitle_style_access(free_user, "minimal") is True
        assert quota_service.check_subtitle_style_access(free_user, "hormozi") is False
        assert quota_service.check_subtitle_style_access(free_user, "neon") is False

    def test_check_subtitle_style_access_starter_user(self, quota_service, starter_user):
        """Test subtitle style access for starter user"""
        assert quota_service.check_subtitle_style_access(starter_user, "clean") is True
        assert quota_service.check_subtitle_style_access(starter_user, "hormozi") is True
        assert quota_service.check_subtitle_style_access(starter_user, "neon") is True
        assert quota_service.check_subtitle_style_access(starter_user, "karaoke") is True

    def test_check_subtitle_style_access_enterprise_user(self, quota_service, enterprise_user):
        """Test subtitle style access for enterprise user (all styles)"""
        assert quota_service.check_subtitle_style_access(enterprise_user, "clean") is True
        assert quota_service.check_subtitle_style_access(enterprise_user, "custom") is True
        assert quota_service.check_subtitle_style_access(enterprise_user, "any_style") is True

    def test_should_apply_watermark_free_user(self, quota_service, free_user):
        """Test watermark requirement for free user"""
        assert quota_service.should_apply_watermark(free_user) is True

    def test_should_apply_watermark_paid_user(self, quota_service, starter_user):
        """Test watermark requirement for paid user"""
        assert quota_service.should_apply_watermark(starter_user) is False

    def test_get_next_reset_date(self, quota_service):
        """Test getting next monthly reset date"""
        reset_date = quota_service._get_next_reset_date()

        # Should be first day of next month
        now = datetime.utcnow()
        if now.month == 12:
            expected = datetime(now.year + 1, 1, 1)
        else:
            expected = datetime(now.year, now.month + 1, 1)

        assert reset_date.year == expected.year
        assert reset_date.month == expected.month
        assert reset_date.day == expected.day

    def test_get_next_week_reset_date(self, quota_service):
        """Test getting next weekly reset date"""
        reset_date = quota_service._get_next_week_reset_date()

        # Should be next Monday
        assert reset_date.weekday() == 0  # Monday
        assert reset_date.hour == 0
        assert reset_date.minute == 0
        assert reset_date.second == 0