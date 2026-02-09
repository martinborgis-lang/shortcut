from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Project info (auto-generated from video title)
    name = Column(String(255), nullable=True)  # Auto-generated from YouTube title
    description = Column(Text, nullable=True)

    # Source video info (according to PRD)
    source_url = Column(Text, nullable=False)  # Original YouTube/Twitch URL
    source_s3_key = Column(Text, nullable=True)  # S3 key for downloaded video
    source_filename = Column(String(255), nullable=True)
    source_size = Column(Integer, nullable=True)  # bytes
    source_duration = Column(Float, nullable=True)  # seconds

    # Video metadata
    video_metadata = Column(JSON, nullable=True)  # width, height, fps, codec, etc.

    # Processing status (according to PRD pipeline stages)
    status = Column(String(50), default="pending", nullable=False)  # pending, downloading, transcribing, analyzing, processing, done, failed
    current_step = Column(String(50), nullable=True)  # Current pipeline step
    processing_progress = Column(Integer, default=0, nullable=False)  # 0-100
    error_message = Column(Text, nullable=True)

    # AI Analysis results (according to PRD)
    transcript_json = Column(JSON, nullable=True)  # Deepgram transcript with word-level timestamps
    viral_segments = Column(JSON, nullable=True)  # Claude Haiku detected segments with scores
    max_clips_requested = Column(Integer, default=5, nullable=False)  # Number of clips requested

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="projects")
    clips = relationship("Clip", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.id}, name={self.name}, status={self.status})>"