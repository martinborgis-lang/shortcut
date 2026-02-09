from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from enum import Enum

from ..database import Base


class PlanType(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clerk_id = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    profile_image_url = Column(Text, nullable=True)

    # Plan and usage tracking
    plan = Column(SQLEnum(PlanType), default=PlanType.FREE, nullable=False)
    monthly_minutes_used = Column(Integer, default=0, nullable=False)

    # Stripe subscription info
    is_premium = Column(Boolean, default=False, nullable=False)  # Legacy field
    stripe_customer_id = Column(String, nullable=True)
    subscription_status = Column(String, nullable=True)  # active, canceled, past_due, etc.

    # Usage tracking
    clips_generated = Column(Integer, default=0, nullable=False)  # Legacy field
    clips_limit = Column(Integer, default=10, nullable=False)  # Legacy field
    monthly_clips_generated = Column(Integer, default=0, nullable=False)  # New monthly tracking

    # Grace period for failed payments (F7-11)
    grace_period_end = Column(DateTime(timezone=True), nullable=True)

    # Monthly usage reset tracking
    last_monthly_reset = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    social_accounts = relationship("SocialAccount", back_populates="user", cascade="all, delete-orphan")

    @property
    def name(self) -> str:
        """Unified name field (computed from first_name + last_name)"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return ""

    @property
    def monthly_minutes_limit(self) -> int:
        """Get monthly minutes limit based on plan"""
        limits = {
            PlanType.FREE: 30,  # 30 minutes
            PlanType.STARTER: 120,  # 120 minutes (2 hours)
            PlanType.PRO: 600,  # 600 minutes (10 hours)
            PlanType.ENTERPRISE: 999999  # Unlimited
        }
        return limits.get(self.plan, 30)

    def reset_monthly_usage(self):
        """Reset monthly usage counters"""
        from datetime import datetime, timezone
        self.monthly_minutes_used = 0
        self.monthly_clips_generated = 0
        self.last_monthly_reset = datetime.now(timezone.utc)

    def can_use_minutes(self, minutes: int) -> bool:
        """Check if user can use the specified number of minutes"""
        if self.plan == PlanType.ENTERPRISE:
            return True
        return (self.monthly_minutes_used + minutes) <= self.monthly_minutes_limit

    def use_minutes(self, minutes: int) -> bool:
        """Use minutes if available, return True if successful"""
        if self.can_use_minutes(minutes):
            self.monthly_minutes_used += minutes
            return True
        return False

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, plan={self.plan})>"