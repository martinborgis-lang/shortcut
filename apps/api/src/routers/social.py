"""
Social media account management and OAuth endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
from typing import List, Optional, Dict, Any
import structlog
import re

from ..database import get_db
from ..middleware.auth import get_current_user
from ..models.user import User
from ..models.social_account import SocialAccount
from ..schemas.social import (
    TikTokAuthResponse,
    OAuthCallbackRequest,
    SocialAccountResponse,
    SocialAccountUpdate,
    ConnectedAccountsResponse,
    DisconnectAccountResponse,
    BulkAccountStatusResponse,
    AccountMetricsResponse,
    SocialAccountStatus
)
from ..services.tiktok_oauth import tiktok_oauth_service
from ..services.encryption import encryption_service

logger = structlog.get_logger()
router = APIRouter()


@router.get("/tiktok/auth", response_model=TikTokAuthResponse)
async def tiktok_auth(current_user: User = Depends(get_current_user)):
    """
    Generate TikTok OAuth authorization URL

    F6-01: Endpoint GET `/api/social/tiktok/auth`
    Génère l'URL d'autorisation TikTok OAuth 2.0, redirige l'utilisateur
    """
    try:
        auth_url, state = tiktok_oauth_service.generate_auth_url(str(current_user.id))

        logger.info("Generated TikTok OAuth URL",
                   user_id=current_user.id, auth_url=auth_url[:100])

        return TikTokAuthResponse(auth_url=auth_url)

    except Exception as e:
        logger.error("Failed to generate TikTok OAuth URL",
                    user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate OAuth URL: {str(e)}"
        )


@router.get("/tiktok/callback")
async def tiktok_callback(
    code: str = Query(..., description="Authorization code from TikTok"),
    state: str = Query(..., description="State parameter for security"),
    user_id: Optional[str] = Query(None, description="User ID for state verification"),
    db: Session = Depends(get_db)
):
    """
    Handle TikTok OAuth callback with enhanced security validation

    F6-02: Endpoint GET `/api/social/tiktok/callback`
    Reçoit le code d'autorisation, échange contre access_token + refresh_token
    """
    try:
        # Enhanced input validation
        if not _validate_oauth_callback_inputs(code, state):
            logger.warning("Invalid OAuth callback parameters",
                          code_length=len(code) if code else 0,
                          state_length=len(state) if state else 0)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OAuth callback parameters"
            )

        # Validate state parameter format and extract user info if present
        extracted_user_id = _extract_user_from_state(state)
        if not extracted_user_id and user_id:
            extracted_user_id = user_id

        # Exchange code for tokens with user validation
        token_data = await tiktok_oauth_service.exchange_code_for_tokens(
            code, state, extracted_user_id
        )
        user_info = token_data["user_info"]

        # Validate user info from TikTok
        if not _validate_tiktok_user_info(user_info):
            logger.error("Invalid user info from TikTok", user_info=user_info)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user information from TikTok"
            )

        # Check if user already has this TikTok account connected
        existing_account = db.query(SocialAccount).filter(
            and_(
                SocialAccount.platform == "tiktok",
                SocialAccount.platform_user_id == user_info["open_id"]
            )
        ).first()

        if existing_account:
            # Validate account ownership if user_id provided
            if extracted_user_id and existing_account.user_id != extracted_user_id:
                logger.warning("TikTok account ownership mismatch",
                              existing_user=existing_account.user_id,
                              callback_user=extracted_user_id)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="TikTok account belongs to different user"
                )

            # Update existing account with new tokens
            existing_account.access_token = token_data["access_token"]
            existing_account.refresh_token = token_data["refresh_token"]
            existing_account.token_expires_at = token_data["token_expires_at"]
            existing_account.username = _sanitize_username(user_info.get("username", existing_account.username))
            existing_account.display_name = _sanitize_display_name(user_info.get("display_name"))
            existing_account.is_active = True
            existing_account.last_error = None
            existing_account.error_count = 0
            existing_account.connected_at = datetime.utcnow()
            existing_account.account_metadata = _sanitize_user_metadata(user_info)

            db.commit()
            db.refresh(existing_account)

            logger.info("Updated existing TikTok account",
                       account_id=str(existing_account.id)[:8] + "...",
                       username=existing_account.username)

            return {
                "message": "TikTok account reconnected successfully",
                "account_id": str(existing_account.id),
                "user_id": extracted_user_id
            }

        else:
            # For callback without authenticated user, return secure instructions
            return {
                "message": "TikTok authorization successful",
                "instructions": "Please complete the connection process in your application",
                "user_info": {
                    "username": _sanitize_username(user_info.get("username")),
                    "display_name": _sanitize_display_name(user_info.get("display_name")),
                    "platform_user_id": user_info.get("open_id")[:8] + "..." if user_info.get("open_id") else None
                },
                "user_id": extracted_user_id
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("TikTok OAuth callback failed",
                    code=code[:10] + "..." if code else "None",
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth callback failed. Please try again."
        )


@router.post("/tiktok/connect")
async def connect_tiktok_account(
    request: OAuthCallbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Connect a TikTok account for the authenticated user with enhanced security
    This endpoint is called from the frontend after OAuth callback
    """
    try:
        # Enhanced input validation
        if not _validate_oauth_callback_inputs(request.code, request.state):
            logger.warning("Invalid OAuth connect request",
                          user_id=str(current_user.id)[:8] + "...")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OAuth parameters"
            )

        # Verify state parameter with enhanced security
        if not tiktok_oauth_service.verify_state(request.state, str(current_user.id)):
            logger.warning("State parameter verification failed",
                          user_id=str(current_user.id)[:8] + "...",
                          state=request.state[:16] + "...")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Security validation failed. Please try again."
            )

        # Exchange code for tokens with user verification
        token_data = await tiktok_oauth_service.exchange_code_for_tokens(
            request.code, request.state, str(current_user.id)
        )
        user_info = token_data["user_info"]

        # Validate TikTok user info
        if not _validate_tiktok_user_info(user_info):
            logger.error("Invalid TikTok user info received",
                        user_id=str(current_user.id)[:8] + "...")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user information from TikTok"
            )

        # Check for existing TikTok account conflicts
        platform_user_id = user_info["open_id"]
        conflicting_account = db.query(SocialAccount).filter(
            and_(
                SocialAccount.platform == "tiktok",
                SocialAccount.platform_user_id == platform_user_id,
                SocialAccount.user_id != current_user.id
            )
        ).first()

        if conflicting_account:
            logger.warning("TikTok account already connected to different user",
                          platform_user_id=platform_user_id[:8] + "...",
                          current_user=str(current_user.id)[:8] + "...")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This TikTok account is already connected to another user"
            )

        # Check if user already has this TikTok account
        existing_account = db.query(SocialAccount).filter(
            and_(
                SocialAccount.user_id == current_user.id,
                SocialAccount.platform == "tiktok",
                SocialAccount.platform_user_id == platform_user_id
            )
        ).first()

        if existing_account:
            # Update existing account with enhanced data validation
            existing_account.access_token = token_data["access_token"]
            existing_account.refresh_token = token_data["refresh_token"]
            existing_account.token_expires_at = token_data["token_expires_at"]
            existing_account.username = _sanitize_username(user_info.get("username", existing_account.username))
            existing_account.display_name = _sanitize_display_name(user_info.get("display_name"))
            existing_account.is_active = True
            existing_account.last_error = None
            existing_account.error_count = 0
            existing_account.connected_at = datetime.utcnow()
            existing_account.account_metadata = _sanitize_user_metadata(user_info)
            existing_account.last_sync = datetime.utcnow()

        else:
            # Validate account limits
            tiktok_accounts_count = db.query(SocialAccount).filter(
                and_(
                    SocialAccount.user_id == current_user.id,
                    SocialAccount.platform == "tiktok",
                    SocialAccount.is_active == True
                )
            ).count()

            # Limit TikTok accounts per user (configurable)
            MAX_TIKTOK_ACCOUNTS = 3
            if tiktok_accounts_count >= MAX_TIKTOK_ACCOUNTS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Maximum {MAX_TIKTOK_ACCOUNTS} TikTok accounts allowed per user"
                )

            # Create new social account with enhanced validation
            social_account = SocialAccount(
                user_id=current_user.id,
                platform="tiktok",
                platform_user_id=platform_user_id,
                username=_sanitize_username(user_info.get("username", "")),
                display_name=_sanitize_display_name(user_info.get("display_name")),
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                token_expires_at=token_data["token_expires_at"],
                is_active=True,
                is_verified=bool(user_info.get("is_verified", False)),
                connected_at=datetime.utcnow(),
                last_sync=datetime.utcnow(),
                account_metadata=_sanitize_user_metadata(user_info),
                publishing_permissions={"video_upload": True, "video_publish": True}
            )

            db.add(social_account)
            existing_account = social_account

        db.commit()
        db.refresh(existing_account)

        logger.info("TikTok account connected successfully",
                   user_id=str(current_user.id)[:8] + "...",
                   account_id=str(existing_account.id)[:8] + "...")

        return SocialAccountResponse.from_orm(existing_account)

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error("Failed to connect TikTok account",
                    user_id=str(current_user.id)[:8] + "...",
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to connect TikTok account. Please try again."
        )


