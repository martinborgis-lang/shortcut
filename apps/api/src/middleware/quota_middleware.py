"""Quota middleware for enforcing plan limits"""

import structlog
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Callable, Awaitable, Optional
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..services.quota_service import QuotaService
from ..middleware.auth import get_current_user_from_request

logger = structlog.get_logger()


class QuotaMiddleware:
    """Middleware to check quotas before expensive operations"""

    def __init__(self):
        self.quota_endpoints = {
            # Upload endpoints that need quota checking
            "/api/projects/": ["POST"],  # Creating new project with upload
            "/api/projects/{project_id}/upload": ["POST"],  # Uploading to existing project
            "/api/clips/generate": ["POST"],  # Generating clips
            "/api/schedule/": ["POST"],  # Scheduling posts
        }

    async def __call__(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """
        Middleware to check quotas for specific endpoints

        Args:
            request: FastAPI request object
            call_next: Next middleware/endpoint in chain

        Returns:
            Response object
        """
        # Skip quota checking for non-quota endpoints
        if not self._should_check_quota(request):
            return await call_next(request)

        try:
            # Get database session
            db = next(get_db())

            # Get current user from request
            user = await get_current_user_from_request(request, db)
            if not user:
                return await call_next(request)  # Let auth middleware handle this

            # Initialize quota service
            quota_service = QuotaService(db)

            # Check quotas based on endpoint
            quota_check = await self._check_quota_for_endpoint(request, user, quota_service)

            if not quota_check.allowed:
                # Return 429 Too Many Requests with quota information
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Quota exceeded",
                        "message": quota_check.reason,
                        "quota_info": {
                            "remaining": quota_check.remaining,
                            "limit": quota_check.limit,
                            "reset_date": quota_check.reset_date.isoformat() if quota_check.reset_date else None
                        }
                    }
                )

            # Continue to next middleware/endpoint
            response = await call_next(request)

            # Track usage after successful operation (if needed)
            await self._track_usage_after_success(request, user, quota_service, response)

            return response

        except Exception as e:
            logger.error(
                "Error in quota middleware",
                error=str(e),
                path=request.url.path,
                method=request.method
            )
            # Continue to next middleware on error
            return await call_next(request)

    def _should_check_quota(self, request: Request) -> bool:
        """
        Check if this endpoint requires quota checking

        Args:
            request: FastAPI request object

        Returns:
            bool: True if quota should be checked
        """
        path = request.url.path
        method = request.method

        # Check exact matches
        if path in self.quota_endpoints and method in self.quota_endpoints[path]:
            return True

        # Check pattern matches (for parameterized routes)
        for pattern, methods in self.quota_endpoints.items():
            if method in methods and self._path_matches_pattern(path, pattern):
                return True

        return False

    def _path_matches_pattern(self, path: str, pattern: str) -> bool:
        """
        Check if path matches pattern with parameters

        Args:
            path: Actual request path
            pattern: Pattern with {param} placeholders

        Returns:
            bool: True if path matches pattern
        """
        # Simple pattern matching for paths with parameters
        # e.g., "/api/projects/123/upload" matches "/api/projects/{project_id}/upload"

        path_parts = path.strip('/').split('/')
        pattern_parts = pattern.strip('/').split('/')

        if len(path_parts) != len(pattern_parts):
            return False

        for path_part, pattern_part in zip(path_parts, pattern_parts):
            if pattern_part.startswith('{') and pattern_part.endswith('}'):
                # This is a parameter, matches any value
                continue
            elif path_part != pattern_part:
                return False

        return True

    async def _check_quota_for_endpoint(self, request: Request, user: User, quota_service: QuotaService):
        """
        Check quota for specific endpoint

        Args:
            request: FastAPI request object
            user: User object
            quota_service: QuotaService instance

        Returns:
            QuotaCheckResponse
        """
        path = request.url.path
        method = request.method

        # Project upload endpoints
        if ("/api/projects/" in path and method == "POST") or \
           ("/upload" in path and method == "POST"):
            # For upload endpoints, we need to check the video duration
            # This would require parsing the multipart form data
            # For now, assume average video duration and check general upload quota
            return quota_service.check_upload_quota(user, 5.0)  # Assume 5 minutes average

        # Clip generation endpoint
        elif path == "/api/clips/generate" and method == "POST":
            return quota_service.check_clip_quota(user)

        # Scheduling endpoint
        elif path == "/api/schedule/" and method == "POST":
            return quota_service.check_scheduling_quota(user)

        # Default: allow (shouldn't reach here)
        else:
            from ..schemas.billing import QuotaCheckResponse
            return QuotaCheckResponse(allowed=True)

    async def _track_usage_after_success(
        self,
        request: Request,
        user: User,
        quota_service: QuotaService,
        response: Response
    ):
        """
        Track usage after successful operation

        Args:
            request: FastAPI request object
            user: User object
            quota_service: QuotaService instance
            response: Response object
        """
        # Only track usage for successful operations (2xx status codes)
        if response.status_code < 200 or response.status_code >= 300:
            return

        # This would require more sophisticated tracking based on the actual
        # operation performed. For now, we'll leave this as a placeholder.
        # The actual usage tracking would be done in the endpoint handlers
        # using the BillingService.
        pass


