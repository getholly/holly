from uuid import uuid4

from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from loguru import logger

from holly.github_ext.models import RepositoryDetail
from holly.holly.models.knowledge import Knowledge
from holly.holly.models.llms import (
    LLM,
)  # Changed import to directly reference llms.py
from holly.holly.models.tools import Tools

User = get_user_model()


# TODO: do we want to create a MissionSession so a Mission can have multiple sessions?
# Create a session-like object for the container service
# class MissionSession:
#     def __init__(self, mission_id, container_id: str | None = None, port_mappings: dict[int, int] = {},
#                  ip_address: str | None = None):
#         self.id = mission_id
#         self.container_id = container_id
#         self.port_mappings = port_mappings
#         self.ip_address = ip_address
#
#     def save(self, **kwargs):
#         # This is called by container_service when it sets container_id
#         pass
#
#
# session = MissionSession(mission.id, mission.container_id)


class MissionRepos(models.Model):
    repository = models.ForeignKey(
        RepositoryDetail,
        on_delete=models.CASCADE,
        help_text="Name of repo attached to this mission",
        db_index=True,
    )
    branch_name = models.CharField(
        max_length=255,
        help_text="Name of the branch from which to branch or create new branches from",
    )

    class Meta:
        verbose_name = _("MissionRepos")
        verbose_name_plural = _("MissionRepos")


