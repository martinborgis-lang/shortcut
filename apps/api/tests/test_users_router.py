"""
Test users router endpoints
"""
from unittest.mock import patch, Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models.user import User, PlanType


class TestUsersRouter:
    """Test user endpoints"""

    def create_auth_header(self, user: User):
        """Create authorization header for authenticated requests"""
        # In a real test, you would create a valid JWT token
        # For this test, we'll mock the authentication
        return {"Authorization": "Bearer mock_token"}

    @patch('src.middleware.auth.get_current_user')
    def test_get_current_user_info_success(self, mock_get_user, client: TestClient, test_user):
        """Test successful retrieval of current user info"""
        mock_get_user.return_value = test_user

        response = client.get(
            "/api/users/me",
            headers=self.create_auth_header(test_user)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["clerk_id"] == test_user.clerk_id
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name
        assert data["plan"] == test_user.plan.value
        assert data["monthly_minutes_used"] == test_user.monthly_minutes_used
        assert data["monthly_minutes_limit"] == test_user.monthly_minutes_limit

    @patch('src.middleware.auth.get_current_user')
    def test_get_user_usage_success(self, mock_get_user, client: TestClient, test_user):
        """Test successful retrieval of user usage stats"""
        mock_get_user.return_value = test_user

        response = client.get(
            "/api/users/me/usage",
            headers=self.create_auth_header(test_user)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["monthly_minutes_used"] == test_user.monthly_minutes_used
        assert data["monthly_minutes_limit"] == test_user.monthly_minutes_limit
        assert data["monthly_minutes_remaining"] == (
            test_user.monthly_minutes_limit - test_user.monthly_minutes_used
        )
        assert data["clips_generated"] == test_user.clips_generated
        assert data["clips_limit"] == test_user.clips_limit
        assert data["plan"] == test_user.plan.value

    @patch('src.middleware.auth.get_current_user')
    def test_reset_monthly_usage_success(self, mock_get_user, client: TestClient, test_user, db_session):
        """Test successful reset of monthly usage"""
        # Set some usage first
        test_user.monthly_minutes_used = 50
        db_session.commit()

        mock_get_user.return_value = test_user

        response = client.post(
            "/api/users/me/reset-usage",
            headers=self.create_auth_header(test_user)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["monthly_minutes_used"] == 0

        # Verify in database
        db_session.refresh(test_user)
        assert test_user.monthly_minutes_used == 0

    def test_unauthorized_access(self, client: TestClient):
        """Test unauthorized access to protected endpoints"""
        response = client.get("/api/users/me")
        assert response.status_code == 422  # FastAPI validation error for missing auth

        response = client.get("/api/users/me/usage")
        assert response.status_code == 422

        response = client.post("/api/users/me/reset-usage")
        assert response.status_code == 422

    @patch('src.middleware.auth.get_current_user')
    def test_get_user_info_database_error(self, mock_get_user, client: TestClient):
        """Test user info endpoint with database error"""
        # Create a user that will cause an error when accessing properties
        mock_user = Mock()
        mock_user.id = "test_id"
        mock_user.clerk_id = "test_clerk"
        mock_user.email = "test@example.com"
        mock_user.name = "Test User"
        mock_user.first_name = "Test"
        mock_user.last_name = "User"
        mock_user.profile_image_url = None
        mock_user.plan = PlanType.FREE
        mock_user.monthly_minutes_used = 0
        mock_user.monthly_minutes_limit = 60
        mock_user.created_at = None  # This will cause an error

        mock_get_user.return_value = mock_user

        response = client.get(
            "/api/users/me",
            headers={"Authorization": "Bearer mock_token"}
        )

        # Should still work as we handle the None case
        assert response.status_code == 200
        data = response.json()
        assert data["created_at"] == ""


class TestUserUsageLogic:
    """Test user usage business logic"""

    def test_usage_calculation_free_plan(self):
        """Test usage calculation for free plan"""
        user = User(
            clerk_id="test",
            email="test@example.com",
            plan=PlanType.FREE,
            monthly_minutes_used=30,
            clips_generated=5,
            clips_limit=10
        )

        # Test remaining minutes
        remaining = user.monthly_minutes_limit - user.monthly_minutes_used
        assert remaining == 30

        # Test can use within limit
        assert user.can_use_minutes(20) == True
        assert user.can_use_minutes(40) == False

    def test_usage_calculation_enterprise_plan(self):
        """Test usage calculation for enterprise plan"""
        user = User(
            clerk_id="test",
            email="test@example.com",
            plan=PlanType.ENTERPRISE,
            monthly_minutes_used=50000  # Way above other plan limits
        )

        # Enterprise should always allow usage
        assert user.can_use_minutes(99999) == True

    def test_plan_limits(self):
        """Test different plan limits"""
        plans_and_limits = [
            (PlanType.FREE, 60),
            (PlanType.STARTER, 300),
            (PlanType.PRO, 1200),
            (PlanType.ENTERPRISE, 999999)
        ]

        for plan, expected_limit in plans_and_limits:
            user = User(
                clerk_id="test",
                email="test@example.com",
                plan=plan
            )
            assert user.monthly_minutes_limit == expected_limit