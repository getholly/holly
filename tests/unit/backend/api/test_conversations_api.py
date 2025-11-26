"""
Tests for the conversations API endpoints.
"""

from unittest.mock import AsyncMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from holly.holly.api.proxy import MCPProxyClient

User = get_user_model()


@pytest.fixture
def authenticated_client():
    """Create a authenticated client for testing."""
    client = Client()
    User.objects.create_user(username="testuser", password="testpassword")
    client.login(username="testuser", password="testpassword")
    return client


@pytest.fixture
def unauthenticated_client():
    """Create a standard client for testing."""
    return Client()


@pytest.mark.django_db
class TestConversationsAPI:
    """Test the conversations API endpoints."""

    def test_list_conversations_auth_required(self, unauthenticated_client, authenticated_client):
        """Test that authentication is required for listing conversations."""
        url = reverse("api-1.0.0:holly_conversations_list_conversations")

        # Unauthenticated request should be rejected
        response = unauthenticated_client.get(url)
        assert response.status_code == 401

        # For authenticated request, we mock the proxy response
        with patch.object(MCPProxyClient, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = [
                {
                    "id": "123",
                    "title": "Test Conversation",
                    "created_at": "2025-05-13T00:00:00Z",
                    "updated_at": "2025-05-13T00:00:00Z",
                }
            ]
            response = authenticated_client.get(url)
            assert response.status_code == 200
            assert len(response.json()) == 1
            assert response.json()[0]["id"] == "123"

    def test_get_conversation_auth_required(self, unauthenticated_client, authenticated_client):
        """Test that authentication is required for getting a conversation."""
        conversation_id = "123"
        url = reverse("api-1.0.0:holly_conversations_get_conversation", kwargs={"conversation_id": conversation_id})

        # Unauthenticated request should be rejected
        response = unauthenticated_client.get(url)
        assert response.status_code == 401

        # For authenticated request, we mock the proxy response
        with patch.object(MCPProxyClient, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_data = {
                "id": conversation_id,
                "title": "Test Conversation",
                "created_at": "2025-05-13T00:00:00Z",
                "updated_at": "2025-05-13T00:00:00Z",
                "messages": [
                    {
                        "id": "msg1",
                        "conversation_id": conversation_id,
                        "role": "user",
                        "content": "Hello",
                        "created_at": "2025-05-13T00:00:00Z",
                    },
                    {
                        "id": "msg2",
                        "conversation_id": conversation_id,
                        "role": "assistant",
                        "content": "Hi there!",
                        "created_at": "2025-05-13T00:00:01Z",
                    },
                ],
            }
            mock_request.return_value = mock_data
            response = authenticated_client.get(url)
            assert response.status_code == 200
            assert response.json()["id"] == conversation_id
            assert len(response.json()["messages"]) == 2

    def test_start_conversation_auth_required(self, unauthenticated_client, authenticated_client):
        """Test that authentication is required for starting a conversation."""
        url = reverse("api-1.0.0:holly_conversations_start_conversation")
        data = {"title": "New Conversation", "initial_message": "Hello there"}

        # Unauthenticated request should be rejected
        response = unauthenticated_client.post(url, data, content_type="application/json")
        assert response.status_code == 401

        # For authenticated request, we mock the proxy response
        with patch.object(MCPProxyClient, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_data = {
                "id": "new-conv-123",
                "title": "New Conversation",
                "created_at": "2025-05-13T00:00:00Z",
                "updated_at": "2025-05-13T00:00:00Z",
                "messages": [
                    {
                        "id": "msg1",
                        "conversation_id": "new-conv-123",
                        "role": "user",
                        "content": "Hello there",
                        "created_at": "2025-05-13T00:00:00Z",
                    }
                ],
            }
            mock_request.return_value = mock_data
            response = authenticated_client.post(url, data, content_type="application/json")
            assert response.status_code == 200
            assert response.json()["id"] == "new-conv-123"
            assert response.json()["title"] == "New Conversation"
            assert len(response.json()["messages"]) == 1

    def test_send_message_auth_required(self, unauthenticated_client, authenticated_client):
        """Test that authentication is required for sending a message."""
        conversation_id = "123"
        url = reverse("api-1.0.0:holly_conversations_send_message", kwargs={"conversation_id": conversation_id})
        data = {"content": "Hello from the test"}

        # Unauthenticated request should be rejected
        response = unauthenticated_client.post(url, data, content_type="application/json")
        assert response.status_code == 401

        # For authenticated request, we mock the proxy response
        with patch.object(MCPProxyClient, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_data = {
                "assistant_message": {
                    "id": "resp1",
                    "conversation_id": conversation_id,
                    "role": "assistant",
                    "content": "Hello there!",
                    "created_at": "2025-05-13T00:00:01Z",
                },
                "conversation": {
                    "id": conversation_id,
                    "title": "Test Conversation",
                    "created_at": "2025-05-13T00:00:00Z",
                    "updated_at": "2025-05-13T00:00:01Z",
                    "messages": [
                        {
                            "id": "msg1",
                            "conversation_id": conversation_id,
                            "role": "user",
                            "content": "Hello from the test",
                            "created_at": "2025-05-13T00:00:00Z",
                        },
                        {
                            "id": "resp1",
                            "conversation_id": conversation_id,
                            "role": "assistant",
                            "content": "Hello there!",
                            "created_at": "2025-05-13T00:00:01Z",
                        },
                    ],
                },
            }
            mock_request.return_value = mock_data
            response = authenticated_client.post(url, data, content_type="application/json")
            assert response.status_code == 200
            assert "assistant_message" in response.json()
            assert "conversation" in response.json()
            assert response.json()["assistant_message"]["role"] == "assistant"
            assert len(response.json()["conversation"]["messages"]) == 2
