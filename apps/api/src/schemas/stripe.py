"""Stripe schemas for API requests and responses"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from enum import Enum


class PlanType(str, Enum):
    """Available subscription plans"""
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class CreateCheckoutRequest(BaseModel):
    """Request schema for creating Stripe checkout session"""
    plan: PlanType = Field(..., description="Subscription plan to purchase")
    success_url: Optional[str] = Field(None, description="URL to redirect after successful payment")
    cancel_url: Optional[str] = Field(None, description="URL to redirect after cancelled payment")

    @validator('plan')
    def validate_plan(cls, v):
        if v not in [PlanType.STARTER, PlanType.PRO, PlanType.ENTERPRISE]:
            raise ValueError('Invalid plan type')
        return v


class CheckoutResponse(BaseModel):
    """Response schema for checkout session creation"""
    checkout_url: str = Field(..., description="Stripe checkout session URL")
    session_id: str = Field(..., description="Stripe session ID")


class PortalResponse(BaseModel):
    """Response schema for customer portal creation"""
    portal_url: str = Field(..., description="Stripe customer portal URL")


class StripeWebhookEvent(BaseModel):
    """Schema for processing Stripe webhook events"""
    id: str
    object: str
    type: str
    data: Dict[str, Any]
    created: int
    livemode: bool
    pending_webhooks: int
    request: Optional[Dict[str, Any]] = None


class CheckoutSessionCompleted(BaseModel):
    """Schema for checkout.session.completed event data"""
    id: str
    object: str
    customer: str
    subscription: str
    metadata: Dict[str, str]
    mode: str
    status: str


class SubscriptionUpdated(BaseModel):
    """Schema for customer.subscription.updated event data"""
    id: str
    object: str
    customer: str
    status: str
    current_period_end: int
    current_period_start: int
    items: Dict[str, Any]
    metadata: Dict[str, str]


class SubscriptionDeleted(BaseModel):
    """Schema for customer.subscription.deleted event data"""
    id: str
    object: str
    customer: str
    status: str
    canceled_at: int
    ended_at: Optional[int]


class InvoicePaymentFailed(BaseModel):
    """Schema for invoice.payment_failed event data"""
    id: str
    object: str
    customer: str
    subscription: str
    status: str
    attempt_count: int
    next_payment_attempt: Optional[int]


class MockStripeResponse(BaseModel):
    """Mock response for development mode"""
    success: bool = True
    message: str = "Mock Stripe response"
    data: Dict[str, Any] = {}