@router.get("/accounts", response_model=ConnectedAccountsResponse)
async def get_connected_accounts(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    active_only: bool = Query(True, description="Show only active accounts"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of connected social media accounts

    F6-04: Endpoint GET `/api/social/accounts`
    Liste les comptes sociaux connectés de l'utilisateur
    """
    try:
        # Build query
        query = db.query(SocialAccount).filter(SocialAccount.user_id == current_user.id)

        if platform:
            query = query.filter(SocialAccount.platform == platform)

        if active_only:
            query = query.filter(SocialAccount.is_active == True)

        # Order by creation date
        accounts = query.order_by(SocialAccount.created_at.desc()).all()

        logger.info("Retrieved connected accounts",
                   user_id=current_user.id, count=len(accounts))

        return ConnectedAccountsResponse(
            accounts=[SocialAccountResponse.from_orm(account) for account in accounts],
            total=len(accounts)
        )

    except Exception as e:
        logger.error("Failed to retrieve connected accounts",
                    user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve accounts: {str(e)}"
        )


@router.get("/accounts/{account_id}", response_model=SocialAccountResponse)
async def get_social_account(
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific social media account"""
    try:
        account = db.query(SocialAccount).filter(
            and_(
                SocialAccount.id == account_id,
                SocialAccount.user_id == current_user.id
            )
        ).first()

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Social media account not found"
            )

        logger.info("Retrieved social account details",
                   user_id=current_user.id, account_id=account_id)

        return SocialAccountResponse.from_orm(account)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve social account",
                    user_id=current_user.id, account_id=account_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve account: {str(e)}"
        )


