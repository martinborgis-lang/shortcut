"""
URL Validation Service for Video Platforms

Provides robust validation for YouTube and Twitch URLs according to PRD F4-14.
Supports:
- YouTube: youtu.be, youtube.com/watch, youtube.com/shorts
- Twitch: twitch.tv/videos/
"""

import re
import structlog
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs

logger = structlog.get_logger()


class VideoURLValidator:
    """Validates and extracts information from video platform URLs."""

    # YouTube URL patterns
    YOUTUBE_PATTERNS = [
        # Standard watch URLs
        r'^https?://(www\.)?(youtube\.com/watch\?.*v=([a-zA-Z0-9_-]+))',
        r'^https?://(m\.)?(youtube\.com/watch\?.*v=([a-zA-Z0-9_-]+))',

        # Short URLs
        r'^https?://(www\.)?(youtu\.be/([a-zA-Z0-9_-]+))',

        # Shorts URLs
        r'^https?://(www\.)?(youtube\.com/shorts/([a-zA-Z0-9_-]+))',

        # Embed URLs
        r'^https?://(www\.)?(youtube\.com/embed/([a-zA-Z0-9_-]+))',

        # Watch URLs with additional parameters
        r'^https?://(www\.)?(youtube\.com/watch\?.*v=([a-zA-Z0-9_-]+).*)',
    ]

    # Twitch URL patterns
    TWITCH_PATTERNS = [
        # Video URLs
        r'^https?://(www\.)?(twitch\.tv/videos/(\d+))',

        # Live stream URLs (also supported)
        r'^https?://(www\.)?(twitch\.tv/([a-zA-Z0-9_-]+))(?:/.*)?$',
    ]

    @classmethod
    def validate_url(cls, url: str) -> Dict[str, Any]:
        """
        Validate a video URL and extract platform information.

        Args:
            url: The URL to validate

        Returns:
            Dict containing:
            - is_valid: bool
            - platform: Optional['youtube'|'twitch']
            - video_id: Optional[str]
            - error: Optional[str]
            - original_url: str
            - normalized_url: Optional[str]
        """
        if not url or not isinstance(url, str):
            return {
                'is_valid': False,
                'platform': None,
                'video_id': None,
                'error': 'URL is required and must be a string',
                'original_url': url,
                'normalized_url': None
            }

        url = url.strip()

        # Try YouTube patterns
        youtube_result = cls._validate_youtube_url(url)
        if youtube_result['is_valid']:
            logger.info("Valid YouTube URL detected", url=url, video_id=youtube_result['video_id'])
            return youtube_result

        # Try Twitch patterns
        twitch_result = cls._validate_twitch_url(url)
        if twitch_result['is_valid']:
            logger.info("Valid Twitch URL detected", url=url, video_id=twitch_result['video_id'])
            return twitch_result

        # No valid patterns found
        logger.warning("Invalid video URL provided", url=url)
        return {
            'is_valid': False,
            'platform': None,
            'video_id': None,
            'error': 'URL must be from YouTube (youtu.be, youtube.com/watch, youtube.com/shorts) or Twitch (twitch.tv/videos/)',
            'original_url': url,
            'normalized_url': None
        }

    @classmethod
    def _validate_youtube_url(cls, url: str) -> Dict[str, Any]:
        """Validate YouTube URL and extract video ID."""
        for pattern in cls.YOUTUBE_PATTERNS:
            match = re.match(pattern, url, re.IGNORECASE)
            if match:
                try:
                    # Extract video ID from different URL formats
                    video_id = cls._extract_youtube_video_id(url)
                    if video_id and len(video_id) == 11:  # YouTube video IDs are 11 characters
                        normalized_url = f"https://www.youtube.com/watch?v={video_id}"
                        return {
                            'is_valid': True,
                            'platform': 'youtube',
                            'video_id': video_id,
                            'error': None,
                            'original_url': url,
                            'normalized_url': normalized_url
                        }
                except Exception as e:
                    logger.warning("Error extracting YouTube video ID", url=url, error=str(e))
                    continue

        return {
            'is_valid': False,
            'platform': None,
            'video_id': None,
            'error': 'Invalid YouTube URL format',
            'original_url': url,
            'normalized_url': None
        }

    @classmethod
    def _validate_twitch_url(cls, url: str) -> Dict[str, Any]:
        """Validate Twitch URL and extract video/channel ID."""
        for pattern in cls.TWITCH_PATTERNS:
            match = re.match(pattern, url, re.IGNORECASE)
            if match:
                try:
                    # Extract video ID or channel name
                    video_id = cls._extract_twitch_id(url)
                    if video_id:
                        # Determine if it's a video or live stream
                        if '/videos/' in url:
                            normalized_url = f"https://www.twitch.tv/videos/{video_id}"
                        else:
                            normalized_url = f"https://www.twitch.tv/{video_id}"

                        return {
                            'is_valid': True,
                            'platform': 'twitch',
                            'video_id': video_id,
                            'error': None,
                            'original_url': url,
                            'normalized_url': normalized_url
                        }
                except Exception as e:
                    logger.warning("Error extracting Twitch ID", url=url, error=str(e))
                    continue

        return {
            'is_valid': False,
            'platform': None,
            'video_id': None,
            'error': 'Invalid Twitch URL format',
            'original_url': url,
            'normalized_url': None
        }

    @classmethod
    def _extract_youtube_video_id(cls, url: str) -> Optional[str]:
        """Extract YouTube video ID from various URL formats."""
        parsed = urlparse(url)

        if parsed.hostname in ['youtu.be']:
            # youtu.be/VIDEO_ID
            return parsed.path.lstrip('/')

        elif parsed.hostname in ['youtube.com', 'www.youtube.com', 'm.youtube.com']:
            if parsed.path.startswith('/watch'):
                # youtube.com/watch?v=VIDEO_ID
                query_params = parse_qs(parsed.query)
                return query_params.get('v', [None])[0]

            elif parsed.path.startswith('/shorts/'):
                # youtube.com/shorts/VIDEO_ID
                return parsed.path.split('/shorts/')[1].split('?')[0]

            elif parsed.path.startswith('/embed/'):
                # youtube.com/embed/VIDEO_ID
                return parsed.path.split('/embed/')[1].split('?')[0]

        return None

    @classmethod
    def _extract_twitch_id(cls, url: str) -> Optional[str]:
        """Extract Twitch video ID or channel name."""
        parsed = urlparse(url)

        if parsed.hostname in ['twitch.tv', 'www.twitch.tv']:
            path_parts = parsed.path.strip('/').split('/')

            if len(path_parts) >= 2 and path_parts[0] == 'videos':
                # twitch.tv/videos/123456
                return path_parts[1]

            elif len(path_parts) >= 1 and path_parts[0]:
                # twitch.tv/channelname
                return path_parts[0]

        return None


def validate_video_url(url: str) -> Dict[str, Any]:
    """
    Convenience function to validate a video URL.

    Args:
        url: The URL to validate

    Returns:
        Validation result dictionary
    """
    return VideoURLValidator.validate_url(url)