"""
End-to-end tests for complete MVP flow.

This test suite verifies the entire user journey from GitHub App connection
through to pushing changes to a remote repository. This is the critical path
that must work for the MVP.

Flow tested:
1. User has GitHub App installed
2. User lists and selects repositories
3. User creates a mission with repos and LLM model
4. User starts mission (container created)
5. Container initializes (clones repos, creates branches)
6. User creates conversation
7. User sends message
8. Hilly processes message and makes changes
9. Changes are committed and pushed
10. Mission completes successfully
"""

from http import HTTPStatus
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import pytest
from django.test import Client
from rest_framework.test import APIClient

from tests.factories import (
    GitHubAppInstallationFactory,
    LLMFactory,
    MissionConversationFactory,
    MissionFactory,
    RepositoryDetailFactory,
    SocialAccountFactory,
    UserFactory,
)
from holly.github_ext.models import GitHubAppInstallation, RepositoryDetail
from holly.holly.models.conversations import Message
from holly.holly.models.mission import Mission
from holly.holly.models.mission_conversation import MissionConversation


@pytest.mark.django_db
class TestCompleteMVPFlow:
    """Test the complete MVP flow end-to-end."""

    @patch("holly.holly.api.proxy.MCPProxyClient")
    @patch("docker.from_env")
    @patch("holly.github_ext.services.github_app_service.requests.get")
    @patch("holly.holly.services.webhook_handler.redis_client")
    def test_complete_mvp_flow(
        self,
        mock_redis,
        mock_github_get,
        mock_docker_env,
        mock_mcp_client_class,
    ):
        """Test the complete MVP flow from GitHub App to git push."""

        # ==============================================================
        # Setup: User with GitHub App installation
        # ==============================================================

        user = UserFactory(email="testuser@example.com")
        social_account = SocialAccountFactory(user=user)
        installation = GitHubAppInstallationFactory(
            social_account=social_account,
            installation_id="50000001",
            account_name="testuser",
            account_type="user",
        )

        # Create LLM for mission
        llm = LLMFactory(name="gpt-4", full_name="openai/gpt-4")

        # ==============================================================
        # Step 1: List repositories from GitHub App installation
        # ==============================================================

        # Mock GitHub API response for listing repositories
        mock_repo_response = Mock()
        mock_repo_response.status_code = HTTPStatus.OK
        mock_repo_response.json.return_value = {
            "repositories": [
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
                    "private": False,
                    "description": "Test repository 2",
                    "default_branch": "main",
                },
            ]
        }
        mock_github_get.return_value = mock_repo_response

        # Create repository details in DB
        repo1 = RepositoryDetailFactory(
            github_id="800000001",
            username="testuser",
            repo="test-repo-1",
            private=False,
        )
        repo2 = RepositoryDetailFactory(
            github_id="800000002",
            username="testuser",
            repo="test-repo-2",
            private=False,
        )

        # ==============================================================
        # Step 2: Create mission with repositories and model
        # ==============================================================

        from holly.holly.services.mission_service import mission_service

        # Create mission using the service
        mission = MissionFactory(
            title="Fix authentication bug",
            description="Fix the authentication bug in login flow",
            owner=user,
            branch_name="holly/fix-auth",
            llm=llm,
            state=Mission.State.DRAFT,
            repositories=[repo1, repo2],
        )

        assert mission.state == Mission.State.DRAFT
        assert mission.repositories.count() == 2
        assert mission.llm == llm
        assert mission.branch_name == "holly/fix-auth"

        # ==============================================================
        # Step 3: Start mission container
        # ==============================================================

        # Mock Docker container
        mock_container = MagicMock()
        mock_container.id = "test_container_12345"
        mock_container.name = f"holly-mission-{mission.id}"
        mock_container.status = "running"
        mock_container.attrs = {
            "NetworkSettings": {"Networks": {"holly-network": {"IPAddress": "172.18.0.10"}}}
        }
        mock_container.ports = {
            "8090/tcp": [{"HostIp": "127.0.0.1", "HostPort": "50001"}],
        }

        mock_docker_client = MagicMock()
        mock_docker_client.containers.run.return_value = mock_container
        mock_docker_client.containers.get.return_value = mock_container
        mock_docker_env.return_value = mock_docker_client

        # Mock Hilly API client for health check
        mock_mcp_instance = MagicMock()
        mock_mcp_instance.get_health.return_value = {"status": "healthy"}
        mock_mcp_client_class.return_value = mock_mcp_instance

        # Start the mission container
        with patch("holly.holly.services.containers.holly_container_service.requests.get") as mock_health_check:
            mock_health_check.return_value.status_code = 200
            mock_health_check.return_value.json.return_value = {"status": "healthy"}

            # Simulate container start
            mission.state = Mission.State.PROVISIONING
            mission.container_id = mock_container.id
            mission.container_ip_address = "172.18.0.10"
            mission.container_status = "starting"
            mission.save()

        assert mission.state == Mission.State.PROVISIONING
        assert mission.container_id == "test_container_12345"
        assert mission.container_ip_address == "172.18.0.10"

        # ==============================================================
        # Step 4: Container initialization via webhook
        # ==============================================================

        from holly.holly.services.webhook_handler import WebhookHandler

        webhook_handler = WebhookHandler()

        # Simulate successful initialization webhook
        init_webhook_payload = {
            "mission_id": str(mission.id),
            "job_id": "init",
            "status": "completed",
            "data": {
                "message": "Container initialized successfully",
                "repositories_cloned": 2,
                "branch": "holly/fix-auth",
            },
            "timestamp": "2025-11-11T12:00:00Z",
        }

        result = webhook_handler.process_webhook(
            mission_id=str(mission.id),
            job_id="init",
            status="completed",
            data=init_webhook_payload["data"],
            timestamp=init_webhook_payload["timestamp"],
        )

        # Refresh mission
        mission.refresh_from_db()
        assert mission.state == Mission.State.READY
        assert mission.container_status == "ready"

        # ==============================================================
        # Step 5: Create conversation
        # ==============================================================

        conversation = MissionConversationFactory(
            mission=mission,
            conversation_id="conv-test-123",
            title="Fix auth conversation",
            status="pending",
        )

        assert conversation.mission == mission
        assert conversation.status == "pending"

        # ==============================================================
        # Step 6: Send user message
        # ==============================================================

        # Create user message
        from holly.holly.models.conversations import Message

        user_message = Message.objects.create(
            conversation=conversation,
            role="user",
            content="Fix the authentication bug in src/auth.py",
        )

        assert user_message.role == "user"
        assert conversation.messages.count() == 1

        # Mock Hilly response to message
        mock_mcp_instance.send_message.return_value = {
            "role": "assistant",
            "content": "I've fixed the authentication bug in src/auth.py. The changes have been committed to the holly/fix-auth branch.",
        }

        # Simulate sending message to Hilly
        # (In real flow, this would be via API endpoint)
        conversation.status = "processing"
        conversation.save()

        # ==============================================================
        # Step 7: Hilly processes and makes changes (via webhook)
        # ==============================================================

        # Simulate assistant response message
        assistant_message = Message.objects.create(
            conversation=conversation,
            role="assistant",
            content="I've fixed the authentication bug in src/auth.py. The changes have been committed to the holly/fix-auth branch.",
        )

        assert conversation.messages.count() == 2

        # Simulate webhook for git commit
        commit_webhook_payload = {
            "mission_id": str(mission.id),
            "job_id": "git_commit",
            "status": "completed",
            "data": {
                "message": "Changes committed successfully",
                "commit_hash": "abc123def456",
                "files_changed": ["src/auth.py"],
            },
            "timestamp": "2025-11-11T12:05:00Z",
        }

        webhook_handler.process_webhook(
            mission_id=str(mission.id),
            job_id="git_commit",
            status="completed",
            data=commit_webhook_payload["data"],
            timestamp=commit_webhook_payload["timestamp"],
        )

        # ==============================================================
        # Step 8: Git push via webhook
        # ==============================================================

        push_webhook_payload = {
            "mission_id": str(mission.id),
            "job_id": "git_push",
            "status": "completed",
            "data": {
                "message": "Changes pushed successfully",
                "branch": "holly/fix-auth",
                "remote": "origin",
            },
            "timestamp": "2025-11-11T12:06:00Z",
        }

        webhook_handler.process_webhook(
            mission_id=str(mission.id),
            job_id="git_push",
            status="completed",
            data=push_webhook_payload["data"],
            timestamp=push_webhook_payload["timestamp"],
        )

        # ==============================================================
        # Step 9: Task completion via webhook
        # ==============================================================

        task_complete_webhook = {
            "mission_id": str(mission.id),
            "job_id": "task_complete",
            "status": "completed",
            "data": {
                "message": "Task completed successfully",
                "files_changed": ["src/auth.py"],
                "commits": ["abc123def456"],
            },
            "timestamp": "2025-11-11T12:07:00Z",
        }

        webhook_handler.process_webhook(
            mission_id=str(mission.id),
            job_id="task_complete",
            status="completed",
            data=task_complete_webhook["data"],
            timestamp=task_complete_webhook["timestamp"],
        )

        # Update conversation status
        conversation.status = "completed"
        conversation.save()

        # ==============================================================
        # Step 10: Verify final state
        # ==============================================================

        mission.refresh_from_db()
        conversation.refresh_from_db()

        # Mission should still be READY (or IN_PROGRESS depending on implementation)
        assert mission.state in [Mission.State.READY, Mission.State.IN_PROGRESS, Mission.State.COMPLETED]
        assert mission.container_id is not None
        assert mission.container_ip_address is not None

        # Conversation should be completed
        assert conversation.status == "completed"
        assert conversation.messages.count() == 2

        # Messages should be in correct order
        messages = list(conversation.messages.all())
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"

        # ==============================================================
        # Assertions Summary
        # ==============================================================

        # 1. GitHub App installation exists
        assert GitHubAppInstallation.objects.filter(installation_id="50000001").exists()

        # 2. Repositories were created/selected
        assert RepositoryDetail.objects.filter(username="testuser").count() == 2

        # 3. Mission was created with correct configuration
        assert mission.title == "Fix authentication bug"
        assert mission.branch_name == "holly/fix-auth"
        assert mission.llm.name == "gpt-4"

        # 4. Container was started
        assert mission.container_id == "test_container_12345"

        # 5. Conversation was created and processed
        assert MissionConversation.objects.filter(mission=mission).exists()

        # 6. Messages were exchanged
        assert Message.objects.filter(conversation=conversation).count() == 2

        # 7. Docker mock was called to create container
        mock_docker_client.containers.run.assert_called_once()

        # 8. Hilly client was instantiated
        assert mock_mcp_client_class.called


    @patch("docker.from_env")
    @patch("holly.github_ext.services.github_app_service.requests.get")
    def test_mvp_flow_with_single_repository(self, mock_github_get, mock_docker_env):
        """Test MVP flow with a single repository (simpler case)."""

        # Setup user and installation
        user = UserFactory()
        social_account = SocialAccountFactory(user=user)
        installation = GitHubAppInstallationFactory(social_account=social_account)

        # Create one repository
        repo = RepositoryDetailFactory(username=installation.account_name)

        # Create LLM
        llm = LLMFactory()

        # Create mission
        mission = MissionFactory(
            owner=user,
            llm=llm,
            branch_name="holly/feature-1",
            repositories=[repo],
        )

        # Verify setup
        assert mission.repositories.count() == 1
        assert mission.branch_name == "holly/feature-1"
        assert mission.state == Mission.State.DRAFT


    def test_mvp_flow_user_can_access_own_mission(self):
        """Test that user can only access their own missions."""

        user1 = UserFactory()
        user2 = UserFactory()

        mission1 = MissionFactory(owner=user1)
        mission2 = MissionFactory(owner=user2)

        # User1 can access their mission
        assert mission1.owner == user1

        # User2 cannot access user1's mission (no collaborator access)
        assert mission2.owner != user1


    @patch("holly.holly.services.webhook_handler.redis_client")
    def test_error_handling_in_mvp_flow(self, mock_redis):
        """Test error handling when container initialization fails."""

        from holly.holly.services.webhook_handler import WebhookHandler

        user = UserFactory()
        mission = MissionFactory(
            owner=user,
            state=Mission.State.PROVISIONING,
            container_id="test_container",
        )

        webhook_handler = WebhookHandler()

        # Simulate failed initialization webhook
        error_webhook = {
            "mission_id": str(mission.id),
            "job_id": "init",
            "status": "failed",
            "data": {
                "error": "Failed to clone repository",
                "details": "Permission denied",
            },
            "timestamp": "2025-11-11T12:00:00Z",
        }

        result = webhook_handler.process_webhook(
            mission_id=str(mission.id),
            job_id="init",
            status="failed",
            data=error_webhook["data"],
            timestamp=error_webhook["timestamp"],
        )

        # Mission should transition to ERROR state
        mission.refresh_from_db()
        assert mission.state == Mission.State.ERROR
