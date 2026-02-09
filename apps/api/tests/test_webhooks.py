"""
Test webhook handlers
"""
import json
import hmac
import hashlib
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models.user import User, PlanType


class TestClerkWebhook:
    """Test Clerk webhook handling"""

    def create_webhook_signature(self, payload: str, secret: str) -> str:
        """Create a valid webhook signature"""
        signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"v1={signature}"

    @patch('src.config.settings.CLERK_WEBHOOK_SECRET', 'test_secret')
    def test_user_created_webhook_success(self, client: TestClient, db_session: Session, clerk_webhook_payload):
        """Test successful user creation via webhook"""
        payload = json.dumps(clerk_webhook_payload)
        signature = self.create_webhook_signature(payload, 'test_secret')

        response = client.post(
            "/api/webhooks/clerk",
            content=payload,
            headers={
                "svix-signature": signature,
                "content-type": "application/json"
            }
        )

        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["event_type"] == "user.created"

        # Verify user was created in database
        user = db_session.query(User).filter(User.clerk_id == "user_12345").first()
        assert user is not None
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.plan == PlanType.FREE
        assert user.monthly_minutes_used == 0

    @patch('src.config.settings.CLERK_WEBHOOK_SECRET', 'test_secret')
    def test_user_updated_webhook(self, client: TestClient, db_session: Session, test_user):
        """Test user update via webhook"""
        payload = json.dumps({
            "type": "user.updated",
            "data": {
                "id": test_user.clerk_id,
                "email_addresses": [
                    {
                        "id": "email_12345",
                        "email_address": "updated@example.com"
                    }
                ],
                "primary_email_address_id": "email_12345",
                "first_name": "Updated",
                "last_name": "User",
                "image_url": "https://example.com/new_avatar.jpg"
            }
        })
        signature = self.create_webhook_signature(payload, 'test_secret')

        response = client.post(
            "/api/webhooks/clerk",
            content=payload,
            headers={
                "svix-signature": signature,
                "content-type": "application/json"
            }
        )

        assert response.status_code == 200

        # Verify user was updated
        db_session.refresh(test_user)
        assert test_user.email == "updated@example.com"
        assert test_user.first_name == "Updated"

    @patch('src.config.settings.CLERK_WEBHOOK_SECRET', 'test_secret')
    def test_user_deleted_webhook(self, client: TestClient, db_session: Session, test_user):
        """Test user deletion via webhook"""
        payload = json.dumps({
            "type": "user.deleted",
            "data": {
                "id": test_user.clerk_id
            }
        })
        signature = self.create_webhook_signature(payload, 'test_secret')

        response = client.post(
            "/api/webhooks/clerk",
            content=payload,
            headers={
                "svix-signature": signature,
                "content-type": "application/json"
            }
        )

        assert response.status_code == 200

        # Verify user was deleted
        user = db_session.query(User).filter(User.clerk_id == test_user.clerk_id).first()
        assert user is None

    def test_invalid_signature(self, client: TestClient, clerk_webhook_payload):
        """Test webhook with invalid signature"""
        payload = json.dumps(clerk_webhook_payload)

        response = client.post(
            "/api/webhooks/clerk",
            content=payload,
            headers={
                "svix-signature": "v1=invalid_signature",
                "content-type": "application/json"
            }
        )

        assert response.status_code == 401

    def test_missing_signature(self, client: TestClient, clerk_webhook_payload):
        """Test webhook with missing signature"""
        payload = json.dumps(clerk_webhook_payload)

        response = client.post(
            "/api/webhooks/clerk",
            content=payload,
            headers={"content-type": "application/json"}
        )

        assert response.status_code == 401

    def test_invalid_json(self, client: TestClient):
        """Test webhook with invalid JSON"""
        response = client.post(
            "/api/webhooks/clerk",
            content="invalid json",
            headers={
                "svix-signature": "v1=signature",
                "content-type": "application/json"
            }
        )

        assert response.status_code == 400

    def test_missing_event_type(self, client: TestClient):
        """Test webhook with missing event type"""
        payload = json.dumps({"data": {}})

        response = client.post(
            "/api/webhooks/clerk",
            content=payload,
            headers={
                "svix-signature": "v1=signature",
                "content-type": "application/json"
            }
        )

        assert response.status_code == 400

    @patch('src.config.settings.CLERK_WEBHOOK_SECRET', None)
    def test_missing_webhook_secret(self, client: TestClient, clerk_webhook_payload):
        """Test webhook when secret is not configured"""
        payload = json.dumps(clerk_webhook_payload)

        response = client.post(
            "/api/webhooks/clerk",
            content=payload,
            headers={
                "svix-signature": "v1=signature",
                "content-type": "application/json"
            }
        )

        assert response.status_code == 401