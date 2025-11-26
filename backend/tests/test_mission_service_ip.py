from unittest.mock import patch

import pytest

from holly.holly.api.tests.factories.missions import MissionFactory
from holly.holly.api.tests.factories.users import UserFactory
from holly.holly.models.mission import Mission
from holly.holly.services.mission_service import MissionService


@pytest.mark.django_db
@patch("holly.holly.services.mission_service.clone_repositories_task")
@patch("holly.holly.services.mission_service.get_github_oauth_token")
def test_start_container_sets_ip(mock_get_token, mock_clone):
    mock_get_token.return_value = "token"
    user = UserFactory()
    mission = MissionFactory(
        owner=user,
        state=Mission.State.DRAFT,
        container_id=None,
        container_ip_address=None,
    )
    service = MissionService()
    with (
        patch.object(service.container_service, "start_container", return_value="cid") as mock_start,
        patch.object(service.container_service, "get_container_ip", return_value="10.0.0.2"),
    ):
        success, msg, cid = service.start_mission_container(mission.id, user)

    mission.refresh_from_db()
    assert success is True
    assert cid == "cid"
    assert mission.container_ip_address == "10.0.0.2"
    mock_start.assert_called_once()
