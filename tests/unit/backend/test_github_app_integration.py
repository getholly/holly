"""
Unit tests for GitHub App integration.

Tests GitHub App installation, token management, and repository access.
This is critical for the MVP flow as GitHub App is the primary auth method.
"""

from http import HTTPStatus
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.contrib.auth import get_user_model

from tests.factories import (
    GitHubAppInstallationFactory,
    RepositoryDetailFactory,
    SocialAccountFactory,
    UserFactory,
)
from holly.github_ext.auth_utils import (
    create_auth_headers,
    get_best_github_auth,
    get_github_app_installations,
    get_github_app_token,
    get_github_oauth_token,
    get_repository_url_with_auth,
)
from holly.github_ext.models import GitHubAppInstallation
from holly.github_ext.services.github_app_service import GitHubAppService

User = get_user_model()


# ==============================================================================
# Model Tests
# ==============================================================================


@pytest.mark.django_db
class TestGitHubAppInstallationModel:
    """Test the GitHub App Installation model."""

    def test_create_installation(self):
        """Test creating a GitHub App installation."""
        installation = GitHubAppInstallationFactory(
            installation_id="50000001",
            account_name="testuser",
            account_type="user",
        )

        assert installation.id is not None
        assert installation.installation_id == "50000001"
        assert installation.account_name == "testuser"
        assert installation.account_type == "user"
        assert installation.social_account is not None

    def test_installation_str_representation(self):
        """Test string representation of installation."""
        installation = GitHubAppInstallationFactory(
            account_name="testorg",
            installation_id="12345",
        )

        assert str(installation) == "testorg - 12345"

    def test_unique_constraint(self):
        """Test that social_account + installation_id must be unique."""
        social_account = SocialAccountFactory()

        # Create first installation
        GitHubAppInstallationFactory(
            social_account=social_account,
            installation_id="50000001",
        )

        # Try to create duplicate - should use the existing one due to get_or_create
        installation2 = GitHubAppInstallationFactory(
            social_account=social_account,
            installation_id="50000001",
        )

        # Should be the same instance
        assert GitHubAppInstallation.objects.filter(
            social_account=social_account,
            installation_id="50000001",
        ).count() == 1

    def test_multiple_installations_per_user(self):
        """Test that a user can have multiple installations."""
        user = UserFactory()
        social_account = SocialAccountFactory(user=user)

        installation1 = GitHubAppInstallationFactory(
            social_account=social_account,
            installation_id="50000001",
            account_type="user",
        )

        installation2 = GitHubAppInstallationFactory(
            social_account=social_account,
            installation_id="50000002",
            account_type="organization",
        )

        assert installation1.social_account == installation2.social_account
        assert installation1.installation_id != installation2.installation_id


# ==============================================================================
# Auth Utility Tests
# ==============================================================================


@pytest.mark.django_db
class TestAuthUtils:
    """Test GitHub authentication utility functions."""

    def test_get_repository_url_with_auth_github_app(self):
        """Test creating authenticated git URL for GitHub App."""
        auth_info = {
            "type": "github_app",
            "token": "ghs_test_token",
            "installation_id": "12345",
        }

        url = get_repository_url_with_auth(auth_info, "testuser", "test-repo")

        assert url == "https://x-access-token:ghs_test_token@github.com/testuser/test-repo.git"

    def test_get_repository_url_with_auth_oauth(self):
        """Test creating authenticated git URL for OAuth."""
        auth_info = {
            "type": "oauth",
            "token": "ghp_oauth_token",
        }

        url = get_repository_url_with_auth(auth_info, "testuser", "test-repo")

        assert url == "https://ghp_oauth_token@github.com/testuser/test-repo.git"

    def test_get_repository_url_with_auth_no_auth(self):
        """Test creating git URL without authentication."""
        auth_info = {
            "type": "none",
            "token": None,
        }

        url = get_repository_url_with_auth(auth_info, "testuser", "test-repo")

        assert url == "https://github.com/testuser/test-repo.git"

    def test_create_auth_headers_github_app(self):
        """Test creating auth headers for GitHub App."""
        auth_info = {
            "type": "github_app",
            "token": "ghs_test_token",
        }

        headers = create_auth_headers(auth_info)

        assert headers["Authorization"] == "token ghs_test_token"
        assert headers["Accept"] == "application/vnd.github.v3+json"

    def test_create_auth_headers_oauth(self):
        """Test creating auth headers for OAuth."""
        auth_info = {
            "type": "oauth",
            "token": "ghp_oauth_token",
        }

        headers = create_auth_headers(auth_info)

        assert headers["Authorization"] == "token ghp_oauth_token"
        assert headers["Accept"] == "application/vnd.github.v3+json"

    def test_create_auth_headers_no_auth(self):
        """Test creating headers without authentication."""
        auth_info = {
            "type": "none",
            "token": None,
        }

        headers = create_auth_headers(auth_info)

        assert "Authorization" not in headers
        assert headers["Accept"] == "application/vnd.github.v3+json"


