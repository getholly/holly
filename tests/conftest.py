import sys
from unittest.mock import MagicMock, Mock, patch

import django
import pytest
from django.test import Client
from loguru import logger
from rest_framework.test import APIClient

from holly.users.models import User

logger.debug(f"PYTHONPATH for tests/conftest.py: {sys.path}")

django.setup()

TEST_USER_EMAIL = "testuser@example.com"
TEST_ADMIN_EMAIL = "testsuperuser@example.com"
TEST_CUSTOMER_ID = "cus_RtRchEGiCEzkZ4"


# ============================================================================
# User Fixtures (existing, kept for compatibility)
# ============================================================================


@pytest.fixture
def user(db):
    return User.objects.create_user(email=TEST_USER_EMAIL, password="password")  # noqa: S106


@pytest.fixture
def customer(user):
    user.stripe_customer_id = TEST_CUSTOMER_ID
    user.save()
    return user


@pytest.fixture
def superuser():
    return User.objects.create_superuser(email="testsuperuser@example.com", password="password")  # noqa: S106


# ============================================================================
# Factory Fixtures
# ============================================================================


@pytest.fixture
def user_factory():
    """Import UserFactory for creating multiple users in tests."""
    from tests.factories import UserFactory

    return UserFactory


@pytest.fixture
def repository_factory():
    """Import RepositoryDetailFactory for creating repositories in tests."""
    from tests.factories import RepositoryDetailFactory

    return RepositoryDetailFactory


@pytest.fixture
def mission_factory():
    """Import MissionFactory for creating missions in tests."""
    from tests.factories import MissionFactory

    return MissionFactory


@pytest.fixture
def github_app_installation_factory():
    """Import GitHubAppInstallationFactory for creating installations in tests."""
    from tests.factories import GitHubAppInstallationFactory

    return GitHubAppInstallationFactory


# ============================================================================
# API Client Fixtures
# ============================================================================


@pytest.fixture
def api_client():
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def authenticated_api_client(user):
    """Return an authenticated API client."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def web_client():
    """Return a Django test client for web views."""
    return Client()


# ============================================================================
# Docker Mocking Fixtures
# ============================================================================


@pytest.fixture
def mock_docker_container():
    """Mock a Docker container object."""
    container = MagicMock()
    container.id = "test_container_12345"
    container.name = "holly-mission-test"
    container.status = "running"
    container.attrs = {
        "NetworkSettings": {
            "Networks": {
                "holly-network": {"IPAddress": "172.18.0.10"}
            }
        }
    }
    container.ports = {
        "8090/tcp": [{"HostIp": "127.0.0.1", "HostPort": "50001"}],
        "5900/tcp": [{"HostIp": "127.0.0.1", "HostPort": "50002"}],
        "6080/tcp": [{"HostIp": "127.0.0.1", "HostPort": "50003"}],
    }
    container.logs.return_value = b"Container started successfully"
    container.reload = MagicMock()
    container.stop = MagicMock()
    container.remove = MagicMock()
    return container


@pytest.fixture
def mock_docker_client(mock_docker_container):
    """Mock the Docker client."""
    docker_client = MagicMock()
    docker_client.containers.run.return_value = mock_docker_container
    docker_client.containers.get.return_value = mock_docker_container
    docker_client.containers.list.return_value = [mock_docker_container]
    docker_client.networks.get.return_value = MagicMock(name="holly-network")
    docker_client.images.pull.return_value = MagicMock()

    with patch("docker.from_env", return_value=docker_client):
        with patch("docker.DockerClient", return_value=docker_client):
            yield docker_client


# ============================================================================
# Hilly API Mocking Fixtures
# ============================================================================


@pytest.fixture
def mock_hilly_health_response():
    """Mock Hilly health check response."""
    return {"status": "healthy", "version": "1.0.0"}


@pytest.fixture
def mock_hilly_clone_response():
    """Mock Hilly git clone response."""
    return {
        "status": "success",
        "message": "Repository cloned successfully",
        "path": "/data/testuser/test-repo/main",
    }


@pytest.fixture
def mock_hilly_worktree_response():
    """Mock Hilly worktree creation response."""
    return {
        "status": "success",
        "message": "Worktree created successfully",
        "branch": "holly/feature-test",
        "path": "/data/testuser/test-repo/holly/feature-test",
    }


@pytest.fixture
def mock_hilly_commit_response():
    """Mock Hilly commit response."""
    return {
        "status": "success",
        "message": "Changes committed successfully",
        "commit_hash": "abc123def456",
    }


@pytest.fixture
def mock_hilly_push_response():
    """Mock Hilly push response."""
    return {
        "status": "success",
        "message": "Changes pushed successfully",
        "branch": "holly/feature-test",
    }


@pytest.fixture
def mock_hilly_api_client(
    mock_hilly_health_response,
    mock_hilly_clone_response,
    mock_hilly_worktree_response,
    mock_hilly_commit_response,
    mock_hilly_push_response,
):
    """Mock the Hilly REST API client."""
    mock_client = MagicMock()

    # Health check
    mock_client.get_health.return_value = mock_hilly_health_response

    # Git operations
    mock_client.clone_repository.return_value = mock_hilly_clone_response
    mock_client.create_worktree.return_value = mock_hilly_worktree_response
    mock_client.commit_changes.return_value = mock_hilly_commit_response
    mock_client.push_changes.return_value = mock_hilly_push_response

    # Conversation operations
    mock_client.send_message.return_value = {
        "role": "assistant",
        "content": "I've completed the requested changes.",
    }

    with patch("holly.holly.api.proxy.MCPProxyClient", return_value=mock_client):
        yield mock_client


# ============================================================================
# GitHub App API Mocking Fixtures
# ============================================================================


@pytest.fixture
def mock_github_installation_token():
    """Mock GitHub App installation token."""
    return {
        "token": "ghs_mock_installation_token_12345",
        "expires_at": "2025-12-31T23:59:59Z",
    }


@pytest.fixture
def mock_github_repositories():
    """Mock GitHub repositories list."""
    return [
        {
            "id": 800000001,
            "name": "test-repo-1",
            "full_name": "testuser/test-repo-1",
            "private": False,
            "description": "Test repository 1",
            "default_branch": "main",
        },
        {
            "id": 800000002,
            "name": "test-repo-2",
            "full_name": "testuser/test-repo-2",
            "private": True,
            "description": "Test repository 2",
            "default_branch": "main",
        },
    ]


@pytest.fixture
def mock_github_app_integration(mock_github_installation_token, mock_github_repositories):
    """Mock the GitHub App Integration service."""
    mock_integration = MagicMock()
    mock_integration.get_installation_access_token.return_value = mock_github_installation_token
    mock_integration.get_installation_repositories.return_value = mock_github_repositories

    with patch(
        "holly.github_ext.services.github_app_integration.GitHubAppIntegration", return_value=mock_integration
    ):
        yield mock_integration


# ============================================================================
# LLM Provider Mocking Fixtures
# ============================================================================


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(content="This is a test response from GPT-4.", role="assistant"),
            finish_reason="stop",
        )
    ]
    mock_response.usage = MagicMock(prompt_tokens=50, completion_tokens=10, total_tokens=60)
    return mock_response


@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="This is a test response from Claude.")]
    mock_response.usage = MagicMock(input_tokens=50, output_tokens=10)
    mock_response.stop_reason = "end_turn"
    return mock_response


@pytest.fixture
def mock_openai_client(mock_openai_response):
    """Mock OpenAI client."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_openai_response

    with patch("openai.OpenAI", return_value=mock_client):
        yield mock_client


