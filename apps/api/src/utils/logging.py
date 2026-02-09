"""
Logging utilities for secure logging in production
"""
from typing import Optional
import structlog
from ..config import settings

logger = structlog.get_logger()


def mask_sensitive_data(data: str, mask_length: int = 3) -> str:
    """
    Mask sensitive data for production logging

    Args:
        data: The sensitive data to mask
        mask_length: Number of characters to show before masking

    Returns:
        Masked string if not in DEBUG mode, original string otherwise
    """
    if not data:
        return "***"

    if settings.DEBUG:
        return data

    if len(data) <= mask_length:
        return "***"

    return f"{data[:mask_length]}***"


def mask_email(email: str) -> str:
    """
    Mask email address for production logging

    Args:
        email: Email address to mask

    Returns:
        Masked email if not in DEBUG mode, original email otherwise
    """
    if not email or "@" not in email:
        return "***@***"

    if settings.DEBUG:
        return email

    username, domain = email.split("@", 1)

    if len(username) <= 3:
        masked_username = "***"
    else:
        masked_username = f"{username[:3]}***"

    return f"{masked_username}@{domain}"


def safe_log_user_data(user_id: str, clerk_id: Optional[str] = None, email: Optional[str] = None) -> dict:
    """
    Create a safe dictionary for logging user data

    Args:
        user_id: User ID (always safe to log)
        clerk_id: Clerk ID to mask
        email: Email to mask

    Returns:
        Dictionary with masked data for logging
    """
    log_data = {"user_id": user_id}

    if clerk_id:
        log_data["clerk_id"] = mask_sensitive_data(clerk_id, 8)

    if email:
        log_data["email"] = mask_email(email)

    return log_data