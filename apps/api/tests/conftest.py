"""
Test configuration and fixtures
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.database import Base, get_db
from src.models.user import User, PlanType

# Test database configuration
# Use in-memory SQLite for faster tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "isolation_level": None,  # For autocommit mode
    },
    poolclass=StaticPool,
    echo=False,  # Set to True for SQL debugging
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def client():
    """Create test client"""
    # Override database dependency
    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "id": "user_12345",
        "email_addresses": [
            {
                "id": "email_12345",
                "email_address": "test@example.com"
            }
        ],
        "primary_email_address_id": "email_12345",
        "first_name": "Test",
        "last_name": "User",
        "image_url": "https://example.com/avatar.jpg"
    }


@pytest.fixture
def test_user(db_session):
    """Create a test user in the database"""
    user = User(
        clerk_id="user_test123",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        plan=PlanType.FREE,
        monthly_minutes_used=10
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def clerk_webhook_payload():
    """Sample Clerk webhook payload"""
    return {
        "type": "user.created",
        "data": {
            "id": "user_12345",
            "email_addresses": [
                {
                    "id": "email_12345",
                    "email_address": "test@example.com"
                }
            ],
            "primary_email_address_id": "email_12345",
            "first_name": "Test",
            "last_name": "User",
            "image_url": "https://example.com/avatar.jpg"
        }
    }


@pytest.fixture
def mock_jwt_token():
    """Mock JWT token for testing"""
    import jwt
    import time
    from src.config import settings

    payload = {
        "sub": "user_test123",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,  # 1 hour from now
        "iss": "https://clerk.example.com",
        "aud": "test-audience"
    }

    # Create a test token (verification disabled in tests)
    token = jwt.encode(payload, "test-secret", algorithm="HS256")
    return f"Bearer {token}"


@pytest.fixture
def authenticated_headers(mock_jwt_token):
    """Headers for authenticated requests"""
    return {"Authorization": mock_jwt_token}