@router.patch("/accounts/{account_id}", response_model=SocialAccountResponse)
async def update_social_account(
    account_id: str,
    update_data: SocialAccountUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update social media account settings"""
    try:
        account = db.query(SocialAccount).filter(
            and_(
                SocialAccount.id == account_id,
                SocialAccount.user_id == current_user.id
            )
        ).first()

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Social media account not found"
            )

        # Update fields
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(account, field, value)

        db.commit()
        db.refresh(account)

        logger.info("Updated social account",
                   user_id=current_user.id, account_id=account_id)

        return SocialAccountResponse.from_orm(account)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Failed to update social account",
                    user_id=current_user.id, account_id=account_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update account: {str(e)}"
        )


@router.delete("/accounts/{account_id}", response_model=DisconnectAccountResponse)
async def disconnect_social_account(
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disconnect a social media account

    F6-05: Endpoint DELETE `/api/social/accounts/{id}`
    Déconnecte un compte social (supprime les tokens)
    """
    try:
        account = db.query(SocialAccount).filter(
            and_(
                SocialAccount.id == account_id,
                SocialAccount.user_id == current_user.id
            )
        ).first()

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Social media account not found"
            )

        account_response = SocialAccountResponse.from_orm(account)

        # Remove the account (this will cascade to scheduled_posts due to relationship)
        db.delete(account)
        db.commit()

        logger.info("Disconnected social account",
                   user_id=current_user.id, account_id=account_id,
                   platform=account.platform)

        return DisconnectAccountResponse(
            message=f"{account.platform.title()} account disconnected successfully",
            disconnected_account=account_response
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Failed to disconnect social account",
                    user_id=current_user.id, account_id=account_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect account: {str(e)}"
        )


@router.get("/accounts/status/bulk", response_model=BulkAccountStatusResponse)
async def get_accounts_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get status of all connected social media accounts"""
    try:
        accounts = db.query(SocialAccount).filter(
            SocialAccount.user_id == current_user.id
        ).all()

        account_statuses = []
        summary = {"total": len(accounts), "active": 0, "needs_reconnection": 0, "has_errors": 0}

        for account in accounts:
            # Check if token is expired or expiring soon
            needs_reconnection = False
            if account.token_expires_at:
                time_until_expiry = account.token_expires_at - datetime.utcnow()
                needs_reconnection = time_until_expiry.total_seconds() < 3600  # Expiring in 1 hour

            has_publishing_permission = bool(
                account.publishing_permissions and
                account.publishing_permissions.get("video_upload") and
                account.publishing_permissions.get("video_publish")
            )

            status = SocialAccountStatus(
                platform=account.platform,
                is_connected=True,
                is_active=account.is_active,
                has_publishing_permission=has_publishing_permission,
                last_error=account.last_error,
                token_expires_at=account.token_expires_at,
                needs_reconnection=needs_reconnection
            )

            account_statuses.append(status)

            # Update summary
            if account.is_active:
                summary["active"] += 1
            if needs_reconnection:
                summary["needs_reconnection"] += 1
            if account.last_error:
                summary["has_errors"] += 1

        logger.info("Retrieved accounts status",
                   user_id=current_user.id, summary=summary)

        return BulkAccountStatusResponse(
            accounts=account_statuses,
            summary=summary
        )

    except Exception as e:
        logger.error("Failed to retrieve accounts status",
                    user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve accounts status: {str(e)}"
        )


# Security utility functions

def _validate_oauth_callback_inputs(code: str, state: str) -> bool:
    """Validate OAuth callback input parameters"""
    if not code or not isinstance(code, str):
        return False

    if len(code) < 10 or len(code) > 500:
        return False

    if not state or not isinstance(state, str):
        return False

    if len(state) < 16 or len(state) > 1000:
        return False

    # Check for suspicious characters
    if not re.match(r'^[a-zA-Z0-9._-]+$', code):
        return False

    return True


def _extract_user_from_state(state: str) -> Optional[str]:
    """Extract user ID from secure state parameter"""
    try:
        # This would implement the reverse of the secure state generation
        # For now, return None to maintain compatibility
        return None
    except Exception:
        return None


def _validate_tiktok_user_info(user_info: Dict[str, Any]) -> bool:
    """Validate TikTok user information from API"""
    if not isinstance(user_info, dict):
        return False

    # Required fields
    required_fields = ["open_id"]
    for field in required_fields:
        if not user_info.get(field):
            return False

    # Validate open_id format
    open_id = user_info.get("open_id")
    if not isinstance(open_id, str) or len(open_id) < 5:
        return False

    # Validate optional fields if present
    username = user_info.get("username")
    if username and (not isinstance(username, str) or len(username) > 100):
        return False

    display_name = user_info.get("display_name")
    if display_name and (not isinstance(display_name, str) or len(display_name) > 200):
        return False

    return True


def _sanitize_username(username: str) -> str:
    """Sanitize username for safe storage"""
    if not username or not isinstance(username, str):
        return ""

    # Remove potentially harmful characters
    sanitized = re.sub(r'[^\w.-]', '', username)

    # Limit length
    return sanitized[:100]


def _sanitize_display_name(display_name: str) -> str:
    """Sanitize display name for safe storage"""
    if not display_name or not isinstance(display_name, str):
        return ""

    # Remove control characters but allow unicode
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', display_name)

    # Limit length
    return sanitized[:200]


def _sanitize_user_metadata(user_info: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize user metadata for safe storage"""
    if not isinstance(user_info, dict):
        return {}

    # Allowlist of safe fields
    safe_fields = {
        "open_id", "union_id", "username", "display_name",
        "avatar_url", "is_verified", "follower_count", "following_count"
    }

    sanitized = {}
    for key, value in user_info.items():
        if key in safe_fields:
            if isinstance(value, str):
                # Sanitize string values
                sanitized_value = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)
                sanitized[key] = sanitized_value[:500]  # Limit length
            elif isinstance(value, (int, bool)):
                sanitized[key] = value
            elif value is None:
                sanitized[key] = None

    return sanitized