# Dependency function for quota checking in specific endpoints
async def check_upload_quota(
    request: Request,
    video_duration_minutes: float,
    db: Session = None
):
    """
    Dependency function to check upload quota for specific video duration

    Args:
        request: FastAPI request
        video_duration_minutes: Duration of video to upload
        db: Database session

    Raises:
        HTTPException: If quota exceeded
    """
    try:
        if not db:
            db = next(get_db())

        user = await get_current_user_from_request(request, db)
        if not user:
            return  # Let auth handle this

        quota_service = QuotaService(db)
        quota_check = quota_service.check_upload_quota(user, video_duration_minutes)

        if not quota_check.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Upload quota exceeded",
                    "message": quota_check.reason,
                    "quota_info": {
                        "remaining": quota_check.remaining,
                        "limit": quota_check.limit,
                        "reset_date": quota_check.reset_date.isoformat() if quota_check.reset_date else None
                    }
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error checking upload quota", error=str(e))
        # Don't block the request on quota check errors


async def check_clip_quota(request: Request, clips_count: int = 1, db: Session = None):
    """
    Dependency function to check clip generation quota

    Args:
        request: FastAPI request
        clips_count: Number of clips to generate
        db: Database session

    Raises:
        HTTPException: If quota exceeded
    """
    try:
        if not db:
            db = next(get_db())

        user = await get_current_user_from_request(request, db)
        if not user:
            return

        quota_service = QuotaService(db)
        quota_check = quota_service.check_clip_quota(user, clips_count)

        if not quota_check.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Clip generation quota exceeded",
                    "message": quota_check.reason,
                    "quota_info": {
                        "remaining": quota_check.remaining,
                        "limit": quota_check.limit,
                        "reset_date": quota_check.reset_date.isoformat() if quota_check.reset_date else None
                    }
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error checking clip quota", error=str(e))


async def check_scheduling_quota(request: Request, db: Session = None):
    """
    Dependency function to check scheduling quota

    Args:
        request: FastAPI request
        db: Database session

    Raises:
        HTTPException: If quota exceeded
    """
    try:
        if not db:
            db = next(get_db())

        user = await get_current_user_from_request(request, db)
        if not user:
            return

        quota_service = QuotaService(db)
        quota_check = quota_service.check_scheduling_quota(user)

        if not quota_check.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Scheduling quota exceeded",
                    "message": quota_check.reason,
                    "quota_info": {
                        "remaining": quota_check.remaining,
                        "limit": quota_check.limit,
                        "reset_date": quota_check.reset_date.isoformat() if quota_check.reset_date else None
                    }
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error checking scheduling quota", error=str(e))