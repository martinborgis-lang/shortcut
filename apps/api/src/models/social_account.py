from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..database import Base


class SocialAccount(Base):
    __tablename__ = "social_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Platform info
    platform = Column(String(50), nullable=False, index=True)  # tiktok, instagram, youtube, twitter
    platform_user_id = Column(String(255), nullable=False)  # User ID on the platform
    username = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=True)

    # Authentication
    access_token = Column(Text, nullable=True)  # Encrypted access token
    refresh_token = Column(Text, nullable=True)  # Encrypted refresh token
    token_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    last_sync = Column(DateTime(timezone=True), nullable=True)

    # Platform-specific data
    account_metadata = Column(JSON, nullable=True)  # Follower count, bio, etc.
    publishing_permissions = Column(JSON, nullable=True)  # What we can post

    # Error tracking
    last_error = Column(Text, nullable=True)
    error_count = Column(Integer, default=0, nullable=False)
    disabled_until = Column(DateTime(timezone=True), nullable=True)

    # Publishing settings
    default_caption_template = Column(Text, nullable=True)
    default_hashtags = Column(JSON, nullable=True)
    posting_schedule = Column(JSON, nullable=True)  # Optimal posting times

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    connected_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="social_accounts")
    scheduled_posts = relationship("ScheduledPost", back_populates="social_account", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SocialAccount(id={self.id}, platform={self.platform}, username={self.username})>"