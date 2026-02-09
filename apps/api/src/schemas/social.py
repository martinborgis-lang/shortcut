"""
Schemas for social media account management and OAuth
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID


class TikTokAuthResponse(BaseModel):
    """Response for TikTok OAuth authorization URL"""
    auth_url: str = Field(..., description="TikTok OAuth authorization URL")


class OAuthCallbackRequest(BaseModel):
    """Request schema for OAuth callback"""
    code: str = Field(..., description="Authorization code from OAuth provider")
    state: str = Field(..., description="State parameter for CSRF protection")


class SocialAccountBase(BaseModel):
    """Base schema for social account"""
    platform: str = Field(..., description="Social media platform (tiktok, instagram, youtube)")
    username: str = Field(..., description="Username on the platform")
    display_name: Optional[str] = Field(None, description="Display name on the platform")
    is_active: bool = Field(True, description="Whether the account is active")


class SocialAccountCreate(SocialAccountBase):
    """Schema for creating a social account"""
    platform_user_id: str = Field(..., description="User ID on the platform")
    access_token: str = Field(..., description="Encrypted access token")
    refresh_token: Optional[str] = Field(None, description="Encrypted refresh token")
    token_expires_at: Optional[datetime] = Field(None, description="Token expiration time")
    account_metadata: Optional[Dict[str, Any]] = Field(None, description="Platform-specific metadata")


class SocialAccountResponse(SocialAccountBase):
    """Schema for social account response"""
    id: UUID = Field(..., description="Account ID")
    user_id: UUID = Field(..., description="User ID")
    platform_user_id: str = Field(..., description="User ID on the platform")
    is_verified: bool = Field(..., description="Whether the account is verified")
    last_sync: Optional[datetime] = Field(None, description="Last synchronization time")
    account_metadata: Optional[Dict[str, Any]] = Field(None, description="Platform-specific metadata")
    publishing_permissions: Optional[Dict[str, Any]] = Field(None, description="Publishing permissions")
    error_count: int = Field(..., description="Number of consecutive errors")
    last_error: Optional[str] = Field(None, description="Last error message")
    disabled_until: Optional[datetime] = Field(None, description="Account disabled until this time")
    default_hashtags: Optional[List[str]] = Field(None, description="Default hashtags for posts")
    created_at: datetime = Field(..., description="Account creation time")
    updated_at: Optional[datetime] = Field(None, description="Last update time")
    connected_at: Optional[datetime] = Field(None, description="Connection time")

    class Config:
        from_attributes = True


class SocialAccountUpdate(BaseModel):
    """Schema for updating a social account"""
    is_active: Optional[bool] = Field(None, description="Whether the account is active")
    default_hashtags: Optional[List[str]] = Field(None, description="Default hashtags for posts")
    default_caption_template: Optional[str] = Field(None, description="Default caption template")


class ConnectedAccountsResponse(BaseModel):
    """Response schema for connected accounts"""
    accounts: List[SocialAccountResponse] = Field(..., description="List of connected social accounts")
    total: int = Field(..., description="Total number of connected accounts")


class DisconnectAccountResponse(BaseModel):
    """Response for account disconnection"""
    message: str = Field(..., description="Success message")
    disconnected_account: SocialAccountResponse = Field(..., description="Disconnected account details")


class TikTokUserInfo(BaseModel):
    """TikTok user information"""
    open_id: str = Field(..., description="TikTok open ID")
    union_id: Optional[str] = Field(None, description="TikTok union ID")
    username: Optional[str] = Field(None, description="TikTok username")
    display_name: Optional[str] = Field(None, description="TikTok display name")
    avatar_url: Optional[str] = Field(None, description="TikTok avatar URL")
    follower_count: Optional[int] = Field(None, description="Number of followers")
    following_count: Optional[int] = Field(None, description="Number of following")
    likes_count: Optional[int] = Field(None, description="Total likes received")
    video_count: Optional[int] = Field(None, description="Number of videos posted")
    is_verified: Optional[bool] = Field(None, description="Whether the account is verified")


class TokenRefreshResponse(BaseModel):
    """Response for token refresh"""
    access_token: str = Field(..., description="New encrypted access token")
    refresh_token: str = Field(..., description="New encrypted refresh token")
    expires_at: datetime = Field(..., description="Token expiration time")


class SocialAccountStatus(BaseModel):
    """Status information for a social account"""
    platform: str = Field(..., description="Platform name")
    is_connected: bool = Field(..., description="Whether account is connected")
    is_active: bool = Field(..., description="Whether account is active")
    has_publishing_permission: bool = Field(..., description="Whether we can publish to this account")
    last_error: Optional[str] = Field(None, description="Last error encountered")
    token_expires_at: Optional[datetime] = Field(None, description="When the token expires")
    needs_reconnection: bool = Field(..., description="Whether account needs to be reconnected")


class BulkAccountStatusResponse(BaseModel):
    """Response for bulk account status check"""
    accounts: List[SocialAccountStatus] = Field(..., description="Account statuses")
    summary: Dict[str, int] = Field(..., description="Summary statistics")


class AccountMetrics(BaseModel):
    """Metrics for a social media account"""
    platform: str = Field(..., description="Platform name")
    follower_count: Optional[int] = Field(None, description="Number of followers")
    following_count: Optional[int] = Field(None, description="Number of following")
    total_posts: Optional[int] = Field(None, description="Total number of posts")
    total_likes: Optional[int] = Field(None, description="Total likes received")
    engagement_rate: Optional[float] = Field(None, description="Average engagement rate")
    last_updated: Optional[datetime] = Field(None, description="When metrics were last updated")


class AccountMetricsResponse(BaseModel):
    """Response for account metrics"""
    account_id: UUID = Field(..., description="Account ID")
    metrics: AccountMetrics = Field(..., description="Account metrics")
    history: List[Dict[str, Any]] = Field([], description="Historical metrics data")