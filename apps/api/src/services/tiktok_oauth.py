"""
TikTok OAuth 2.0 service for user authentication and token management
"""
import asyncio
import httpx
import secrets
import hashlib
import hmac
import base64
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlencode, parse_qs, urlparse
import structlog

from ..config import settings
from .encryption import encryption_service

logger = structlog.get_logger()


class TikTokOAuthService:
    """Service for handling TikTok OAuth 2.0 flow"""

    BASE_URL = "https://www.tiktok.com"
    API_BASE_URL = "https://open.tiktokapis.com"

    # TikTok OAuth endpoints
    AUTH_URL = f"{BASE_URL}/v2/auth/authorize/"
    TOKEN_URL = f"{API_BASE_URL}/v2/oauth/token/"
    USER_INFO_URL = f"{API_BASE_URL}/v2/user/info/"
    REFRESH_TOKEN_URL = f"{API_BASE_URL}/v2/oauth/token/"

    # Required scopes for video posting
    SCOPES = [
        "user.info.basic",
        "user.info.profile",
        "user.info.stats",
        "video.upload",
        "video.publish",
        "video.list"
    ]

    def __init__(self):
        """Initialize TikTok OAuth service"""
        self.client_key = settings.TIKTOK_CLIENT_KEY
        self.client_secret = settings.TIKTOK_CLIENT_SECRET
        self.redirect_uri = f"{settings.FRONTEND_URL}/auth/tiktok/callback"

    def generate_auth_url(self, user_id: str) -> Tuple[str, str]:
        """
        Generate TikTok OAuth authorization URL with enhanced security

        Args:
            user_id: Internal user ID for state verification

        Returns:
            Tuple of (auth_url, state) for verification
        """
        if not self.client_key:
            raise ValueError("TikTok client key not configured")

        # Validate redirect URI for security
        if not self._validate_redirect_uri(self.redirect_uri):
            raise ValueError("Invalid redirect URI configuration")

        # Generate secure state parameter with timestamp and nonce
        state = self._generate_secure_state(user_id)

        # Build OAuth parameters
        params = {
            "client_key": self.client_key,
            "scope": ",".join(self.SCOPES),
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "state": state
        }

        auth_url = f"{self.AUTH_URL}?{urlencode(params)}"

        logger.info("Generated TikTok OAuth URL", user_id=user_id[:8] + "...")
        return auth_url, state

    async def exchange_code_for_tokens(self, code: str, state: str, user_id: str = None) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens with enhanced security

        Args:
            code: Authorization code from TikTok
            state: State parameter for verification
            user_id: Optional user ID for additional state verification

        Returns:
            Dictionary containing tokens and user info
        """
        if not self.client_secret:
            if settings.MOCK_MODE:
                return self._mock_token_exchange(code, state)
            raise ValueError("TikTok client secret not configured")

        # Enhanced input validation
        if not code or len(code) < 10:
            raise ValueError("Invalid authorization code")

        if not state or len(state) < 16:
            raise ValueError("Invalid state parameter")

        # Verify state parameter if user_id provided
        if user_id and not self.verify_state(state, user_id):
            logger.warning("State parameter verification failed",
                          user_id=user_id[:8] + "...", state=state[:16] + "...")
            raise ValueError("State parameter verification failed")

        try:
            # Use timeout with retry configuration
            timeout = httpx.Timeout(30.0, connect=10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                # Exchange code for tokens with retry logic
                token_data = await self._request_tokens_with_retry(client, code)

                # Validate token response
                if not self._validate_token_response(token_data):
                    raise ValueError("Invalid token response from TikTok")

                # Get user information with error handling
                user_info = await self._get_user_info_with_retry(client, token_data["access_token"])

                # Encrypt tokens before returning
                encrypted_access_token = encryption_service.encrypt_token(token_data["access_token"])
                encrypted_refresh_token = encryption_service.encrypt_token(token_data["refresh_token"])

                # Calculate token expiry with buffer
                expires_in = token_data.get("expires_in", 86400)
                expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

                result = {
                    "access_token": encrypted_access_token,
                    "refresh_token": encrypted_refresh_token,
                    "token_expires_at": expires_at,
                    "user_info": user_info,
                    "platform": "tiktok"
                }

                logger.info("Successfully exchanged TikTok code for tokens",
                          user_id=user_info.get("open_id", "unknown")[:8] + "...")
                return result

        except httpx.TimeoutException:
            logger.error("Timeout during TikTok OAuth exchange", code=code[:10] + "...")
            raise RuntimeError("TikTok OAuth exchange timed out")
        except httpx.HTTPStatusError as e:
            logger.error("HTTP error during TikTok OAuth exchange",
                        status_code=e.response.status_code,
                        code=code[:10] + "...")
            raise RuntimeError(f"TikTok OAuth exchange failed: HTTP {e.response.status_code}")
        except Exception as e:
            logger.error("Failed to exchange TikTok code for tokens",
                        error=str(e), code=code[:10] + "...")
            raise RuntimeError(f"TikTok OAuth exchange failed: {e}")

    async def refresh_access_token(self, encrypted_refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an expired access token with enhanced error handling

        Args:
            encrypted_refresh_token: Encrypted refresh token

        Returns:
            Dictionary containing new tokens
        """
        if not self.client_secret:
            if settings.MOCK_MODE:
                return self._mock_token_refresh(encrypted_refresh_token)
            raise ValueError("TikTok client secret not configured")

        if not encrypted_refresh_token:
            raise ValueError("Refresh token is required")

        try:
            # Decrypt refresh token with validation
            try:
                refresh_token = encryption_service.decrypt_token(encrypted_refresh_token)
            except Exception:
                raise ValueError("Invalid or corrupted refresh token")

            # Validate refresh token format
            if not refresh_token or len(refresh_token) < 10:
                raise ValueError("Malformed refresh token")

            timeout = httpx.Timeout(30.0, connect=10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    self.REFRESH_TOKEN_URL,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data={
                        "client_key": self.client_key,
                        "client_secret": self.client_secret,
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token
                    }
                )

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After", "60")
                    logger.warning("Rate limited during token refresh", retry_after=retry_after)
                    raise RuntimeError(f"Rate limited, retry after {retry_after} seconds")

                response.raise_for_status()
                token_data = response.json()

                # Validate token response
                if not self._validate_token_response(token_data):
                    raise ValueError("Invalid token response from TikTok")

                # Encrypt new tokens
                encrypted_access_token = encryption_service.encrypt_token(token_data["access_token"])
                encrypted_new_refresh_token = encryption_service.encrypt_token(token_data["refresh_token"])

                # Calculate new expiry with safety buffer
                expires_in = token_data.get("expires_in", 86400)
                expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

                result = {
                    "access_token": encrypted_access_token,
                    "refresh_token": encrypted_new_refresh_token,
                    "token_expires_at": expires_at
                }

                logger.info("Successfully refreshed TikTok access token")
                return result

        except httpx.TimeoutException:
            logger.error("Timeout during TikTok token refresh")
            raise RuntimeError("Token refresh timed out")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Unauthorized during token refresh - refresh token invalid")
                raise RuntimeError("Refresh token expired or invalid")
            elif e.response.status_code == 400:
                logger.error("Bad request during token refresh", response=e.response.text)
                raise RuntimeError("Invalid token refresh request")
            else:
                logger.error("HTTP error during token refresh",
                           status_code=e.response.status_code)
                raise RuntimeError(f"Token refresh failed: HTTP {e.response.status_code}")
        except Exception as e:
            logger.error("Failed to refresh TikTok access token", error=str(e))
            raise RuntimeError(f"TikTok token refresh failed: {e}")

    def verify_state(self, state: str, user_id: str) -> bool:
        """
        Verify OAuth state parameter with enhanced security

        Args:
            state: State parameter from OAuth callback
            user_id: Expected user ID

        Returns:
            True if state is valid
        """
        try:
            # Basic validation
            if not state or not user_id:
                return False

            # Check state format and length
            if len(state) < 32:
                return False

            # Decode and verify state components
            return self._verify_secure_state(state, user_id)
        except Exception as e:
            logger.warning("State verification failed", error=str(e))
            return False

    def _generate_secure_state(self, user_id: str) -> str:
        """Generate cryptographically secure state parameter with timestamp and nonce"""
        try:
            # Generate random nonce
            nonce = secrets.token_hex(16)

            # Current timestamp
            timestamp = int(datetime.utcnow().timestamp())

            # State payload
            state_payload = {
                "user_id": user_id,
                "timestamp": timestamp,
                "nonce": nonce
            }

            # Encode payload
            payload_json = json.dumps(state_payload, separators=(',', ':'))
            payload_bytes = payload_json.encode('utf-8')
            payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode('ascii')

            # Generate HMAC signature
            signature = hmac.new(
                settings.SECRET_KEY.encode('utf-8'),
                payload_b64.encode('ascii'),
                hashlib.sha256
            ).hexdigest()

            # Combine payload and signature
            state = f"{payload_b64}.{signature}"

            logger.debug("Generated secure OAuth state", user_id=user_id[:8] + "...")
            return state

        except Exception as e:
            logger.error("Failed to generate secure state", error=str(e))
            # Fallback to simpler method
            data = f"{user_id}:{int(datetime.utcnow().timestamp())}:{secrets.token_hex(16)}"
            return hashlib.sha256(f"{data}:{settings.SECRET_KEY}".encode()).hexdigest()

    def _verify_secure_state(self, state: str, user_id: str) -> bool:
        """Verify secure state parameter with timestamp validation"""
        try:
            # Split state into payload and signature
            parts = state.split('.')
            if len(parts) != 2:
                return False

            payload_b64, provided_signature = parts

            # Verify signature
            expected_signature = hmac.new(
                settings.SECRET_KEY.encode('utf-8'),
                payload_b64.encode('ascii'),
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(provided_signature, expected_signature):
                logger.warning("State signature verification failed")
                return False

            # Decode payload
            try:
                payload_bytes = base64.urlsafe_b64decode(payload_b64.encode('ascii'))
                state_payload = json.loads(payload_bytes.decode('utf-8'))
            except (ValueError, json.JSONDecodeError):
                logger.warning("Invalid state payload format")
                return False

            # Verify user ID
            if state_payload.get('user_id') != user_id:
                logger.warning("State user ID mismatch")
                return False

            # Verify timestamp (state should not be older than 1 hour)
            timestamp = state_payload.get('timestamp')
            if not timestamp:
                return False

            now = int(datetime.utcnow().timestamp())
            if now - timestamp > 3600:  # 1 hour
                logger.warning("State parameter expired", age_seconds=now - timestamp)
                return False

            # Verify nonce exists
            if not state_payload.get('nonce'):
                return False

            logger.debug("State verification successful", user_id=user_id[:8] + "...")
            return True

        except Exception as e:
            logger.warning("State verification error", error=str(e))
            return False

    def _validate_redirect_uri(self, redirect_uri: str) -> bool:
        """Validate redirect URI for security"""
        try:
            parsed = urlparse(redirect_uri)

            # Must be HTTPS in production
            if not settings.MOCK_MODE and parsed.scheme != 'https':
                return False

            # Must match configured frontend URL domain
            frontend_parsed = urlparse(settings.FRONTEND_URL)
            if parsed.netloc != frontend_parsed.netloc:
                return False

            # Path should be auth callback
            if not parsed.path.endswith('/auth/tiktok/callback'):
                return False

            return True

        except Exception:
            return False

    def _validate_token_response(self, token_data: Dict[str, Any]) -> bool:
        """Validate token response from TikTok"""
        required_fields = ['access_token', 'refresh_token', 'token_type']

        for field in required_fields:
            if not token_data.get(field):
                logger.warning("Missing required field in token response", field=field)
                return False

        # Validate token type
        if token_data.get('token_type', '').lower() != 'bearer':
            logger.warning("Invalid token type", token_type=token_data.get('token_type'))
            return False

        # Validate token lengths
        if len(token_data['access_token']) < 20 or len(token_data['refresh_token']) < 20:
            logger.warning("Suspicious token lengths")
            return False

        return True

    async def _request_tokens_with_retry(self, client: httpx.AsyncClient, code: str) -> Dict[str, Any]:
        """Request tokens from TikTok with retry logic and enhanced error handling"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await client.post(
                    self.TOKEN_URL,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "User-Agent": "TikTokAPI/1.0"
                    },
                    data={
                        "client_key": self.client_key,
                        "client_secret": self.client_secret,
                        "code": code,
                        "grant_type": "authorization_code",
                        "redirect_uri": self.redirect_uri
                    }
                )

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    if attempt < max_retries - 1:
                        logger.warning("Rate limited, retrying",
                                     attempt=attempt + 1, retry_after=retry_after)
                        await asyncio.sleep(min(retry_after, 300))  # Max 5 minutes
                        continue
                    else:
                        raise RuntimeError(f"Rate limited after {max_retries} attempts")

                response.raise_for_status()
                return response.json()

            except httpx.RequestError as e:
                if attempt < max_retries - 1:
                    logger.warning("Network error, retrying",
                                 attempt=attempt + 1, error=str(e))
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise

        raise RuntimeError(f"Failed to request tokens after {max_retries} attempts")

    async def _get_user_info_with_retry(self, client: httpx.AsyncClient, access_token: str) -> Dict[str, Any]:
        """Get user information from TikTok API with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await client.post(
                    self.USER_INFO_URL,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                        "User-Agent": "TikTokAPI/1.0"
                    },
                    json={"fields": ["open_id", "union_id", "avatar_url", "display_name", "username"]}
                )

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    if attempt < max_retries - 1:
                        logger.warning("Rate limited getting user info, retrying",
                                     attempt=attempt + 1, retry_after=retry_after)
                        await asyncio.sleep(min(retry_after, 300))
                        continue
                    else:
                        raise RuntimeError(f"Rate limited after {max_retries} attempts")

                response.raise_for_status()
                data = response.json()

                # Validate user info response
                user_info = data.get("data", {}).get("user", {})
                if not user_info.get("open_id"):
                    raise ValueError("Invalid user info response: missing open_id")

                return user_info

            except httpx.RequestError as e:
                if attempt < max_retries - 1:
                    logger.warning("Network error getting user info, retrying",
                                 attempt=attempt + 1, error=str(e))
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    raise

        raise RuntimeError(f"Failed to get user info after {max_retries} attempts")

    def _mock_token_exchange(self, code: str, state: str) -> Dict[str, Any]:
        """Mock token exchange for development with validation"""
        logger.info("Using mock TikTok token exchange", code=code[:10] + "...")

        # Validate inputs even in mock mode
        if not code or len(code) < 10:
            raise ValueError("Invalid authorization code")

        if not state or len(state) < 16:
            raise ValueError("Invalid state parameter")

        # Generate mock encrypted tokens
        mock_access_token = f"mock_access_token_{secrets.token_hex(32)}"
        mock_refresh_token = f"mock_refresh_token_{secrets.token_hex(32)}"

        encrypted_access_token = encryption_service.encrypt_token(mock_access_token)
        encrypted_refresh_token = encryption_service.encrypt_token(mock_refresh_token)

        expires_at = datetime.utcnow() + timedelta(hours=24)

        return {
            "access_token": encrypted_access_token,
            "refresh_token": encrypted_refresh_token,
            "token_expires_at": expires_at,
            "user_info": {
                "open_id": f"mock_user_{secrets.token_hex(16)}",
                "union_id": f"mock_union_{secrets.token_hex(16)}",
                "username": "mock_user",
                "display_name": "Mock TikTok User",
                "avatar_url": "https://via.placeholder.com/100"
            },
            "platform": "tiktok"
        }

    def _mock_token_refresh(self, encrypted_refresh_token: str) -> Dict[str, Any]:
        """Mock token refresh for development with validation"""
        logger.info("Using mock TikTok token refresh")

        # Validate refresh token even in mock mode
        if not encrypted_refresh_token:
            raise ValueError("Refresh token is required")

        try:
            # Verify token can be decrypted
            encryption_service.decrypt_token(encrypted_refresh_token)
        except Exception:
            raise ValueError("Invalid or corrupted refresh token")

        # Generate new mock tokens
        mock_access_token = f"mock_access_token_refreshed_{secrets.token_hex(32)}"
        mock_refresh_token = f"mock_refresh_token_refreshed_{secrets.token_hex(32)}"

        encrypted_access_token = encryption_service.encrypt_token(mock_access_token)
        encrypted_new_refresh_token = encryption_service.encrypt_token(mock_refresh_token)

        expires_at = datetime.utcnow() + timedelta(hours=24)

        return {
            "access_token": encrypted_access_token,
            "refresh_token": encrypted_new_refresh_token,
            "token_expires_at": expires_at
        }


# Singleton instance
tiktok_oauth_service = TikTokOAuthService()