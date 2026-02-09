"""Billing worker for scheduled tasks like monthly usage reset"""

import asyncio
import structlog
from datetime import datetime, timezone, timedelta
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..database import get_db
from ..models.user import User, PlanType
from ..services.billing_service import BillingService

logger = structlog.get_logger()


class BillingWorker:
    """Worker for handling billing-related background tasks"""

    def __init__(self):
        self.is_running = False

    async def start(self):
        """Start the billing worker"""
        if self.is_running:
            logger.warning("Billing worker is already running")
            return

        self.is_running = True
        logger.info("Starting billing worker")

        while self.is_running:
            try:
                await self.run_scheduled_tasks()
                # Wait 1 hour before next check
                await asyncio.sleep(3600)  # 1 hour

            except Exception as e:
                logger.error("Error in billing worker", error=str(e))
                # Wait 5 minutes before retrying on error
                await asyncio.sleep(300)

    async def stop(self):
        """Stop the billing worker"""
        logger.info("Stopping billing worker")
        self.is_running = False

    async def run_scheduled_tasks(self):
        """Run all scheduled billing tasks"""
        logger.debug("Running billing scheduled tasks")

        # Get database session
        db = next(get_db())

        try:
            # Check for monthly reset
            await self.check_monthly_reset(db)

            # Check for grace period expiry
            await self.check_grace_period_expiry(db)

            # Cleanup old usage data (optional)
            await self.cleanup_old_data(db)

        finally:
            db.close()

    async def check_monthly_reset(self, db: Session):
        """
        Check if it's time to reset monthly usage for users

        Reset happens on the first day of each month at midnight UTC
        """
        now = datetime.utcnow()

        # Check if it's the first day of the month and early hours
        if now.day != 1 or now.hour >= 2:
            return

        logger.info("Checking for monthly usage reset")

        try:
            # Get all users who need monthly reset
            # Only reset if they haven't been reset this month
            users_to_reset = db.query(User).filter(
                User.monthly_minutes_used > 0
                # Add additional filter to check if already reset this month
                # This would require adding a "last_reset" field to User model
            ).all()

            billing_service = BillingService(db)
            reset_count = 0

            for user in users_to_reset:
                success = await billing_service.reset_monthly_usage(user)
                if success:
                    reset_count += 1
                    logger.debug("Reset monthly usage", user_id=str(user.id))

            if reset_count > 0:
                logger.info(
                    "Monthly usage reset completed",
                    users_reset=reset_count,
                    total_users=len(users_to_reset)
                )

        except Exception as e:
            logger.error("Error during monthly reset", error=str(e))
            raise

    async def check_grace_period_expiry(self, db: Session):
        """
        Check for users whose grace period has expired and downgrade them to free plan
        """
        now = datetime.utcnow()

        try:
            # Find users with expired grace periods
            # This requires the grace_period_end field to be added to User model
            expired_users = []

            # For now, simulate the query since we haven't added the field yet
            # expired_users = db.query(User).filter(
            #     and_(
            #         User.grace_period_end.isnot(None),
            #         User.grace_period_end <= now,
            #         User.plan != PlanType.FREE
            #     )
            # ).all()

            if not expired_users:
                return

            logger.info(
                "Processing expired grace periods",
                expired_count=len(expired_users)
            )

            billing_service = BillingService(db)
            downgraded_count = 0

            for user in expired_users:
                success = await billing_service.end_grace_period(user)
                if success:
                    downgraded_count += 1
                    logger.info(
                        "User downgraded after grace period expiry",
                        user_id=str(user.id),
                        previous_plan=user.plan.value
                    )

            if downgraded_count > 0:
                logger.info(
                    "Grace period expiry processing completed",
                    users_downgraded=downgraded_count
                )

        except Exception as e:
            logger.error("Error checking grace period expiry", error=str(e))
            raise

    async def cleanup_old_data(self, db: Session):
        """
        Optional cleanup of old billing data
        Run once per week to clean up old records
        """
        now = datetime.utcnow()

        # Only run cleanup once per week (on Sundays at 2 AM)
        if now.weekday() != 6 or now.hour != 2:
            return

        logger.info("Running billing data cleanup")

        try:
            # Example: Clean up old usage logs older than 1 year
            # This would depend on what additional tracking tables you implement
            cutoff_date = now - timedelta(days=365)

            # Placeholder for cleanup logic
            logger.debug("Billing data cleanup completed", cutoff_date=cutoff_date)

        except Exception as e:
            logger.error("Error during billing data cleanup", error=str(e))
            raise

    async def reset_user_monthly_usage(self, user_id: str, db: Session = None) -> bool:
        """
        Manually reset monthly usage for a specific user

        Args:
            user_id: User ID to reset
            db: Database session (optional)

        Returns:
            bool: True if reset successful
        """
        if not db:
            db = next(get_db())

        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error("User not found for manual reset", user_id=user_id)
                return False

            billing_service = BillingService(db)
            success = await billing_service.reset_monthly_usage(user)

            if success:
                logger.info("Manual monthly reset completed", user_id=user_id)
            else:
                logger.error("Manual monthly reset failed", user_id=user_id)

            return success

        except Exception as e:
            logger.error("Error in manual monthly reset", error=str(e), user_id=user_id)
            return False

        finally:
            if db:
                db.close()

    async def force_grace_period_check(self, db: Session = None) -> int:
        """
        Manually trigger grace period expiry check

        Args:
            db: Database session (optional)

        Returns:
            int: Number of users processed
        """
        if not db:
            db = next(get_db())

        try:
            await self.check_grace_period_expiry(db)
            logger.info("Manual grace period check completed")
            return 0  # Placeholder since we don't have the field yet

        except Exception as e:
            logger.error("Error in manual grace period check", error=str(e))
            return 0

        finally:
            if db:
                db.close()


# Global worker instance
billing_worker = BillingWorker()


async def start_billing_worker():
    """Start the billing worker (call this from your app startup)"""
    await billing_worker.start()


async def stop_billing_worker():
    """Stop the billing worker (call this from your app shutdown)"""
    await billing_worker.stop()


# Convenience functions for manual operations
async def reset_all_monthly_usage():
    """Manually reset monthly usage for all users"""
    db = next(get_db())
    try:
        users = db.query(User).filter(User.monthly_minutes_used > 0).all()
        billing_service = BillingService(db)

        reset_count = 0
        for user in users:
            if await billing_service.reset_monthly_usage(user):
                reset_count += 1

        logger.info("Manual reset completed", users_reset=reset_count)
        return reset_count

    finally:
        db.close()


async def check_all_grace_periods():
    """Manually check all grace periods"""
    db = next(get_db())
    try:
        return await billing_worker.force_grace_period_check(db)
    finally:
        db.close()