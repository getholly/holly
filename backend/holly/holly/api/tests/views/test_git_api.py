"""
Unit tests for the Git API endpoints.
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase

from holly.holly.models.mission import Mission

User = get_user_model()


class GitAPITest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpassword")
        self.client.login(username="testuser", password="testpassword")

        # Create a test mission
        self.mission = Mission.objects.create(
            owner=self.user,
            title="Test Mission",
            description="Test Mission Description",
            branch_name="main",
            state=Mission.State.IN_PROGRESS,
            container_id="test-container-id",
        )

        # API endpoint base path
        self.base_url = "/_api/holly/git"

    @patch("holly.holly.api.views.git.container_service._get_container_ip")
    @patch("httpx.AsyncClient.post")
    def test_clone_repository(self, mock_post, mock_get_ip):
        # Mock the container service response
        mock_get_ip.return_value = "172.17.0.2"

        # Mock the httpx response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "message": "Repository cloned successfully",
            "path": "/test/path",
            "branch": "main",
        }
        mock_post.return_value = mock_response

        # Make the API request
        response = self.client.post(
            f"{self.base_url}/clone",
            {
                "mission_id": str(self.mission.id),
                "repo_owner": "test-owner",
                "repo_name": "test-repo",
                "branch": "main",
            },
            content_type="application/json",
        )

        # Assert the response
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Assert the mock calls
        mock_get_ip.assert_called_once_with("test-container-id")
        mock_post.assert_called_once()

    @patch("holly.holly.api.views.git.container_service._get_container_ip")
    @patch("httpx.AsyncClient.post")
    def test_commit_changes(self, mock_post, mock_get_ip):
        # Mock the container service response
        mock_get_ip.return_value = "172.17.0.2"

        # Mock the httpx response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "message": "Changes committed successfully",
            "path": "/test/path",
            "branch": "main",
        }
        mock_post.return_value = mock_response

        # Make the API request
        response = self.client.post(
            f"{self.base_url}/commit",
            {
                "mission_id": str(self.mission.id),
                "repo_owner": "test-owner",
                "repo_name": "test-repo",
                "branch": "main",
                "commit_message": "Test commit",
            },
            content_type="application/json",
        )

        # Assert the response
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Assert the mock calls
        mock_get_ip.assert_called_once_with("test-container-id")
        mock_post.assert_called_once()

    @patch("holly.holly.api.views.git.container_service._get_container_ip")
    def test_mission_not_started(self, mock_get_ip):
        # Create a mission without a container_id
        mission = Mission.objects.create(
            owner=self.user,
            title="Test Mission 2",
            description="Test Mission Description",
            branch_name="main",
            state=Mission.State.DRAFT,
        )

        # Make the API request
        response = self.client.post(
            f"{self.base_url}/clone",
            {"mission_id": str(mission.id), "repo_owner": "test-owner", "repo_name": "test-repo", "branch": "main"},
            content_type="application/json",
        )

        # Assert the response
        assert response.status_code == 200
        assert response.json()["success"] is False
        assert "not running" in response.json()["message"]

        # Assert the mock was not called
        mock_get_ip.assert_not_called()

    @patch("holly.holly.api.views.git.container_service._get_container_ip")
    def test_invalid_container_id(self, mock_get_ip):
        # Mock the container service response - no IP found
        mock_get_ip.return_value = None

        # Make the API request
        response = self.client.post(
            f"{self.base_url}/clone",
            {
                "mission_id": str(self.mission.id),
                "repo_owner": "test-owner",
                "repo_name": "test-repo",
                "branch": "main",
            },
            content_type="application/json",
        )

        # Assert the response
        assert response.status_code == 200
        assert response.json()["success"] is False
        assert "Could not connect" in response.json()["message"]

        # Assert the mock was called
        mock_get_ip.assert_called_once_with("test-container-id")

    def test_mission_not_found(self):
        # Make the API request with a non-existent mission ID
        response = self.client.post(
            f"{self.base_url}/clone",
            {
                "mission_id": str(uuid4()),  # Random UUID that doesn't exist
                "repo_owner": "test-owner",
                "repo_name": "test-repo",
                "branch": "main",
            },
            content_type="application/json",
        )

        # Assert the response
        assert response.status_code == 404

    def test_unauthorized_access(self):
        # Create another user
        other_user = User.objects.create_user(username="otheruser", email="other@example.com", password="otherpassword")

        # Create a mission owned by the other user
        other_mission = Mission.objects.create(
            owner=other_user,
            title="Other Mission",
            description="Other Mission Description",
            branch_name="main",
            state=Mission.State.IN_PROGRESS,
            container_id="other-container-id",
        )

        # Make the API request
        response = self.client.post(
            f"{self.base_url}/clone",
            {
                "mission_id": str(other_mission.id),
                "repo_owner": "test-owner",
                "repo_name": "test-repo",
                "branch": "main",
            },
            content_type="application/json",
        )

        # Assert the response
        assert response.status_code == 200
        assert response.json()["success"] is False
        assert "permission" in response.json()["message"]

    @patch("holly.holly.api.views.git.container_service._get_container_ip")
    @patch("httpx.AsyncClient.post")
    def test_worktree_creation(self, mock_post, mock_get_ip):
        # Mock the container service response
        mock_get_ip.return_value = "172.17.0.2"

        # Mock the httpx response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "message": "Worktree created successfully",
            "path": "/test/path",
            "branch": "feature-branch",
        }
        mock_post.return_value = mock_response

        # Make the API request
        response = self.client.post(
            f"{self.base_url}/worktree",
            {
                "mission_id": str(self.mission.id),
                "repo_owner": "test-owner",
                "repo_name": "test-repo",
                "branch": "feature-branch",
                "base_branch": "main",
            },
            content_type="application/json",
        )

        # Assert the response
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Assert the mock calls
        mock_get_ip.assert_called_once_with("test-container-id")
        mock_post.assert_called_once()

    @patch("holly.holly.api.views.git.container_service._get_container_ip")
    @patch("httpx.AsyncClient.post")
    def test_pull_changes(self, mock_post, mock_get_ip):
        # Mock the container service response
        mock_get_ip.return_value = "172.17.0.2"

        # Mock the httpx response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "message": "Changes pulled successfully",
            "path": "/test/path",
            "branch": "main",
        }
        mock_post.return_value = mock_response

        # Make the API request
        response = self.client.post(
            f"{self.base_url}/pull",
            {
                "mission_id": str(self.mission.id),
                "repo_owner": "test-owner",
                "repo_name": "test-repo",
                "branch": "main",
            },
            content_type="application/json",
        )

        # Assert the response
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Assert the mock calls
        mock_get_ip.assert_called_once_with("test-container-id")
        mock_post.assert_called_once()

    @patch("holly.holly.api.views.git.container_service._get_container_ip")
    @patch("httpx.AsyncClient.post")
    def test_push_changes(self, mock_post, mock_get_ip):
        # Mock the container service response
        mock_get_ip.return_value = "172.17.0.2"

        # Mock the httpx response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "message": "Changes pushed successfully",
            "path": "/test/path",
            "branch": "main",
        }
        mock_post.return_value = mock_response

        # Make the API request
        response = self.client.post(
            f"{self.base_url}/push",
            {
                "mission_id": str(self.mission.id),
                "repo_owner": "test-owner",
                "repo_name": "test-repo",
                "branch": "main",
                "force": False,
            },
            content_type="application/json",
        )

        # Assert the response
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Assert the mock calls
        mock_get_ip.assert_called_once_with("test-container-id")
        mock_post.assert_called_once()

    @patch("holly.holly.api.views.git.container_service._get_container_ip")
    @patch("httpx.AsyncClient.post")
    def test_list_branches(self, mock_post, mock_get_ip):
        # Mock the container service response
        mock_get_ip.return_value = "172.17.0.2"

        # Mock the httpx response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "message": "Branches retrieved successfully",
            "branches": ["main", "dev", "feature-branch"],
            "current_branch": "main",
        }
        mock_post.return_value = mock_response

        # Make the API request
        response = self.client.post(
            f"{self.base_url}/branches",
            {"mission_id": str(self.mission.id), "repo_owner": "test-owner", "repo_name": "test-repo"},
            content_type="application/json",
        )

        # Assert the response
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert len(response.json()["branches"]) == 3

        # Assert the mock calls
        mock_get_ip.assert_called_once_with("test-container-id")
        mock_post.assert_called_once()
