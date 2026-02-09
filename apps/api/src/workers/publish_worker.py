"""
Social media publishing workers with Celery Beat integration

F6-11: Worker publish_worker
Celery Beat qui vérifie les posts programmés et les publie à l'heure prévue
"""

import asyncio
import httpx
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
import structlog
import time

from .celery_app import celery_app
from ..database import SessionLocal
from ..models.scheduled_post import ScheduledPost
from ..models.social_account import SocialAccount
from ..models.clip import Clip
from ..services.tiktok_publisher import tiktok_publisher_service
from ..services.tiktok_oauth import tiktok_oauth_service
from ..services.encryption import encryption_service

logger = structlog.get_logger()


@celery_app.task(bind=True, max_retries=3)
def check_scheduled_posts(self):
    """
    Check for scheduled posts that are due for publishing

    F6-11: Celery Beat task that runs every minute to check for posts to publish
    """
    logger.info("Checking for scheduled posts to publish")

    db: Session = SessionLocal()
    try:
        # Get current time with small buffer to avoid timing issues
        now = datetime.utcnow()
        check_time = now + timedelta(minutes=1)

        # Find posts that are due for publishing
        due_posts = db.query(ScheduledPost).options(
            joinedload(ScheduledPost.clip),
            joinedload(ScheduledPost.social_account)
        ).filter(
            and_(
                ScheduledPost.status == "scheduled",
                ScheduledPost.scheduled_time <= check_time
            )
        ).all()

        logger.info(f"Found {len(due_posts)} posts due for publishing")

        for post in due_posts:
            # Update status to publishing immediately to avoid double processing
            post.status = "publishing"
            db.commit()

            # Trigger async publishing task
            publish_scheduled_post.delay(str(post.id))

        # Check for posts that need retry
        retry_failed_posts.delay()

        return {"posts_queued": len(due_posts)}

    except Exception as e:
        logger.error("Failed to check scheduled posts", error=str(e))
        raise self.retry(countdown=60, exc=e)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def publish_scheduled_post(self, scheduled_post_id: str):
    """
    Publish a single scheduled post to its target platform

    Args:
        scheduled_post_id: ID of the scheduled post to publish
    """
    logger.info("Publishing scheduled post", post_id=scheduled_post_id)

    db: Session = SessionLocal()
    try:
        # Get the scheduled post with related data
        post = db.query(ScheduledPost).options(
            joinedload(ScheduledPost.clip),
            joinedload(ScheduledPost.social_account)
        ).filter(ScheduledPost.id == scheduled_post_id).first()

        if not post:
            logger.error("Scheduled post not found", post_id=scheduled_post_id)
            return {"error": "Post not found"}

        if post.status != "publishing":
            logger.warning("Post not in publishing status",
                         post_id=scheduled_post_id, status=post.status)
            return {"error": "Post not in publishing status"}

        # Check if social account is still active
        if not post.social_account.is_active:
            post.status = "failed"
            post.error_message = "Social account is inactive"
            post.failed_at = datetime.utcnow()
            db.commit()
            logger.error("Social account inactive", post_id=scheduled_post_id)
            return {"error": "Social account inactive"}

        # Check if we need to refresh token
        if _needs_token_refresh(post.social_account):
            _refresh_account_token_sync(post.social_account, db)

        # Publish based on platform
        platform = post.social_account.platform
        if platform == "tiktok":
            result = _publish_to_tiktok_sync(post, db)
        else:
            raise ValueError(f"Unsupported platform: {platform}")

        logger.info("Successfully published scheduled post",
                   post_id=scheduled_post_id, platform=platform)

        return result

    except Exception as e:
        logger.error("Failed to publish scheduled post",
                    post_id=scheduled_post_id, error=str(e))

        # Update post with error
        if 'post' in locals():
            post.status = "failed"
            post.error_message = str(e)
            post.failed_at = datetime.utcnow()
            post.retry_count += 1

            # Schedule retry if retries remaining
            if post.retry_count < post.max_retries:
                retry_delay = min(300 * (2 ** post.retry_count), 3600)  # Exponential backoff, max 1 hour
                post.next_retry_at = datetime.utcnow() + timedelta(seconds=retry_delay)
                post.status = "scheduled"
                logger.info("Scheduled post retry",
                           post_id=scheduled_post_id,
                           retry_count=post.retry_count,
                           retry_at=post.next_retry_at)

            db.commit()

        # Re-raise for Celery retry logic
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=300, exc=e)

        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task
