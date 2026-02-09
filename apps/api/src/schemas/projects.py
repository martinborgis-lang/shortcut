from pydantic import BaseModel, HttpUrl, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class CreateProjectRequest(BaseModel):
    """Request schema for creating a new project from video URL"""
    url: str
    max_clips: Optional[int] = 5

    @validator('url')
    def validate_video_url(cls, v):
        """Basic URL validation - detailed validation is performed by the URL validator service"""
        if not v or not isinstance(v, str):
            raise ValueError('URL is required and must be a string')
        return v.strip()

    @validator('max_clips')
    def validate_max_clips(cls, v):
        if v and (v < 1 or v > 10):
            raise ValueError('max_clips must be between 1 and 10')
        return v


class ViralSegment(BaseModel):
    """Viral segment detected by AI"""
    start_time: float
    end_time: float
    title: str
    virality_score: int
    reason: str
    hook: str


class ClipResponse(BaseModel):
    """Clip information in project response"""
    id: uuid.UUID
    title: str
    description: Optional[str]
    start_time: float
    end_time: float
    duration: float
    video_url: Optional[str]
    thumbnail_url: Optional[str]
    viral_score: Optional[float]
    reason: Optional[str]
    hook: Optional[str]
    subtitle_style: str
    status: str
    processing_progress: int
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectResponse(BaseModel):
    """Project information response"""
    id: uuid.UUID
    user_id: uuid.UUID
    name: Optional[str]
    description: Optional[str]
    source_url: str
    source_s3_key: Optional[str]
    source_filename: Optional[str]
    source_size: Optional[int]
    source_duration: Optional[float]
    video_metadata: Optional[Dict[str, Any]]
    status: str
    current_step: Optional[str]
    processing_progress: int
    error_message: Optional[str]
    transcript_json: Optional[Dict[str, Any]]
    viral_segments: Optional[List[ViralSegment]]
    max_clips_requested: int
    clips: List[ClipResponse]
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ProjectStatusResponse(BaseModel):
    """Detailed project status for real-time updates"""
    id: uuid.UUID
    status: str
    current_step: Optional[str]
    processing_progress: int
    error_message: Optional[str]

    # Step-specific details
    step_details: Optional[Dict[str, Any]]

    # Pipeline stages info
    stages: Dict[str, Dict[str, Any]] = {
        "downloading": {"progress": 0, "description": "Downloading video from source"},
        "transcribing": {"progress": 0, "description": "Extracting audio and transcribing with Deepgram"},
        "analyzing": {"progress": 0, "description": "Detecting viral segments with AI"},
        "processing": {"progress": 0, "description": "Cutting and processing video clips"},
        "done": {"progress": 100, "description": "Processing complete"}
    }

    class Config:
        from_attributes = True


class CreateProjectResponse(BaseModel):
    """Response after creating a project"""
    id: uuid.UUID
    status: str
    message: str
    estimated_completion: Optional[datetime]

    class Config:
        from_attributes = True