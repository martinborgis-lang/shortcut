"""
Clerk Authentication Middleware for FastAPI
"""
from typing import Optional, Tuple
import jwt
import requests
import structlog

def log_to_file(msg):
    import os
    log_path = os.path.join(os.getcwd(), "debug.log")
    with open(log_path, "a") as f:
        f.write(f"[{os.getcwd()}] {str(msg)}\n")
from fastapi import HTTPException, Request, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from ..config import settings
from ..database import get_db
from ..models.user import User
from ..utils.logging import safe_log_user_data

logger = structlog.get_logger()

# Clerk JWT security scheme
security = HTTPBearer()

class ClerkJWTBearer(HTTPBearer):
    """Custom JWT Bearer for Clerk authentication"""

    def __init__(self, auto_error: bool = True):
        super(ClerkJWTBearer, self).__init__(auto_error=auto_error)
        self._jwks_cache: Optional[dict] = None
        self._jwks_cache_time: Optional[datetime] = None

    async def get_jwks(self) -> dict:
        """Get JWKS from Clerk with caching"""
        now = datetime.now(timezone.utc)

        # Cache JWKS for 1 hour
        if (self._jwks_cache and self._jwks_cache_time and
            (now - self._jwks_cache_time).total_seconds() < 3600):
            return self._jwks_cache

        try:
            response = requests.get(
                "https://api.clerk.com/v1/jwks",
                timeout=10
            )
            response.raise_for_status()
            self._jwks_cache = response.json()
            self._jwks_cache_time = now
            return self._jwks_cache
        except Exception as e:
            logger.error("Failed to fetch Clerk JWKS", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to verify token"
            )

    async def verify_jwt(self, token: str) -> dict:
        """Verify Clerk JWT token"""
        if not settings.CLERK_SECRET_KEY:
            logger.error("CLERK_SECRET_KEY not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication not configured"
            )

        try:
            # JWT verification based on environment configuration
            # In production, set CLERK_JWT_VERIFY_SIGNATURE=True with proper JWKS
            payload = jwt.decode(
                token,
                settings.CLERK_SECRET_KEY,
                algorithms=["RS256"],
                options={"verify_signature": settings.CLERK_JWT_VERIFY_SIGNATURE}
            )

            # Check if token is expired
            if "exp" in payload:
                exp_timestamp = payload["exp"]
                if datetime.now(timezone.utc).timestamp() > exp_timestamp:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token has expired"
                    )

            return payload

        except jwt.InvalidTokenError as e:
            try:
                with open("C:/Users/marti/shortcut/error_log.txt", "a") as f:
                    f.write(f"JWT ERROR: {e}\n")
            except:
                pass
            log_to_file(f"=== JWT INVALID TOKEN ERROR: {e} ===")
            logger.error("Invalid JWT token", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )

    async def __call__(self, request: Request) -> Tuple[dict, User]:
        """
        Authenticate request and return JWT payload and User instance
        """
        credentials: HTTPAuthorizationCredentials = await super(ClerkJWTBearer, self).__call__(request)

        if credentials:
            # Verify JWT token
            payload = await self.verify_jwt(credentials.credentials)

            # Extract user ID from token
            clerk_id = payload.get("sub")
            if not clerk_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )

            # Get database session using proper context management
            try:
                db_generator = get_db()
                db: Session = next(db_generator)

                try:
                    # Find user in database or create new one
                    user = db.query(User).filter(User.clerk_id == clerk_id).first()
                    if not user:
                        # Auto-create user on first login
                        log_data = safe_log_user_data("unknown", clerk_id=clerk_id)
                        logger.info("Creating new user on first login", **log_data)

                        # Extract user info from JWT payload
                        email = payload.get("email", "")
                        name = payload.get("name", "")
                        first_name = payload.get("first_name", "")
                        last_name = payload.get("last_name", "")
                        profile_image = payload.get("image_url", "")

                        # Create new user with default FREE plan
                        from ..models.user import PlanType
                        user = User(
                            clerk_id=clerk_id,
                            email=email,
                            first_name=first_name or "Utilisateur",
                            last_name=last_name,
                            profile_image_url=profile_image,
                            plan=PlanType.FREE,
                            monthly_minutes_used=0,
                            is_premium=False,
                            clips_generated=0,
                            clips_limit=10,  # FREE plan limit
                            monthly_clips_generated=0,
                            created_at=datetime.now(timezone.utc),
                            last_login=datetime.now(timezone.utc)
                        )

                        try:
                            db.add(user)
                            db.commit()
                            db.refresh(user)

                            log_data = safe_log_user_data(str(user.id), clerk_id=clerk_id, email=user.email)
                            logger.info("New user created successfully", **log_data)

                        except Exception as e:
                            logger.error("Failed to create new user", error=str(e), clerk_id=clerk_id)
                            db.rollback()
                            raise HTTPException(
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Failed to create user account"
                            )

                    # Update last login
                    user.last_login = datetime.now(timezone.utc)
                    db.commit()

                    # Log authentication with masked data in production
                    log_data = safe_log_user_data(str(user.id), clerk_id=clerk_id, email=user.email)
                    logger.info("User authenticated", **log_data)
                    return payload, user

                except HTTPException:
                    raise
                except Exception as e:
                    logger.error("Database error during authentication", error=str(e))
                    db.rollback()
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Authentication error"
                    )
                finally:
                    try:
                        next(db_generator)  # Close the generator properly
                    except StopIteration:
                        pass  # Expected when generator is closed

            except Exception as e:
                log_to_file(f"=== AUTH ERROR: {e} ===")
                logger.error("Database session error during authentication", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authentication error"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header"
            )


