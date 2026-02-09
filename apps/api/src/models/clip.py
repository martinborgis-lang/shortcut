from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..database import Base


class Clip(Base):
    __tablename__ = "clips"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)

    # Clip info
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Video segment
    start_time = Column(Float, nullable=False)  # seconds
    end_time = Column(Float, nullable=False)  # seconds
    duration = Column(Float, nullable=False)  # seconds

    # Generated content URLs (according to PRD)
    s3_key = Column(Text, nullable=True)  # S3 key for final processed clip
    video_url = Column(Text, nullable=True)  # Signed S3 URL for download
    thumbnail_url = Column(Text, nullable=True)  # S3 URL for thumbnail
    preview_gif_url = Column(Text, nullable=True)  # S3 URL for preview GIF

    # AI Analysis (from ViralDetection)
    viral_score = Column(Float, nullable=True)  # 0-100
    reason = Column(Text, nullable=True)  # Why this moment is viral
    hook = Column(Text, nullable=True)  # Suggested opening line

    # Customizations (according to PRD subtitle styles)
    subtitle_style = Column(String(50), default="hormozi", nullable=False)  # hormozi, clean, neon, karaoke, minimal
    subtitle_config = Column(JSON, nullable=True)  # ASS file parameters
    crop_settings = Column(JSON, nullable=True)  # 9:16 crop configuration

    # Status
    status = Column(String(50), default="pending", nullable=False)  # pending, processing, ready, failed
    processing_progress = Column(Integer, default=0, nullable=False)  # 0-100
    error_message = Column(Text, nullable=True)

    # User customization
    is_favorite = Column(Boolean, default=False, nullable=False)
    user_rating = Column(Integer, nullable=True)  # 1-5
    user_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    generated_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="clips")
    scheduled_posts = relationship("ScheduledPost", back_populates="clip", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Clip(id={self.id}, title={self.title}, viral_score={self.viral_score})>"