@pytest.fixture
def mock_anthropic_client(mock_anthropic_response):
    """Mock Anthropic client."""
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_anthropic_response

    with patch("anthropic.Anthropic", return_value=mock_client):
        yield mock_client


# ============================================================================
# Redis Mocking Fixtures
# ============================================================================


@pytest.fixture
def mock_redis():
    """Mock Redis client for SSE event publishing."""
    mock_client = MagicMock()
    mock_client.publish.return_value = 1
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    mock_client.delete.return_value = 1

    with patch("redis.Redis", return_value=mock_client):
        yield mock_client


# ============================================================================
# Webhook Testing Fixtures
# ============================================================================


@pytest.fixture
def webhook_payload_init_success():
    """Mock webhook payload for successful container initialization."""
    return {
        "mission_id": "test-mission-uuid",
        "job_id": "init-job-123",
        "status": "success",
        "event_type": "container_init",
        "data": {
            "message": "Container initialized successfully",
            "repositories_cloned": 2,
        },
        "timestamp": "2025-11-11T12:00:00Z",
    }


@pytest.fixture
def webhook_payload_task_complete():
    """Mock webhook payload for task completion."""
    return {
        "mission_id": "test-mission-uuid",
        "job_id": "task-job-456",
        "status": "completed",
        "event_type": "task_complete",
        "data": {
            "message": "Task completed successfully",
            "files_changed": ["src/auth.py", "tests/test_auth.py"],
            "commits": ["abc123"],
        },
        "timestamp": "2025-11-11T12:05:00Z",
    }


@pytest.fixture
def webhook_payload_error():
    """Mock webhook payload for error scenario."""
    return {
        "mission_id": "test-mission-uuid",
        "job_id": "error-job-789",
        "status": "error",
        "event_type": "container_error",
        "data": {
            "error": "Failed to clone repository",
            "details": "Permission denied (publickey)",
        },
        "timestamp": "2025-11-11T12:01:00Z",
    }


# ============================================================================
# Sample Data Fixtures
# ============================================================================


@pytest.fixture
def sample_repo_tree():
    """Sample repository file tree structure."""
    return {
        "src": {
            "type": "dir",
            "children": {
                "main.py": {"type": "file", "size": 1500},
                "auth.py": {"type": "file", "size": 2000},
                "utils.py": {"type": "file", "size": 800},
            },
        },
        "tests": {
            "type": "dir",
            "children": {
                "test_main.py": {"type": "file", "size": 1000},
                "test_auth.py": {"type": "file", "size": 1200},
            },
        },
        "README.md": {"type": "file", "size": 500},
        ".gitignore": {"type": "file", "size": 200},
    }


@pytest.fixture
def sample_mission_env_vars():
    """Sample environment variables for mission container."""
    return {
        "MISSION_ID": "test-mission-uuid",
        "MISSION_REPOS": "testuser/repo1,testuser/repo2",
        "MISSION_BRANCH": "holly/feature-test",
        "AUTH_TOKEN": "ghs_mock_token_12345",
        "AUTH_TYPE": "github_app",
        "DJANGO_WEBHOOK_URL": "http://django:8000/_api/holly/webhooks/container-webhook",
        "GIT_EMAIL": "holly@example.com",
        "GIT_USER": "Holly AI",
    }
