from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from .config import settings
# Rate limiting now handled via dependencies, not middleware
from .routers import webhooks, users

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Create FastAPI app
app = FastAPI(
    title="Shortcut API",
    description="AI-powered video clip generation API",
    version="1.0.0",
    debug=settings.DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting is now handled via dependencies in endpoints
# This ensures proper user authentication before rate limiting


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check requested")
    return {"status": "ok"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to Shortcut API"}


# Include routers
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(users.router, prefix="/api/users", tags=["users"])

# Video processing pipeline routers
from .routers import projects, clips, websocket
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(clips.router, prefix="/api/clips", tags=["clips"])

# WebSocket routes for real-time updates (PRD F4-16)
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

# Social media and scheduling routers (F6 Implementation)
from .routers import social, schedule
app.include_router(social.router, prefix="/api/social", tags=["social"])
app.include_router(schedule.router, prefix="/api/schedule", tags=["schedule"])

# Stripe billing routers (F7 Implementation)
from .routers import stripe
app.include_router(stripe.router, prefix="/api/stripe", tags=["stripe", "billing"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )