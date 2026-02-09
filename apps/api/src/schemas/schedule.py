"""
Schemas for scheduled post management
"""
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum


class PostStatus(str, Enum):
    """Status of a scheduled post"""
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PrivacyLevel(str, Enum):
    """Privacy levels for TikTok posts"""
    PUBLIC = "PUBLIC_TO_EVERYONE"
    FRIENDS = "MUTUAL_FOLLOW_FRIENDS"
    PRIVATE = "SELF_ONLY"


class ScheduledPostBase(BaseModel):
    """Base schema for scheduled posts"""
    scheduled_time: datetime = Field(..., description="When to publish the post")
    time_zone: str = Field("UTC", description="Timezone for scheduled time")
    caption: Optional[str] = Field(None, description="Post caption/description", max_length=2200)
    hashtags: Optional[List[str]] = Field(None, description="Hashtags to include in post")
    mentions: Optional[List[str]] = Field(None, description="Users to mention in post")

    @validator('hashtags')
    def validate_hashtags(cls, v):
        if v:
            # Remove # prefix if present and limit to reasonable number
            cleaned = [tag.strip('#').strip() for tag in v if tag.strip()]
            if len(cleaned) > 30:  # TikTok practical limit
                raise ValueError("Too many hashtags (max 30)")
            return cleaned[:30]
        return v

    @validator('caption')
    def validate_caption(cls, v):
        if v and len(v) > 2200:  # TikTok caption limit
            raise ValueError("Caption too long (max 2200 characters)")
        return v


class CreateScheduledPostRequest(ScheduledPostBase):
    """Request schema for creating a scheduled post"""
    clip_id: UUID = Field(..., description="ID of the clip to post")
    social_account_id: UUID = Field(..., description="ID of the social account to post to")
    platform_settings: Optional[Dict[str, Any]] = Field(None, description="Platform-specific settings")

    class TikTokSettings(BaseModel):
        """TikTok-specific settings"""
        privacy_level: PrivacyLevel = Field(PrivacyLevel.PUBLIC, description="Privacy level")
        disable_duet: bool = Field(False, description="Disable duet feature")
        disable_comment: bool = Field(False, description="Disable comments")
        disable_stitch: bool = Field(False, description="Disable stitch feature")
        brand_content_toggle: bool = Field(False, description="Mark as branded content")
        brand_organic_toggle: bool = Field(False, description="Mark as organic branded content")


class ScheduledPostResponse(ScheduledPostBase):
    """Response schema for scheduled posts"""
    id: UUID = Field(..., description="Post ID")
    clip_id: UUID = Field(..., description="Clip ID")
    social_account_id: UUID = Field(..., description="Social account ID")
    status: PostStatus = Field(..., description="Current post status")
    platform_settings: Optional[Dict[str, Any]] = Field(None, description="Platform-specific settings")
    post_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    # Status tracking
    posted_at: Optional[datetime] = Field(None, description="When the post was published")
    failed_at: Optional[datetime] = Field(None, description="When the post failed")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    # Platform response
    platform_post_id: Optional[str] = Field(None, description="Post ID from platform")
    platform_response: Optional[Dict[str, Any]] = Field(None, description="Full platform response")

    # Performance metrics (populated after posting)
    views: Optional[int] = Field(None, description="Number of views")
    likes: Optional[int] = Field(None, description="Number of likes")
    shares: Optional[int] = Field(None, description="Number of shares")
    comments: Optional[int] = Field(None, description="Number of comments")
    engagement_rate: Optional[float] = Field(None, description="Engagement rate percentage")

    # Retry information
    retry_count: int = Field(0, description="Number of retry attempts")
    max_retries: int = Field(3, description="Maximum retry attempts")
    next_retry_at: Optional[datetime] = Field(None, description="When to retry next")

    # Timestamps
    created_at: datetime = Field(..., description="When the post was scheduled")
    updated_at: Optional[datetime] = Field(None, description="Last update time")

    class Config:
        from_attributes = True


