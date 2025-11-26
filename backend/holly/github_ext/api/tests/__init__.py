"""
Tests for the GitHub API endpoints.
"""

import json
from unittest.mock import MagicMock, patch

from django.test import Client, TestCase
from django.urls import reverse

from holly.users.models import User


class GitHubAPITestCase(TestCase):
    """Tests for the GitHub API endpoints."""

    def setUp(self):
        """Set up test environment."""
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpassword")
        self.client.login(username="testuser", password="testpassword")

        # Mock repository data for testing
        self.mock_repo_data = [
            {
                "id": 123456789,
                "name": "test-repo",
                "full_name": "testuser/test-repo",
                "owner": {
                    "login": "testuser",
                    "id": 12345,
                    "avatar_url": "https://avatars.githubusercontent.com/u/12345?v=4",
                },
                "html_url": "https://github.com/testuser/test-repo",
                "description": "A test repository",
                "private": False,
                "fork": False,
                "stargazers_count": 10,
                "watchers_count": 5,
                "forks_count": 2,
                "open_issues_count": 1,
                "default_branch": "main",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-02T00:00:00Z",
                "pushed_at": "2023-01-03T00:00:00Z",
                "topics": ["python", "django"],
            }
        ]

    @patch("holly.github_ext.services.github_app_service.GitHubAppService.list_repositories")
    def test_list_repositories_endpoint(self, mock_list_repositories):
        """Test the list repositories endpoint."""
        # Configure mock to return test data
        mock_list_repositories.return_value = self.mock_repo_data

        # Make request to API endpoint
        response = self.client.get("/_api/github/repositories")

        # Assertions
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data) == 1
        assert response_data[0]["name"] == "test-repo"
        assert response_data[0]["full_name"] == "testuser/test-repo"
        assert response_data[0]["private"] is False

    def test_list_repositories_unauthenticated(self):
        """Test the list repositories endpoint with an unauthenticated user."""
        # Logout the user
        self.client.logout()

        # Make request to API endpoint
        response = self.client.get("/_api/github/repositories")

        # Assertions - expect 401 Unauthorized
        assert response.status_code == 401

    @patch("holly.github_ext.services.github_app_service.GitHubAppService.list_repositories")
    def test_list_repositories_empty(self, mock_list_repositories):
        """Test the list repositories endpoint when there are no repositories."""
        # Configure mock to return empty list
        mock_list_repositories.return_value = []

        # Make request to API endpoint
        response = self.client.get("/_api/github/repositories")

        # Assertions
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data) == 0

    @patch("holly.github_ext.services.github_app_service.GitHubAppService.list_repositories")
    def test_list_repositories_error(self, mock_list_repositories):
        """Test the list repositories endpoint when an error occurs."""
        # Configure mock to raise an exception
        mock_list_repositories.side_effect = Exception("API error")

        # Make request to API endpoint
        response = self.client.get("/_api/github/repositories")

        # Assertions - expect empty list but success status
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data) == 0
