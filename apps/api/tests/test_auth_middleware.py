"""
Test authentication middleware
"""
import jwt
from unittest.mock import patch, Mock
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.middleware.auth import ClerkJWTBearer
from src.models.user import User, PlanType


class TestClerkJWTBearer:
    """Test Clerk JWT authentication"""

    @pytest.fixture
    def auth_middleware(self):
        """Create auth middleware instance"""
        return ClerkJWTBearer(auto_error=True)

    @pytest.fixture
    def valid_jwt_payload(self):
        """Create valid JWT payload"""
        return {
            "sub": "user_test123",
            "exp": int((datetime.now(timezone.utc).timestamp() + 3600)),  # 1 hour from now
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "email": "test@example.com"
        }

    @pytest.fixture
    def expired_jwt_payload(self):
        """Create expired JWT payload"""
        return {
            "sub": "user_test123",
            "exp": int((datetime.now(timezone.utc).timestamp() - 3600)),  # 1 hour ago
            "iat": int((datetime.now(timezone.utc).timestamp() - 7200)),   # 2 hours ago
            "email": "test@example.com"
        }

    @patch('src.config.settings.CLERK_SECRET_KEY', 'test_secret')
    def test_verify_jwt_success(self, auth_middleware, valid_jwt_payload):
        """Test successful JWT verification"""
        token = jwt.encode(valid_jwt_payload, 'test_secret', algorithm='HS256')

        # Mock the decode to bypass signature verification for testing
        with patch('jwt.decode', return_value=valid_jwt_payload):
            result = pytest.run(auth_middleware.verify_jwt(token))
            assert result == valid_jwt_payload

    @patch('src.config.settings.CLERK_SECRET_KEY', 'test_secret')
    def test_verify_jwt_expired(self, auth_middleware, expired_jwt_payload):
        """Test JWT verification with expired token"""
        token = jwt.encode(expired_jwt_payload, 'test_secret', algorithm='HS256')

        with patch('jwt.decode', return_value=expired_jwt_payload):
            with pytest.raises(HTTPException) as exc_info:
                pytest.run(auth_middleware.verify_jwt(token))
            assert exc_info.value.status_code == 401
            assert "expired" in exc_info.value.detail.lower()

    def test_verify_jwt_no_secret(self, auth_middleware, valid_jwt_payload):
        """Test JWT verification without secret configured"""
        token = jwt.encode(valid_jwt_payload, 'secret', algorithm='HS256')

        with patch('src.config.settings.CLERK_SECRET_KEY', None):
            with pytest.raises(HTTPException) as exc_info:
                pytest.run(auth_middleware.verify_jwt(token))
            assert exc_info.value.status_code == 500

    @patch('src.config.settings.CLERK_SECRET_KEY', 'test_secret')
    def test_verify_jwt_invalid_token(self, auth_middleware):
        """Test JWT verification with invalid token"""
        with patch('jwt.decode', side_effect=jwt.InvalidTokenError("Invalid token")):
            with pytest.raises(HTTPException) as exc_info:
                pytest.run(auth_middleware.verify_jwt("invalid_token"))
            assert exc_info.value.status_code == 401

    def test_call_missing_user_in_db(self, auth_middleware, valid_jwt_payload, db_session):
        """Test authentication when user doesn't exist in database"""
        token = jwt.encode(valid_jwt_payload, 'test_secret', algorithm='HS256')

        mock_request = Mock()
        mock_credentials = Mock()
        mock_credentials.credentials = token

        with patch.object(auth_middleware, 'verify_jwt', return_value=valid_jwt_payload):
            with patch('src.database.get_db', return_value=iter([db_session])):
                with patch('src.middleware.auth.super') as mock_super:
                    mock_super().return_value = mock_credentials

                    with pytest.raises(HTTPException) as exc_info:
                        pytest.run(auth_middleware(mock_request))
                    assert exc_info.value.status_code == 401
                    assert "not found" in exc_info.value.detail.lower()

    def test_call_successful_auth(self, auth_middleware, valid_jwt_payload, test_user, db_session):
        """Test successful authentication flow"""
        # Update test user to match payload
        test_user.clerk_id = valid_jwt_payload["sub"]
        db_session.commit()

        token = jwt.encode(valid_jwt_payload, 'test_secret', algorithm='HS256')

        mock_request = Mock()
        mock_credentials = Mock()
        mock_credentials.credentials = token

        with patch.object(auth_middleware, 'verify_jwt', return_value=valid_jwt_payload):
            with patch('src.database.get_db', return_value=iter([db_session])):
                with patch('src.middleware.auth.super') as mock_super:
                    mock_super().return_value = mock_credentials

                    payload, user = pytest.run(auth_middleware(mock_request))
                    assert payload == valid_jwt_payload
                    assert user.clerk_id == valid_jwt_payload["sub"]
                    assert user.last_login is not None


class TestUserModel:
    """Test User model methods"""

    def test_name_property_full_name(self, db_session):
        """Test name property with both first and last name"""
        user = User(
            clerk_id="test123",
            email="test@example.com",
            first_name="John",
            last_name="Doe"
        )
        assert user.name == "John Doe"

    def test_name_property_first_name_only(self, db_session):
        """Test name property with first name only"""
        user = User(
            clerk_id="test123",
            email="test@example.com",
            first_name="John",
            last_name=None
        )
        assert user.name == "John"

    def test_name_property_last_name_only(self, db_session):
        """Test name property with last name only"""
        user = User(
            clerk_id="test123",
            email="test@example.com",
            first_name=None,
            last_name="Doe"
        )
        assert user.name == "Doe"

    def test_name_property_no_names(self, db_session):
        """Test name property with no names"""
        user = User(
            clerk_id="test123",
            email="test@example.com",
            first_name=None,
            last_name=None
        )
        assert user.name == ""

    def test_monthly_minutes_limit(self):
        """Test monthly minutes limit for different plans"""
        user = User(clerk_id="test", email="test@example.com")

        user.plan = PlanType.FREE
        assert user.monthly_minutes_limit == 60

        user.plan = PlanType.STARTER
        assert user.monthly_minutes_limit == 300

        user.plan = PlanType.PRO
        assert user.monthly_minutes_limit == 1200

        user.plan = PlanType.ENTERPRISE
        assert user.monthly_minutes_limit == 999999

    def test_can_use_minutes(self):
        """Test can_use_minutes method"""
        user = User(
            clerk_id="test",
            email="test@example.com",
            plan=PlanType.FREE,
            monthly_minutes_used=30
        )

        # Can use within limit
        assert user.can_use_minutes(20) == True

        # Cannot exceed limit
        assert user.can_use_minutes(40) == False

        # Enterprise plan can always use
        user.plan = PlanType.ENTERPRISE
        assert user.can_use_minutes(999999) == True

    def test_use_minutes(self, db_session):
        """Test use_minutes method"""
        user = User(
            clerk_id="test",
            email="test@example.com",
            plan=PlanType.FREE,
            monthly_minutes_used=30
        )

        # Successful usage
        assert user.use_minutes(20) == True
        assert user.monthly_minutes_used == 50

        # Failed usage (exceeds limit)
        assert user.use_minutes(20) == False
        assert user.monthly_minutes_used == 50  # Should not change

    def test_reset_monthly_usage(self):
        """Test reset_monthly_usage method"""
        user = User(
            clerk_id="test",
            email="test@example.com",
            monthly_minutes_used=100
        )

        user.reset_monthly_usage()
        assert user.monthly_minutes_used == 0