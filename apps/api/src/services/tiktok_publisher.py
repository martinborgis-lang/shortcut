"""
TikTok Content Publishing Service for video upload and publishing
"""
import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
import structlog
import secrets
from urllib.parse import urlparse
from enum import Enum

from ..config import settings
from .encryption import encryption_service

logger = structlog.get_logger()


class TikTokError(Exception):
    """Base exception for TikTok API errors"""
    pass

class TikTokRateLimitError(TikTokError):
    """Rate limit exceeded error"""
    def __init__(self, retry_after: int = None):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds.")

class TikTokAuthError(TikTokError):
    """Authentication/authorization error"""
    pass

class TikTokUploadError(TikTokError):
    """Video upload error"""
    pass

class TikTokValidationError(TikTokError):
    """Input validation error"""
    pass

class TikTokNetworkError(TikTokError):
    """Network/connectivity error"""
    pass

class TikTokPublisherService:
    """Service for publishing video content to TikTok with enhanced error handling"""

    API_BASE_URL = "https://open.tiktokapis.com"

    # TikTok API endpoints
    CONTENT_INIT_URL = f"{API_BASE_URL}/v2/post/publish/inbox/video/init/"
    CONTENT_UPLOAD_URL = f"{API_BASE_URL}/v2/post/publish/video/init/"
    CONTENT_PUBLISH_URL = f"{API_BASE_URL}/v2/post/publish/submit/"
    CONTENT_STATUS_URL = f"{API_BASE_URL}/v2/post/publish/status/fetch/"

    # Video constraints
    MAX_FILE_SIZE = 4 * 1024 * 1024 * 1024  # 4GB
    MAX_DURATION = 10 * 60  # 10 minutes
    ALLOWED_FORMATS = ["mp4", "mov", "mpeg", "flv", "webm", "3gp"]

    # Rate limiting
    MAX_RETRIES = 3
    RETRY_DELAYS = [5, 15, 30]  # Progressive delays in seconds
    RATE_LIMIT_WAIT = 300  # 5 minutes default wait

    def __init__(self):
        """Initialize TikTok publisher service"""
        pass

    async def publish_video(
        self,
        encrypted_access_token: str,
        video_url: str,
        caption: str,
        hashtags: Optional[List[str]] = None,
        privacy_level: str = "SELF_ONLY",  # PUBLIC_TO_EVERYONE, MUTUAL_FOLLOW_FRIENDS, SELF_ONLY
        disable_duet: bool = False,
        disable_comment: bool = False,
        disable_stitch: bool = False,
        brand_content_toggle: bool = False,
        brand_organic_toggle: bool = False
    ) -> Dict[str, Any]:
        """
        Publish a video to TikTok with metadata and comprehensive error handling

        Args:
            encrypted_access_token: Encrypted access token
            video_url: URL to the video file (S3, etc.)
            caption: Video caption/description
            hashtags: List of hashtags to include
            privacy_level: Privacy setting for the video
            disable_duet: Whether to disable duet feature
            disable_comment: Whether to disable comments
            disable_stitch: Whether to disable stitch feature
            brand_content_toggle: Whether this is branded content
            brand_organic_toggle: Whether this is organic branded content

        Returns:
            Dictionary with publish_id and status

        Raises:
            TikTokValidationError: Invalid input parameters
            TikTokAuthError: Authentication/authorization issues
            TikTokRateLimitError: Rate limiting issues
            TikTokUploadError: Video upload issues
            TikTokNetworkError: Network connectivity issues
            TikTokError: Other TikTok API errors
        """
        # Input validation
        self._validate_publish_inputs(
            encrypted_access_token, video_url, caption, hashtags, privacy_level
        )

        try:
            # Mock mode for development
            if settings.MOCK_MODE or not encrypted_access_token:
                return await self._mock_publish_video(video_url, caption, hashtags)

            # Decrypt access token with error handling
            try:
                access_token = encryption_service.decrypt_token(encrypted_access_token)
            except Exception as e:
                logger.error("Failed to decrypt access token", error=str(e))
                raise TikTokAuthError("Invalid or corrupted access token")

            # Validate access token format
            if not access_token or len(access_token) < 20:
                raise TikTokAuthError("Malformed access token")

            # Execute publish workflow with retry logic
            return await self._execute_publish_workflow(
                access_token=access_token,
                video_url=video_url,
                caption=caption,
                hashtags=hashtags,
                privacy_level=privacy_level,
                disable_duet=disable_duet,
                disable_comment=disable_comment,
                disable_stitch=disable_stitch,
                brand_content_toggle=brand_content_toggle,
                brand_organic_toggle=brand_organic_toggle
            )

        except TikTokError:
            # Re-raise TikTok-specific errors
            raise
        except httpx.TimeoutException:
            logger.error("Timeout publishing video to TikTok", video_url=video_url[:50])
            raise TikTokNetworkError("Request timeout - TikTok API is not responding")
        except httpx.NetworkError as e:
            logger.error("Network error publishing video to TikTok", error=str(e))
            raise TikTokNetworkError(f"Network connectivity issue: {e}")
        except Exception as e:
            logger.error("Unexpected error publishing video to TikTok",
                        error=str(e), video_url=video_url[:50])
            raise TikTokError(f"Unexpected error during video publishing: {e}")

    async def get_publish_status(
        self,
        encrypted_access_token: str,
        publish_id: str
    ) -> Dict[str, Any]:
        """
        Check the status of a published video with enhanced error handling

        Args:
            encrypted_access_token: Encrypted access token
            publish_id: Publish ID returned from publish_video

        Returns:
            Dictionary with status and video information

        Raises:
            TikTokValidationError: Invalid input parameters
            TikTokAuthError: Authentication issues
            TikTokRateLimitError: Rate limiting issues
            TikTokNetworkError: Network issues
            TikTokError: Other API errors
        """
        # Input validation
        if not publish_id or len(publish_id) < 5:
            raise TikTokValidationError("Invalid publish ID")

        if not encrypted_access_token:
            raise TikTokValidationError("Access token is required")

        try:
            if settings.MOCK_MODE:
                return self._mock_publish_status(publish_id)

            # Decrypt access token with error handling
            try:
                access_token = encryption_service.decrypt_token(encrypted_access_token)
            except Exception:
                raise TikTokAuthError("Invalid or corrupted access token")

            return await self._get_status_with_retry(access_token, publish_id)

        except TikTokError:
            raise
        except httpx.TimeoutException:
            logger.error("Timeout getting TikTok publish status", publish_id=publish_id)
            raise TikTokNetworkError("Request timeout checking publish status")
        except Exception as e:
            logger.error("Failed to get TikTok publish status",
                        error=str(e), publish_id=publish_id)
            raise TikTokError(f"Status check failed: {e}")

    def _validate_publish_inputs(
        self,
        encrypted_access_token: str,
        video_url: str,
        caption: str,
        hashtags: Optional[List[str]],
        privacy_level: str
    ):
        """Validate input parameters for video publishing"""
        if not encrypted_access_token:
            raise TikTokValidationError("Access token is required")

        if not video_url or not video_url.startswith(('http://', 'https://')):
            raise TikTokValidationError("Valid video URL is required")

        if not caption:
            raise TikTokValidationError("Caption is required")

        if len(caption) > 2200:
            raise TikTokValidationError("Caption exceeds 2200 character limit")

        if privacy_level not in ["PUBLIC_TO_EVERYONE", "MUTUAL_FOLLOW_FRIENDS", "SELF_ONLY"]:
            raise TikTokValidationError(f"Invalid privacy level: {privacy_level}")

        if hashtags:
            if len(hashtags) > 10:
                raise TikTokValidationError("Maximum 10 hashtags allowed")
            for tag in hashtags:
                if not tag or len(tag) > 50:
                    raise TikTokValidationError("Invalid hashtag format or length")

    async def _execute_publish_workflow(
        self,
        access_token: str,
        video_url: str,
        caption: str,
        hashtags: Optional[List[str]] = None,
        privacy_level: str = "SELF_ONLY",
        disable_duet: bool = False,
        disable_comment: bool = False,
        disable_stitch: bool = False,
        brand_content_toggle: bool = False,
        brand_organic_toggle: bool = False
    ) -> Dict[str, Any]:
        """Execute the complete publish workflow with retry logic"""
        for attempt in range(self.MAX_RETRIES):
            try:
                timeout = httpx.Timeout(60.0, connect=15.0)
                async with httpx.AsyncClient(timeout=timeout) as client:
                    # Step 1: Initialize video upload
                    upload_info = await self._init_video_upload_with_retry(client, access_token)

                    # Step 2: Upload video file
                    await self._upload_video_file_with_retry(client, upload_info, video_url)

                    # Step 3: Publish video with metadata
                    publish_result = await self._publish_video_content_with_retry(
                        client=client,
                        access_token=access_token,
                        upload_info=upload_info,
                        caption=caption,
                        hashtags=hashtags,
                        privacy_level=privacy_level,
                        disable_duet=disable_duet,
                        disable_comment=disable_comment,
                        disable_stitch=disable_stitch,
                        brand_content_toggle=brand_content_toggle,
                        brand_organic_toggle=brand_organic_toggle
                    )

                    logger.info("Successfully published video to TikTok",
                              publish_id=publish_result.get("publish_id"))
                    return publish_result

            except TikTokRateLimitError as e:
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = e.retry_after or self.RETRY_DELAYS[attempt]
                    logger.warning("Rate limited, retrying",
                                 attempt=attempt + 1, wait_time=wait_time)
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise

            except (TikTokNetworkError, httpx.RequestError) as e:
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = self.RETRY_DELAYS[attempt]
                    logger.warning("Network error, retrying",
                                 attempt=attempt + 1, wait_time=wait_time, error=str(e))
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise TikTokNetworkError(f"Network error after {self.MAX_RETRIES} attempts: {e}")

            except TikTokError:
                # Don't retry other TikTok errors
                raise

        raise TikTokError(f"Publishing failed after {self.MAX_RETRIES} attempts")

    async def _init_video_upload_with_retry(self, client: httpx.AsyncClient, access_token: str) -> Dict[str, Any]:
        """Initialize video upload session with error handling"""
        try:
            response = await client.post(
                self.CONTENT_UPLOAD_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "User-Agent": "TikTokAPI/1.0"
                },
                json={
                    "source_info": {
                        "source": "FILE_UPLOAD",
                        "video_size": self.MAX_FILE_SIZE,  # Placeholder, will be updated
                        "chunk_size": 10 * 1024 * 1024,  # 10MB chunks
                        "total_chunk_count": 1
                    }
                }
            )

            await self._handle_api_response(response, "upload initialization")
            data = response.json()
            upload_info = data.get("data", {})

            if not upload_info.get("upload_url"):
                raise TikTokUploadError("No upload URL provided by TikTok")

            return upload_info

        except httpx.HTTPStatusError as e:
            await self._handle_http_error(e, "upload initialization")

    async def _upload_video_file_with_retry(
        self,
        client: httpx.AsyncClient,
        upload_info: Dict[str, Any],
        video_url: str
    ):
        """Upload video file to TikTok's servers with retry logic"""
        upload_url = upload_info.get("upload_url")
        if not upload_url:
            raise TikTokUploadError("No upload URL provided by TikTok")

        try:
            # First, get video info for validation
            async with client.stream("HEAD", video_url) as head_response:
                head_response.raise_for_status()
                content_length = head_response.headers.get("content-length")

                if content_length:
                    file_size = int(content_length)
                    if file_size > self.MAX_FILE_SIZE:
                        raise TikTokValidationError(f"Video file too large: {file_size} bytes")

            # Download and upload video with progress tracking
            async with client.stream("GET", video_url) as video_response:
                video_response.raise_for_status()

                # Collect video data with size limit
                video_data = b""
                async for chunk in video_response.aiter_bytes(chunk_size=1024 * 1024):  # 1MB chunks
                    video_data += chunk
                    if len(video_data) > self.MAX_FILE_SIZE:
                        raise TikTokValidationError("Video file too large during download")

                # Upload video to TikTok
                upload_response = await client.put(
                    upload_url,
                    content=video_data,
                    headers={
                        "Content-Type": "video/mp4",
                        "Content-Length": str(len(video_data))
                    }
                )

                if upload_response.status_code == 413:
                    raise TikTokValidationError("Video file too large for TikTok")

                upload_response.raise_for_status()
                logger.info("Video upload completed", size_bytes=len(video_data))

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise TikTokUploadError("Video file not found at provided URL")
            elif e.response.status_code == 403:
                raise TikTokUploadError("Access denied to video file")
            else:
                await self._handle_http_error(e, "video upload")
        except httpx.RequestError as e:
            raise TikTokNetworkError(f"Network error during video upload: {e}")

    async def _publish_video_content_with_retry(
        self,
        client: httpx.AsyncClient,
        access_token: str,
        upload_info: Dict[str, Any],
        caption: str,
        hashtags: Optional[List[str]] = None,
        privacy_level: str = "SELF_ONLY",
        disable_duet: bool = False,
        disable_comment: bool = False,
        disable_stitch: bool = False,
        brand_content_toggle: bool = False,
        brand_organic_toggle: bool = False
    ) -> Dict[str, Any]:
        """Publish uploaded video with metadata and error handling"""

        # Validate video_id from upload_info
        video_id = upload_info.get("video_id")
        if not video_id:
            raise TikTokUploadError("Video ID missing from upload info")

        # Build caption with hashtags
        full_caption = caption
        if hashtags:
            cleaned_hashtags = [tag.strip('#').strip() for tag in hashtags if tag.strip()]
            if cleaned_hashtags:
                hashtag_string = " ".join([f"#{tag}" for tag in cleaned_hashtags])
                full_caption = f"{caption} {hashtag_string}".strip()

        # Prepare post info with validation
        post_info = {
            "title": full_caption[:2200],  # TikTok caption limit
            "privacy_level": privacy_level,
            "disable_duet": disable_duet,
            "disable_comment": disable_comment,
            "disable_stitch": disable_stitch,
            "video_cover_timestamp_ms": 1000  # Use frame at 1 second as cover
        }

        # Add brand content settings if enabled
        if brand_content_toggle:
            post_info["brand_content_toggle"] = True
        if brand_organic_toggle:
            post_info["brand_organic_toggle"] = True

        try:
            # Submit for publishing
            response = await client.post(
                self.CONTENT_PUBLISH_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "User-Agent": "TikTokAPI/1.0"
                },
                json={
                    "post_info": post_info,
                    "source_info": {
                        "source": "FILE_UPLOAD",
                        "video_id": video_id
                    }
                }
            )

            await self._handle_api_response(response, "video publishing")
            data = response.json()

            publish_data = data.get("data", {})
            publish_id = publish_data.get("publish_id")

            if not publish_id:
                raise TikTokError("No publish ID returned from TikTok")

            return {
                "publish_id": publish_id,
                "status": "submitted",
                "message": "Video submitted for publishing",
                "video_id": video_id
            }

        except httpx.HTTPStatusError as e:
            await self._handle_http_error(e, "video publishing")

    async def _get_status_with_retry(self, access_token: str, publish_id: str) -> Dict[str, Any]:
        """Get publish status with retry logic"""
        for attempt in range(self.MAX_RETRIES):
            try:
                timeout = httpx.Timeout(30.0, connect=10.0)
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        self.CONTENT_STATUS_URL,
                        headers={
                            "Authorization": f"Bearer {access_token}",
                            "Content-Type": "application/json",
                            "User-Agent": "TikTokAPI/1.0"
                        },
                        json={"publish_id": publish_id}
                    )

                    await self._handle_api_response(response, "status check")
                    result = response.json()

                    logger.info("Retrieved TikTok publish status",
                              publish_id=publish_id,
                              status=result.get("data", {}).get("status"))
                    return result

            except TikTokRateLimitError as e:
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = e.retry_after or self.RETRY_DELAYS[attempt]
                    logger.warning("Rate limited getting status, retrying",
                                 attempt=attempt + 1, wait_time=wait_time)
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise

            except httpx.RequestError as e:
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = self.RETRY_DELAYS[attempt]
                    logger.warning("Network error getting status, retrying",
                                 attempt=attempt + 1, error=str(e))
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise TikTokNetworkError(f"Network error after {self.MAX_RETRIES} attempts")

        raise TikTokError(f"Status check failed after {self.MAX_RETRIES} attempts")

    async def _handle_api_response(self, response: httpx.Response, operation: str):
        """Handle TikTok API response and convert to appropriate exceptions"""
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", self.RATE_LIMIT_WAIT))
            logger.warning(f"Rate limited during {operation}", retry_after=retry_after)
            raise TikTokRateLimitError(retry_after)

        if response.status_code == 401:
            logger.error(f"Unauthorized during {operation}")
            raise TikTokAuthError("Access token expired or invalid")

        if response.status_code == 403:
            logger.error(f"Forbidden during {operation}")
            raise TikTokAuthError("Insufficient permissions or account restricted")

        response.raise_for_status()

    async def _handle_http_error(self, error: httpx.HTTPStatusError, operation: str):
        """Handle HTTP errors and convert to appropriate TikTok exceptions"""
        status_code = error.response.status_code

        if status_code == 400:
            logger.error(f"Bad request during {operation}", response=error.response.text)
            raise TikTokValidationError(f"Invalid request for {operation}")
        elif status_code == 401:
            raise TikTokAuthError("Access token expired or invalid")
        elif status_code == 403:
            raise TikTokAuthError("Insufficient permissions or account restricted")
        elif status_code == 404:
            raise TikTokError(f"Resource not found during {operation}")
        elif status_code == 413:
            raise TikTokValidationError("Request payload too large")
        elif status_code == 429:
            retry_after = int(error.response.headers.get("Retry-After", self.RATE_LIMIT_WAIT))
            raise TikTokRateLimitError(retry_after)
        elif 500 <= status_code < 600:
            logger.error(f"Server error during {operation}", status_code=status_code)
            raise TikTokError(f"TikTok server error during {operation}: {status_code}")
        else:
            logger.error(f"Unexpected HTTP error during {operation}",
                        status_code=status_code, response=error.response.text)
            raise TikTokError(f"Unexpected error during {operation}: {status_code}")

    async def _mock_publish_video(
        self,
        video_url: str,
        caption: str,
        hashtags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Mock video publishing for development with validation"""
        logger.info("Using mock TikTok video publishing",
                   video_url=video_url[:50], caption=caption[:50])

        # Validate inputs even in mock mode
        if not video_url or not video_url.startswith(('http://', 'https://')):
            raise TikTokValidationError("Valid video URL is required")

        if not caption:
            raise TikTokValidationError("Caption is required")

        # Simulate upload delay
        await asyncio.sleep(2)

        mock_publish_id = f"mock_publish_{secrets.token_hex(16)}"
        mock_video_id = f"mock_video_{secrets.token_hex(20)}"

        return {
            "publish_id": mock_publish_id,
            "video_id": mock_video_id,
            "status": "submitted",
            "message": "Mock video submitted for publishing",
            "share_url": f"https://www.tiktok.com/@mockuser/video/{mock_video_id}",
            "created_time": int(datetime.utcnow().timestamp())
        }

    def _mock_publish_status(self, publish_id: str) -> Dict[str, Any]:
        """Mock publish status for development with validation"""
        if not publish_id:
            raise TikTokValidationError("Publish ID is required")

        return {
            "data": {
                "publish_id": publish_id,
                "status": "PUBLISHED_SUCCESS",
                "video_id": f"mock_video_{secrets.token_hex(20)}",
                "share_url": f"https://www.tiktok.com/@mockuser/video/mock_video_{secrets.token_hex(20)}",
                "created_time": int(datetime.utcnow().timestamp()),
                "updated_time": int(datetime.utcnow().timestamp())
            }
        }

    def validate_video_constraints(self, video_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate video against TikTok constraints

        Args:
            video_info: Dictionary with video metadata (size, duration, format)

        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []

        # Check file size
        file_size = video_info.get("size", 0)
        if file_size > self.MAX_FILE_SIZE:
            errors.append(f"Video file size ({file_size / 1024 / 1024:.1f}MB) exceeds TikTok limit ({self.MAX_FILE_SIZE / 1024 / 1024:.1f}MB)")

        # Check duration
        duration = video_info.get("duration", 0)
        if duration > self.MAX_DURATION:
            errors.append(f"Video duration ({duration}s) exceeds TikTok limit ({self.MAX_DURATION}s)")

        if duration < 3:
            warnings.append("Videos shorter than 3 seconds may not perform well on TikTok")

        # Check format
        file_format = video_info.get("format", "").lower()
        if file_format not in self.ALLOWED_FORMATS:
            errors.append(f"Video format '{file_format}' not supported. Allowed formats: {', '.join(self.ALLOWED_FORMATS)}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }


# Singleton instance
tiktok_publisher_service = TikTokPublisherService()