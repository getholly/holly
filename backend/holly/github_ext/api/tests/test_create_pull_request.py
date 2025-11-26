import json
from unittest.mock import patch

import pytest
from django.test import Client

from holly.holly.api.tests.factories.conversations import MissionConversationFactory
from holly.holly.api.tests.factories.missions import MissionFactory
from holly.holly.api.tests.factories.repositories import RepositoryDetailFactory
from holly.holly.api.tests.factories.users import UserFactory


@pytest.mark.django_db
def test_create_pull_request():
    user = UserFactory()
    repo = RepositoryDetailFactory()
    mission = MissionFactory(owner=user)
    mission.repositories.add(repo)
    conversation = MissionConversationFactory(mission=mission, title="feature-branch")

    client = Client()
    client.login(email=user.email, password="password")

    pr_data = {"html_url": "https://github.com/test/repo/pull/1", "number": 1}
    with patch(
        "holly.github_ext.services.github_app_service.GitHubAppService.create_pull_request",
        return_value=pr_data,
    ) as mock_create:
        response = client.post(f"/_api/github/pull-request/{conversation.id}")

    assert response.status_code == 200
    data = json.loads(response.content)
    assert data["url"] == pr_data["html_url"]
    assert data["number"] == pr_data["number"]
    mock_create.assert_called_once()


@pytest.mark.django_db
def test_create_pull_request_requires_auth():
    conversation = MissionConversationFactory()
    client = Client()
    response = client.post(f"/_api/github/pull-request/{conversation.id}")
    assert response.status_code == 401