class Mission(models.Model):
    """
    Model representing a mission to implement a feature or fix a bug using LLM assistance.

    A mission has an owner (one user) and can have multiple collaborators.
    It is associated with one or more git repositories that all use the same branch.
    A mission can reference knowledge objects and tools to assist the LLM.
    A mission can have multiple conversations tracking interactions with the LLM.
    """

    class State(models.TextChoices):
        DRAFT = "draft", _("Draft")
        PROVISIONING = "provisioning", _("Provisioning")
        READY = "ready", _("Ready")
        IN_PROGRESS = "in_progress", _("In Progress")
        COMPLETED = "completed", _("Completed")
        ABORTED = "aborted", _("Aborted")
        ERROR = "error", _("Error")

    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    title = models.CharField(_("Title"), max_length=255, help_text=_("Mission title"))
    description = models.TextField(_("Description"), blank=True, help_text=_("Detailed description of the mission"))

    # State and dates
    state = models.CharField(
        _("State"),
        max_length=20,
        choices=State.choices,
        default=State.DRAFT,
        help_text=_("Current state of the mission"),
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    # Users
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_missions",
        help_text=_("User who owns this mission"),
        db_index=True,
    )
    collaborators = models.ManyToManyField(
        User,
        related_name="collaborated_missions",
        blank=True,
        help_text=_("Users who can collaborate on this mission"),
    )

    # Git-related fields
    branch_name = models.CharField(
        _("Branch Name"),
        max_length=255,
        help_text=_("Common branch name for all repositories in this mission"),
    )
    repositories = models.ManyToManyField(
        MissionRepos,
        related_name="missions",
        blank=True,
        help_text=_("Git repositories involved in this mission"),
    )

    # Container session reference
    container_id = models.CharField(
        _("Container ID"),
        max_length=64,
        blank=True,
        null=True,
        help_text=_("ID of the container for this mission"),
    )
    container_ip_address = models.CharField(
        _("Container IP Address"),
        max_length=64,
        blank=True,
        null=True,
        help_text=_("IP address of the running container"),
    )
    container_status = models.CharField(
        _("Container Status"),
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ("starting", _("Starting")),
            ("ready", _("Ready")),
            ("error", _("Error")),
            ("stopped", _("Stopped")),
        ],
        help_text=_("Current status of the container"),
    )
    container_started_at = models.DateTimeField(
        _("Container Started At"),
        blank=True,
        null=True,
        help_text=_("When the container was last started"),
    )
    container_stopped_at = models.DateTimeField(
        _("Container Stopped At"),
        blank=True,
        null=True,
        help_text=_("When the container was last stopped"),
    )

    # Job tracking for async operations
    init_job_id = models.CharField(
        _("Init Job ID"),
        max_length=64,
        blank=True,
        null=True,
        help_text=_("ID of the container initialization job"),
    )
    active_jobs = models.JSONField(
        _("Active Jobs"),
        default=list,
        blank=True,
        help_text=_("List of active async jobs"),
    )

    # Knowledge and tools
    knowledge_items = models.ManyToManyField(
        Knowledge,
        related_name="missions",
        blank=True,
        help_text=_("Knowledge items to provide context for this mission"),
    )
    tools = models.ManyToManyField(
        Tools,
        related_name="missions",
        blank=True,
        help_text=_("Tools available for this mission"),
    )
    llm = models.ForeignKey(
        LLM,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("default LLM to use for this mission"),
    )

    # Requirements tracking
    requirements = models.JSONField(
        _("Requirements"),
        default=dict,
        blank=True,
        help_text=_("Requirements for this mission in JSON format"),
    )

    class Meta:
        verbose_name = _("Mission")
        verbose_name_plural = _("Missions")
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"{self.title} ({self.get_state_display()})"

    def is_active(self) -> bool:
        """Check if the mission is currently active (in progress)"""
        return self.state == self.State.IN_PROGRESS

    @sync_to_async
    def can_be_accessed_by(self, user) -> bool:
        """Check if a user can access this mission"""
        return user == self.owner or self.collaborators.filter(id=user.id).exists()

    def get_summary(self) -> dict:
        """Return a summary of the mission"""
        return {
            "id": str(self.id),
            "title": self.title,
            "state": self.state,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "owner": self.owner.username,
            "repositories": list(self.repositories.values_list("repository__repo_name", flat=True)),
            "branch_name": self.branch_name,
        }

    def mark_as_completed(self) -> None:
        """Mark the mission as completed"""
        self.state = self.State.COMPLETED
        self.save(update_fields=["state", "updated_at"])

    def mark_as_aborted(self) -> None:
        """Mark the mission as aborted"""
        self.state = self.State.ABORTED
        self.save(update_fields=["state", "updated_at"])

    def get_job_status(self, job_id: str) -> dict:
        """
        Poll container for job status.

        Args:
            job_id: The job ID to query

        Returns:
            Dictionary with job status information
        """
        import requests
        from django.conf import settings
        from holly.holly.services.containers.holly_container_service import HollyContainerService

        if not self.container_id:
            return {"error": "No container running", "job_id": job_id}

        try:
            container_service = HollyContainerService()
            container_ip = container_service.get_container_ip(self.container_id)

            if not container_ip:
                return {"error": "Could not get container IP", "job_id": job_id}

            url = f"http://{container_ip}:{settings.REST_MCP_SERVER_PORT}/api/git/jobs/{job_id}"

            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            return {"error": str(e), "job_id": job_id}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}", "job_id": job_id}

    async def is_container_ready(self) -> bool:
        """
        Check if container is ready and accepting connections.

        Returns:
            bool: True if container is ready, False otherwise
        """
        import httpx
        from django.conf import settings

        if not self.container_ip_address:
            return False

        try:
            url = f"http://{self.container_ip_address}:{settings.REST_MCP_SERVER_PORT}/api/health"
            async with httpx.AsyncClient(timeout=3) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception:
            return False

    async def get_container_url(self, user: User) -> str | None:
        from holly.holly.services.mission_service import mission_service

        success, error_message, container_url = await mission_service.ensure_mission_container(self.id, user)
        if not success:
            logger.error(f"Could not get container URL: {error_message}")
            return None
        return container_url

    def get_tools(self):
        tools = {}
        for tool in self.tools.all():
            tools.update(tool.config)
        return tools

    async def aget_tools(self):
        @sync_to_async
        def get_all_tools():
            return self.get_tools()

        return await get_all_tools()
