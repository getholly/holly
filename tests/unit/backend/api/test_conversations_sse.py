"""Tests for the SSE conversation endpoints."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from django.test import Client
from django.urls import reverse
from django_eventstream.testing import EventSource

from holly.holly.eventstream import conversation_channel

from .factories.conversations import MissionConversationFactory
from .factories.users import UserFactory


@pytest.fixture
def authenticated_client() -> tuple[Client, object]:
    """Return a logged in client with its user."""
    user = UserFactory()
    client = Client()
    client.login(email=user.email, password="password")  # noqa: S106
    return client, user


@pytest.mark.django_db
class TestConversationSSE:
    """Tests for streaming conversation endpoints."""

    def _setup_conversation(self, user):
        return MissionConversationFactory(mission__owner=user)

    def _mock_sse(self, lines: list[str]):
        async def stream(_resp):
            for line in lines:
                yield line

        return stream

    def test_start_conversation_sse(self, authenticated_client: tuple[Client, object]):
        client, user = authenticated_client
        conversation = MissionConversationFactory(mission__owner=user)
        url = reverse(
            "api-1.0.0:holly_conversations_start_conversation_sse",
            kwargs={"conversation_id": str(conversation.id)},
        )

        fake_lines = [
            'data: {"role": "assistant", "content": "hi"}',
            "data: [DONE]",
        ]

        with (
            patch(
                "holly.holly.api.views.conversations.MissionConversation.objects.aget",
                new=AsyncMock(return_value=conversation),
            ),
            patch(
                "holly.holly.api.views.conversations.mission_service.ensure_mission_container",
                new=AsyncMock(return_value=(True, "", "http://container")),
            ),
            patch(
                "holly.holly.api.views.conversations.MCPProxyClient.get_sse",
                new=AsyncMock(return_value=MagicMock()),
            ),
            patch(
                "holly.holly.api.views.conversations.MCPProxyClient.stream_sse",
                new=self._mock_sse(fake_lines),
            ),
            patch("holly.holly.api.views.conversations.MessageModel.objects.create"),
        ):
            es = EventSource(conversation_channel(str(conversation.id)))
            response = client.get(url)

        assert response.status_code == 200
        assert es.get_next_event()["data"]["text"] == fake_lines[0]
        assert es.get_next_event()["data"]["text"] == fake_lines[1]

    def test_send_message_sse(self, authenticated_client: tuple[Client, object]):
        client, user = authenticated_client
        conversation = MissionConversationFactory(mission__owner=user)
        url = reverse(
            "api-1.0.0:holly_conversations_send_message_sse",
            kwargs={"conversation_id": str(conversation.id)},
        )

        fake_lines = [
            'data: {"role": "assistant", "content": "pong"}',
            "data: [DONE]",
        ]

        with (
            patch(
                "holly.holly.api.views.conversations.MissionConversation.objects.aget",
                new=AsyncMock(return_value=conversation),
            ),
            patch(
                "holly.holly.api.views.conversations.mission_service.ensure_mission_container",
                new=AsyncMock(return_value=(True, "", "http://container")),
            ),
            patch(
                "holly.holly.api.views.conversations.MCPProxyClient.post_sse",
                new=AsyncMock(return_value=MagicMock()),
            ),
            patch(
                "holly.holly.api.views.conversations.MCPProxyClient.stream_sse",
                new=self._mock_sse(fake_lines),
            ),
            patch("holly.holly.api.views.conversations.MessageModel.objects.create"),
        ):
            es = EventSource(conversation_channel(str(conversation.id)))
            response = client.post(
                url,
                data=json.dumps({"content": "ping"}),
                content_type="application/json",
            )

        assert response.status_code == 200
        assert es.get_next_event()["data"]["text"] == fake_lines[0]
        assert es.get_next_event()["data"]["text"] == fake_lines[1]
