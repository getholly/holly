from unittest.mock import MagicMock, patch

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from holly.github_ext.models import RepositoryDetail
from holly.holly.models.mission import Mission, MissionConversation
from holly.holly.services.mission_service import MissionService

User = get_user_model()


class MissionModelTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username="testuser", password="testpass123", email="test@example.com")

        # Create a test repo
        self.repo = RepositoryDetail.objects.create(username="testorg", repo_name="testrepo", user=self.user)

        # Create a test mission
        self.mission = Mission.objects.create(
            title="Test Mission",
            description="Test mission description",
            branch_name="feature/test-branch",
            owner=self.user,
            state=Mission.State.DRAFT,
        )

        # Add the repo to the mission
        self.mission.repositories.add(self.repo)

    def test_mission_creation(self):
        """Test that a mission can be created with appropriate fields"""
        assert self.mission.title == "Test Mission"
        assert self.mission.description == "Test mission description"
        assert self.mission.branch_name == "feature/test-branch"
        assert self.mission.owner == self.user
        assert self.mission.state == Mission.State.DRAFT
        assert self.mission.repositories.filter(id=self.repo.id).exists()

    def test_mission_string_representation(self):
        """Test the string representation of the mission"""
        expected_string = "Test Mission (Draft)"
        assert str(self.mission) == expected_string

    def test_is_active_method(self):
        """Test the is_active method"""
        assert not self.mission.is_active()

        # Update to in progress
        self.mission.state = Mission.State.IN_PROGRESS
        self.mission.save()
        assert self.mission.is_active()

        # Update to completed
        self.mission.state = Mission.State.COMPLETED
        self.mission.save()
        assert not self.mission.is_active()

    def test_can_be_accessed_by_method(self):
        """Test the can_be_accessed_by method"""
        # Owner should have access
        assert async_to_sync(self.mission.can_be_accessed_by)(self.user)

        # Create another user
        other_user = User.objects.create_user(username="otheruser", password="testpass123", email="other@example.com")

        # Other user should not have access
        assert not async_to_sync(self.mission.can_be_accessed_by)(other_user)

        # Add other user as collaborator
        self.mission.collaborators.add(other_user)

        # Now they should have access
        assert async_to_sync(self.mission.can_be_accessed_by)(other_user)

    def test_mark_as_completed_method(self):
        """Test the mark_as_completed method"""
        self.mission.mark_as_completed()
        assert self.mission.state == Mission.State.COMPLETED

    def test_mark_as_aborted_method(self):
        """Test the mark_as_aborted method"""
        self.mission.mark_as_aborted()
        assert self.mission.state == Mission.State.ABORTED

    def test_get_summary_method(self):
        """Test the get_summary method"""
        summary = self.mission.get_summary()
        assert summary["id"] == str(self.mission.id)
        assert summary["title"] == "Test Mission"
        assert summary["branch_name"] == "feature/test-branch"
        assert summary["owner"] == "testuser"
        assert summary["repositories"] == ["testrepo"]


class MissionConversationModelTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username="testuser", password="testpass123", email="test@example.com")

        # Create a test mission
        self.mission = Mission.objects.create(
            title="Test Mission",
            description="Test mission description",
            branch_name="feature/test-branch",
            owner=self.user,
            state=Mission.State.IN_PROGRESS,
        )

        # Create a test conversation
        self.conversation = MissionConversation.objects.create(
            mission=self.mission, conversation_id="test-conversation-id", title="Test Conversation"
        )

    def test_conversation_creation(self):
        """Test that a conversation can be created with appropriate fields"""
        assert self.conversation.mission == self.mission
        assert self.conversation.conversation_id == "test-conversation-id"
        assert self.conversation.title == "Test Conversation"
        assert not self.conversation.is_summarized
        assert self.conversation.summary == ""
        assert self.conversation.remaining_tasks == []

    def test_conversation_string_representation(self):
        """Test the string representation of the conversation"""
        expected_date = timezone.now().strftime("%Y-%m-%d")
        expected_string = f"Conversation for Test Mission ({expected_date})"
        assert str(self.conversation) == expected_string

    def test_update_summary(self):
        """Test updating the conversation summary"""
        self.conversation.is_summarized = True
        self.conversation.summary = "This is a summary of the conversation"
        self.conversation.remaining_tasks = ["Task 1", "Task 2"]
        self.conversation.save()

        # Refresh from database
        self.conversation.refresh_from_db()

        assert self.conversation.is_summarized
        assert self.conversation.summary == "This is a summary of the conversation"
        assert self.conversation.remaining_tasks == ["Task 1", "Task 2"]


