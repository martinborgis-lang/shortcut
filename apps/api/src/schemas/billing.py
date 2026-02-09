"""Billing schemas for plans, quotas, and usage tracking"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum


class PlanType(str, Enum):
    """Available subscription plans"""
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class PlanLimits(BaseModel):
    """Schema for plan limits and features"""
    monthly_upload_minutes: Optional[int] = Field(..., description="Monthly upload minutes limit (None = unlimited)")
    monthly_clips: Optional[int] = Field(..., description="Monthly clips generation limit (None = unlimited)")
    max_source_duration: Optional[int] = Field(..., description="Max video duration in seconds (None = unlimited)")
    scheduling_enabled: bool = Field(..., description="Whether scheduling is enabled")
    max_scheduled_per_week: Optional[int] = Field(None, description="Max scheduled posts per week (None = unlimited)")
    platforms: Union[List[str], str] = Field(..., description="Available platforms")
    subtitle_styles: Union[List[str], str] = Field(..., description="Available subtitle styles")
    watermark: bool = Field(..., description="Whether watermark is applied")


class UsageStats(BaseModel):
    """Schema for user usage statistics"""
    monthly_minutes_used: int = Field(0, description="Minutes used this month")
    monthly_clips_generated: int = Field(0, description="Clips generated this month")
    scheduled_posts_this_week: int = Field(0, description="Posts scheduled this week")
    reset_date: Optional[datetime] = Field(None, description="Next reset date")


class BillingInfo(BaseModel):
    """Schema for user billing information"""
    plan: PlanType = Field(..., description="Current subscription plan")
    status: str = Field("active", description="Subscription status")
    next_payment_date: Optional[datetime] = Field(None, description="Next payment date")
    grace_period_end: Optional[datetime] = Field(None, description="Grace period end date")
    limits: PlanLimits = Field(..., description="Current plan limits")
    usage: UsageStats = Field(..., description="Current usage statistics")


class Invoice(BaseModel):
    """Schema for invoice information"""
    id: str = Field(..., description="Invoice ID")
    date: datetime = Field(..., description="Invoice date")
    amount: int = Field(..., description="Amount in cents")
    status: str = Field(..., description="Payment status")
    pdf_url: Optional[str] = Field(None, description="PDF download URL")


class BillingOverview(BaseModel):
    """Schema for complete billing overview"""
    billing_info: BillingInfo
    invoices: List[Invoice] = Field([], description="Recent invoices")


class QuotaCheckRequest(BaseModel):
    """Request schema for quota checking"""
    action_type: str = Field(..., description="Type of action (upload, clip_generation, scheduling)")
    resource_amount: int = Field(1, description="Amount of resource needed")


class QuotaCheckResponse(BaseModel):
    """Response schema for quota checking"""
    allowed: bool = Field(..., description="Whether action is allowed")
    reason: Optional[str] = Field(None, description="Reason if not allowed")
    remaining: Optional[int] = Field(None, description="Remaining quota")
    limit: Optional[int] = Field(None, description="Total limit")
    reset_date: Optional[datetime] = Field(None, description="Next reset date")


class UsageTrackingRequest(BaseModel):
    """Request schema for tracking usage"""
    action_type: str = Field(..., description="Type of action to track")
    amount: int = Field(1, description="Amount to track")
    metadata: Optional[Dict[str, Any]] = Field({}, description="Additional metadata")


class PlanFeatures(BaseModel):
    """Schema for displaying plan features"""
    name: str = Field(..., description="Plan name")
    price: str = Field(..., description="Plan price display")
    price_cents: Optional[int] = Field(None, description="Price in cents")
    interval: str = Field("month", description="Billing interval")
    features: List[str] = Field(..., description="List of plan features")
    popular: bool = Field(False, description="Whether this is the popular plan")
    cta_text: str = Field("Subscribe", description="Call to action button text")