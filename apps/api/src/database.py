from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import structlog

from .config import settings

logger = structlog.get_logger()

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create declarative base
Base = declarative_base()


# Dependency to get DB session
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error("Database session error", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()


# Database initialization
async def init_db():
    """Initialize database tables"""
    try:
        # Import all models to ensure they are registered with SQLAlchemy
        from .models import user, project, clip, scheduled_post, social_account

        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


# Database health check
async def check_db_health():
    """Check database connectivity"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return False