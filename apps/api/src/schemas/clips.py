from pydantic import BaseModel, validator
from typing import Optional, Dict, Any, ClassVar
from datetime import datetime
import uuid


class ClipResponse(BaseModel):
    """Response schema for a clip"""
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    description: Optional[str]
    start_time: float
    end_time: float
    duration: float
    s3_key: Optional[str]
    video_url: Optional[str]
    thumbnail_url: Optional[str]
    preview_gif_url: Optional[str]
    viral_score: Optional[float]
    reason: Optional[str]
    hook: Optional[str]
    subtitle_style: str
    subtitle_config: Optional[Dict[str, Any]]
    crop_settings: Optional[Dict[str, Any]]
    status: str
    processing_progress: int
    error_message: Optional[str]
    is_favorite: bool
    user_rating: Optional[int]
    user_notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    generated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ClipDetailResponse(ClipResponse):
    """Detailed clip response with signed URLs"""
    signed_video_url: Optional[str]
    signed_thumbnail_url: Optional[str]
    signed_preview_gif_url: Optional[str]
    download_url: Optional[str]


class UpdateClipRequest(BaseModel):
    """Request schema for updating a clip"""
    title: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    subtitle_style: Optional[str] = None
    is_favorite: Optional[bool] = None
    user_rating: Optional[int] = None
    user_notes: Optional[str] = None

    @validator('title')
    def validate_title(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError('Title cannot be empty')
        return v.strip() if v else v

    @validator('start_time', 'end_time')
    def validate_times(cls, v):
        if v is not None and v < 0:
            raise ValueError('Time cannot be negative')
        return v

    @validator('subtitle_style')
    def validate_subtitle_style(cls, v):
        if v is not None:
            allowed_styles = ['hormozi', 'clean', 'neon', 'karaoke', 'minimal']
            if v not in allowed_styles:
                raise ValueError(f'Subtitle style must be one of: {", ".join(allowed_styles)}')
        return v

    @validator('user_rating')
    def validate_rating(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Rating must be between 1 and 5')
        return v

    def validate_timing(self):
        """Additional validation for timing consistency"""
        if self.start_time is not None and self.end_time is not None:
            if self.start_time >= self.end_time:
                raise ValueError('Start time must be before end time')

            duration = self.end_time - self.start_time
            if duration < 10:
                raise ValueError('Clip duration must be at least 10 seconds')
            if duration > 120:
                raise ValueError('Clip duration cannot exceed 120 seconds')


class RegenerateClipRequest(BaseModel):
    """Request schema for regenerating a clip"""
    subtitle_style: Optional[str] = None
    crop_settings: Optional[Dict[str, Any]] = None

    @validator('subtitle_style')
    def validate_subtitle_style(cls, v):
        if v is not None:
            allowed_styles = ['hormozi', 'clean', 'neon', 'karaoke', 'minimal']
            if v not in allowed_styles:
                raise ValueError(f'Subtitle style must be one of: {", ".join(allowed_styles)}')
        return v


class ClipDownloadResponse(BaseModel):
    """Response schema for clip download"""
    download_url: str
    expires_at: datetime
    filename: str
    file_size: Optional[int]


class ClipsListResponse(BaseModel):
    """Response schema for clips list"""
    clips: list[ClipResponse]
    total: int
    page: int
    size: int
    total_pages: int


class ClipsSortBy(BaseModel):
    """Enum-like model for sorting options"""
    VIRAL_SCORE: ClassVar[str] = "viral_score"
    CREATED_AT: ClassVar[str] = "created_at"
    DURATION: ClassVar[str] = "duration"
    TITLE: ClassVar[str] = "title"
    USER_RATING: ClassVar[str] = "user_rating"


class ClipsFilterRequest(BaseModel):
    """Request schema for filtering and sorting clips"""
    project_id: Optional[uuid.UUID] = None
    status: Optional[str] = None
    subtitle_style: Optional[str] = None
    is_favorite: Optional[bool] = None
    min_viral_score: Optional[float] = None
    max_viral_score: Optional[float] = None
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None
    sort_by: Optional[str] = "viral_score"
    sort_order: Optional[str] = "desc"
    page: int = 1
    size: int = 20

    @validator('sort_by')
    def validate_sort_by(cls, v):
        allowed_sorts = ['viral_score', 'created_at', 'duration', 'title', 'user_rating']
        if v not in allowed_sorts:
            raise ValueError(f'Sort by must be one of: {", ".join(allowed_sorts)}')
        return v

    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('Sort order must be "asc" or "desc"')
        return v

    @validator('size')
    def validate_size(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Page size must be between 1 and 100')
        return v

    @validator('page')
    def validate_page(cls, v):
        if v < 1:
            raise ValueError('Page must be at least 1')
        return v


class BulkDownloadRequest(BaseModel):
    """Request schema for bulk download"""
    clip_ids: list[uuid.UUID]
    project_id: Optional[uuid.UUID] = None

    @validator('clip_ids')
    def validate_clip_ids(cls, v):
        if len(v) == 0:
            raise ValueError('At least one clip ID is required')
        if len(v) > 50:
            raise ValueError('Cannot download more than 50 clips at once')
        return v


class BulkDownloadResponse(BaseModel):
    """Response schema for bulk download"""
    download_url: str
    expires_at: datetime
    filename: str
    clips_count: int
    total_size: Optional[int]