@pytest.mark.django_db
class TestGetBestGitHubAuth:
    """Test the get_best_github_auth function priority logic."""

    @patch("holly.github_ext.auth_utils.get_github_app_token")
    @patch("holly.github_ext.auth_utils.get_github_oauth_token")
    def test_prefers_github_app_over_oauth(self, mock_oauth, mock_app):
        """Test that GitHub App token is preferred over OAuth token."""
        user = UserFactory()

        # Setup mocks
        mock_app.return_value = [("ghs_app_token", "12345")]
        mock_oauth.return_value = "ghp_oauth_token"

        result = get_best_github_auth(user)

        # Should return GitHub App auth
        assert len(result) == 1
        assert result[0]["type"] == "github_app"
        assert result[0]["token"] == "ghs_app_token"
        assert result[0]["installation_id"] == "12345"

        # OAuth should not be called since app token exists
        mock_app.assert_called_once_with(user, None)

    @patch("holly.github_ext.auth_utils.get_github_app_token")
    @patch("holly.github_ext.auth_utils.get_github_oauth_token")
    def test_falls_back_to_oauth(self, mock_oauth, mock_app):
        """Test fallback to OAuth when GitHub App token unavailable."""
        user = UserFactory()

        # Setup mocks
        mock_app.return_value = None
        mock_oauth.return_value = "ghp_oauth_token"

        result = get_best_github_auth(user)

        # Should return OAuth auth
        assert len(result) == 1
        assert result[0]["type"] == "oauth"
        assert result[0]["token"] == "ghp_oauth_token"

    @patch("holly.github_ext.auth_utils.get_github_app_token")
    @patch("holly.github_ext.auth_utils.get_github_oauth_token")
    def test_returns_none_when_no_auth(self, mock_oauth, mock_app):
        """Test that 'none' is returned when no auth available."""
        user = UserFactory()

        # Setup mocks
        mock_app.return_value = None
        mock_oauth.return_value = None

        result = get_best_github_auth(user)

        # Should return 'none' type
        assert len(result) == 1
        assert result[0]["type"] == "none"
        assert result[0]["token"] is None

    @patch("holly.github_ext.auth_utils.get_github_app_token")
    def test_multiple_github_app_installations(self, mock_app):
        """Test handling multiple GitHub App installations."""
        user = UserFactory()

        # Setup mocks with multiple installations
        mock_app.return_value = [
            ("ghs_app_token_1", "12345"),
            ("ghs_app_token_2", "67890"),
        ]

        result = get_best_github_auth(user)

        # Should return all GitHub App auths
        assert len(result) == 2
        assert result[0]["type"] == "github_app"
        assert result[0]["token"] == "ghs_app_token_1"
        assert result[0]["installation_id"] == "12345"
        assert result[1]["type"] == "github_app"
        assert result[1]["token"] == "ghs_app_token_2"
        assert result[1]["installation_id"] == "67890"


# ==============================================================================
# GitHub App Service Tests
# ==============================================================================