# Global instance
clerk_auth = ClerkJWTBearer()


async def get_current_user(auth_data: Tuple[dict, User] = Depends(clerk_auth)) -> User:
    """
    Dependency to get the current authenticated user
    Usage: user = Depends(get_current_user)
    """
    _, user = auth_data
    return user


async def get_current_user_payload(auth_data: Tuple[dict, User] = Depends(clerk_auth)) -> Tuple[dict, User]:
    """
    Dependency to get both JWT payload and user
    Usage: payload, user = Depends(get_current_user_payload)
    """
    return auth_data


async def get_current_user_from_token(token: str, db: Session) -> User:
    """
    Get current user from a JWT token string (for WebSocket authentication)
    """
    try:
        # Create a temporary ClerkJWTBearer instance for token verification
        auth_handler = ClerkJWTBearer()
        payload = await auth_handler.verify_jwt(token)

        # Extract user ID from token
        clerk_id = payload.get("sub")
        if not clerk_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        # Find user in database
        user = db.query(User).filter(User.clerk_id == clerk_id).first()
        if not user:
            log_data = safe_log_user_data("unknown", clerk_id=clerk_id)
            logger.warning("User not found in database", **log_data)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        # Log authentication with masked data in production
        log_data = safe_log_user_data(str(user.id), clerk_id=clerk_id, email=user.email)
        logger.info("User authenticated via token", **log_data)
        return user

    except HTTPException:
        raise
    except Exception as e:
        try:
            with open("C:/Users/marti/shortcut/error_log.txt", "a") as f:
                f.write(f"TOKEN AUTH FAILED: {e}\n")
        except:
            pass
        logger.error("Token authentication failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )


async def get_current_user_from_request(request: Request, db: Session) -> Optional[User]:
    """
    Get current user from a FastAPI request (for middleware usage)

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        User object if authenticated, None otherwise
    """
    try:
        # Extract Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        # Extract token
        token = auth_header.split(" ")[1]

        # Use existing token authentication
        return await get_current_user_from_token(token, db)

    except HTTPException:
        # Authentication failed, return None instead of raising
        return None
    except Exception as e:
        logger.error("Error getting user from request", error=str(e))
        return None