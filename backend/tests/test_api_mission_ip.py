import pytest
from django.test import Client
from django.urls import reverse

from holly.holly.api.tests.factories.missions import MissionFactory
from holly.holly.api.tests.factories.users import UserFactory


@pytest.mark.django_db
def test_get_mission_returns_ip():
    user = UserFactory()
    mission = MissionFactory(owner=user, container_ip_address="192.168.0.5")
    client = Client()
    client.login(email=user.email, password="password")

    url = reverse("api-1.0.0:holly_missions_get_mission", kwargs={"mission_id": mission.id})
    response = client.get(url)
    assert response.status_code == 200
    assert response.json()["container_ip_address"] == "192.168.0.5"
