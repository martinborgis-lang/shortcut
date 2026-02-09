"""
Rate Limiting Dependencies based on user plan
"""
import time
import structlog
from typing import Dict, Optional
from fastapi import HTTPException, Request, status, Depends
from starlette.middleware.base import BaseHTTPMiddleware

from ..models.user import User, PlanType
from ..middleware.auth import get_current_user

logger = structlog.get_logger()


class RateLimitStore:
    """In-memory rate limit store (use Redis in production)"""

    def __init__(self):
        self._store: Dict[str, Dict[str, float]] = {}

    def get_requests(self, key: str, window: int) -> int:
        """Get number of requests in the window"""
        current_time = time.time()
        window_start = current_time - window

        if key not in self._store:
            self._store[key] = {}

        # Clean old entries
        self._store[key] = {
            timestamp: count for timestamp, count in self._store[key].items()
            if float(timestamp) > window_start
        }

        return sum(self._store[key].values())

    def add_request(self, key: str) -> None:
        """Add a request to the store"""
        current_time = str(time.time())

        if key not in self._store:
            self._store[key] = {}

        self._store[key][current_time] = 1


# Global rate limit store (use Redis in production)
rate_limit_store = RateLimitStore()


class PlanBasedRateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware based on user plan"""

    def __init__(self, app):
        super().__init__(app)
        self.rate_limits = {
            PlanType.FREE: {"requests": 100, "window": 3600},      # 100 req/hour
            PlanType.STARTER: {"requests": 500, "window": 3600},   # 500 req/hour
            PlanType.PRO: {"requests": 2000, "window": 3600},      # 2000 req/hour
            PlanType.ENTERPRISE: {"requests": 10000, "window": 3600}  # 10000 req/hour
        }

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for public routes
        if self.is_public_route(request.url.path):
            return await call_next(request)

        # Check if user is authenticated
        user = getattr(request.state, 'user', None)
        if not user:
            # No user means authentication will be handled by auth middleware
            return await call_next(request)

        # Apply rate limiting
        plan = user.plan if hasattr(user, 'plan') else PlanType.FREE
        limits = self.rate_limits.get(plan, self.rate_limits[PlanType.FREE])

        # Create rate limit key
        rate_limit_key = f"rate_limit:{user.id}:{plan.value}"

        # Check current usage
        current_requests = rate_limit_store.get_requests(rate_limit_key, limits["window"])

        if current_requests >= limits["requests"]:
            logger.warning(
                "Rate limit exceeded",
                user_id=str(user.id),
                plan=plan.value,
                current_requests=current_requests,
                limit=limits["requests"]
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Plan {plan.value} allows {limits['requests']} requests per hour."
            )

        # Add request to store
        rate_limit_store.add_request(rate_limit_key)

        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limits["requests"])
        response.headers["X-RateLimit-Remaining"] = str(limits["requests"] - current_requests - 1)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + limits["window"]))

        return response

    def is_public_route(self, path: str) -> bool:
        """Check if route is public (no rate limiting)"""
        public_routes = [
            "/health",
            "/",
            "/docs",
            "/openapi.json",
            "/webhooks/",  # Webhooks should not be rate limited
        ]

        return any(path.startswith(route) for route in public_routes)


class MinuteUsageMiddleware(BaseHTTPMiddleware):
    """Middleware to track minute usage for video processing endpoints"""

    def __init__(self, app):
        super().__init__(app)
        self.minute_consuming_routes = [
            "/api/clips/generate",
            "/api/clips/process",
        ]

    async def dispatch(self, request: Request, call_next):
        # Check if this is a minute-consuming route
        if not any(request.url.path.startswith(route) for route in self.minute_consuming_routes):
            return await call_next(request)

        # Get user
        user = getattr(request.state, 'user', None)
        if not user:
            return await call_next(request)

        # Check if user can use minutes (this will be set by the endpoint)
        # For now, just proceed and let the endpoint handle the logic
        return await call_next(request)


# Rate limiting functions for use as dependencies
async def check_rate_limit(
    request: Request,
    user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to check rate limits for authenticated users
    """
    # Rate limiting configuration
    rate_limits = {
        PlanType.FREE: {"requests": 100, "window": 3600},      # 100 req/hour
        PlanType.STARTER: {"requests": 500, "window": 3600},   # 500 req/hour
        PlanType.PRO: {"requests": 2000, "window": 3600},      # 2000 req/hour
        PlanType.ENTERPRISE: {"requests": 10000, "window": 3600}  # 10000 req/hour
    }

    # Skip rate limiting for public routes
    public_routes = [
        "/health",
        "/",
        "/docs",
        "/openapi.json",
        "/api/webhooks/",  # Webhooks should not be rate limited
    ]

    if any(request.url.path.startswith(route) for route in public_routes):
        return user

    # Apply rate limiting
    plan = user.plan if hasattr(user, 'plan') else PlanType.FREE
    limits = rate_limits.get(plan, rate_limits[PlanType.FREE])

    # Create rate limit key
    rate_limit_key = f"rate_limit:{user.id}:{plan.value}"

    # Check current usage
    current_requests = rate_limit_store.get_requests(rate_limit_key, limits["window"])

    if current_requests >= limits["requests"]:
        logger.warning(
            "Rate limit exceeded",
            user_id=str(user.id),
            plan=plan.value,
            current_requests=current_requests,
            limit=limits["requests"]
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Plan {plan.value} allows {limits['requests']} requests per hour."
        )

    # Add request to store
    rate_limit_store.add_request(rate_limit_key)

    # Log successful rate limit check
    logger.debug(
        "Rate limit check passed",
        user_id=str(user.id),
        plan=plan.value,
        current_requests=current_requests + 1,
        limit=limits["requests"]
    )

    return user


async def check_minute_usage(
    request: Request,
    user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to check minute usage for video processing endpoints
    """
    minute_consuming_routes = [
        "/api/clips/generate",
        "/api/clips/process",
    ]

    # Check if this is a minute-consuming route
    if not any(request.url.path.startswith(route) for route in minute_consuming_routes):
        return user

    # Check if user has enough minutes remaining
    if user.monthly_minutes_used >= user.monthly_minutes_limit:
        logger.warning(
            "Monthly minute limit exceeded",
            user_id=str(user.id),
            minutes_used=user.monthly_minutes_used,
            limit=user.monthly_minutes_limit
        )
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Monthly minute limit of {user.monthly_minutes_limit} minutes exceeded. Please upgrade your plan."
        )

    logger.debug(
        "Minute usage check passed",
        user_id=str(user.id),
        minutes_used=user.monthly_minutes_used,
        limit=user.monthly_minutes_limit
    )

    return user


# Combined dependency for endpoints that need both rate limiting and minute checking
async def check_rate_limit_and_minutes(
    request: Request,
    user: User = Depends(check_rate_limit)
) -> User:
    """
    Combined dependency that checks both rate limits and minute usage
    """
    return await check_minute_usage(request, user)