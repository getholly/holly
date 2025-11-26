import json
from unittest.mock import patch

import pytest
from django.test import Client
from django.urls import reverse

from holly.holly.models.mission import Mission

from .factories.missions import MissionFactory
from .factories.users import UserFactory


class _FakePubSub:
    def __init__(self, messages: list[dict]):
        self._messages = messages

    def subscribe(self, channel: str) -> None:
        self._channel = channel

    def unsubscribe(self, channel: str) -> None:
        pass

    def close(self) -> None:
        pass

    def listen(self):
        for msg in self._messages:
            yield {"type": "message", "data": json.dumps(msg)}


class _FakeRedis:
    def __init__(self, messages: list[dict]):
        self._messages = messages

    def pubsub(self):
        return _FakePubSub(self._messages)


@pytest.fixture
def authenticated_client() -> tuple[Client, object]:
    user = UserFactory()
    client = Client()
    client.login(email=user.email, password="password")  # noqa: S106
    return client, user


@pytest.mark.django_db
def test_start_mission_sse(authenticated_client: tuple[Client, object]):
    client, user = authenticated_client
    mission = MissionFactory(owner=user, state=Mission.State.DRAFT, container_id=None)
    url = reverse("api-1.0.0:holly_missions_start_mission_sse", kwargs={"mission_id": mission.id})

    redis_messages = [
        {"status": "started", "message": "cloning"},
        {"status": "completed", "message": "done"},
    ]

    with (
        patch(
            "holly.holly.api.views.mission.mission_service.start_mission_container",
            return_value=(True, "ok", "cid"),
        ),
        patch(
            "holly.holly.api.views.mission.redis.StrictRedis.from_url",
            return_value=_FakeRedis(redis_messages),
        ),
    ):
        response = client.get(url)
        events = [line.decode().strip() for line in response.streaming_content]

    assert response.status_code == 200
    assert "container_started" in events[1]
    assert json.loads(events[2][6:]) == redis_messages[0]
    assert events[-1] == "data: [DONE]"