class MissionServiceTest(TestCase):
    @patch("holly.holly.services.mission_service.ContainerService")
    def setUp(self, mock_container_service):
        # Create mock container service
        self.mock_container_service = MagicMock()
        mock_container_service.return_value = self.mock_container_service

        # Create mission service
        self.mission_service = MissionService()

        # Create a test user
        self.user = User.objects.create_user(username="testuser", password="testpass123", email="test@example.com")

        # Create a test repo
        self.repo = RepositoryDetail.objects.create(username="testorg", repo_name="testrepo", user=self.user)

    def test_create_mission(self):
        """Test creating a mission through the service"""
        mission = self.mission_service.create_mission(
            owner=self.user,
            title="Test Service Mission",
            description="Created via service",
            branch_name="feature/service-test",
            repositories=[self.repo.id],
            requirements={"test": "requirement"},
        )

        assert mission.title == "Test Service Mission"
        assert mission.description == "Created via service"
        assert mission.branch_name == "feature/service-test"
        assert mission.owner == self.user
        assert mission.state == Mission.State.DRAFT
        assert mission.repositories.filter(id=self.repo.id).exists()
        assert mission.requirements == {"test": "requirement"}

    def test_update_mission(self):
        """Test updating a mission through the service"""
        # Create a mission
        mission = Mission.objects.create(
            title="Original Title",
            description="Original description",
            branch_name="feature/original",
            owner=self.user,
            state=Mission.State.DRAFT,
        )

        # Update the mission
        updates = {
            "title": "Updated Title",
            "description": "Updated description",
            "branch_name": "feature/updated",
            "state": Mission.State.IN_PROGRESS,
            "requirements": {"updated": "requirement"},
        }

        success, message, updated_mission = self.mission_service.update_mission(mission_id=mission.id, updates=updates)

        assert success
        assert message == "Mission updated successfully"
        assert updated_mission.title == "Updated Title"
        assert updated_mission.description == "Updated description"
        assert updated_mission.branch_name == "feature/updated"
        assert updated_mission.state == Mission.State.IN_PROGRESS
        assert updated_mission.requirements == {"updated": "requirement"}

    @patch("holly.holly.services.mission_service.get_github_oauth_token")
    def test_start_mission_container(self, mock_get_token):
        """Test starting a container for a mission"""
        # Mock the GitHub token
        mock_get_token.return_value = "fake-token"

        # Mock the container service start_container method
        self.mock_container_service.start_container.return_value = "fake-container-id"

        # Create a mission
        mission = Mission.objects.create(
            title="Container Test Mission",
            description="Test starting a container",
            branch_name="feature/container-test",
            owner=self.user,
            state=Mission.State.DRAFT,
        )

        # Start the container
        success, message, container_id = self.mission_service.start_mission_container(
            mission_id=mission.id, user=self.user
        )

        # Check the results
        assert success
        assert message == "Mission container started successfully"
        assert container_id == "fake-container-id"

        # Check that the mission was updated
        mission.refresh_from_db()
        assert mission.container_id == "fake-container-id"
        assert mission.state == Mission.State.IN_PROGRESS

    def test_end_mission(self):
        """Test ending a mission"""
        # Create a mission
        mission = Mission.objects.create(
            title="End Test Mission",
            description="Test ending a mission",
            branch_name="feature/end-test",
            owner=self.user,
            state=Mission.State.IN_PROGRESS,
            container_id="fake-container-id",
        )

        # Mock the stop_mission_container method
        self.mission_service.stop_mission_container = MagicMock(return_value=(True, "Container stopped"))

        # End the mission as completed
        success, message = self.mission_service.end_mission(mission_id=mission.id, user=self.user, complete=True)

        # Check the results
        assert success
        assert message == "Mission marked as completed"

        # Check that the mission state was updated
        mission.refresh_from_db()
        assert mission.state == Mission.State.COMPLETED

        # Verify stop_mission_container was called
        self.mission_service.stop_mission_container.assert_called_once_with(mission.id, self.user)
