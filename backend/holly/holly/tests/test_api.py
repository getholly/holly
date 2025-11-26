import json

from django.test import Client, TestCase
from holly.models import LLM


class LLMApiTestCase(TestCase):
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.api_key = "test_api_key"
        self.llm = LLM.objects.create(name="Test LLM", system_prompt="Test system prompt")

    def test_list_llms(self):
        """Test listing all LLMs."""
        response = self.client.get("/api/holly/llms/", HTTP_X_API_KEY=self.api_key)
        assert response.status_code == 200
        data = json.loads(response.content)
        assert len(data) == 1
        assert data[0]["name"] == "Test LLM"

    def test_get_llm(self):
        """Test getting a specific LLM."""
        response = self.client.get(f"/api/holly/llms/{self.llm.id}", HTTP_X_API_KEY=self.api_key)
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["name"] == "Test LLM"
        assert data["system_prompt"] == "Test system prompt"

    def test_create_llm(self):
        """Test creating a new LLM."""
        payload = {"name": "New LLM", "system_prompt": "New system prompt"}
        response = self.client.post(
            "/api/holly/llms/", data=json.dumps(payload), content_type="application/json", HTTP_X_API_KEY=self.api_key
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["name"] == "New LLM"
        assert data["system_prompt"] == "New system prompt"

        # Verify it was created in the database
        llm = LLM.objects.get(name="New LLM")
        assert llm.system_prompt == "New system prompt"

    def test_update_llm(self):
        """Test updating an existing LLM."""
        payload = {"name": "Updated LLM"}
        response = self.client.put(
            f"/api/holly/llms/{self.llm.id}",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_API_KEY=self.api_key,
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["name"] == "Updated LLM"

        # Verify it was updated in the database
        llm = LLM.objects.get(id=self.llm.id)
        assert llm.name == "Updated LLM"

    def test_delete_llm(self):
        """Test deleting an LLM."""
        response = self.client.delete(f"/api/holly/llms/{self.llm.id}", HTTP_X_API_KEY=self.api_key)
        assert response.status_code == 204

        # Verify it was deleted from the database
        assert LLM.objects.filter(id=self.llm.id).count() == 0

    def test_api_key_required(self):
        """Test that API key is required for authentication."""
        # Try without API key
        response = self.client.get("/api/holly/llms/")
        assert response.status_code == 401
