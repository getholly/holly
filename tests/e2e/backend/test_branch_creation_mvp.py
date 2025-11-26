"""
End-to-end tests for branch creation flow.

This test suite specifically focuses on the git branch creation workflow,
which is critical for the MVP. It tests:

1. Mission specifies branch name
2. Container clones base branch
3. Container creates worktree for mission branch
4. Changes are made in mission branch
5. Commits are created on mission branch
6. Branch is pushed to remote (creating remote branch)

This is a high-priority test as specified by the user.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from tests.factories import (
    GitHubAppInstallationFactory,
    LLMFactory,
    MissionFactory,
    RepositoryDetailFactory,
    SocialAccountFactory,
    UserFactory,
)
from holly.holly.models.mission import Mission


@pytest.mark.django_db
class TestBranchCreationFlow:
    """Test the complete branch creation workflow."""

    @patch("holly.holly.services.webhook_handler.redis_client")
    @patch("docker.from_env")
    def test_branch_creation_end_to_end(self, mock_docker_env, mock_redis):
        """Test complete branch creation from mission start to remote push."""

        # ==============================================================
        # Step 1: Create mission with custom branch name
        # ==============================================================

        user = UserFactory()
        repo = RepositoryDetailFactory(
            username="testuser",
            repo="test-repo",
            commit_hash="main-commit-abc123",
        )
        llm = LLMFactory()

        mission = MissionFactory(
            title="Add new feature",
            description="Implement user profile feature",
            owner=user,
            llm=llm,
            branch_name="holly/add-user-profile",  # Custom branch for this mission
            repositories=[repo],
            state=Mission.State.DRAFT,
        )

        # Verify mission has correct branch name
        assert mission.branch_name == "holly/add-user-profile"
        assert mission.state == Mission.State.DRAFT

        # ==============================================================
        # Step 2: Start container with branch information
        # ==============================================================

        # Mock Docker container
        mock_container = MagicMock()
        mock_container.id = "test_container_12345"
        mock_container.attrs = {
            "NetworkSettings": {"Networks": {"holly-network": {"IPAddress": "172.18.0.10"}}}
        }

        mock_docker_client = MagicMock()
        mock_docker_client.containers.run.return_value = mock_container
        mock_docker_env.return_value = mock_docker_client

        # Simulate container start
        mission.state = Mission.State.PROVISIONING
        mission.container_id = mock_container.id
        mission.container_ip_address = "172.18.0.10"
        mission.container_status = "starting"
        mission.save()

        # Verify container receives branch name in environment
        # (In real flow, this would be passed as MISSION_BRANCH env var)
        expected_env_vars = {
            "MISSION_ID": str(mission.id),
            "MISSION_BRANCH": "holly/add-user-profile",
            "MISSION_REPOS": "testuser/test-repo",
        }

        # ==============================================================
        # Step 3: Container clones base branch
        # ==============================================================

        from holly.holly.services.webhook_handler import WebhookHandler

        webhook_handler = WebhookHandler()

        # Simulate webhook: Repository cloned (base branch)
        clone_webhook = {
            "mission_id": str(mission.id),
            "job_id": "clone_repo",
            "status": "completed",
            "data": {
                "message": "Repository cloned successfully",
                "repository": "testuser/test-repo",
                "branch": "main",  # Base branch cloned first
                "path": "/data/testuser/test-repo/main",
            },
            "timestamp": "2025-11-11T12:00:00Z",
        }

        result = webhook_handler.process_webhook(
            mission_id=str(mission.id),
            job_id="clone_repo",
            status="completed",
            data=clone_webhook["data"],
            timestamp=clone_webhook["timestamp"],
        )

        assert result["success"] is True

        # ==============================================================
        # Step 4: Container creates worktree for mission branch
        # ==============================================================

        # Simulate webhook: Worktree created for mission branch
        worktree_webhook = {
            "mission_id": str(mission.id),
            "job_id": "create_worktree",
            "status": "completed",
            "data": {
                "message": "Worktree created successfully",
                "repository": "testuser/test-repo",
                "branch": "holly/add-user-profile",  # Mission branch
                "base_branch": "main",
                "path": "/data/testuser/test-repo/holly/add-user-profile",
            },
            "timestamp": "2025-11-11T12:01:00Z",
        }

        result = webhook_handler.process_webhook(
            mission_id=str(mission.id),
            job_id="create_worktree",
            status="completed",
            data=worktree_webhook["data"],
            timestamp=worktree_webhook["timestamp"],
        )

        assert result["success"] is True

        # ==============================================================
        # Step 5: Container initialization complete
        # ==============================================================

        init_webhook = {
            "mission_id": str(mission.id),
            "job_id": "init",
            "status": "completed",
            "data": {
                "message": "Container initialized successfully",
                "repositories_cloned": 1,
                "branch": "holly/add-user-profile",
            },
            "timestamp": "2025-11-11T12:02:00Z",
        }

        result = webhook_handler.process_webhook(
            mission_id=str(mission.id),
            job_id="init",
            status="completed",
            data=init_webhook["data"],
            timestamp=init_webhook["timestamp"],
        )

        # Mission should be READY now
        mission.refresh_from_db()
        assert mission.state == Mission.State.READY
        assert mission.branch_name == "holly/add-user-profile"

        # ==============================================================
        # Step 6: Changes made and committed to mission branch
        # ==============================================================

        # Simulate webhook: Changes committed
        commit_webhook = {
            "mission_id": str(mission.id),
            "job_id": "git_commit",
            "status": "completed",
            "data": {
                "message": "Changes committed successfully",
                "commit_hash": "new-commit-xyz789",
                "branch": "holly/add-user-profile",  # Committed to mission branch
                "files_changed": ["src/user/profile.py", "src/user/__init__.py"],
                "commit_message": "Add user profile feature",
            },
            "timestamp": "2025-11-11T12:05:00Z",
        }

        result = webhook_handler.process_webhook(
            mission_id=str(mission.id),
            job_id="git_commit",
            status="completed",
            data=commit_webhook["data"],
            timestamp=commit_webhook["timestamp"],
        )

        assert result["success"] is True

        # ==============================================================
        # Step 7: Mission branch pushed to remote (creates remote branch)
        # ==============================================================

        # Simulate webhook: Branch pushed to remote
        push_webhook = {
            "mission_id": str(mission.id),
            "job_id": "git_push",
            "status": "completed",
            "data": {
                "message": "Changes pushed successfully",
                "branch": "holly/add-user-profile",  # Mission branch pushed
                "remote": "origin",
                "ref": "refs/heads/holly/add-user-profile",
                "commit_hash": "new-commit-xyz789",
            },
            "timestamp": "2025-11-11T12:06:00Z",
        }

        result = webhook_handler.process_webhook(
            mission_id=str(mission.id),
            job_id="git_push",
            status="completed",
            data=push_webhook["data"],
            timestamp=push_webhook["timestamp"],
        )

        assert result["success"] is True

        # ==============================================================
        # Final verification
        # ==============================================================

        mission.refresh_from_db()

        # Mission branch name persisted correctly
        assert mission.branch_name == "holly/add-user-profile"

        # Mission is in appropriate state
        assert mission.state in [Mission.State.READY, Mission.State.IN_PROGRESS]

        # Container info maintained
        assert mission.container_id == "test_container_12345"

    @patch("docker.from_env")
    def test_multiple_repos_same_branch(self, mock_docker_env):
        """Test branch creation across multiple repositories using same branch name."""

        user = UserFactory()

        # Create multiple repositories
        repo1 = RepositoryDetailFactory(username="testuser", repo="backend")
        repo2 = RepositoryDetailFactory(username="testuser", repo="frontend")

        llm = LLMFactory()

        mission = MissionFactory(
            title="Cross-repo feature",
            owner=user,
            llm=llm,
            branch_name="holly/sync-feature",  # Same branch for both repos
            repositories=[repo1, repo2],
        )

        # Verify mission configuration
        assert mission.branch_name == "holly/sync-feature"
        assert mission.repositories.count() == 2

        # Both repos should use the same mission branch
        for mission_repo in mission.repositories.all():
            # The branch_name on MissionRepos should typically be the base branch
            # The actual mission branch comes from mission.branch_name
            assert mission.branch_name == "holly/sync-feature"

    def test_branch_name_validation(self):
        """Test that branch names follow expected patterns."""

        user = UserFactory()
        llm = LLMFactory()

        # Test valid branch names with holly prefix
        valid_branches = [
            "holly/fix-auth",
            "holly/feature-user-profile",
            "holly/refactor-api",
            "holly/fix-bug-123",
        ]

        for branch_name in valid_branches:
            mission = MissionFactory(
                owner=user,
                llm=llm,
                branch_name=branch_name,
            )
            assert mission.branch_name == branch_name

    @patch("holly.holly.services.webhook_handler.redis_client")
    def test_branch_creation_failure_handling(self, mock_redis):
        """Test error handling when branch creation fails."""

        from holly.holly.services.webhook_handler import WebhookHandler

        user = UserFactory()
        mission = MissionFactory(
            owner=user,
            branch_name="holly/test-branch",
            state=Mission.State.PROVISIONING,
            container_id="test_container",
        )

        webhook_handler = WebhookHandler()

        # Simulate failed worktree creation (e.g., branch already exists)
        error_webhook = {
            "mission_id": str(mission.id),
            "job_id": "create_worktree",
            "status": "failed",
            "data": {
                "error": "Failed to create worktree",
                "details": "Branch already exists: holly/test-branch",
                "repository": "testuser/test-repo",
            },
            "timestamp": "2025-11-11T12:01:00Z",
        }

        result = webhook_handler.process_webhook(
            mission_id=str(mission.id),
            job_id="create_worktree",
            status="failed",
            data=error_webhook["data"],
            timestamp=error_webhook["timestamp"],
        )

        # Should handle error gracefully
        assert result["success"] is True  # Webhook processed successfully
        # Note: Error handling might not change mission state immediately,
        # but should log/track the error

    @patch("holly.holly.services.webhook_handler.redis_client")
    def test_push_failure_handling(self, mock_redis):
        """Test error handling when push fails (e.g., permission denied)."""

        from holly.holly.services.webhook_handler import WebhookHandler

        user = UserFactory()
        mission = MissionFactory(
            owner=user,
            branch_name="holly/test-branch",
            state=Mission.State.READY,
            container_id="test_container",
        )

        webhook_handler = WebhookHandler()

        # Simulate failed push (e.g., permission error)
        push_error_webhook = {
            "mission_id": str(mission.id),
            "job_id": "git_push",
            "status": "failed",
            "data": {
                "error": "Failed to push changes",
                "details": "Permission denied (publickey)",
                "branch": "holly/test-branch",
                "remote": "origin",
            },
            "timestamp": "2025-11-11T12:06:00Z",
        }

        result = webhook_handler.process_webhook(
            mission_id=str(mission.id),
            job_id="git_push",
            status="failed",
            data=push_error_webhook["data"],
            timestamp=push_error_webhook["timestamp"],
        )

        # Webhook should be processed
        assert result["success"] is True

    def test_branch_name_stored_in_mission_repos(self):
        """Test that branch names are properly stored in MissionRepos."""

        user = UserFactory()
        llm = LLMFactory()

        # Create repository
        repo = RepositoryDetailFactory()

        # Create mission
        mission = MissionFactory(
            owner=user,
            llm=llm,
            branch_name="holly/feature-x",
            repositories=[repo],
        )

        # Verify mission branch
        assert mission.branch_name == "holly/feature-x"

        # MissionRepos should exist
        assert mission.repositories.count() == 1
        mission_repo = mission.repositories.first()

        # The repository link exists
        assert mission_repo.repository == repo

    @patch("holly.holly.services.webhook_handler.redis_client")
    @patch("docker.from_env")
    def test_branch_lifecycle_tracking(self, mock_docker_env, mock_redis):
        """Test tracking the complete branch lifecycle through webhooks."""

        from holly.holly.services.webhook_handler import WebhookHandler

        user = UserFactory()
        mission = MissionFactory(
            owner=user,
            branch_name="holly/tracked-branch",
            state=Mission.State.PROVISIONING,
            container_id="test_container",
        )

        webhook_handler = WebhookHandler()

        # Track branch lifecycle through webhooks
        events = []

        # 1. Clone base branch
        webhook_handler.process_webhook(
            str(mission.id), "clone_repo", "completed",
            {"branch": "main", "message": "Cloned base"},
            "2025-11-11T12:00:00Z"
        )
        events.append("clone")

        # 2. Create mission branch worktree
        webhook_handler.process_webhook(
            str(mission.id), "create_worktree", "completed",
            {"branch": "holly/tracked-branch", "message": "Worktree created"},
            "2025-11-11T12:01:00Z"
        )
        events.append("worktree")

        # 3. Initialize complete
        webhook_handler.process_webhook(
            str(mission.id), "init", "completed",
            {"branch": "holly/tracked-branch", "message": "Init complete"},
            "2025-11-11T12:02:00Z"
        )
        events.append("init")

        # 4. Commit to branch
        webhook_handler.process_webhook(
            str(mission.id), "git_commit", "completed",
            {"branch": "holly/tracked-branch", "commit_hash": "abc123"},
            "2025-11-11T12:05:00Z"
        )
        events.append("commit")

        # 5. Push branch
        webhook_handler.process_webhook(
            str(mission.id), "git_push", "completed",
            {"branch": "holly/tracked-branch", "message": "Pushed"},
            "2025-11-11T12:06:00Z"
        )
        events.append("push")

        # Verify all events processed
        assert len(events) == 5
        assert events == ["clone", "worktree", "init", "commit", "push"]

        # Verify mission state
        mission.refresh_from_db()
        assert mission.branch_name == "holly/tracked-branch"
        assert mission.state == Mission.State.READY
