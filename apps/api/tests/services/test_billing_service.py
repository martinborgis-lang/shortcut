"""Tests for BillingService"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock

from src.services.billing_service import BillingService
from src.models.user import User, PlanType
from src.schemas.billing import BillingInfo, UsageStats, PlanFeatures


@pytest.fixture
def mock_db():
    """Mock database session"""
    db = Mock()
    db.commit = Mock()
    db.rollback = Mock()
    return db


@pytest.fixture
def mock_quota_service():
    """Mock QuotaService"""
    return Mock()


@pytest.fixture
def mock_stripe_service():
    """Mock StripeService"""
    service = Mock()
    service.get_subscription_by_customer = AsyncMock()
    return service


@pytest.fixture
def billing_service(mock_db):
    """Create BillingService instance with mock db"""
    return BillingService(mock_db)


@pytest.fixture
def free_user():
    """Create a free plan user"""
    user = Mock(spec=User)
    user.id = "user-123"
    user.plan = PlanType.FREE
    user.monthly_minutes_used = 15
    user.monthly_clips_generated = 2
    user.stripe_customer_id = None
    return user


@pytest.fixture
def starter_user():
    """Create a starter plan user"""
    user = Mock(spec=User)
    user.id = "user-456"
    user.plan = PlanType.STARTER
    user.monthly_minutes_used = 60
    user.monthly_clips_generated = 10
    user.stripe_customer_id = "cus_test123"
    return user


class TestBillingService:
    """Test cases for BillingService"""

    @patch('src.services.billing_service.BillingService.get_usage_stats')
    @patch('src.services.billing_service.QuotaService')
    async def test_get_billing_info_free_user(self, mock_quota_class, mock_usage_stats, billing_service, free_user):
        """Test getting billing info for free user"""
        # Setup mocks
        mock_quota_service = Mock()
        mock_quota_class.return_value = mock_quota_service
        mock_quota_service.get_plan_limits.return_value = Mock(
            monthly_upload_minutes=30,
            monthly_clips=5,
            scheduling_enabled=False
        )

        mock_usage_stats.return_value = Mock(
            monthly_minutes_used=15,
            monthly_clips_generated=2,
            scheduled_posts_this_week=0
        )

        # Test
        billing_info = await billing_service.get_billing_info(free_user)

        # Assertions
        assert billing_info.plan == PlanType.FREE
        assert billing_info.status == "active"
        assert billing_info.next_payment_date is None
        assert billing_info.limits.monthly_upload_minutes == 30

    @patch('src.services.billing_service.BillingService.get_usage_stats')
    @patch('src.services.billing_service.QuotaService')
    @patch('src.services.billing_service.StripeService')
    async def test_get_billing_info_paid_user(self, mock_stripe_class, mock_quota_class, mock_usage_stats, billing_service, starter_user):
        """Test getting billing info for paid user"""
        # Setup mocks
        mock_quota_service = Mock()
        mock_quota_class.return_value = mock_quota_service
        mock_quota_service.get_plan_limits.return_value = Mock(
            monthly_upload_minutes=120,
            monthly_clips=30,
            scheduling_enabled=True
        )

        mock_stripe_service = Mock()
        mock_stripe_class.return_value = mock_stripe_service
        mock_stripe_service.get_subscription_by_customer = AsyncMock(return_value={
            'current_period_end': 1640995200,  # 2022-01-01
            'status': 'active'
        })

        mock_usage_stats.return_value = Mock(
            monthly_minutes_used=60,
            monthly_clips_generated=10,
            scheduled_posts_this_week=2
        )

        # Test
        billing_info = await billing_service.get_billing_info(starter_user)

        # Assertions
        assert billing_info.plan == PlanType.STARTER
        assert billing_info.status == "active"
        assert billing_info.next_payment_date is not None
        assert billing_info.limits.monthly_upload_minutes == 120

    @patch('src.services.billing_service.QuotaService')
    async def test_track_upload_minutes_success(self, mock_quota_class, billing_service, free_user):
        """Test successful upload minutes tracking"""
        # Setup mocks
        mock_quota_service = Mock()
        mock_quota_class.return_value = mock_quota_service
        mock_quota_service.check_upload_quota.return_value = Mock(allowed=True)

        # Test
        result = await billing_service.track_upload_minutes(free_user, 10.5)

        # Assertions
        assert result is True
        assert free_user.monthly_minutes_used == 25  # 15 + 10
        billing_service.db.commit.assert_called_once()

    @patch('src.services.billing_service.QuotaService')
    async def test_track_upload_minutes_quota_exceeded(self, mock_quota_class, billing_service, free_user):
        """Test upload minutes tracking when quota exceeded"""
        # Setup mocks
        mock_quota_service = Mock()
        mock_quota_class.return_value = mock_quota_service
        mock_quota_service.check_upload_quota.return_value = Mock(
            allowed=False,
            reason="Quota exceeded"
        )

        # Test
        result = await billing_service.track_upload_minutes(free_user, 20.0)

        # Assertions
        assert result is False
        assert free_user.monthly_minutes_used == 15  # unchanged
        billing_service.db.commit.assert_not_called()

    async def test_reset_monthly_usage_success(self, billing_service, starter_user):
        """Test successful monthly usage reset"""
        # Setup initial values
        starter_user.monthly_minutes_used = 100
        starter_user.monthly_clips_generated = 25

        # Test
        result = await billing_service.reset_monthly_usage(starter_user)

        # Assertions
        assert result is True
        assert starter_user.monthly_minutes_used == 0
        assert starter_user.monthly_clips_generated == 0
        billing_service.db.commit.assert_called_once()

    async def test_reset_monthly_usage_error(self, billing_service, starter_user):
        """Test monthly usage reset with database error"""
        # Setup error
        billing_service.db.commit.side_effect = Exception("Database error")

        # Test
        result = await billing_service.reset_monthly_usage(starter_user)

        # Assertions
        assert result is False
        billing_service.db.rollback.assert_called_once()

    async def test_update_user_plan_success(self, billing_service, free_user):
        """Test successful user plan update"""
        # Test
        result = await billing_service.update_user_plan(
            free_user,
            PlanType.STARTER,
            "active"
        )

        # Assertions
        assert result is True
        assert free_user.plan == PlanType.STARTER
        assert free_user.subscription_status == "active"
        billing_service.db.commit.assert_called_once()

    async def test_start_grace_period_success(self, billing_service, starter_user):
        """Test successful grace period start"""
        # Test
        result = await billing_service.start_grace_period(starter_user, days=7)

        # Assertions
        assert result is True
        assert starter_user.subscription_status == "past_due"
        assert hasattr(starter_user, 'grace_period_end')
        billing_service.db.commit.assert_called_once()

    async def test_end_grace_period_downgrades_to_free(self, billing_service, starter_user):
        """Test grace period end downgrades user to free"""
        with patch.object(billing_service, 'update_user_plan', return_value=True) as mock_update:
            # Test
            result = await billing_service.end_grace_period(starter_user)

            # Assertions
            assert result is True
            mock_update.assert_called_once_with(starter_user, PlanType.FREE, "canceled")

    @patch('src.services.billing_service.BillingService.get_user_invoices')
    @patch('src.services.billing_service.BillingService.get_billing_info')
    async def test_get_billing_overview(self, mock_billing_info, mock_invoices, billing_service, starter_user):
        """Test getting complete billing overview"""
        # Setup mocks
        mock_billing_info.return_value = Mock(spec=BillingInfo)
        mock_invoices.return_value = [
            Mock(id="inv_123", amount=999, status="paid"),
            Mock(id="inv_456", amount=999, status="paid")
        ]

        # Test
        overview = await billing_service.get_billing_overview(starter_user)

        # Assertions
        assert overview.billing_info is not None
        assert len(overview.invoices) == 2
        mock_billing_info.assert_called_once_with(starter_user)
        mock_invoices.assert_called_once_with(starter_user)

    def test_get_available_plans(self, billing_service):
        """Test getting available subscription plans"""
        plans = billing_service.get_available_plans()

        # Assertions
        assert len(plans) == 4  # free, starter, pro, enterprise
        assert all(isinstance(plan, PlanFeatures) for plan in plans)

        # Check free plan
        free_plan = next(p for p in plans if p.name == "Free")
        assert free_plan.price_cents == 0
        assert "30 minutes" in free_plan.features[0]

        # Check starter plan
        starter_plan = next(p for p in plans if p.name == "Starter")
        assert starter_plan.price_cents == 999
        assert starter_plan.popular is True

    @patch('src.services.billing_service.StripeService')
    async def test_get_user_invoices_with_stripe_data(self, mock_stripe_class, billing_service, starter_user):
        """Test getting user invoices from Stripe"""
        # Setup mock Stripe service
        mock_stripe_service = Mock()
        mock_stripe_class.return_value = mock_stripe_service
        mock_stripe_service.mock_mode = False

        # Setup mock Stripe data
        with patch('stripe.Invoice.list') as mock_invoice_list:
            mock_invoice_list.return_value.data = [
                Mock(
                    id="inv_test123",
                    created=1640995200,
                    amount_paid=999,
                    status="paid",
                    invoice_pdf="https://stripe.com/invoice.pdf"
                )
            ]

            # Test
            invoices = await billing_service.get_user_invoices(starter_user)

            # Assertions
            assert len(invoices) == 1
            assert invoices[0].id == "inv_test123"
            assert invoices[0].amount == 999
            assert invoices[0].status == "paid"
            assert invoices[0].pdf_url is not None

    async def test_get_user_invoices_mock_mode(self, billing_service, free_user):
        """Test getting user invoices in mock mode"""
        with patch.object(billing_service.stripe_service, 'mock_mode', True):
            # Test
            invoices = await billing_service.get_user_invoices(free_user)

            # Assertions
            assert len(invoices) == 1
            assert invoices[0].id == "mock_inv_1"
            assert invoices[0].amount == 999