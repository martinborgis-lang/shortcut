"""
Webhook handlers for external services
"""
import hmac
import hashlib
import json
import structlog
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Request, status, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from ..config import settings
from ..database import get_db
from ..models.user import User, PlanType

logger = structlog.get_logger()

router = APIRouter()


def verify_clerk_webhook(request: Request, payload: bytes) -> bool:
    """Verify Clerk webhook signature"""
    if not settings.CLERK_WEBHOOK_SECRET:
        logger.error("CLERK_WEBHOOK_SECRET not configured")
        return False

    # Get signature from headers
    signature = request.headers.get("svix-signature")
    if not signature:
        logger.error("No signature found in webhook headers")
        return False

    # Parse signature header (format: "v1,signature")
    try:
        sig_parts = signature.split(",")
        sig_dict = {}
        for part in sig_parts:
            key, value = part.split("=", 1)
            sig_dict[key] = value

        webhook_signature = sig_dict.get("v1")
        if not webhook_signature:
            logger.error("No v1 signature found")
            return False

    except Exception as e:
        logger.error("Failed to parse signature header", error=str(e))
        return False

    # Verify signature
    expected_signature = hmac.new(
        settings.CLERK_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(webhook_signature, expected_signature):
        logger.error("Invalid webhook signature")
        return False

    return True


async def handle_user_created(event_data: Dict[str, Any], db: Session) -> None:
    """Handle user.created event from Clerk"""
    try:
        user_data = event_data.get("data", {})
        clerk_id = user_data.get("id")

        if not clerk_id:
            logger.error("No user ID in webhook data")
            return

        # Extract user information
        email_addresses = user_data.get("email_addresses", [])
        primary_email = None
        for email in email_addresses:
            if email.get("id") == user_data.get("primary_email_address_id"):
                primary_email = email.get("email_address")
                break

        if not primary_email:
            logger.error("No primary email found", clerk_id=clerk_id)
            return

        # Check if user already exists
        existing_user = db.query(User).filter(User.clerk_id == clerk_id).first()
        if existing_user:
            logger.info("User already exists", clerk_id=clerk_id, user_id=str(existing_user.id))
            return

        # Create new user
        new_user = User(
            clerk_id=clerk_id,
            email=primary_email,
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            profile_image_url=user_data.get("image_url"),
            plan=PlanType.FREE,
            monthly_minutes_used=0,
            created_at=datetime.now(timezone.utc)
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        logger.info(
            "User created successfully",
            user_id=str(new_user.id),
            clerk_id=clerk_id,
            email=primary_email,
            plan=new_user.plan.value
        )

    except Exception as e:
        logger.error("Failed to create user", error=str(e), event_data=event_data)
        db.rollback()
        raise


async def handle_user_updated(event_data: Dict[str, Any], db: Session) -> None:
    """Handle user.updated event from Clerk"""
    try:
        user_data = event_data.get("data", {})
        clerk_id = user_data.get("id")

        if not clerk_id:
            logger.error("No user ID in webhook data")
            return

        # Find existing user
        user = db.query(User).filter(User.clerk_id == clerk_id).first()
        if not user:
            logger.warning("User not found for update", clerk_id=clerk_id)
            return

        # Update user information
        email_addresses = user_data.get("email_addresses", [])
        for email in email_addresses:
            if email.get("id") == user_data.get("primary_email_address_id"):
                user.email = email.get("email_address")
                break

        user.first_name = user_data.get("first_name")
        user.last_name = user_data.get("last_name")
        user.profile_image_url = user_data.get("image_url")
        user.updated_at = datetime.now(timezone.utc)

        db.commit()

        logger.info(
            "User updated successfully",
            user_id=str(user.id),
            clerk_id=clerk_id
        )

    except Exception as e:
        logger.error("Failed to update user", error=str(e), event_data=event_data)
        db.rollback()
        raise


async def handle_user_deleted(event_data: Dict[str, Any], db: Session) -> None:
    """Handle user.deleted event from Clerk"""
    try:
        user_data = event_data.get("data", {})
        clerk_id = user_data.get("id")

        if not clerk_id:
            logger.error("No user ID in webhook data")
            return

        # Find and soft delete user (or hard delete based on requirements)
        user = db.query(User).filter(User.clerk_id == clerk_id).first()
        if not user:
            logger.warning("User not found for deletion", clerk_id=clerk_id)
            return

        # For now, we'll soft delete by keeping the record but marking it
        # You might want to hard delete or implement a proper soft delete field
        db.delete(user)
        db.commit()

        logger.info(
            "User deleted successfully",
            user_id=str(user.id),
            clerk_id=clerk_id
        )

    except Exception as e:
        logger.error("Failed to delete user", error=str(e), event_data=event_data)
        db.rollback()
        raise


@router.post("/clerk")
async def clerk_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle Clerk webhooks for user events

    This endpoint handles:
    - user.created: Creates a new user in the database
    - user.updated: Updates user information
    - user.deleted: Removes user from database
    """
    try:
        # Get raw body
        body = await request.body()

        # Verify webhook signature
        if not verify_clerk_webhook(request, body):
            logger.error("Invalid webhook signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )

        # Parse JSON
        try:
            event_data = json.loads(body.decode())
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in webhook", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload"
            )

        event_type = event_data.get("type")
        if not event_type:
            logger.error("No event type in webhook")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing event type"
            )

        logger.info("Received Clerk webhook", event_type=event_type)

        # Handle different event types
        if event_type == "user.created":
            await handle_user_created(event_data, db)
        elif event_type == "user.updated":
            await handle_user_updated(event_data, db)
        elif event_type == "user.deleted":
            await handle_user_deleted(event_data, db)
        else:
            logger.warning("Unhandled event type", event_type=event_type)

        return {"status": "ok", "event_type": event_type}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in webhook handler", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


async def verify_stripe_webhook(request: Request, payload: bytes) -> bool:
    """Verify Stripe webhook signature"""
    try:
        from ..services.stripe_service import StripeService

        # Get database session
        db = next(get_db())
        stripe_service = StripeService(db)

        # Get signature from headers
        sig_header = request.headers.get("stripe-signature")
        if not sig_header:
            logger.error("No Stripe signature found in webhook headers")
            return False

        # Verify signature
        return await stripe_service.verify_webhook_signature(payload, sig_header)

    except Exception as e:
        logger.error("Error verifying Stripe webhook", error=str(e))
        return False


async def handle_checkout_session_completed(event_data: Dict[str, Any], db: Session) -> None:
    """Handle checkout.session.completed event from Stripe"""
    try:
        session_data = event_data.get("data", {}).get("object", {})

        # Extract metadata
        metadata = session_data.get("metadata", {})
        user_id = metadata.get("user_id")
        plan = metadata.get("plan")

        if not user_id or not plan:
            logger.error("Missing user_id or plan in checkout session metadata", metadata=metadata)
            return

        # Find user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error("User not found for checkout session", user_id=user_id)
            return

        # Update user with Stripe customer ID and subscription info
        user.stripe_customer_id = session_data.get("customer")

        # Import PlanType enum and update plan
        try:
            new_plan = PlanType(plan)
            user.plan = new_plan
            user.subscription_status = "active"

            # Clear any grace period
            if hasattr(user, 'grace_period_end'):
                user.grace_period_end = None

        except ValueError:
            logger.error("Invalid plan type in metadata", plan=plan)
            return

        db.commit()

        logger.info(
            "User plan updated from checkout session",
            user_id=user_id,
            new_plan=plan,
            customer_id=user.stripe_customer_id
        )

    except Exception as e:
        logger.error("Failed to handle checkout session completed", error=str(e), event_data=event_data)
        db.rollback()
        raise


async def handle_subscription_updated(event_data: Dict[str, Any], db: Session) -> None:
    """Handle customer.subscription.updated event from Stripe"""
    try:
        subscription_data = event_data.get("data", {}).get("object", {})

        customer_id = subscription_data.get("customer")
        subscription_status = subscription_data.get("status")

        if not customer_id:
            logger.error("No customer ID in subscription update")
            return

        # Find user by Stripe customer ID
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if not user:
            logger.warning("User not found for subscription update", customer_id=customer_id)
            return

        # Get plan from subscription items
        items = subscription_data.get("items", {}).get("data", [])
        if not items:
            logger.error("No subscription items found")
            return

        price_id = items[0].get("price", {}).get("id")
        if not price_id:
            logger.error("No price ID found in subscription")
            return

        # Import StripeService to get plan from price ID
        from ..services.stripe_service import StripeService
        stripe_service = StripeService(db)
        new_plan = stripe_service.get_plan_from_price_id(price_id)

        if not new_plan:
            logger.error("Unknown price ID", price_id=price_id)
            return

        # Update user plan and status
        old_plan = user.plan
        user.plan = new_plan
        user.subscription_status = subscription_status

        # Clear grace period if subscription is active
        if subscription_status == "active" and hasattr(user, 'grace_period_end'):
            user.grace_period_end = None

        db.commit()

        logger.info(
            "User plan updated from subscription change",
            user_id=str(user.id),
            old_plan=old_plan.value,
            new_plan=new_plan.value,
            status=subscription_status
        )

    except Exception as e:
        logger.error("Failed to handle subscription updated", error=str(e), event_data=event_data)
        db.rollback()
        raise


async def handle_subscription_deleted(event_data: Dict[str, Any], db: Session) -> None:
    """Handle customer.subscription.deleted event from Stripe"""
    try:
        subscription_data = event_data.get("data", {}).get("object", {})

        customer_id = subscription_data.get("customer")

        if not customer_id:
            logger.error("No customer ID in subscription deletion")
            return

        # Find user by Stripe customer ID
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if not user:
            logger.warning("User not found for subscription deletion", customer_id=customer_id)
            return

        # Downgrade user to free plan
        old_plan = user.plan
        user.plan = PlanType.FREE
        user.subscription_status = "canceled"

        # Clear grace period
        if hasattr(user, 'grace_period_end'):
            user.grace_period_end = None

        db.commit()

        logger.info(
            "User downgraded to free plan",
            user_id=str(user.id),
            old_plan=old_plan.value,
            reason="subscription_deleted"
        )

    except Exception as e:
        logger.error("Failed to handle subscription deleted", error=str(e), event_data=event_data)
        db.rollback()
        raise


async def handle_invoice_payment_failed(event_data: Dict[str, Any], db: Session) -> None:
    """Handle invoice.payment_failed event from Stripe"""
    try:
        invoice_data = event_data.get("data", {}).get("object", {})

        customer_id = invoice_data.get("customer")
        attempt_count = invoice_data.get("attempt_count", 0)

        if not customer_id:
            logger.error("No customer ID in payment failure")
            return

        # Find user by Stripe customer ID
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if not user:
            logger.warning("User not found for payment failure", customer_id=customer_id)
            return

        # Start grace period on first payment failure
        if attempt_count == 1:
            from ..services.billing_service import BillingService
            billing_service = BillingService(db)
            await billing_service.start_grace_period(user, days=7)

            logger.info(
                "Grace period started for payment failure",
                user_id=str(user.id),
                attempt_count=attempt_count
            )

        # Update subscription status
        user.subscription_status = "past_due"
        db.commit()

        logger.info(
            "Payment failure handled",
            user_id=str(user.id),
            attempt_count=attempt_count,
            status=user.subscription_status
        )

    except Exception as e:
        logger.error("Failed to handle payment failure", error=str(e), event_data=event_data)
        db.rollback()
        raise


@router.post("/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle Stripe webhooks for subscription events

    This endpoint handles:
    - checkout.session.completed: User successfully subscribes to plan
    - customer.subscription.updated: Plan changes (upgrade/downgrade)
    - customer.subscription.deleted: Subscription cancelled
    - invoice.payment_failed: Payment failures and grace period
    """
    try:
        # Get raw body
        body = await request.body()

        # Verify webhook signature (F7-12)
        if not await verify_stripe_webhook(request, body):
            logger.error("Invalid Stripe webhook signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )

        # Parse JSON
        try:
            event_data = json.loads(body.decode())
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in Stripe webhook", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload"
            )

        event_type = event_data.get("type")
        if not event_type:
            logger.error("No event type in Stripe webhook")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing event type"
            )

        logger.info("Received Stripe webhook", event_type=event_type)

        # Handle different event types (F7-04)
        if event_type == "checkout.session.completed":
            await handle_checkout_session_completed(event_data, db)
        elif event_type == "customer.subscription.updated":
            await handle_subscription_updated(event_data, db)
        elif event_type == "customer.subscription.deleted":
            await handle_subscription_deleted(event_data, db)
        elif event_type == "invoice.payment_failed":
            await handle_invoice_payment_failed(event_data, db)
        else:
            logger.warning("Unhandled Stripe event type", event_type=event_type)

        return {"status": "ok", "event_type": event_type}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in Stripe webhook handler", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )