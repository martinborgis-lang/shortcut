"""Stripe service for payment processing and webhook handling"""

import stripe
import structlog
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from ..config import settings
from ..models.user import User, PlanType
from ..schemas.stripe import (
    PlanType as SchemaPlanType,
    CheckoutResponse,
    PortalResponse,
    MockStripeResponse
)

logger = structlog.get_logger()

# Configure Stripe (only if key is available)
if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY

# Plan to Price ID mapping
PLAN_PRICE_IDS = {
    SchemaPlanType.STARTER: settings.STRIPE_STARTER_PRICE_ID,
    SchemaPlanType.PRO: settings.STRIPE_PRO_PRICE_ID,
    SchemaPlanType.ENTERPRISE: settings.STRIPE_ENTERPRISE_PRICE_ID,
}


class StripeService:
    """Service for handling Stripe operations"""

    def __init__(self, db: Session):
        self.db = db
        self.mock_mode = settings.MOCK_MODE or not settings.STRIPE_SECRET_KEY

    async def create_checkout_session(
        self,
        user: User,
        plan: SchemaPlanType,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> CheckoutResponse:
        """
        Create a Stripe checkout session for plan subscription

        Args:
            user: User object
            plan: Plan to subscribe to
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect after cancelled payment

        Returns:
            CheckoutResponse with checkout URL and session ID
        """
        logger.info(
            "Creating checkout session",
            user_id=str(user.id),
            plan=plan.value,
            mock_mode=self.mock_mode
        )

        # Mock mode for development
        if self.mock_mode:
            return CheckoutResponse(
                checkout_url=f"https://mock-stripe.com/checkout?plan={plan.value}",
                session_id=f"mock_session_{user.id}_{plan.value}"
            )

        # Get or create Stripe customer
        customer_id = await self._get_or_create_customer(user)

        # Get price ID for the plan
        price_id = PLAN_PRICE_IDS.get(plan)
        if not price_id:
            raise ValueError(f"No price ID configured for plan: {plan}")

        # Default URLs
        if not success_url:
            success_url = f"{settings.FRONTEND_URL}/billing/success"
        if not cancel_url:
            cancel_url = f"{settings.FRONTEND_URL}/pricing"

        try:
            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=cancel_url,
                metadata={
                    'user_id': str(user.id),
                    'plan': plan.value,
                    'email': user.email
                },
                billing_address_collection='auto',
                customer_update={
                    'address': 'auto'
                }
            )

            logger.info(
                "Checkout session created successfully",
                session_id=session.id,
                user_id=str(user.id)
            )

            return CheckoutResponse(
                checkout_url=session.url,
                session_id=session.id
            )

        except stripe.error.StripeError as e:
            logger.error(
                "Failed to create checkout session",
                error=str(e),
                user_id=str(user.id),
                plan=plan.value
            )
            raise Exception(f"Failed to create checkout session: {str(e)}")

    async def create_customer_portal(self, user: User) -> PortalResponse:
        """
        Create a Stripe customer portal session

        Args:
            user: User object

        Returns:
            PortalResponse with portal URL
        """
        logger.info(
            "Creating customer portal session",
            user_id=str(user.id),
            mock_mode=self.mock_mode
        )

        # Mock mode for development
        if self.mock_mode:
            return PortalResponse(
                portal_url=f"https://mock-stripe.com/portal?user={user.id}"
            )

        # Check if user has Stripe customer ID
        if not user.stripe_customer_id:
            raise ValueError("User does not have a Stripe customer ID")

        try:
            # Create portal session
            session = stripe.billing_portal.Session.create(
                customer=user.stripe_customer_id,
                return_url=f"{settings.FRONTEND_URL}/settings/billing"
            )

            logger.info(
                "Customer portal session created successfully",
                user_id=str(user.id)
            )

            return PortalResponse(portal_url=session.url)

        except stripe.error.StripeError as e:
            logger.error(
                "Failed to create customer portal session",
                error=str(e),
                user_id=str(user.id)
            )
            raise Exception(f"Failed to create customer portal session: {str(e)}")

    async def verify_webhook_signature(self, payload: bytes, sig_header: str) -> bool:
        """
        Verify Stripe webhook signature

        Args:
            payload: Raw webhook payload
            sig_header: Stripe signature header

        Returns:
            bool: True if signature is valid
        """
        if self.mock_mode:
            logger.info("Mock mode: Skipping webhook signature verification")
            return True

        if not settings.STRIPE_WEBHOOK_SECRET:
            logger.warning("No webhook secret configured")
            return False

        try:
            stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            return True
        except (ValueError, stripe.error.SignatureVerificationError) as e:
            logger.error("Webhook signature verification failed", error=str(e))
            return False

    async def _get_or_create_customer(self, user: User) -> str:
        """
        Get existing or create new Stripe customer

        Args:
            user: User object

        Returns:
            str: Stripe customer ID
        """
        # Return existing customer ID if available
        if user.stripe_customer_id:
            return user.stripe_customer_id

        try:
            # Create new customer
            customer = stripe.Customer.create(
                email=user.email,
                name=user.name,
                metadata={
                    'user_id': str(user.id),
                    'clerk_id': user.clerk_id
                }
            )

            # Save customer ID to user
            user.stripe_customer_id = customer.id
            self.db.commit()

            logger.info(
                "Created new Stripe customer",
                customer_id=customer.id,
                user_id=str(user.id)
            )

            return customer.id

        except stripe.error.StripeError as e:
            logger.error(
                "Failed to create Stripe customer",
                error=str(e),
                user_id=str(user.id)
            )
            raise Exception(f"Failed to create Stripe customer: {str(e)}")

    async def get_subscription_by_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get active subscription for customer

        Args:
            customer_id: Stripe customer ID

        Returns:
            Optional subscription object
        """
        if self.mock_mode:
            return {
                "id": f"mock_sub_{customer_id}",
                "status": "active",
                "current_period_end": 1234567890,
                "items": {"data": [{"price": {"id": "mock_price"}}]}
            }

        try:
            subscriptions = stripe.Subscription.list(
                customer=customer_id,
                status='active',
                limit=1
            )

            if subscriptions.data:
                return subscriptions.data[0]
            return None

        except stripe.error.StripeError as e:
            logger.error(
                "Failed to get customer subscription",
                error=str(e),
                customer_id=customer_id
            )
            return None

    def get_plan_from_price_id(self, price_id: str) -> Optional[PlanType]:
        """
        Get plan type from Stripe price ID

        Args:
            price_id: Stripe price ID

        Returns:
            Optional PlanType
        """
        price_to_plan = {v: k.value for k, v in PLAN_PRICE_IDS.items() if v}
        schema_plan = price_to_plan.get(price_id)

        if schema_plan:
            return PlanType(schema_plan)
        return None