def retry_failed_posts():
    """
    Check for failed posts that are due for retry
    """
    logger.info("Checking for posts to retry")

    db: Session = SessionLocal()
    try:
        now = datetime.utcnow()

        # Find posts that failed but can be retried
        retry_posts = db.query(ScheduledPost).filter(
            and_(
                ScheduledPost.status == "scheduled",
                ScheduledPost.retry_count > 0,
                ScheduledPost.retry_count < ScheduledPost.max_retries,
                ScheduledPost.next_retry_at <= now
            )
        ).all()

        logger.info(f"Found {len(retry_posts)} posts to retry")

        for post in retry_posts:
            post.status = "publishing"
            db.commit()
            publish_scheduled_post.delay(str(post.id))

        return {"posts_retried": len(retry_posts)}

    except Exception as e:
        logger.error("Failed to check retry posts", error=str(e))
        raise
    finally:
        db.close()


@celery_app.task
def refresh_social_tokens():
    """
    F6-06: Token refresh automatique
    Cron job qui refresh les tokens avant expiration (24h TikTok)
    """
    logger.info("Refreshing social media tokens")

    db: Session = SessionLocal()
    try:
        # Find accounts with tokens expiring in the next 2 hours
        expiry_threshold = datetime.utcnow() + timedelta(hours=2)

        accounts = db.query(SocialAccount).filter(
            and_(
                SocialAccount.is_active == True,
                SocialAccount.token_expires_at <= expiry_threshold,
                SocialAccount.refresh_token.isnot(None)
            )
        ).all()

        logger.info(f"Found {len(accounts)} accounts needing token refresh")

        refreshed_count = 0
        failed_count = 0

        for account in accounts:
            try:
                if account.platform == "tiktok":
                    _refresh_tiktok_token_sync(account, db)
                    refreshed_count += 1
                    logger.info("Refreshed token for account",
                               account_id=account.id, platform=account.platform)

            except Exception as e:
                failed_count += 1
                account.error_count += 1
                account.last_error = str(e)

                # Disable account if too many consecutive failures
                if account.error_count >= 5:
                    account.is_active = False
                    account.disabled_until = datetime.utcnow() + timedelta(hours=24)
                    logger.error("Disabled account due to repeated token refresh failures",
                               account_id=account.id, platform=account.platform)

                db.commit()
                logger.error("Failed to refresh token for account",
                           account_id=account.id, platform=account.platform, error=str(e))

        result = {
            "accounts_checked": len(accounts),
            "refreshed": refreshed_count,
            "failed": failed_count
        }

        logger.info("Token refresh completed", result=result)
        return result

    except Exception as e:
        logger.error("Failed to refresh social tokens", error=str(e))
        raise
    finally:
        db.close()


@celery_app.task
def sync_social_accounts():
    """
    Periodic task to sync social account metadata and check permissions
    """
    logger.info("Syncing social media accounts")

    db: Session = SessionLocal()
    try:
        # Get all active accounts
        accounts = db.query(SocialAccount).filter(
            SocialAccount.is_active == True
        ).all()

        synced_count = 0
        error_count = 0

        for account in accounts:
            try:
                # Basic sync - update last_sync timestamp
                account.last_sync = datetime.utcnow()
                synced_count += 1

                # Platform-specific sync could be added here
                # For now, just update timestamp

            except Exception as e:
                error_count += 1
                account.error_count += 1
                account.last_error = str(e)
                logger.error("Failed to sync account",
                           account_id=account.id, platform=account.platform, error=str(e))

        db.commit()

        result = {
            "accounts_synced": synced_count,
            "errors": error_count
        }

        logger.info("Social accounts sync completed", result=result)
        return result

    except Exception as e:
        logger.error("Failed to sync social accounts", error=str(e))
        raise
    finally:
        db.close()


# Helper functions

def _needs_token_refresh(account: SocialAccount) -> bool:
    """Check if account token needs refresh"""
    if not account.token_expires_at:
        return False

    # Refresh if expiring in the next hour
    expiry_threshold = datetime.utcnow() + timedelta(hours=1)
    return account.token_expires_at <= expiry_threshold


def _refresh_account_token_sync(account: SocialAccount, db: Session):
    """Refresh access token for an account (sync version for Celery)"""
    if account.platform == "tiktok":
        _refresh_tiktok_token_sync(account, db)
    else:
        raise ValueError(f"Token refresh not implemented for platform: {account.platform}")