@pytest.mark.django_db
class TestGitHubAppService:
    """Test the GitHub App Service."""

    @patch("holly.github_ext.auth_utils.get_best_github_auth")
    def test_service_initialization(self, mock_auth):
        """Test service initialization with user."""
        user = UserFactory()
        mock_auth.return_value = [{"type": "github_app", "token": "test_token", "installation_id": "12345"}]

        service = GitHubAppService(user)

        assert service.user == user
        assert service.auth_infos == [{"type": "github_app", "token": "test_token"}]
        mock_auth.assert_called_once_with(user)

    @patch("holly.github_ext.services.github_app_service.requests.get")
    @patch("holly.github_ext.auth_utils.get_best_github_auth")
    def test_list_repositories_with_github_app(self, mock_auth, mock_get):
        """Test listing repositories using GitHub App token."""
        user = UserFactory()
        mock_auth.return_value = [
            {"type": "github_app", "token": "ghs_installation_token", "installation_id": "12345"}
        ]

        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_response.json.return_value = {
            "repositories": [
                {"id": 800000001, "name": "repo1", "full_name": "testuser/repo1"},
                {"id": 800000002, "name": "repo2", "full_name": "testuser/repo2"},
            ]
        }
        mock_get.return_value = mock_response

        service = GitHubAppService(user)
        repos = service.list_repositories()

        assert len(repos) == 2
        assert repos[0]["name"] == "repo1"
        assert repos[1]["name"] == "repo2"

        # Verify correct API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == "https://api.github.com/installation/repositories"
        assert call_args[1]["headers"]["Authorization"] == "token ghs_installation_token"

    @patch("holly.github_ext.services.github_app_service.requests.get")
    @patch("holly.github_ext.auth_utils.get_best_github_auth")
    def test_list_repositories_oauth_fallback(self, mock_auth, mock_get):
        """Test listing repositories falling back to OAuth token."""
        user = UserFactory()
        mock_auth.return_value = [{"type": "oauth", "token": "ghp_oauth_token"}]

        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_response.json.return_value = [
            {"id": 800000001, "name": "repo1", "full_name": "testuser/repo1"},
        ]
        mock_get.return_value = mock_response

        service = GitHubAppService(user)
        repos = service.list_repositories()

        assert len(repos) == 1
        assert repos[0]["name"] == "repo1"

        # Verify OAuth endpoint was called
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "user/repos" in call_args[0][0]
        assert call_args[1]["headers"]["Authorization"] == "Bearer ghp_oauth_token"

    @patch("holly.github_ext.services.github_app_service.requests.get")
    @patch("holly.github_ext.auth_utils.get_best_github_auth")
    def test_get_repository_by_id(self, mock_auth, mock_get):
        """Test getting a specific repository by GitHub ID."""
        user = UserFactory()
        mock_auth.return_value = [{"type": "github_app", "token": "ghs_token", "installation_id": "12345"}]

        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_response.json.return_value = {
            "id": 800000001,
            "name": "test-repo",
            "full_name": "testuser/test-repo",
            "private": False,
        }
        mock_get.return_value = mock_response

        service = GitHubAppService(user)
        repo = service.get_repository_by_id(800000001)

        assert repo is not None
        assert repo.id == 800000001
        assert repo.name == "test-repo"

        # Verify correct API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == "https://api.github.com/repositories/800000001"

    @patch("holly.github_ext.services.github_app_service.requests.get")
    @patch("holly.github_ext.auth_utils.get_best_github_auth")
    def test_get_repository(self, mock_auth, mock_get):
        """Test getting a repository by owner and name."""
        user = UserFactory()
        mock_auth.return_value = [{"type": "github_app", "token": "ghs_token", "installation_id": "12345"}]

        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_response.json.return_value = {
            "id": 800000001,
            "name": "test-repo",
            "owner": {"login": "testuser"},
        }
        mock_get.return_value = mock_response

        service = GitHubAppService(user)
        repo = service.get_repository("testuser", "test-repo")

        assert repo is not None
        assert repo["name"] == "test-repo"

        # Verify correct API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == "https://api.github.com/repos/testuser/test-repo"

    @patch("holly.github_ext.services.github_app_service.requests.post")
    @patch("holly.github_ext.auth_utils.get_best_github_auth")
    def test_create_pull_request(self, mock_auth, mock_post):
        """Test creating a pull request."""
        user = UserFactory()
        mock_auth.return_value = [{"type": "github_app", "token": "ghs_token", "installation_id": "12345"}]

        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.CREATED
        mock_response.json.return_value = {
            "id": 1,
            "number": 42,
            "title": "Test PR",
            "state": "open",
        }
        mock_post.return_value = mock_response

        service = GitHubAppService(user)
        pr = service.create_pull_request(
            owner="testuser",
            repo="test-repo",
            head_branch="holly/feature-test",
            base_branch="main",
            title="Test PR",
            body="Test description",
        )

        assert pr is not None
        assert pr["number"] == 42
        assert pr["title"] == "Test PR"

        # Verify correct API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://api.github.com/repos/testuser/test-repo/pulls"
        assert call_args[1]["json"]["head"] == "holly/feature-test"
        assert call_args[1]["json"]["base"] == "main"

    @patch("holly.github_ext.services.github_app_service.requests.get")
    @patch("holly.github_ext.auth_utils.get_best_github_auth")
    def test_list_repositories_api_error(self, mock_auth, mock_get):
        """Test handling of API errors when listing repositories."""
        user = UserFactory()
        mock_auth.return_value = [{"type": "github_app", "token": "ghs_token", "installation_id": "12345"}]

        # Mock error response
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.FORBIDDEN
        mock_response.text = "Resource not accessible"
        mock_get.return_value = mock_response

        service = GitHubAppService(user)
        repos = service.list_repositories()

        # Should return empty list on error
        assert repos == []

    @patch("holly.github_ext.services.github_app_service.requests.get")
    @patch("holly.github_ext.auth_utils.get_best_github_auth")
    def test_get_repository_not_found(self, mock_auth, mock_get):
        """Test getting a non-existent repository."""
        user = UserFactory()
        mock_auth.return_value = [{"type": "github_app", "token": "ghs_token", "installation_id": "12345"}]

        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.NOT_FOUND
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response

        service = GitHubAppService(user)
        repo = service.get_repository("testuser", "nonexistent-repo")

        assert repo is None

    @patch("holly.github_ext.auth_utils.get_best_github_auth")
    def test_service_with_no_auth(self, mock_auth):
        """Test service behavior with no authentication available."""
        user = UserFactory()
        mock_auth.return_value = [{"type": "none", "token": None}]

        service = GitHubAppService(user)
        repos = service.list_repositories()

        # Should return empty list when no auth available
        assert repos == []
