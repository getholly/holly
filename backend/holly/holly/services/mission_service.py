from typing import TYPE_CHECKING, Any
from uuid import UUID

from asgiref.sync import async_to_sync, sync_to_async
from django.conf import settings
from django.contrib.auth import get_user_model
from loguru import logger

from holly.github_ext.auth_utils import get_best_github_auth, get_github_oauth_token
from holly.github_ext.models import RepositoryDetail
from holly.github_ext.services.github_app_service import GitHubAppService
from holly.holly.api.mission_schemas import MissionRepoAdd
from holly.holly.models import LLM
from holly.holly.models.knowledge import Knowledge
from holly.holly.models.mission import Mission, MissionRepos
from holly.holly.models.mission_conversation import MissionConversation
from holly.holly.models.tools import Tools
from holly.holly.services.common.errors import ContainerIPError, ContainerStartError
from holly.holly.services.containers.holly_container_service import (
    HollyContainerService,
)
# REMOVED: clone_repositories_task import - container now self-initializes

if TYPE_CHECKING:
    from holly.github_ext.api.schemas import GitHubRepository

User = get_user_model()


def format_languages(primary_language: str | None) -> dict:
    """Convert GitHub's primary language to the expected dict format."""
    if primary_language:
        return {primary_language: 1}  # Use 1 as placeholder count
    return {}
