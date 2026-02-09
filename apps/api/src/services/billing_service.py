"""Billing service for subscription management and usage tracking"""

import structlog
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ..models.user import User, PlanType
from ..schemas.billing import (
    BillingInfo, BillingOverview, UsageStats,
    PlanLimits, Invoice, PlanFeatures
)
from ..services.quota_service import QuotaService, PLAN_LIMITS
from ..services.stripe_service import StripeService

logger = structlog.get_logger()


class BillingService:
    """Service for managing billing, subscriptions, and usage tracking"""

    def __init__(self, db: Session):
        self.db = db
        self.quota_service = QuotaService(db)
        self.stripe_service = StripeService(db)

    async def get_billing_overview(self, user: User) -> BillingOverview:
        """
        Get complete billing overview for user

        Args:
            user: User object

        Returns:
            BillingOverview with billing info and invoices
        """
        # Get billing info
        billing_info = await self.get_billing_info(user)

        # Get recent invoices
        invoices = await self.get_user_invoices(user)

        return BillingOverview(
            billing_info=billing_info,
            invoices=invoices
        )

    async def get_billing_info(self, user: User) -> BillingInfo:
        """
        Get billing information for user

        Args:
            user: User object

        Returns:
            BillingInfo with plan, status, and usage
        """
        # Get plan limits
        limits = self.quota_service.get_plan_limits(user.plan)

        # Get usage stats
        usage = await self.get_usage_stats(user)

        # Get subscription info from Stripe (if not free plan)
        next_payment_date = None
        status = "active"
        grace_period_end = None

        if user.plan != PlanType.FREE and user.stripe_customer_id:
            subscription = await self.stripe_service.get_subscription_by_customer(
                user.stripe_customer_id
            )
            if subscription:
                next_payment_date = datetime.fromtimestamp(subscription['current_period_end'])
                status = subscription['status']

                # Check for grace period (payment failed but not cancelled yet)
                if hasattr(user, 'grace_period_end') and user.grace_period_end:
                    grace_period_end = user.grace_period_end

        return BillingInfo(
            plan=user.plan,
            status=status,
            next_payment_date=next_payment_date,
            grace_period_end=grace_period_end,
            limits=limits,
            usage=usage
        )

    async def get_usage_stats(self, user: User) -> UsageStats:
        """
        Get current usage statistics for user

        Args:
            user: User object

        Returns:
            UsageStats with current month's usage
        """
        # Get scheduled posts this week
        scheduled_this_week = self.quota_service._get_scheduled_posts_this_week(user)

        # Get monthly clips generated (from user model or separate tracking)
        monthly_clips = getattr(user, 'monthly_clips_generated', 0)

        return UsageStats(
            monthly_minutes_used=user.monthly_minutes_used or 0,
            monthly_clips_generated=monthly_clips,
            scheduled_posts_this_week=scheduled_this_week,
            reset_date=self.quota_service._get_next_reset_date()
        )

    async def track_upload_minutes(self, user: User, minutes: float) -> bool:
        """
        Track minutes uploaded by user

        Args:
            user: User object
            minutes: Minutes to add to usage

        Returns:
            bool: True if tracking successful
        """
        try:
            # Check if user can use these minutes
            quota_check = self.quota_service.check_upload_quota(user, minutes)
            if not quota_check.allowed:
                logger.warning(
                    "Upload minutes quota exceeded",
                    user_id=str(user.id),
                    minutes=minutes,
                    reason=quota_check.reason
                )
                return False

            # Track the usage
            if user.monthly_minutes_used is None:
                user.monthly_minutes_used = 0
            user.monthly_minutes_used += int(minutes)

            self.db.commit()

            logger.info(
                "Upload minutes tracked",
                user_id=str(user.id),
                minutes=minutes,
                total_used=user.monthly_minutes_used
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to track upload minutes",
                error=str(e),
                user_id=str(user.id),
                minutes=minutes
            )
            self.db.rollback()
            return False

    async def track_clip_generation(self, user: User, clips_count: int = 1) -> bool:
        """
        Track clips generated by user

        Args:
            user: User object
            clips_count: Number of clips generated

        Returns:
            bool: True if tracking successful
        """
        try:
            # Check if user can generate these clips
            quota_check = self.quota_service.check_clip_quota(user, clips_count)
            if not quota_check.allowed:
                logger.warning(
                    "Clip generation quota exceeded",
                    user_id=str(user.id),
                    clips_count=clips_count,
                    reason=quota_check.reason
                )
                return False

            # Track the usage (you'll need to add this field to User model)
            if not hasattr(user, 'monthly_clips_generated'):
                # For now, use the existing clips_generated field
                user.clips_generated += clips_count
            else:
                user.monthly_clips_generated += clips_count

            self.db.commit()

            logger.info(
                "Clip generation tracked",
                user_id=str(user.id),
                clips_count=clips_count
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to track clip generation",
                error=str(e),
                user_id=str(user.id),
                clips_count=clips_count
            )
            self.db.rollback()
            return False

    async def reset_monthly_usage(self, user: User) -> bool:
        """
        Reset monthly usage counters (called by worker)

        Args:
            user: User object

        Returns:
            bool: True if reset successful
        """
        try:
            user.monthly_minutes_used = 0
            if hasattr(user, 'monthly_clips_generated'):
                user.monthly_clips_generated = 0

            self.db.commit()

            logger.info(
                "Monthly usage reset",
                user_id=str(user.id)
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to reset monthly usage",
                error=str(e),
                user_id=str(user.id)
            )
            self.db.rollback()
            return False

    async def update_user_plan(
        self,
        user: User,
        new_plan: PlanType,
        subscription_status: str = "active"
    ) -> bool:
        """
        Update user's subscription plan

        Args:
            user: User object
            new_plan: New plan to assign
            subscription_status: Stripe subscription status

        Returns:
            bool: True if update successful
        """
        try:
            old_plan = user.plan
            user.plan = new_plan
            user.subscription_status = subscription_status

            # Clear grace period if upgrading
            if hasattr(user, 'grace_period_end') and new_plan != PlanType.FREE:
                user.grace_period_end = None

            self.db.commit()

            logger.info(
                "User plan updated",
                user_id=str(user.id),
                old_plan=old_plan.value,
                new_plan=new_plan.value,
                status=subscription_status
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to update user plan",
                error=str(e),
                user_id=str(user.id),
                new_plan=new_plan.value
            )
            self.db.rollback()
            return False

    async def start_grace_period(self, user: User, days: int = 7) -> bool:
        """
        Start grace period for user (payment failed)

        Args:
            user: User object
            days: Number of grace period days

        Returns:
            bool: True if grace period started
        """
        try:
            grace_end = datetime.utcnow() + timedelta(days=days)
            user.grace_period_end = grace_end
            user.subscription_status = "past_due"

            self.db.commit()

            logger.info(
                "Grace period started",
                user_id=str(user.id),
                grace_end=grace_end
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to start grace period",
                error=str(e),
                user_id=str(user.id)
            )
            self.db.rollback()
            return False

    async def end_grace_period(self, user: User) -> bool:
        """
        End grace period and downgrade user to free

        Args:
            user: User object

        Returns:
            bool: True if downgrade successful
        """
        return await self.update_user_plan(user, PlanType.FREE, "canceled")

    async def get_user_invoices(self, user: User, limit: int = 10) -> List[Invoice]:
        """
        Get user's recent invoices from Stripe

        Args:
            user: User object
            limit: Number of invoices to retrieve

        Returns:
            List of Invoice objects
        """
        if not user.stripe_customer_id or self.stripe_service.mock_mode:
            # Return mock invoices in development
            return [
                Invoice(
                    id="mock_inv_1",
                    date=datetime.utcnow() - timedelta(days=30),
                    amount=999,  # €9.99 in cents
                    status="paid",
                    pdf_url="https://mock-stripe.com/invoice.pdf"
                )
            ]

        try:
            import stripe
            invoices = stripe.Invoice.list(
                customer=user.stripe_customer_id,
                limit=limit
            )

            result = []
            for invoice in invoices.data:
                result.append(Invoice(
                    id=invoice.id,
                    date=datetime.fromtimestamp(invoice.created),
                    amount=invoice.amount_paid,
                    status=invoice.status,
                    pdf_url=invoice.invoice_pdf if invoice.status == "paid" else None
                ))

            return result

        except Exception as e:
            logger.error(
                "Failed to get user invoices",
                error=str(e),
                user_id=str(user.id)
            )
            return []

    def get_available_plans(self) -> List[PlanFeatures]:
        """
        Get list of available subscription plans

        Returns:
            List of PlanFeatures for display
        """
        return [
            PlanFeatures(
                name="Free",
                price="€0",
                price_cents=0,
                interval="month",
                features=[
                    "30 minutes upload/month",
                    "5 clips/month",
                    "TikTok only",
                    "Basic subtitle styles",
                    "Watermark included"
                ],
                popular=False,
                cta_text="Current Plan"
            ),
            PlanFeatures(
                name="Starter",
                price="€9.99",
                price_cents=999,
                interval="month",
                features=[
                    "2 hours upload/month",
                    "30 clips/month",
                    "TikTok + YouTube",
                    "5 styles + scheduling",
                    "No watermark"
                ],
                popular=True,
                cta_text="Upgrade"
            ),
            PlanFeatures(
                name="Pro",
                price="€29.99",
                price_cents=2999,
                interval="month",
                features=[
                    "10 hours upload/month",
                    "150 clips/month",
                    "All platforms",
                    "All styles + unlimited scheduling",
                    "Priority support"
                ],
                popular=False,
                cta_text="Upgrade"
            ),
            PlanFeatures(
                name="Enterprise",
                price="€79.99",
                price_cents=7999,
                interval="month",
                features=[
                    "Unlimited uploads",
                    "Unlimited clips",
                    "All platforms",
                    "All features",
                    "Dedicated support"
                ],
                popular=False,
                cta_text="Upgrade"
            )
        ]