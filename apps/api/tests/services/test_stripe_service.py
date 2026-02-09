"""Tests for StripeService"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import stripe

from src.services.stripe_service import StripeService
from src.models.user import User, PlanType
from src.schemas.stripe import CheckoutResponse, PortalResponse, PlanType as SchemaPlanType


@pytest.fixture
def mock_db():
    """Mock database session"""
    db = Mock()
    db.commit = Mock()
    db.rollback = Mock()
    return db


@pytest.fixture
def stripe_service(mock_db):
    """Create StripeService instance with mock db"""
    with patch('src.services.stripe_service.settings') as mock_settings:
        mock_settings.MOCK_MODE = False
        mock_settings.STRIPE_SECRET_KEY = "sk_test_mock"
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_mock"
        mock_settings.FRONTEND_URL = "http://localhost:3000"
        mock_settings.STRIPE_STARTER_PRICE_ID = "price_starter_test"
        mock_settings.STRIPE_PRO_PRICE_ID = "price_pro_test"
        mock_settings.STRIPE_ENTERPRISE_PRICE_ID = "price_enterprise_test"
        return StripeService(mock_db)


@pytest.fixture
def stripe_service_mock_mode(mock_db):
    """Create StripeService instance in mock mode"""
    with patch('src.services.stripe_service.settings') as mock_settings:
        mock_settings.MOCK_MODE = True
        mock_settings.STRIPE_SECRET_KEY = None
        return StripeService(mock_db)


@pytest.fixture
def test_user():
    """Create a test user"""
    user = Mock(spec=User)
    user.id = "user-123"
    user.email = "test@example.com"
    user.name = "Test User"
    user.stripe_customer_id = None
    return user


@pytest.fixture
def test_user_with_customer():
    """Create a test user with Stripe customer ID"""
    user = Mock(spec=User)
    user.id = "user-456"
    user.email = "test2@example.com"
    user.name = "Test User 2"
    user.stripe_customer_id = "cus_test123"
    return user


class TestStripeService:
    """Test cases for StripeService"""

    async def test_create_checkout_session_mock_mode(self, stripe_service_mock_mode, test_user):
        """Test checkout session creation in mock mode"""
        result = await stripe_service_mock_mode.create_checkout_session(
            user=test_user,
            plan=SchemaPlanType.STARTER
        )

        assert isinstance(result, CheckoutResponse)
        assert "mock-stripe.com" in result.checkout_url
        assert "mock_session_" in result.session_id

    @patch('stripe.checkout.Session.create')
    @patch.object(StripeService, '_get_or_create_customer')
    async def test_create_checkout_session_real_mode(
        self,
        mock_get_customer,
        mock_stripe_create,
        stripe_service,
        test_user
    ):
        """Test checkout session creation in real mode"""
        # Setup mocks
        mock_get_customer.return_value = "cus_test123"
        mock_stripe_create.return_value = Mock(
            id="cs_test123",
            url="https://checkout.stripe.com/pay/cs_test123"
        )

        # Test
        result = await stripe_service.create_checkout_session(
            user=test_user,
            plan=SchemaPlanType.STARTER,
            success_url="http://localhost:3000/success",
            cancel_url="http://localhost:3000/cancel"
        )

        # Assertions
        assert isinstance(result, CheckoutResponse)
        assert result.checkout_url == "https://checkout.stripe.com/pay/cs_test123"
        assert result.session_id == "cs_test123"

        # Verify Stripe API was called correctly
        mock_stripe_create.assert_called_once()
        call_args = mock_stripe_create.call_args[1]
        assert call_args['customer'] == "cus_test123"
        assert call_args['mode'] == 'subscription'
        assert call_args['line_items'][0]['price'] == "price_starter_test"

    @patch('stripe.checkout.Session.create')
    async def test_create_checkout_session_stripe_error(self, mock_stripe_create, stripe_service, test_user):
        """Test checkout session creation with Stripe error"""
        # Setup error
        mock_stripe_create.side_effect = stripe.error.StripeError("Payment failed")

        # Test and verify exception
        with pytest.raises(Exception) as exc_info:
            await stripe_service.create_checkout_session(
                user=test_user,
                plan=SchemaPlanType.STARTER
            )

        assert "Failed to create checkout session" in str(exc_info.value)

    async def test_create_customer_portal_mock_mode(self, stripe_service_mock_mode, test_user_with_customer):
        """Test customer portal creation in mock mode"""
        result = await stripe_service_mock_mode.create_customer_portal(test_user_with_customer)

        assert isinstance(result, PortalResponse)
        assert "mock-stripe.com/portal" in result.portal_url

    @patch('stripe.billing_portal.Session.create')
    async def test_create_customer_portal_real_mode(
        self,
        mock_portal_create,
        stripe_service,
        test_user_with_customer
    ):
        """Test customer portal creation in real mode"""
        # Setup mock
        mock_portal_create.return_value = Mock(
            url="https://billing.stripe.com/portal/session_test123"
        )

        # Test
        result = await stripe_service.create_customer_portal(test_user_with_customer)

        # Assertions
        assert isinstance(result, PortalResponse)
        assert result.portal_url == "https://billing.stripe.com/portal/session_test123"

        # Verify Stripe API was called correctly
        mock_portal_create.assert_called_once()
        call_args = mock_portal_create.call_args[1]
        assert call_args['customer'] == "cus_test123"
        assert "billing" in call_args['return_url']

    async def test_create_customer_portal_no_customer_id(self, stripe_service, test_user):
        """Test customer portal creation without Stripe customer ID"""
        with pytest.raises(ValueError) as exc_info:
            await stripe_service.create_customer_portal(test_user)

        assert "does not have a Stripe customer ID" in str(exc_info.value)

    @patch('stripe.Webhook.construct_event')
    async def test_verify_webhook_signature_success(self, mock_construct, stripe_service):
        """Test successful webhook signature verification"""
        mock_construct.return_value = {"type": "checkout.session.completed"}

        result = await stripe_service.verify_webhook_signature(
            payload=b'{"test": "data"}',
            sig_header="t=123,v1=signature"
        )

        assert result is True
        mock_construct.assert_called_once()

    @patch('stripe.Webhook.construct_event')
    async def test_verify_webhook_signature_failure(self, mock_construct, stripe_service):
        """Test failed webhook signature verification"""
        mock_construct.side_effect = stripe.error.SignatureVerificationError("Invalid signature", "sig")

        result = await stripe_service.verify_webhook_signature(
            payload=b'{"test": "data"}',
            sig_header="t=123,v1=invalid_signature"
        )

        assert result is False

    async def test_verify_webhook_signature_mock_mode(self, stripe_service_mock_mode):
        """Test webhook signature verification in mock mode"""
        result = await stripe_service_mock_mode.verify_webhook_signature(
            payload=b'{"test": "data"}',
            sig_header="t=123,v1=signature"
        )

        assert result is True  # Always returns True in mock mode

    @patch('stripe.Customer.create')
    async def test_get_or_create_customer_new_customer(self, mock_customer_create, stripe_service, test_user):
        """Test creating new Stripe customer"""
        # Setup mock
        mock_customer_create.return_value = Mock(id="cus_new123")

        # Test
        customer_id = await stripe_service._get_or_create_customer(test_user)

        # Assertions
        assert customer_id == "cus_new123"
        assert test_user.stripe_customer_id == "cus_new123"
        stripe_service.db.commit.assert_called_once()

        # Verify Stripe API was called correctly
        mock_customer_create.assert_called_once()
        call_args = mock_customer_create.call_args[1]
        assert call_args['email'] == test_user.email
        assert call_args['name'] == test_user.name

    async def test_get_or_create_customer_existing_customer(self, stripe_service, test_user_with_customer):
        """Test using existing Stripe customer"""
        customer_id = await stripe_service._get_or_create_customer(test_user_with_customer)

        assert customer_id == "cus_test123"
        # Should not commit since no changes made
        stripe_service.db.commit.assert_not_called()

    @patch('stripe.Subscription.list')
    async def test_get_subscription_by_customer_found(self, mock_sub_list, stripe_service):
        """Test getting subscription by customer ID"""
        # Setup mock
        mock_subscription = Mock(
            id="sub_test123",
            status="active",
            current_period_end=1640995200
        )
        mock_sub_list.return_value.data = [mock_subscription]

        # Test
        result = await stripe_service.get_subscription_by_customer("cus_test123")

        # Assertions
        assert result == mock_subscription
        mock_sub_list.assert_called_once_with(
            customer="cus_test123",
            status='active',
            limit=1
        )

    @patch('stripe.Subscription.list')
    async def test_get_subscription_by_customer_not_found(self, mock_sub_list, stripe_service):
        """Test getting subscription by customer ID when none exists"""
        # Setup mock
        mock_sub_list.return_value.data = []

        # Test
        result = await stripe_service.get_subscription_by_customer("cus_test123")

        # Assertions
        assert result is None

    async def test_get_subscription_by_customer_mock_mode(self, stripe_service_mock_mode):
        """Test getting subscription in mock mode"""
        result = await stripe_service_mock_mode.get_subscription_by_customer("cus_test123")

        assert result is not None
        assert result["id"] == "mock_sub_cus_test123"
        assert result["status"] == "active"

    def test_get_plan_from_price_id_valid(self, stripe_service):
        """Test getting plan from valid price ID"""
        plan = stripe_service.get_plan_from_price_id("price_starter_test")
        assert plan == PlanType.STARTER

        plan = stripe_service.get_plan_from_price_id("price_pro_test")
        assert plan == PlanType.PRO

        plan = stripe_service.get_plan_from_price_id("price_enterprise_test")
        assert plan == PlanType.ENTERPRISE

    def test_get_plan_from_price_id_invalid(self, stripe_service):
        """Test getting plan from invalid price ID"""
        plan = stripe_service.get_plan_from_price_id("price_invalid")
        assert plan is None