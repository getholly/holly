from uuid import uuid4

from django.db import models
from django.utils.translation import gettext_lazy as _

from holly.holly.models.mission import Mission


class MissionConversation(models.Model):
    """
    Model representing a conversation within a mission.

    This links existing conversation objects to missions and adds
    mission-specific metadata.
    """

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    mission = models.ForeignKey(
        Mission,
        on_delete=models.CASCADE,
        related_name="conversations",
        help_text=_("Mission this conversation belongs to"),
    )
    conversation_id = models.CharField(
        _("Conversation ID"),
        max_length=64,
        help_text=_("ID of the conversation in the MCP system"),
        unique=True,
    )
    title = models.CharField(
        _("Title"), max_length=255, blank=True, help_text=_("Optional title for this conversation")
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    # Status tracking
    status = models.CharField(
        _("Status"),
        max_length=20,
        default="pending",
        choices=[
            ("pending", _("Pending")),
            ("processing", _("Processing")),
            ("completed", _("Completed")),
            ("error", _("Error")),
            ("archived", _("Archived")),
        ],
        help_text=_("Current status of this conversation"),
    )
    last_activity_at = models.DateTimeField(
        _("Last Activity At"),
        auto_now=True,
        help_text=_("Timestamp of last activity in this conversation"),
    )
    error_message = models.TextField(
        _("Error Message"),
        blank=True,
        help_text=_("Error message if conversation failed"),
    )

    # Context management
    is_summarized = models.BooleanField(
        _("Is Summarized"),
        default=False,
        help_text=_("Whether this conversation has been summarized due to context window limits"),
    )
    summary = models.TextField(
        _("Summary"), blank=True, help_text=_("Summary of this conversation if it exceeded context limits")
    )
    remaining_tasks = models.JSONField(
        _("Remaining Tasks"),
        default=list,
        blank=True,
        help_text=_("Tasks remaining after this conversation in JSON format"),
    )

    class Meta:
        verbose_name = _("Mission Conversation")
        verbose_name_plural = _("Mission Conversations")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["mission"]),
            models.Index(fields=["conversation_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.title or self.mission.title} ({self.created_at.strftime('%Y-%m-%d %H:%M:%S')})"