class MissionService:
    """Service for managing missions and their containers

    This class uses the singleton pattern of HollyContainerService to ensure
    only one container service instance exists.
    """

    # Singleton instance
    _instance = None
    _initialized = False

    def __new__(cls):
        """Create a new instance of the class if one doesn't exist."""
        if cls._instance is None:
            logger.debug("Creating new MissionService instance")
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the mission service."""
        # Skip initialization if already initialized
        if self._initialized:
            logger.debug("MissionService already initialized, skipping")
            return

        self.container_service = HollyContainerService()

        # Mark as initialized to prevent further initialization
        MissionService._initialized = True

    def get_mission_by_id(self, mission_id: str | UUID) -> Mission | None:
        """
        Get a mission by its ID.

        Args:
            mission_id: The UUID of the mission to retrieve

        Returns:
            Optional[Mission]: The mission if found, None otherwise
        """
        try:
            return Mission.objects.get(id=mission_id)
        except Mission.DoesNotExist:
            return None

    def get_missions_for_user(self, user: User) -> list[Mission]:
        """
        Get all missions accessible by a user (owned or collaborated).

        Args:
            user: The user to get missions for

        Returns:
            List[Mission]: List of missions accessible by the user
        """
        # Get missions owned by the user
        owned_missions = Mission.objects.filter(owner=user)

        # Get missions where the user is a collaborator
        collaborated_missions = Mission.objects.filter(collaborators=user)

        # Combine and remove duplicates
        return list(set(list(owned_missions) + list(collaborated_missions)))

    def create_mission(
        self,
        owner: User,
        title: str,
        description: str,
        branch_name: str,
        repositories: list[MissionRepoAdd] | None = None,
        knowledge_item_ids: list[int] | None = None,
        tool_ids: list[int] | None = None,
        requirements: dict[str, Any] | None = None,
        llm: LLM | None = None,
    ) -> Mission:
        """
        Create a new mission.

        Args:
            owner: The user who will own the mission
            title: The mission title
            description: The mission description
            branch_name: The common branch name for all repositories
            repositories: List of the repos+branch_names
            knowledge_item_ids: List of knowledge item IDs to add to the mission
            tool_ids: List of tool IDs to add to the mission
            requirements: JSON dictionary of mission requirements
            llm: The default LLM to use

        Returns:
            Mission: The newly created mission
        """

        # TODO: create title via llm, the title will also serve as the branch name where the code will be updated

        # Create the mission object
        mission = Mission.objects.create(
            owner=owner,
            title=title,
            description=description,
            branch_name=branch_name,
            container_ip_address="",  # TODO: this should be set when the container is started
            state=Mission.State.DRAFT,
            requirements=requirements or {},
            llm=llm,
        )

        # add repos
        self.add_repositories(owner, mission_id=mission.id, repos=repositories)

        # Add knowledge items if provided
        if knowledge_item_ids:
            knowledge_items = Knowledge.objects.filter(id__in=knowledge_item_ids)
            mission.knowledge_items.set(knowledge_items)

        # Add tools if provided
        if tool_ids:
            tools = Tools.objects.filter(id__in=tool_ids)
            mission.tools.set(tools)

        return mission

    def update_mission(self, mission_id: str | UUID, updates: dict[str, Any]) -> tuple[bool, str, Mission | None]:
        """
        Update an existing mission.

        Args:
            mission_id: The UUID of the mission to update
            updates: Dictionary of fields to update

        Returns:
            Tuple[bool, str, Optional[Mission]]: Success flag, message, and updated mission
        """
        try:
            mission = Mission.objects.get(id=mission_id)

            # Update simple fields
            if updates.get("title"):
                mission.title = updates["title"]

            if "description" in updates and updates["description"] is not None:
                mission.description = updates["description"]

            if updates.get("branch_name"):
                mission.branch_name = updates["branch_name"]

            if updates.get("state"):
                if updates["state"] in [s[0] for s in Mission.State.choices]:
                    mission.state = updates["state"]
                else:
                    return False, f"Invalid state: {updates['state']}", None

            if "requirements" in updates and updates["requirements"] is not None:
                mission.requirements = updates["requirements"]

            # Save changes
            mission.save()
            return True, "Mission updated successfully", mission

        except Mission.DoesNotExist:
            return False, f"Mission with ID {mission_id} not found", None
        except Exception as e:
            logger.error(f"Error updating mission {mission_id}: {e!s}")
            return False, f"Error updating mission: {e!s}", None

    def add_collaborators(self, mission_id: str | UUID, user_ids: list[int]) -> tuple[bool, str, list[str] | None]:
        """
        Add collaborators to a mission.

        Args:
            mission_id: The UUID of the mission
            user_ids: List of user IDs to add as collaborators

        Returns:
            Tuple[bool, str, Optional[List[str]]]: Success flag, message, and list of added usernames
        """
        try:
            mission = Mission.objects.get(id=mission_id)
            users = User.objects.filter(id__in=user_ids)

            # Filter out users who are already collaborators or the owner
            new_collaborators = [
                u for u in users if u != mission.owner and not mission.collaborators.filter(id=u.id).exists()
            ]

            if not new_collaborators:
                return True, "No new collaborators to add", []

            # Add new collaborators
            mission.collaborators.add(*new_collaborators)

            usernames = [u.username for u in new_collaborators]
            return True, f"Added {len(usernames)} collaborators", usernames

        except Mission.DoesNotExist:
            return False, f"Mission with ID {mission_id} not found", None
        except Exception as e:
            logger.error(f"Error adding collaborators to mission {mission_id}: {e!s}")
            return False, f"Error adding collaborators: {e!s}", None

    def remove_collaborators(self, mission_id: str | UUID, user_ids: list[int]) -> tuple[bool, str, list[str] | None]:
        """
        Remove collaborators from a mission.

        Args:
            mission_id: The UUID of the mission
            user_ids: List of user IDs to remove from collaborators

        Returns:
            Tuple[bool, str, Optional[List[str]]]: Success flag, message, and list of removed usernames
        """
        try:
            mission = Mission.objects.get(id=mission_id)
            users = User.objects.filter(id__in=user_ids)

            # Check which users are actually collaborators
            current_collaborators = [u for u in users if mission.collaborators.filter(id=u.id).exists()]

            if not current_collaborators:
                return True, "No collaborators to remove", []

            # Remove collaborators
            mission.collaborators.remove(*current_collaborators)

            usernames = [u.username for u in current_collaborators]
            return True, f"Removed {len(usernames)} collaborators", usernames

        except Mission.DoesNotExist:
            return False, f"Mission with ID {mission_id} not found", None
        except Exception as e:
            logger.error(f"Error removing collaborators from mission {mission_id}: {e!s}")
            return False, f"Error removing collaborators: {e!s}", None

    def add_repositories(
        self, user: User, mission_id: str | UUID, repos: list[MissionRepoAdd]
    ) -> tuple[bool, str, list[str] | None]:
        """
        Add repositories to a mission.

        Args:
            user: User object for adding repos
            mission_id: The UUID of the mission
            repos: List of GITHUB repository IDs with branch names to add

        Returns:
            Tuple[bool, str, Optional[List[str]]]: Success flag, message, and list of added repository names
        """
        try:
            mission = Mission.objects.get(id=mission_id)

            new_repositories = []
            app_service = GitHubAppService(user)
            for add_repo in repos:
                if not mission.repositories.filter(repository__github_id=add_repo.github_id).exists():
                    repo: GitHubRepository = app_service.get_repository_by_id(add_repo.github_id)
                    repo_new, created = RepositoryDetail.objects.get_or_create(
                        github_id=add_repo.github_id,
                        defaults={
                            "username": repo.owner.login,
                            "repo": repo.name,
                            "description": repo.description or "",
                            "languages": format_languages(repo.language),
                            "stargazers_count": repo.stargazers_count,
                            "watchers_count": repo.watchers_count,
                            "forks_count": repo.forks_count,
                            "open_issues_count": repo.open_issues_count,
                            "size": repo.size,
                            "private": repo.visibility != "public",
                            "file_tree": {},
                        },
                    )
                    mission_repo, _ = MissionRepos.objects.get_or_create(
                        repository=repo_new, branch_name=add_repo.branch_name
                    )
                    new_repositories.append(mission_repo)

            if len(new_repositories) == 0:
                return True, "No new repositories to add", []

            # Add new repositories
            mission.repositories.add(*new_repositories)

            repo_names = [f"{r.repository.username}/{r.repository.repo}" for r in new_repositories]
            return True, f"Added {len(repo_names)} repositories", repo_names

        except Mission.DoesNotExist:
            return False, f"Mission with ID {mission_id} not found", None
        except Exception as e:
            logger.error(f"Error adding repositories to mission {mission_id}: {e!s}")
            return False, f"Error adding repositories: {e!s}", None

    def remove_repositories(
        self, mission_id: str | UUID, repository_ids: list[int]
    ) -> tuple[bool, str, list[str] | None]:
        """
        Remove repositories from a mission.

        Args:
            mission_id: The UUID of the mission
            repository_ids: List of RepositoryDetail IDs to remove

        Returns:
            Tuple[bool, str, Optional[List[str]]]: Success flag, message, and list of removed repository names
        """
        try:
            mission = Mission.objects.get(id=mission_id)
            repositories = RepositoryDetail.objects.filter(id__in=repository_ids)

            # Check which repositories are actually in the mission
            current_repositories = [
                r for r in repositories if mission.repositories.filter(repository__id=r.id).exists()
            ]

            if not current_repositories:
                return True, "No repositories to remove", []

            # Remove repositories
            mission.repositories.remove(*current_repositories)

            repo_names = [f"{r.username}/{r.repo_name}" for r in current_repositories]
            return True, f"Removed {len(repo_names)} repositories", repo_names

        except Mission.DoesNotExist:
            return False, f"Mission with ID {mission_id} not found", None
        except Exception as e:
            logger.error(f"Error removing repositories from mission {mission_id}: {e!s}")
            return False, f"Error removing repositories: {e!s}", None

    def add_knowledge_items(
        self, mission_id: str | UUID, knowledge_item_ids: list[int]
    ) -> tuple[bool, str, list[str] | None]:
        """
        Add knowledge items to a mission.

        Args:
            mission_id: The UUID of the mission
            knowledge_item_ids: List of knowledge item IDs to add

        Returns:
            Tuple[bool, str, Optional[List[str]]]: Success flag, message, and list of added knowledge item names
        """
        try:
            mission = Mission.objects.get(id=mission_id)
            knowledge_items = Knowledge.objects.filter(id__in=knowledge_item_ids)

            # Filter out knowledge items that are already in the mission
            new_knowledge_items = [k for k in knowledge_items if not mission.knowledge_items.filter(id=k.id).exists()]

            if not new_knowledge_items:
                return True, "No new knowledge items to add", []

            # Add knowledge items
            mission.knowledge_items.add(*new_knowledge_items)

            knowledge_names = [k.name for k in new_knowledge_items]
            return (
                True,
                f"Added {len(knowledge_names)} knowledge items",
                knowledge_names,
            )

        except Mission.DoesNotExist:
            return False, f"Mission with ID {mission_id} not found", None
        except Exception as e:
            logger.error(f"Error adding knowledge items to mission {mission_id}: {e!s}")
            return False, f"Error adding knowledge items: {e!s}", None

    def remove_knowledge_items(
        self, mission_id: str | UUID, knowledge_item_ids: list[int]
    ) -> tuple[bool, str, list[str] | None]:
        """
        Remove knowledge items from a mission.

        Args:
            mission_id: The UUID of the mission
            knowledge_item_ids: List of knowledge item IDs to remove

        Returns:
            Tuple[bool, str, Optional[List[str]]]: Success flag, message, and list of removed knowledge item names
        """
        try:
            mission = Mission.objects.get(id=mission_id)
            knowledge_items = Knowledge.objects.filter(id__in=knowledge_item_ids)

            # Check which knowledge items are actually in the mission
            current_knowledge_items = [k for k in knowledge_items if mission.knowledge_items.filter(id=k.id).exists()]

            if not current_knowledge_items:
                return True, "No knowledge items to remove", []

            # Remove knowledge items
            mission.knowledge_items.remove(*current_knowledge_items)

            knowledge_names = [k.name for k in current_knowledge_items]
            return (
                True,
                f"Removed {len(knowledge_names)} knowledge items",
                knowledge_names,
            )

        except Mission.DoesNotExist:
            return False, f"Mission with ID {mission_id} not found", None
        except Exception as e:
            logger.error(f"Error removing knowledge items from mission {mission_id}: {e!s}")
            return False, f"Error removing knowledge items: {e!s}", None

    def set_repositories(
        self, user: User, mission_id: str | UUID, repos: list[MissionRepoAdd]
    ) -> tuple[bool, str, list[str] | None]:
        """
        Set repositories for a mission (replaces all existing repositories).

        Args:
            user: User object for adding repos
            mission_id: The UUID of the mission
            repos: Complete list of repository data to set

        Returns:
            Tuple[bool, str, Optional[List[str]]]: Success flag, message, and list of repository names
        """
        try:
            mission = Mission.objects.get(id=mission_id)

            # Clear all existing repositories
            mission.repositories.clear()

            # Add all new repositories
            if repos:
                success, message, repo_names = self.add_repositories(user, mission_id, repos)
                if not success:
                    return success, message, repo_names
                return True, f"Set {len(repo_names)} repositories", repo_names
            return True, "Cleared all repositories", []

        except Mission.DoesNotExist:
            return False, f"Mission with ID {mission_id} not found", None
        except Exception as e:
            logger.error(f"Error setting repositories for mission {mission_id}: {e!s}")
            return False, f"Error setting repositories: {e!s}", None

    def set_knowledge_items(
        self, mission_id: str | UUID, knowledge_item_ids: list[int]
    ) -> tuple[bool, str, list[str] | None]:
        """
        Set knowledge items for a mission (replaces all existing knowledge items).

        Args:
            mission_id: The UUID of the mission
            knowledge_item_ids: Complete list of knowledge item IDs to set

        Returns:
            Tuple[bool, str, Optional[List[str]]]: Success flag, message, and list of knowledge item names
        """
        try:
            mission = Mission.objects.get(id=mission_id)

            # Clear all existing knowledge items
            mission.knowledge_items.clear()

            # Add all new knowledge items
            if knowledge_item_ids:
                success, message, knowledge_names = self.add_knowledge_items(mission_id, knowledge_item_ids)
                if not success:
                    return success, message, knowledge_names
                return (
                    True,
                    f"Set {len(knowledge_names)} knowledge items",
                    knowledge_names,
                )
            return True, "Cleared all knowledge items", []

        except Mission.DoesNotExist:
            return False, f"Mission with ID {mission_id} not found", None
        except Exception as e:
            logger.error(f"Error setting knowledge items for mission {mission_id}: {e!s}")
            return False, f"Error setting knowledge items: {e!s}", None

    def add_tools(self, mission_id: str | UUID, tool_ids: list[int]) -> tuple[bool, str, list[str] | None]:
        """
        Add tools to a mission.

        Args:
            mission_id: The UUID of the mission
            tool_ids: List of tool IDs to add

        Returns:
            Tuple[bool, str, Optional[List[str]]]: Success flag, message, and list of added tool names
        """
        try:
            mission = Mission.objects.get(id=mission_id)
            tools = Tools.objects.filter(id__in=tool_ids)

            # Filter out tools that are already in the mission
            new_tools = [t for t in tools if not mission.tools.filter(id=t.id).exists()]

            if not new_tools:
                return True, "No new tools to add", []

            # Add tools
            mission.tools.add(*new_tools)

            tool_names = [t.name for t in new_tools]
            return True, f"Added {len(tool_names)} tools", tool_names

        except Mission.DoesNotExist:
            return False, f"Mission with ID {mission_id} not found", None
        except Exception as e:
            logger.error(f"Error adding tools to mission {mission_id}: {e!s}")
            return False, f"Error adding tools: {e!s}", None

    def remove_tools(self, mission_id: str | UUID, tool_ids: list[int]) -> tuple[bool, str, list[str] | None]:
        """
        Remove tools from a mission.

        Args:
            mission_id: The UUID of the mission
            tool_ids: List of tool IDs to remove

        Returns:
            Tuple[bool, str, Optional[List[str]]]: Success flag, message, and list of removed tool names
        """
        try:
            mission = Mission.objects.get(id=mission_id)
            tools = Tools.objects.filter(id__in=tool_ids)

            # Check which tools are actually in the mission
            current_tools = [t for t in tools if mission.tools.filter(id=t.id).exists()]

            if not current_tools:
                return True, "No tools to remove", []

            # Remove tools
            mission.tools.remove(*current_tools)

            tool_names = [t.name for t in current_tools]
            return True, f"Removed {len(tool_names)} tools", tool_names

        except Mission.DoesNotExist:
            return False, f"Mission with ID {mission_id} not found", None
        except Exception as e:
            logger.error(f"Error removing tools from mission {mission_id}: {e!s}")
            return False, f"Error removing tools: {e!s}", None

    def set_tools(self, mission_id: str | UUID, tool_ids: list[int]) -> tuple[bool, str, list[str] | None]:
        """
        Set tools for a mission (replaces all existing tools).

        Args:
            mission_id: The UUID of the mission
            tool_ids: Complete list of tool IDs to set

        Returns:
            Tuple[bool, str, Optional[List[str]]]: Success flag, message, and list of tool names
        """
        try:
            mission = Mission.objects.get(id=mission_id)

            # Clear all existing tools
            mission.tools.clear()

            # Add all new tools
            if tool_ids:
                success, message, tool_names = self.add_tools(mission_id, tool_ids)
                if not success:
                    return success, message, tool_names
                return True, f"Set {len(tool_names)} tools", tool_names
            return True, "Cleared all tools", []

        except Mission.DoesNotExist:
            return False, f"Mission with ID {mission_id} not found", None
        except Exception as e:
            logger.error(f"Error setting tools for mission {mission_id}: {e!s}")
            return False, f"Error setting tools: {e!s}", None

    def start_mission_container(self, mission_id: str | UUID, user: User) -> tuple[bool, str, str | None]:
        """
        Start a container for a mission.

        Args:
            mission_id: The UUID of the mission
            user: The user starting the container (must be owner or collaborator)

        Returns:
            Tuple[bool, str, Optional[str]]: Success flag, message, and container ID if successful
        """
        try:
            mission = Mission.objects.get(id=mission_id)

            # Verify user has access
            if not async_to_sync(mission.can_be_accessed_by)(user):
                return (
                    False,
                    "You do not have permission to start this mission's container",
                    None,
                )

            # Check if mission is in a valid state to start
            # Allow starting containers for DRAFT, IN_PROGRESS, READY, and COMPLETED missions
            # Only reject ABORTED and ERROR states
            if mission.state in [Mission.State.ABORTED, Mission.State.ERROR]:
                return (
                    False,
                    f"Mission in state '{mission.get_state_display()}' cannot be started",
                    None,
                )

            # Get best available GitHub authentication
            auth_infos = get_best_github_auth(user)

            if not auth_infos or auth_infos[0].get("type") == "none" or not auth_infos[0].get("token"):
                logger.error(f"No GitHub authentication available for user {user.id}")
                return False, "No GitHub authentication token available", None

            # Use the first available auth token
            auth_token = auth_infos[0]["token"]
            logger.info(f"Using {auth_infos[0]['type']} authentication for container startup")

            # Try to start the container
            try:
                # Prepare environment with mission context for self-initialization
                repos_str = ",".join([
                    f"{r.repository.username}/{r.repository.repo}:{r.branch_name}"
                    for r in mission.repositories.select_related('repository').all()
                ])

                # Build Django webhook URL (use host.docker.internal for Windows/Mac Docker)
                django_base_url = getattr(settings, 'DJANGO_BASE_URL', 'http://host.docker.internal:8000')
                webhook_url = f"{django_base_url}/_api/holly/webhooks/container-webhook"

                environment = {
                    "AIAGENTS_WORKING_DIR": settings.HOLLY_WORKING_DIRECTORY,
                    "MISSION_ID": str(mission_id),
                    "MISSION_REPOS": repos_str,
                    "MISSION_BRANCH": mission.branch_name,
                    "DJANGO_WEBHOOK_URL": webhook_url,
                    "AUTH_TOKEN": auth_token,
                    "AUTH_TYPE": auth_infos[0]["type"],  # 'github_app' or 'oauth'
                    "GIT_EMAIL": "holly-bot@yourdomain.com",
                    "GIT_USER": "Holly Bot",
                    "REDIS_HOST": getattr(settings, 'REDIS_HOST', 'localhost'),
                    "REDIS_PORT": str(getattr(settings, 'REDIS_PORT', 6379)),
                }

                from django.utils import timezone

                container_id = self.container_service.start_container(mission, auth_token, environment)
                container_ip = self.container_service.get_container_ip(container_id)

                mission.container_id = container_id
                mission.container_ip_address = container_ip
                mission.container_status = "starting"
                mission.container_started_at = timezone.now()
                mission.state = Mission.State.PROVISIONING  # Changed from IN_PROGRESS
                mission.save(
                    update_fields=[
                        "container_id",
                        "container_ip_address",
                        "container_status",
                        "container_started_at",
                        "state",
                        "updated_at",
                    ]
                )

                # Container will self-initialize and send webhooks
                # No more clone_repositories_task!
                logger.info(f"Container started for mission {mission_id}, initializing...")

                return (
                    True,
                    "Container started, initializing...",
                    mission.container_id,
                )

            except (ContainerStartError, ContainerIPError) as e:
                logger.error(f"Error starting container for mission {mission_id}: {e!s}")
                return False, f"Error starting container: {e!s}", None

        except Mission.DoesNotExist:
            return False, f"Mission with ID {mission_id} not found", None
        except Exception as e:
            logger.error(f"Error starting container for mission {mission_id}: {e!s}")
            return False, f"Error starting container: {e!s}", None

    def stop_mission_container(self, mission_id: str | UUID, user: User) -> tuple[bool, str]:
        """
        Stop a mission's container.

        Args:
            mission_id: The UUID of the mission
            user: The user stopping the container (must be owner or collaborator)

        Returns:
            Tuple[bool, str]: Success flag and message
        """
        try:
            mission = Mission.objects.get(id=mission_id)

            # Verify user has access
            if not async_to_sync(mission.can_be_accessed_by)(user):
                return (
                    False,
                    "You do not have permission to stop this mission's container",
                )

            # Check if mission has a container
            if not mission.container_id:
                return True, "No container running for this mission"

            # Try to stop the container
            success = self.container_service.stop_container(mission)

            if success:
                # Update mission to remove container ID
                mission.container_id = None
                mission.save(update_fields=["container_id", "updated_at"])
                return True, "Mission container stopped successfully"
            return False, "Error stopping mission container"

        except Mission.DoesNotExist:
            return False, f"Mission with ID {mission_id} not found"
        except Exception as e:
            logger.error(f"Error stopping container for mission {mission_id}: {e!s}")
            return False, f"Error stopping container: {e!s}"

    def end_mission(self, mission_id: str | UUID, user: User, complete: bool = True) -> tuple[bool, str]:
        """
        End a mission (mark as completed or aborted).

        Args:
            mission_id: The UUID of the mission
            user: The user ending the mission (must be owner or collaborator)
            complete: If True, mark as completed; if False, mark as aborted

        Returns:
            Tuple[bool, str]: Success flag and message
        """
        try:
            mission = Mission.objects.get(id=mission_id)

            # Verify user has access
            if not async_to_sync(mission.can_be_accessed_by)(user):
                return False, "You do not have permission to end this mission"

            # Check if mission is already ended
            if mission.state in [Mission.State.COMPLETED, Mission.State.ABORTED]:
                return (
                    True,
                    f"Mission is already in state: {mission.get_state_display()}",
                )

            # Stop the container if running
            if mission.container_id:
                self.stop_mission_container(mission_id, user)

            # Update mission state
            if complete:
                mission.mark_as_completed()
                return True, "Mission marked as completed"
            mission.mark_as_aborted()
            return True, "Mission marked as aborted"

        except Mission.DoesNotExist:
            return False, f"Mission with ID {mission_id} not found"
        except Exception as e:
            logger.error(f"Error ending mission {mission_id}: {e!s}")
            return False, f"Error ending mission: {e!s}"

    async def acreate_mission_conversation(
        self, mission_id: str | UUID, conversation_id: str, title: str | None = None
    ) -> tuple[bool, str, MissionConversation | None]:
        """
        Create a new conversation link for a mission.

        Args:
            mission_id: The UUID of the mission
            conversation_id: The ID of the conversation in the MCP system
            title: Optional title for the conversation

        Returns:
            Tuple[bool, str, Optional[MissionConversation]]: Success flag, message, and conversation if successful
        """
        try:
            mission = await Mission.objects.aget(id=mission_id)

            # Create the conversation link
            conversation = await MissionConversation.objects.acreate(
                mission=mission, conversation_id=conversation_id, title=title or ""
            )

            return True, "Conversation created successfully", conversation

        except Mission.DoesNotExist:
            return False, f"Mission with ID {mission_id} not found", None
        except Exception as e:
            logger.error(f"Error creating conversation for mission {mission_id}: {e!s}")
            return False, f"Error creating conversation: {e!s}", None

    def update_conversation_summary(
        self,
        mission_id: str | UUID,
        conversation_id: str,
        summary: str,
        remaining_tasks: list[str],
    ) -> tuple[bool, str]:
        """
        Update a conversation with a summary and remaining tasks list.

        This is used when context window limits are reached and the conversation
        needs to be summarized for future context.

        Args:
            mission_id: The UUID of the mission
            conversation_id: The ID of the conversation in the MCP system
            summary: The summarized content of the conversation
            remaining_tasks: List of tasks that still need to be completed

        Returns:
            Tuple[bool, str]: Success flag and message
        """
        try:
            mission = Mission.objects.get(id=mission_id)

            # Find the conversation
            try:
                conversation = MissionConversation.objects.get(mission=mission, conversation_id=conversation_id)
            except MissionConversation.DoesNotExist:
                return (
                    False,
                    f"Conversation with ID {conversation_id} not found in mission",
                )

            # Update the conversation
            conversation.is_summarized = True
            conversation.summary = summary
            conversation.remaining_tasks = remaining_tasks
            conversation.save(
                update_fields=[
                    "is_summarized",
                    "summary",
                    "remaining_tasks",
                    "updated_at",
                ]
            )

            return True, "Conversation summary updated"

        except Mission.DoesNotExist:
            return False, f"Mission with ID {mission_id} not found"
        except Exception as e:
            logger.error(f"Error updating conversation summary for mission {mission_id}: {e!s}")
            return False, f"Error updating conversation summary: {e!s}"

    async def ensure_mission_container(self, mission_id: str | UUID, user: User):
        """
        Ensure the mission container is running, check state instead of polling.

        Args:
            user: The requesting user

        Returns:
            tuple[bool, Optional[str], Optional[str]]: (success, error_message, container_url)
        """
        try:
            mission = await sync_to_async(Mission.objects.get)(id=mission_id)

            # If READY (or IN_PROGRESS/COMPLETED with running container), return URL
            if mission.state in [Mission.State.READY, Mission.State.IN_PROGRESS, Mission.State.COMPLETED]:
                if mission.container_id and await sync_to_async(
                    self.container_service.is_container_running
                )(mission):
                    # Try to use Docker host-mapped port for the REST API
                    try:
                        ports = await sync_to_async(self.container_service.get_container_ports)(mission.container_id)
                        rest_host_port = ports.get("rest_api")
                    except Exception as _e:  # noqa: BLE001
                        rest_host_port = None

                    if rest_host_port:
                        # Always use localhost with host-mapped port for reliable connectivity
                        return True, None, f"http://127.0.0.1:{rest_host_port}"

                    # No host port mapping found - container may not be properly configured
                    logger.error(f"Container {mission.container_id} has no REST API port mapping")
                    return False, "Container REST API port not accessible. Please restart the container.", None

            # If PROVISIONING, container is still initializing
            if mission.state == Mission.State.PROVISIONING:
                return False, "Container is initializing, please wait", None

            # If ERROR, initialization failed
            if mission.state == Mission.State.ERROR:
                return False, "Container initialization failed, please restart mission", None

            # Start new container
            success, message, container_id = await sync_to_async(
                self.start_mission_container
            )(mission_id=mission_id, user=user)

            if not success:
                return False, message, None

            # Return immediately - frontend gets updates via webhook/SSE
            return False, "Container started, initializing repositories...", None

        except Exception as e:
            logger.error(f"Error ensuring mission container: {e!s}")
            return False, f"Error ensuring mission container: {e!s}", None

    async def start_container_with_conversation_job(
        self,
        mission_id: str | UUID,
        conversation_id: str,
        job_id: str,
        initial_message: str,
        user: User
    ) -> tuple[bool, str]:
        """
        Start container with conversation context for self-initialization.

        This method starts a container with environment variables that tell it
        to process an initial message after initialization.

        Args:
            mission_id: Mission ID
            conversation_id: Conversation ID
            job_id: Job ID for tracking
            initial_message: Initial message to process
            user: User starting the conversation

        Returns:
            Tuple[bool, str]: Success flag and message
        """
        try:
            mission = await sync_to_async(Mission.objects.get)(id=mission_id)

            # Get best available auth (GitHub App or OAuth)
            auth_infos = await sync_to_async(get_best_github_auth)(user)

            if not auth_infos or auth_infos[0].get("type") == "none" or not auth_infos[0].get("token"):
                logger.error(f"No GitHub authentication available for user {user.id}")
                return False, "No GitHub authentication token available"

            # Use the first available auth token
            auth_token = auth_infos[0]["token"]
            logger.info(f"Using {auth_infos[0]['type']} authentication for container startup")

            # Build repository string (need to select_related to avoid sync queries)
            repos = await sync_to_async(
                lambda: list(mission.repositories.select_related('repository').all())
            )()
            repos_str = ",".join([
                f"{r.repository.username}/{r.repository.repo}:{r.branch_name}"
                for r in repos
            ])

            # Build Django webhook URL (use host.docker.internal for Windows/Mac Docker)
            django_base_url = getattr(settings, 'DJANGO_BASE_URL', 'http://host.docker.internal:8000')
            webhook_url = f"{django_base_url}/_api/holly/webhooks/container-webhook"

            # Environment with conversation context
            environment = {
                "AIAGENTS_WORKING_DIR": settings.HOLLY_WORKING_DIRECTORY,
                "MISSION_ID": str(mission_id),
                "CONVERSATION_ID": conversation_id,
                "JOB_ID": job_id,
                "INITIAL_MESSAGE": initial_message,
                "MISSION_REPOS": repos_str,
                "MISSION_BRANCH": mission.branch_name,
                "DJANGO_WEBHOOK_URL": webhook_url,
                "AUTH_TOKEN": auth_token,
                "AUTH_TYPE": auth_infos[0]["type"],  # 'github_app' or 'oauth'
                "GIT_EMAIL": "holly-bot@yourdomain.com",
                "GIT_USER": "Holly Bot",
                "REDIS_HOST": getattr(settings, 'REDIS_HOST', 'localhost'),
                "REDIS_PORT": str(getattr(settings, 'REDIS_PORT', 6379)),
            }

            # Start container (returns immediately)
            container_id = await sync_to_async(self.container_service.start_container)(
                mission, auth_token, environment
            )

            # Update mission with container and job tracking
            mission.container_id = container_id
            mission.container_ip_address = await sync_to_async(self.container_service._get_container_ip)(container_id)
            mission.init_job_id = job_id
            mission.state = Mission.State.PROVISIONING

            # Add to active jobs
            active_jobs = mission.active_jobs or []
            active_jobs.append({
                "job_id": job_id,
                "type": "conversation_init",
                "conversation_id": conversation_id,
                "status": "started"
            })
            mission.active_jobs = active_jobs

            await sync_to_async(mission.save)()

            logger.info(f"Started container {container_id} for conversation {conversation_id}")
            return True, "Container started with conversation context"

        except Mission.DoesNotExist:
            return False, f"Mission with ID {mission_id} not found"
        except Exception as e:
            logger.error(f"Error starting container with conversation job: {e!s}")
            return False, f"Error starting container: {e!s}"


# Singleton instance of MissionService
mission_service = MissionService()
