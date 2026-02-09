from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Boolean, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..database import Base


class ScheduledPost(Base):
    __tablename__ = "scheduled_posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clip_id = Column(UUID(as_uuid=True), ForeignKey("clips.id"), nullable=False, index=True)
    social_account_id = Column(UUID(as_uuid=True), ForeignKey("social_accounts.id"), nullable=False, index=True)

    # Scheduling info
    scheduled_time = Column(DateTime(timezone=True), nullable=False, index=True)
    time_zone = Column(String(50), default="UTC", nullable=False)

    # Post content
    caption = Column(Text, nullable=True)
    hashtags = Column(JSON, nullable=True)  # List of hashtags
    mentions = Column(JSON, nullable=True)  # List of mentions

    # Platform-specific settings
    platform_settings = Column(JSON, nullable=True)  # TikTok specific settings
    post_metadata = Column(JSON, nullable=True)  # Additional platform data

    # Status tracking
    status = Column(String(50), default="scheduled", nullable=False)  # scheduled, posted, failed, cancelled
    posted_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    # Platform response
    platform_post_id = Column(String(255), nullable=True)  # ID from TikTok/platform
    platform_response = Column(JSON, nullable=True)  # Full response from platform

    # Performance tracking (filled after posting)
    views = Column(Integer, nullable=True)
    likes = Column(Integer, nullable=True)
    shares = Column(Integer, nullable=True)
    comments = Column(Integer, nullable=True)
    engagement_rate = Column(Float, nullable=True)

    # Retry logic
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    clip = relationship("Clip", back_populates="scheduled_posts")
    social_account = relationship("SocialAccount", back_populates="scheduled_posts")

    def __repr__(self):
        return f"<ScheduledPost(id={self.id}, status={self.status}, scheduled_time={self.scheduled_time})>"