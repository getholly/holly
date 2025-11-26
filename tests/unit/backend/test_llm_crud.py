"""
Unit tests for LLM CRUD API endpoints.

Tests user ownership, permission checks, system LLM protection,
and CRUD operations for LLM configurations.
"""

import pytest
from django.contrib.auth import get_user_model
from ninja_jwt.tokens import AccessToken

from holly.holly.models.llms import LLM
from tests.factories import SystemLLMFactory, UserFactory, UserLLMFactory

User = get_user_model()


@pytest.fixture
def auth_headers(db):
    """Create authenticated user and return JWT auth headers."""
    user = UserFactory()
    token = AccessToken.for_user(user)
    return {"Authorization": f"Bearer {str(token)}"}, user


@pytest.fixture
def second_user_headers(db):
    """Create second authenticated user and return JWT auth headers."""
    user = UserFactory()
    token = AccessToken.for_user(user)
    return {"Authorization": f"Bearer {str(token)}"}, user


@pytest.mark.django_db
class TestLLMList:
    """Test listing LLMs."""

    def test_list_includes_system_llms(self, client, auth_headers):
        """Users should see all system LLMs."""
        headers, user = auth_headers
        system_llm = SystemLLMFactory(name="Claude")

        response = client.get("/_api/holly/llms/", **headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        llm_names = [llm["name"] for llm in data]
        assert "Claude" in llm_names

    def test_list_includes_own_custom_llms(self, client, auth_headers):
        """Users should see their own custom LLMs."""
        headers, user = auth_headers
        custom_llm = UserLLMFactory(user=user, name="My Custom LLM")

        response = client.get("/_api/holly/llms/", **headers)

        assert response.status_code == 200
        data = response.json()
        llm_names = [llm["name"] for llm in data]
        assert "My Custom LLM" in llm_names

    def test_list_excludes_other_users_llms(self, client, auth_headers, second_user_headers):
        """Users should NOT see other users' custom LLMs."""
        headers, user = auth_headers
        _, other_user = second_user_headers

        # Other user's custom LLM
        UserLLMFactory(user=other_user, name="Other User LLM")

        response = client.get("/_api/holly/llms/", **headers)

        assert response.status_code == 200
        data = response.json()
        llm_names = [llm["name"] for llm in data]
        assert "Other User LLM" not in llm_names

    def test_list_shows_is_system_flag(self, client, auth_headers):
        """Response should include is_system flag."""
        headers, user = auth_headers
        SystemLLMFactory(name="System LLM")
        UserLLMFactory(user=user, name="User LLM")

        response = client.get("/_api/holly/llms/", **headers)

        assert response.status_code == 200
        data = response.json()

        system_llm = next(llm for llm in data if llm["name"] == "System LLM")
        user_llm = next(llm for llm in data if llm["name"] == "User LLM")

        assert system_llm["is_system"] is True
        assert user_llm["is_system"] is False


@pytest.mark.django_db
class TestLLMGet:
    """Test getting a single LLM."""

    def test_get_system_llm(self, client, auth_headers):
        """Users can access system LLMs."""
        headers, user = auth_headers
        llm = SystemLLMFactory(name="GPT-4")

        response = client.get(f"/_api/holly/llms/{llm.id}", **headers)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "GPT-4"
        assert data["is_system"] is True

    def test_get_own_custom_llm(self, client, auth_headers):
        """Users can access their own custom LLMs."""
        headers, user = auth_headers
        llm = UserLLMFactory(user=user, name="My LLM")

        response = client.get(f"/_api/holly/llms/{llm.id}", **headers)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "My LLM"
        assert data["is_system"] is False

    def test_get_other_user_llm_forbidden(self, client, auth_headers, second_user_headers):
        """Users cannot access other users' custom LLMs."""
        headers, user = auth_headers
        _, other_user = second_user_headers

        llm = UserLLMFactory(user=other_user, name="Other LLM")

        response = client.get(f"/_api/holly/llms/{llm.id}", **headers)

        assert response.status_code == 403


@pytest.mark.django_db
class TestLLMCreate:
    """Test creating LLMs."""

    def test_create_custom_llm(self, client, auth_headers):
        """Users can create their own custom LLMs."""
        headers, user = auth_headers

        llm_data = {
            "name": "My Custom GPT",
            "full_name": "openai/gpt-4-turbo",
            "base_url": "https://api.openai.com/v1",
            "system_prompt": "Custom prompt",
            "temperature": 0.8,
            "max_tokens": 2048,
        }

        response = client.post("/_api/holly/llms/", json=llm_data, content_type="application/json", **headers)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Custom GPT"
        assert data["is_system"] is False
        assert data["user_id"] == user.id

        # Verify in database
        llm = LLM.objects.get(id=data["id"])
        assert llm.user == user
        assert llm.is_system is False

    def test_create_llm_duplicate_name_same_user(self, client, auth_headers):
        """Users cannot create LLMs with duplicate names."""
        headers, user = auth_headers
        UserLLMFactory(user=user, name="Duplicate Name")

        llm_data = {
            "name": "Duplicate Name",
            "full_name": "openai/gpt-4",
        }

        response = client.post("/_api/holly/llms/", json=llm_data, content_type="application/json", **headers)

        assert response.status_code == 400
        assert "already have an LLM named" in response.json()["error"]

    def test_create_llm_same_name_different_users(self, client, auth_headers, second_user_headers):
        """Different users can create LLMs with the same name."""
        headers1, user1 = auth_headers
        headers2, user2 = second_user_headers

        llm_data = {
            "name": "Same Name",
            "full_name": "openai/gpt-4",
        }

        response1 = client.post("/_api/holly/llms/", json=llm_data, content_type="application/json", **headers1)
        response2 = client.post("/_api/holly/llms/", json=llm_data, content_type="application/json", **headers2)

        assert response1.status_code == 201
        assert response2.status_code == 201

        # Verify both exist
        assert LLM.objects.filter(user=user1, name="Same Name").exists()
        assert LLM.objects.filter(user=user2, name="Same Name").exists()


@pytest.mark.django_db
class TestLLMUpdate:
    """Test updating LLMs."""

    def test_update_own_custom_llm(self, client, auth_headers):
        """Users can update their own custom LLMs."""
        headers, user = auth_headers
        llm = UserLLMFactory(user=user, name="Original Name", temperature=0.5)

        update_data = {
            "name": "Updated Name",
            "temperature": 0.9,
        }

        response = client.put(
            f"/_api/holly/llms/{llm.id}", json=update_data, content_type="application/json", **headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["temperature"] == 0.9

        # Verify in database
        llm.refresh_from_db()
        assert llm.name == "Updated Name"
        assert llm.temperature == 0.9

    def test_update_system_llm_forbidden(self, client, auth_headers):
        """Users cannot update system LLMs."""
        headers, user = auth_headers
        llm = SystemLLMFactory(name="System LLM")

        update_data = {"name": "Hacked Name"}

        response = client.put(
            f"/_api/holly/llms/{llm.id}", json=update_data, content_type="application/json", **headers
        )

        assert response.status_code == 403
        assert "Cannot update system LLMs" in response.json()["error"]

        # Verify not changed
        llm.refresh_from_db()
        assert llm.name == "System LLM"

    def test_update_other_user_llm_forbidden(self, client, auth_headers, second_user_headers):
        """Users cannot update other users' LLMs."""
        headers, user = auth_headers
        _, other_user = second_user_headers

        llm = UserLLMFactory(user=other_user, name="Other User LLM")

        update_data = {"name": "Hacked Name"}

        response = client.put(
            f"/_api/holly/llms/{llm.id}", json=update_data, content_type="application/json", **headers
        )

        assert response.status_code == 403

        # Verify not changed
        llm.refresh_from_db()
        assert llm.name == "Other User LLM"


@pytest.mark.django_db
class TestLLMDelete:
    """Test deleting LLMs."""

    def test_delete_own_custom_llm(self, client, auth_headers):
        """Users can delete their own custom LLMs."""
        headers, user = auth_headers
        llm = UserLLMFactory(user=user, name="To Delete")
        llm_id = llm.id

        response = client.delete(f"/_api/holly/llms/{llm_id}", **headers)

        assert response.status_code == 204
        assert not LLM.objects.filter(id=llm_id).exists()

    def test_delete_system_llm_forbidden(self, client, auth_headers):
        """Users cannot delete system LLMs."""
        headers, user = auth_headers
        llm = SystemLLMFactory(name="System LLM")

        response = client.delete(f"/_api/holly/llms/{llm.id}", **headers)

        assert response.status_code == 403
        assert "Cannot delete system LLMs" in response.json()["error"]

        # Verify still exists
        assert LLM.objects.filter(id=llm.id).exists()

    def test_delete_other_user_llm_forbidden(self, client, auth_headers, second_user_headers):
        """Users cannot delete other users' LLMs."""
        headers, user = auth_headers
        _, other_user = second_user_headers

        llm = UserLLMFactory(user=other_user, name="Other User LLM")

        response = client.delete(f"/_api/holly/llms/{llm.id}", **headers)

        assert response.status_code == 403

        # Verify still exists
        assert LLM.objects.filter(id=llm.id).exists()


@pytest.mark.django_db
class TestLLMModel:
    """Test LLM model behavior."""

    def test_unique_constraint_user_llm_name(self):
        """User cannot have multiple LLMs with same name."""
        user = UserFactory()
        UserLLMFactory(user=user, name="Unique Name")

        with pytest.raises(Exception):  # Django will raise IntegrityError
            UserLLMFactory(user=user, name="Unique Name")

    def test_different_users_same_llm_name(self):
        """Different users can have LLMs with same name."""
        user1 = UserFactory()
        user2 = UserFactory()

        llm1 = UserLLMFactory(user=user1, name="Same Name")
        llm2 = UserLLMFactory(user=user2, name="Same Name")

        assert llm1.id != llm2.id
        assert llm1.name == llm2.name

    def test_system_llm_no_user(self):
        """System LLMs should have no user."""
        llm = SystemLLMFactory()
        assert llm.is_system is True
        assert llm.user is None

    def test_llm_str_representation(self):
        """Test LLM __str__ method."""
        system_llm = SystemLLMFactory(name="GPT-4")
        assert str(system_llm) == "GPT-4 (System)"

        user = UserFactory(username="testuser")
        user_llm = UserLLMFactory(user=user, name="Custom LLM")
        assert str(user_llm) == "Custom LLM (testuser)"
