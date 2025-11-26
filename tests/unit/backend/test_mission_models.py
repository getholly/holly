"""
Unit tests for Mission models.

Tests mission state transitions, repository relationships, access control,
and mission lifecycle management.
"""

import pytest
from django.contrib.auth import get_user_model

from tests.factories import (
    KnowledgeFactory,
    LLMFactory,
    MissionFactory,
    MissionReposFactory,
    RepositoryDetailFactory,
    ToolsFactory,
    UserFactory,
)
from holly.holly.models.mission import Mission, MissionRepos

User = get_user_model()


# ==============================================================================
# MissionRepos Model Tests
# ==============================================================================


@pytest.mark.django_db
class TestMissionReposModel:
    """Test the MissionRepos junction model."""

    def test_create_mission_repos(self):
        """Test creating a MissionRepos link."""
        repo = RepositoryDetailFactory()
        mission_repo = MissionReposFactory(
            repository=repo,
            branch_name="main",
        )

        assert mission_repo.id is not None
        assert mission_repo.repository == repo
        assert mission_repo.branch_name == "main"

    def test_different_branches_per_mission(self):
        """Test that different missions can use different branches of the same repo."""
        repo = RepositoryDetailFactory()

        mission_repo1 = MissionReposFactory(repository=repo, branch_name="main")
        mission_repo2 = MissionReposFactory(repository=repo, branch_name="develop")

        assert mission_repo1.repository == mission_repo2.repository
        assert mission_repo1.branch_name != mission_repo2.branch_name


# ==============================================================================
# Mission Model Basic Tests
# ==============================================================================


@pytest.mark.django_db
class TestMissionModel:
    """Test the Mission model."""

    def test_create_mission(self):
        """Test creating a basic mission."""
        user = UserFactory()
        llm = LLMFactory()

        mission = MissionFactory(
            title="Test Mission",
            description="Fix authentication bug",
            owner=user,
            branch_name="holly/fix-auth",
            llm=llm,
        )

        assert mission.id is not None
        assert mission.title == "Test Mission"
        assert mission.description == "Fix authentication bug"
        assert mission.owner == user
        assert mission.branch_name == "holly/fix-auth"
        assert mission.llm == llm
        assert mission.state == Mission.State.DRAFT

    def test_mission_string_representation(self):
        """Test mission string representation."""
        mission = MissionFactory(title="Test Mission", state=Mission.State.READY)

        assert str(mission) == "Test Mission (Ready)"

    def test_mission_default_state(self):
        """Test that new missions start in DRAFT state."""
        mission = MissionFactory()

        assert mission.state == Mission.State.DRAFT

    def test_mission_with_repositories(self):
        """Test mission with multiple repositories."""
        repos = [RepositoryDetailFactory() for _ in range(3)]

        mission = MissionFactory(repositories=repos)

        assert mission.repositories.count() == 3

    def test_mission_with_collaborators(self):
        """Test mission with collaborators."""
        owner = UserFactory()
        collaborators = [UserFactory() for _ in range(2)]

        mission = MissionFactory(owner=owner, collaborators=collaborators)

        assert mission.owner == owner
        assert mission.collaborators.count() == 2
        assert all(c in mission.collaborators.all() for c in collaborators)

    def test_mission_with_knowledge_items(self):
        """Test mission with knowledge items."""
        owner = UserFactory()
        knowledge = [KnowledgeFactory(owner=owner) for _ in range(2)]

        mission = MissionFactory(owner=owner, knowledge_items=knowledge)

        assert mission.knowledge_items.count() == 2

    def test_mission_with_tools(self):
        """Test mission with tools."""
        owner = UserFactory()
        tools = [ToolsFactory(owner=owner)]

        mission = MissionFactory(owner=owner, tools=tools)

        assert mission.tools.count() == 1


# ==============================================================================
# Mission State Transition Tests
# ==============================================================================