def _refresh_tiktok_token_sync(account: SocialAccount, db: Session):
    """Refresh TikTok access token (sync version for Celery)"""
    try:
        if not account.refresh_token:
            raise ValueError("No refresh token available")

        # Use sync HTTP call for Celery worker
        refresh_token = encryption_service.decrypt_token(account.refresh_token)

        timeout_config = httpx.Timeout(30.0, connect=10.0)
        with httpx.Client(timeout=timeout_config) as client:
            response = client.post(
                "https://open.tiktokapis.com/v2/oauth/token/",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "client_key": tiktok_oauth_service.client_key,
                    "client_secret": tiktok_oauth_service.client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token
                },
                follow_redirects=True
            )

            if response.status_code == 429:
                # Rate limit hit, wait and retry
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning("Rate limit hit, waiting", retry_after=retry_after)
                time.sleep(min(retry_after, 300))  # Max 5 minutes wait
                raise RuntimeError(f"Rate limit hit, retry after {retry_after} seconds")

            response.raise_for_status()
            token_data = response.json()

        # Encrypt new tokens
        encrypted_access_token = encryption_service.encrypt_token(token_data["access_token"])
        encrypted_refresh_token = encryption_service.encrypt_token(token_data["refresh_token"])

        # Update account
        account.access_token = encrypted_access_token
        account.refresh_token = encrypted_refresh_token
        account.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 86400))
        account.error_count = 0
        account.last_error = None

        db.commit()

        logger.info("Successfully refreshed TikTok token (sync)",
                   account_id=account.id)

    except httpx.TimeoutException:
        logger.error("Timeout refreshing TikTok token", account_id=account.id)
        raise RuntimeError("Token refresh timeout")
    except httpx.HTTPStatusError as e:
        logger.error("HTTP error refreshing TikTok token",
                    account_id=account.id, status_code=e.response.status_code)
        raise RuntimeError(f"Token refresh failed: {e.response.status_code}")
    except Exception as e:
        logger.error("Failed to refresh TikTok token (sync)",
                    account_id=account.id, error=str(e))
        raise


def _publish_to_tiktok_sync(post: ScheduledPost, db: Session) -> Dict[str, Any]:
    """Publish a post to TikTok (sync version for Celery)"""
    try:
        # Get video URL from clip
        if not post.clip.s3_url:
            raise ValueError("Clip does not have a video URL")

        # Prepare TikTok-specific settings
        platform_settings = post.platform_settings or {}

        # Use sync version of publisher
        result = _publish_video_sync(
            encrypted_access_token=post.social_account.access_token,
            video_url=post.clip.s3_url,
            caption=post.caption or "",
            hashtags=post.hashtags or [],
            privacy_level=platform_settings.get("privacy_level", "SELF_ONLY"),
            disable_duet=platform_settings.get("disable_duet", False),
            disable_comment=platform_settings.get("disable_comment", False),
            disable_stitch=platform_settings.get("disable_stitch", False),
            brand_content_toggle=platform_settings.get("brand_content_toggle", False),
            brand_organic_toggle=platform_settings.get("brand_organic_toggle", False)
        )

        # Update post with success status
        post.status = "published"
        post.posted_at = datetime.utcnow()
        post.platform_post_id = result.get("publish_id")
        post.platform_response = result
        post.error_message = None

        # Reset social account error count on success
        post.social_account.error_count = 0
        post.social_account.last_error = None

        db.commit()

        return {
            "post_id": str(post.id),
            "platform": "tiktok",
            "platform_post_id": result.get("publish_id"),
            "status": "published"
        }

    except Exception as e:
        # Update post with failure status
        post.status = "failed"
        post.error_message = str(e)
        post.failed_at = datetime.utcnow()
        post.retry_count += 1

        # Update social account error tracking
        post.social_account.error_count += 1
        post.social_account.last_error = str(e)

        db.commit()
        raise