class UpdateScheduledPostRequest(BaseModel):
    """Request schema for updating a scheduled post"""
    scheduled_time: Optional[datetime] = Field(None, description="New scheduled time")
    caption: Optional[str] = Field(None, description="New caption", max_length=2200)
    hashtags: Optional[List[str]] = Field(None, description="New hashtags")
    mentions: Optional[List[str]] = Field(None, description="New mentions")
    platform_settings: Optional[Dict[str, Any]] = Field(None, description="Updated platform settings")

    @validator('caption')
    def validate_caption(cls, v):
        if v and len(v) > 2200:
            raise ValueError("Caption too long (max 2200 characters)")
        return v


class ScheduledPostsListResponse(BaseModel):
    """Response schema for listing scheduled posts"""
    posts: List[ScheduledPostResponse] = Field(..., description="List of scheduled posts")
    total: int = Field(..., description="Total number of posts")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Posts per page")
    total_pages: int = Field(..., description="Total number of pages")


class ScheduledPostFilters(BaseModel):
    """Filters for scheduled posts query"""
    status: Optional[PostStatus] = Field(None, description="Filter by status")
    platform: Optional[str] = Field(None, description="Filter by platform")
    clip_id: Optional[UUID] = Field(None, description="Filter by clip ID")
    social_account_id: Optional[UUID] = Field(None, description="Filter by social account")
    scheduled_after: Optional[datetime] = Field(None, description="Posts scheduled after this time")
    scheduled_before: Optional[datetime] = Field(None, description="Posts scheduled before this time")
    created_after: Optional[datetime] = Field(None, description="Posts created after this time")
    created_before: Optional[datetime] = Field(None, description="Posts created before this time")


class CancelScheduledPostRequest(BaseModel):
    """Request schema for cancelling a scheduled post"""
    reason: Optional[str] = Field(None, description="Reason for cancellation")


class CancelScheduledPostResponse(BaseModel):
    """Response schema for cancelling a scheduled post"""
    message: str = Field(..., description="Cancellation confirmation message")
    cancelled_post: ScheduledPostResponse = Field(..., description="Cancelled post details")


class ScheduledPostStats(BaseModel):
    """Statistics for scheduled posts"""
    total_scheduled: int = Field(..., description="Total scheduled posts")
    total_published: int = Field(..., description="Total published posts")
    total_failed: int = Field(..., description="Total failed posts")
    total_cancelled: int = Field(..., description="Total cancelled posts")
    success_rate: float = Field(..., description="Success rate percentage")
    avg_engagement_rate: Optional[float] = Field(None, description="Average engagement rate")


class PostPerformanceMetrics(BaseModel):
    """Performance metrics for a published post"""
    post_id: UUID = Field(..., description="Scheduled post ID")
    platform_post_id: str = Field(..., description="Platform post ID")
    platform: str = Field(..., description="Platform name")
    published_at: datetime = Field(..., description="When the post was published")

    # Current metrics
    views: int = Field(0, description="Number of views")
    likes: int = Field(0, description="Number of likes")
    shares: int = Field(0, description="Number of shares")
    comments: int = Field(0, description="Number of comments")
    engagement_rate: float = Field(0.0, description="Engagement rate percentage")

    # Performance tracking over time
    metrics_history: List[Dict[str, Any]] = Field([], description="Historical metrics data")
    last_updated: datetime = Field(..., description="When metrics were last updated")


class BulkScheduleRequest(BaseModel):
    """Request for bulk scheduling posts"""
    clip_ids: List[UUID] = Field(..., description="List of clip IDs to schedule")
    social_account_ids: List[UUID] = Field(..., description="List of social account IDs")
    base_scheduled_time: datetime = Field(..., description="Base time to start scheduling")
    time_interval_minutes: int = Field(60, description="Minutes between posts", ge=30)
    caption_template: Optional[str] = Field(None, description="Caption template with placeholders")
    hashtags: Optional[List[str]] = Field(None, description="Common hashtags for all posts")
    platform_settings: Optional[Dict[str, Any]] = Field(None, description="Platform settings")


class BulkScheduleResponse(BaseModel):
    """Response for bulk scheduling"""
    scheduled_posts: List[ScheduledPostResponse] = Field(..., description="Successfully scheduled posts")
    failed_posts: List[Dict[str, Any]] = Field([], description="Posts that failed to schedule")
    summary: Dict[str, int] = Field(..., description="Summary statistics")