@pytest.mark.django_db
class TestMissionStateTransitions:
    """Test mission state transitions."""

    def test_initial_state_is_draft(self):
        """Test that missions start in DRAFT state."""
        mission = MissionFactory()

        assert mission.state == Mission.State.DRAFT

    def test_transition_to_provisioning(self):
        """Test transitioning from DRAFT to PROVISIONING."""
        mission = MissionFactory(state=Mission.State.DRAFT)

        mission.state = Mission.State.PROVISIONING
        mission.save()

        mission.refresh_from_db()
        assert mission.state == Mission.State.PROVISIONING

    def test_transition_to_ready(self):
        """Test transitioning from PROVISIONING to READY."""
        mission = MissionFactory(state=Mission.State.PROVISIONING)

        mission.state = Mission.State.READY
        mission.save()

        mission.refresh_from_db()
        assert mission.state == Mission.State.READY

    def test_transition_to_in_progress(self):
        """Test transitioning from READY to IN_PROGRESS."""
        mission = MissionFactory(state=Mission.State.READY)

        mission.state = Mission.State.IN_PROGRESS
        mission.save()

        mission.refresh_from_db()
        assert mission.state == Mission.State.IN_PROGRESS

    def test_mark_as_completed(self):
        """Test marking mission as completed."""
        mission = MissionFactory(state=Mission.State.IN_PROGRESS)

        mission.mark_as_completed()

        mission.refresh_from_db()
        assert mission.state == Mission.State.COMPLETED

    def test_mark_as_aborted(self):
        """Test marking mission as aborted."""
        mission = MissionFactory(state=Mission.State.IN_PROGRESS)

        mission.mark_as_aborted()

        mission.refresh_from_db()
        assert mission.state == Mission.State.ABORTED

    def test_transition_to_error(self):
        """Test transitioning to ERROR state."""
        mission = MissionFactory(state=Mission.State.PROVISIONING)

        mission.state = Mission.State.ERROR
        mission.save()

        mission.refresh_from_db()
        assert mission.state == Mission.State.ERROR

    def test_is_active_returns_true_for_in_progress(self):
        """Test is_active returns True for IN_PROGRESS missions."""
        mission = MissionFactory(state=Mission.State.IN_PROGRESS)

        assert mission.is_active() is True

    def test_is_active_returns_false_for_other_states(self):
        """Test is_active returns False for non-IN_PROGRESS states."""
        for state in [
            Mission.State.DRAFT,
            Mission.State.PROVISIONING,
            Mission.State.READY,
            Mission.State.COMPLETED,
            Mission.State.ABORTED,
            Mission.State.ERROR,
        ]:
            mission = MissionFactory(state=state)
            assert mission.is_active() is False


# ==============================================================================
# Mission Container Management Tests
# ==============================================================================


@pytest.mark.django_db
class TestMissionContainerManagement:
    """Test mission container-related fields."""

    def test_mission_without_container(self):
        """Test mission before container is started."""
        mission = MissionFactory()

        assert mission.container_id is None
        assert mission.container_ip_address is None
        assert mission.container_status is None
        assert mission.container_started_at is None

    def test_mission_with_container_info(self):
        """Test mission with container information."""
        from datetime import datetime

        mission = MissionFactory(
            container_id="test_container_123",
            container_ip_address="172.18.0.10",
            container_status="ready",
        )
        mission.container_started_at = datetime.now()
        mission.save()

        assert mission.container_id == "test_container_123"
        assert mission.container_ip_address == "172.18.0.10"
        assert mission.container_status == "ready"
        assert mission.container_started_at is not None

    def test_container_status_choices(self):
        """Test valid container status choices."""
        valid_statuses = ["starting", "ready", "error", "stopped"]

        for status in valid_statuses:
            mission = MissionFactory(container_status=status)
            assert mission.container_status == status

    def test_init_job_tracking(self):
        """Test init job ID tracking."""
        mission = MissionFactory(init_job_id="init-job-123")

        assert mission.init_job_id == "init-job-123"

    def test_active_jobs_tracking(self):
        """Test active jobs JSONField."""
        mission = MissionFactory()

        # Should start empty
        assert mission.active_jobs == []

        # Can add jobs
        mission.active_jobs = ["job-1", "job-2"]
        mission.save()

        mission.refresh_from_db()
        assert len(mission.active_jobs) == 2
        assert "job-1" in mission.active_jobs


# ==============================================================================
# Mission Access Control Tests
# ==============================================================================


@pytest.mark.django_db
class TestMissionAccessControl:
    """Test mission access control."""

    @pytest.mark.asyncio
    async def test_owner_can_access_mission(self):
        """Test that mission owner can access the mission."""
        owner = UserFactory()
        mission = MissionFactory(owner=owner)

        can_access = await mission.can_be_accessed_by(owner)

        assert can_access is True

    @pytest.mark.asyncio
    async def test_collaborator_can_access_mission(self):
        """Test that collaborators can access the mission."""
        owner = UserFactory()
        collaborator = UserFactory()
        mission = MissionFactory(owner=owner, collaborators=[collaborator])

        can_access = await mission.can_be_accessed_by(collaborator)

        assert can_access is True

    @pytest.mark.asyncio
    async def test_non_collaborator_cannot_access_mission(self):
        """Test that non-collaborators cannot access the mission."""
        owner = UserFactory()
        other_user = UserFactory()
        mission = MissionFactory(owner=owner)

        can_access = await mission.can_be_accessed_by(other_user)

        assert can_access is False

    @pytest.mark.asyncio
    async def test_multiple_collaborators_can_access(self):
        """Test that multiple collaborators can access the mission."""
        owner = UserFactory()
        collaborators = [UserFactory() for _ in range(3)]
        mission = MissionFactory(owner=owner, collaborators=collaborators)

        for collaborator in collaborators:
            can_access = await mission.can_be_accessed_by(collaborator)
            assert can_access is True