def _publish_video_sync(
    encrypted_access_token: str,
    video_url: str,
    caption: str,
    hashtags: List[str] = None,
    privacy_level: str = "SELF_ONLY",
    disable_duet: bool = False,
    disable_comment: bool = False,
    disable_stitch: bool = False,
    brand_content_toggle: bool = False,
    brand_organic_toggle: bool = False
) -> Dict[str, Any]:
    """Sync version of TikTok video publishing for Celery workers"""
    try:
        # Mock mode check
        from ..config import settings
        if settings.MOCK_MODE or not encrypted_access_token:
            return _mock_publish_video_sync(video_url, caption, hashtags)

        # Decrypt access token
        access_token = encryption_service.decrypt_token(encrypted_access_token)

        # Use sync HTTP client with proper timeout and retry
        timeout_config = httpx.Timeout(60.0, connect=15.0)
        with httpx.Client(timeout=timeout_config) as client:
            # Step 1: Initialize upload
            init_response = client.post(
                "https://open.tiktokapis.com/v2/post/publish/video/init/",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "source_info": {
                        "source": "FILE_UPLOAD",
                        "video_size": 4 * 1024 * 1024 * 1024,  # 4GB max
                        "chunk_size": 10 * 1024 * 1024,  # 10MB chunks
                        "total_chunk_count": 1
                    }
                }
            )

            if init_response.status_code == 429:
                retry_after = int(init_response.headers.get("Retry-After", 60))
                logger.warning("Rate limit hit during init", retry_after=retry_after)
                time.sleep(min(retry_after, 300))  # Max 5 minutes
                raise RuntimeError(f"Rate limit hit, retry after {retry_after} seconds")

            init_response.raise_for_status()
            upload_info = init_response.json().get("data", {})

            # Step 2: Upload video
            upload_url = upload_info.get("upload_url")
            if not upload_url:
                raise RuntimeError("No upload URL provided by TikTok")

            # Download and upload video
            video_response = client.get(video_url, follow_redirects=True)
            video_response.raise_for_status()

            upload_response = client.put(
                upload_url,
                content=video_response.content,
                headers={"Content-Type": "video/mp4"}
            )
            upload_response.raise_for_status()

            # Step 3: Publish
            full_caption = caption
            if hashtags:
                hashtag_string = " ".join([f"#{tag.strip('#')}" for tag in hashtags])
                full_caption = f"{caption} {hashtag_string}".strip()

            post_info = {
                "title": full_caption[:2200],
                "privacy_level": privacy_level,
                "disable_duet": disable_duet,
                "disable_comment": disable_comment,
                "disable_stitch": disable_stitch,
                "video_cover_timestamp_ms": 1000
            }

            if brand_content_toggle:
                post_info["brand_content_toggle"] = True
            if brand_organic_toggle:
                post_info["brand_organic_toggle"] = True

            publish_response = client.post(
                "https://open.tiktokapis.com/v2/post/publish/submit/",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "post_info": post_info,
                    "source_info": {
                        "source": "FILE_UPLOAD",
                        "video_id": upload_info.get("video_id")
                    }
                }
            )

            if publish_response.status_code == 429:
                retry_after = int(publish_response.headers.get("Retry-After", 60))
                logger.warning("Rate limit hit during publish", retry_after=retry_after)
                time.sleep(min(retry_after, 300))
                raise RuntimeError(f"Rate limit hit, retry after {retry_after} seconds")

            publish_response.raise_for_status()
            data = publish_response.json()

            logger.info("Successfully published video to TikTok (sync)",
                       publish_id=data.get("data", {}).get("publish_id"))

            return {
                "publish_id": data.get("data", {}).get("publish_id"),
                "status": "submitted",
                "message": "Video submitted for publishing"
            }

    except httpx.TimeoutException:
        logger.error("Timeout publishing video to TikTok")
        raise RuntimeError("TikTok publishing timeout")
    except httpx.HTTPStatusError as e:
        logger.error("HTTP error publishing to TikTok",
                    status_code=e.response.status_code, response=e.response.text)
        raise RuntimeError(f"TikTok publishing failed: {e.response.status_code}")
    except Exception as e:
        logger.error("Failed to publish video to TikTok (sync)", error=str(e))
        raise RuntimeError(f"TikTok video publishing failed: {e}")


def _mock_publish_video_sync(video_url: str, caption: str, hashtags: List[str] = None) -> Dict[str, Any]:
    """Mock video publishing for development (sync version)"""
    logger.info("Using mock TikTok video publishing (sync)",
               video_url=video_url[:50], caption=caption[:50])

    # Simulate processing delay
    time.sleep(2)

    import secrets
    mock_publish_id = f"mock_publish_{secrets.token_hex(8)}"
    mock_video_id = f"mock_video_{secrets.token_hex(12)}"

    return {
        "publish_id": mock_publish_id,
        "video_id": mock_video_id,
        "status": "published",
        "message": "Mock video published successfully",
        "share_url": f"https://www.tiktok.com/@mockuser/video/{mock_video_id}",
        "created_time": int(datetime.utcnow().timestamp())
    }


# Celery Beat schedule configuration
celery_app.conf.beat_schedule = {
    'check-scheduled-posts': {
        'task': 'apps.api.src.workers.publish_worker.check_scheduled_posts',
        'schedule': 60.0,  # Check every minute
    },
    'refresh-social-tokens': {
        'task': 'apps.api.src.workers.publish_worker.refresh_social_tokens',
        'schedule': 3600.0,  # Check every hour
    },
    'sync-social-accounts': {
        'task': 'apps.api.src.workers.publish_worker.sync_social_accounts',
        'schedule': 21600.0,  # Sync every 6 hours
    },
}

celery_app.conf.timezone = 'UTC'