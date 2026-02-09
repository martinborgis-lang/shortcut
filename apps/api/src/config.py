from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/shortcut"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # AWS S3
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "shortcut-storage"

    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    # Stripe Product Price IDs
    STRIPE_STARTER_PRICE_ID: Optional[str] = None
    STRIPE_PRO_PRICE_ID: Optional[str] = None
    STRIPE_ENTERPRISE_PRICE_ID: Optional[str] = None

    # Deepgram
    DEEPGRAM_API_KEY: Optional[str] = None

    # Anthropic
    ANTHROPIC_API_KEY: Optional[str] = None

    # Clerk
    CLERK_SECRET_KEY: Optional[str] = None
    CLERK_WEBHOOK_SECRET: Optional[str] = None
    CLERK_JWT_VERIFY_SIGNATURE: bool = False  # Set to True in production

    # TikTok OAuth
    TIKTOK_CLIENT_KEY: Optional[str] = None
    TIKTOK_CLIENT_SECRET: Optional[str] = None

    # Encryption key for tokens (32 bytes base64 encoded)
    ENCRYPTION_KEY: str = "dev-encryption-key-change-in-production-32bytes"

    # Frontend URL for OAuth redirects
    FRONTEND_URL: str = "http://localhost:3000"

    # App Config
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    # Development Mode for mocking external services
    MOCK_MODE: bool = False

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003"]

    # File Upload
    MAX_FILE_SIZE: int = 1000 * 1024 * 1024  # 1GB in bytes
    ALLOWED_VIDEO_EXTENSIONS: list[str] = [".mp4", ".avi", ".mov", ".mkv", ".webm"]

    class Config:
        env_file = ".env"


settings = Settings()