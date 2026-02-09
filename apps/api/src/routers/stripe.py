"""Stripe router for payment processing endpoints"""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..middleware.auth import get_current_user
from ..schemas.stripe import (
    CreateCheckoutRequest,
    CheckoutResponse,
    PortalResponse,
    PlanType as SchemaPlanType
)
from ..services.stripe_service import StripeService

logger = structlog.get_logger()

router = APIRouter()


@router.post("/create-checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CreateCheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create Stripe checkout session for plan subscription

    - **plan**: Subscription plan to purchase (starter, pro, enterprise)
    - **success_url**: Optional URL to redirect after successful payment
    - **cancel_url**: Optional URL to redirect after cancelled payment

    Returns checkout URL for Stripe payment page.
    """
    try:
        logger.info(
            "Creating checkout session",
            user_id=str(current_user.id),
            plan=request.plan.value,
            current_plan=current_user.plan.value
        )

        # Check if user is trying to "upgrade" to the same plan
        if current_user.plan.value == request.plan.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You are already subscribed to the {request.plan.value} plan"
            )

        # Check if user is trying to "upgrade" to free plan
        if request.plan == SchemaPlanType.STARTER and current_user.plan.value in ["pro", "enterprise"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot downgrade to a lower plan. Use the customer portal to manage your subscription."
            )

        # Initialize Stripe service
        stripe_service = StripeService(db)

        # Create checkout session
        response = await stripe_service.create_checkout_session(
            user=current_user,
            plan=request.plan,
            success_url=request.success_url,
            cancel_url=request.cancel_url
        )

        logger.info(
            "Checkout session created successfully",
            user_id=str(current_user.id),
            session_id=response.session_id
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to create checkout session",
            error=str(e),
            user_id=str(current_user.id),
            plan=request.plan.value
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session. Please try again."
        )


@router.post("/create-portal", response_model=PortalResponse)
async def create_customer_portal(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create Stripe customer portal session for subscription management

    Allows users to:
    - Update payment methods
    - View billing history
    - Update billing address
    - Cancel or modify subscriptions

    Returns portal URL for Stripe customer portal.
    """
    try:
        logger.info(
            "Creating customer portal session",
            user_id=str(current_user.id),
            plan=current_user.plan.value,
            has_stripe_id=bool(current_user.stripe_customer_id)
        )

        # Check if user has an active subscription
        if current_user.plan.value == "free":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You need an active subscription to access the customer portal. Please upgrade first."
            )

        # Check if user has Stripe customer ID
        if not current_user.stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No billing account found. Please contact support for assistance."
            )

        # Initialize Stripe service
        stripe_service = StripeService(db)

        # Create portal session
        response = await stripe_service.create_customer_portal(current_user)

        logger.info(
            "Customer portal session created successfully",
            user_id=str(current_user.id)
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to create customer portal session",
            error=str(e),
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create customer portal session. Please try again."
        )


@router.get("/plans")
async def get_available_plans():
    """
    Get list of available subscription plans with pricing and features

    Returns plan information for display on pricing page.
    """
    try:
        from ..services.billing_service import BillingService
        from ..database import get_db

        # Create a temporary database session for the service
        db = next(get_db())
        billing_service = BillingService(db)

        plans = billing_service.get_available_plans()

        return {"plans": plans}

    except Exception as e:
        logger.error("Failed to get available plans", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve plans"
        )


@router.get("/billing-info")
async def get_billing_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's billing information and subscription status

    Returns:
    - Current plan and status
    - Usage statistics
    - Next payment date
    - Recent invoices
    """
    try:
        from ..services.billing_service import BillingService

        billing_service = BillingService(db)
        billing_overview = await billing_service.get_billing_overview(current_user)

        return billing_overview.dict()

    except Exception as e:
        logger.error(
            "Failed to get billing info",
            error=str(e),
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve billing information"
        )


@router.get("/quota-status")
async def get_quota_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's current quota usage and limits

    Returns quota information for all plan features:
    - Upload minutes remaining
    - Clips remaining
    - Scheduling availability
    """
    try:
        from ..services.quota_service import QuotaService

        quota_service = QuotaService(db)
        limits = quota_service.get_plan_limits(current_user.plan)

        # Get current usage
        upload_quota = quota_service.check_upload_quota(current_user, 0)  # Check with 0 to get remaining
        clip_quota = quota_service.check_clip_quota(current_user, 0)
        scheduling_quota = quota_service.check_scheduling_quota(current_user)

        return {
            "plan": current_user.plan.value,
            "limits": limits.dict(),
            "usage": {
                "upload_minutes": {
                    "used": current_user.monthly_minutes_used or 0,
                    "remaining": upload_quota.remaining,
                    "limit": upload_quota.limit,
                    "reset_date": upload_quota.reset_date
                },
                "clips": {
                    "generated": getattr(current_user, 'monthly_clips_generated', 0),
                    "remaining": clip_quota.remaining,
                    "limit": clip_quota.limit,
                    "reset_date": clip_quota.reset_date
                },
                "scheduling": {
                    "enabled": limits.scheduling_enabled,
                    "remaining": scheduling_quota.remaining,
                    "limit": scheduling_quota.limit,
                    "reset_date": scheduling_quota.reset_date
                }
            }
        }

    except Exception as e:
        logger.error(
            "Failed to get quota status",
            error=str(e),
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve quota information"
        )