# ==============================================================================
# Mission Summary and Helper Methods Tests
# ==============================================================================


@pytest.mark.django_db
class TestMissionHelperMethods:
    """Test mission helper methods."""

    def test_get_summary(self):
        """Test getting mission summary."""
        owner = UserFactory()
        repos = [RepositoryDetailFactory(repo="test-repo-1"), RepositoryDetailFactory(repo="test-repo-2")]
        mission = MissionFactory(
            title="Test Mission",
            owner=owner,
            state=Mission.State.READY,
            branch_name="holly/test",
            repositories=repos,
        )

        summary = mission.get_summary()

        assert summary["title"] == "Test Mission"
        assert summary["state"] == Mission.State.READY
        assert summary["owner"] == "testuser"
        assert summary["branch_name"] == "holly/test"
        assert "created_at" in summary
        assert "updated_at" in summary

    def test_get_tools(self):
        """Test getting mission tools configuration."""
        owner = UserFactory()
        tool = ToolsFactory(
            owner=owner,
            config={
                "file_editor": {"enabled": True, "description": "Edit files"},
                "terminal": {"enabled": True, "description": "Run commands"},
            },
        )
        mission = MissionFactory(owner=owner, tools=[tool])

        tools = mission.get_tools()

        assert "file_editor" in tools
        assert "terminal" in tools
        assert tools["file_editor"]["enabled"] is True

    def test_get_tools_with_multiple_tools(self):
        """Test getting tools when multiple tool configs exist."""
        owner = UserFactory()
        tool1 = ToolsFactory(owner=owner, config={"file_editor": {"enabled": True}})
        tool2 = ToolsFactory(owner=owner, config={"terminal": {"enabled": True}})
        mission = MissionFactory(owner=owner, tools=[tool1, tool2])

        tools = mission.get_tools()

        assert "file_editor" in tools
        assert "terminal" in tools

    @pytest.mark.asyncio
    async def test_aget_tools(self):
        """Test async version of get_tools."""
        owner = UserFactory()
        tool = ToolsFactory(owner=owner, config={"file_editor": {"enabled": True}})
        mission = MissionFactory(owner=owner, tools=[tool])

        tools = await mission.aget_tools()

        assert "file_editor" in tools


# ==============================================================================
# Mission Requirements Tests
# ==============================================================================


@pytest.mark.django_db
class TestMissionRequirements:
    """Test mission requirements JSONField."""

    def test_mission_with_empty_requirements(self):
        """Test mission with empty requirements."""
        mission = MissionFactory()

        assert mission.requirements == {}

    def test_mission_with_requirements(self):
        """Test mission with custom requirements."""
        requirements = {
            "python_version": "3.11",
            "dependencies": ["django", "pytest"],
            "env_vars": {"DEBUG": "false"},
        }
        mission = MissionFactory(requirements=requirements)

        assert mission.requirements["python_version"] == "3.11"
        assert "django" in mission.requirements["dependencies"]

    def test_update_requirements(self):
        """Test updating mission requirements."""
        mission = MissionFactory(requirements={})

        mission.requirements = {"python_version": "3.12"}
        mission.save()

        mission.refresh_from_db()
        assert mission.requirements["python_version"] == "3.12"


# ==============================================================================
# Mission Ordering and Timestamps Tests
# ==============================================================================


@pytest.mark.django_db
class TestMissionOrderingAndTimestamps:
    """Test mission ordering and timestamp behavior."""

    def test_missions_ordered_by_updated_at(self):
        """Test that missions are ordered by updated_at descending."""
        mission1 = MissionFactory(title="First")
        mission2 = MissionFactory(title="Second")
        mission3 = MissionFactory(title="Third")

        # Update mission1 to make it most recent
        mission1.description = "Updated"
        mission1.save()

        missions = Mission.objects.all()

        # First mission should be the most recently updated
        assert missions[0].id == mission1.id

    def test_created_at_auto_set(self):
        """Test that created_at is automatically set."""
        mission = MissionFactory()

        assert mission.created_at is not None

    def test_updated_at_auto_updates(self):
        """Test that updated_at is automatically updated on save."""
        mission = MissionFactory()
        original_updated = mission.updated_at

        # Modify and save
        mission.description = "Updated description"
        mission.save()

        mission.refresh_from_db()
        assert mission.updated_at > original_updated
