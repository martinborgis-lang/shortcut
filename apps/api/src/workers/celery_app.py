from celery import Celery
import structlog
from ..config import settings

logger = structlog.get_logger()

# Create Celery app
celery_app = Celery(
    "shortcut",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "workers.video_pipeline",
        "workers.publish_worker",
        "workers.regenerate_clip",
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Task routing
    task_routes={
        'workers.video_pipeline.*': {'queue': 'video_processing'},
        'workers.publish_worker.*': {'queue': 'publishing'},
    },

    # Worker configuration
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,

    # Task result expiration
    result_expires=3600,  # 1 hour

    # Task retry configuration
    task_retry_delay=60,  # 1 minute
    task_max_retries=3,

    # Beat schedule for periodic tasks
    beat_schedule={
        'cleanup-expired-tasks': {
            'task': 'workers.video_pipeline.cleanup_expired_tasks',
            'schedule': 300.0,  # Every 5 minutes
        },
        'sync-social-accounts': {
            'task': 'workers.publish_worker.sync_social_accounts',
            'schedule': 3600.0,  # Every hour
        },
    },
)


# Test task for health checking
@celery_app.task(name="ping")
def ping():
    """Simple ping task to test Celery is working"""
    logger.info("Celery ping task executed")
    return {"status": "pong", "message": "Celery is working!"}


# Task to process video uploads
@celery_app.task(name="process_video")
def process_video(project_id: str):
    """Process uploaded video to extract clips"""
    logger.info("Starting video processing", project_id=project_id)

    try:
        # Import here to avoid circular imports
        from .video_pipeline import process_video_pipeline
        return process_video_pipeline(project_id)
    except Exception as e:
        logger.error("Video processing failed", project_id=project_id, error=str(e))
        raise


# Task to generate clips from processed video
@celery_app.task(name="generate_clips")
def generate_clips(project_id: str, viral_moments: list):
    """Generate video clips from detected viral moments"""
    logger.info("Starting clip generation", project_id=project_id, moments_count=len(viral_moments))

    try:
        from .video_pipeline import generate_clips_pipeline
        return generate_clips_pipeline(project_id, viral_moments)
    except Exception as e:
        logger.error("Clip generation failed", project_id=project_id, error=str(e))
        raise


# Task to publish to social media
@celery_app.task(name="publish_to_social")
def publish_to_social(scheduled_post_id: str):
    """Publish a clip to social media platform"""
    logger.info("Starting social media publishing", scheduled_post_id=scheduled_post_id)

    try:
        from .publish_worker import publish_to_platform
        return publish_to_platform(scheduled_post_id)
    except Exception as e:
        logger.error("Social media publishing failed", scheduled_post_id=scheduled_post_id, error=str(e))
        raise


if __name__ == '__main__':
    celery_app.start()