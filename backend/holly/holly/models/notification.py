"""Notification model for user updates."""

from django.conf import settings
from django.db import models
from uuid import uuid4


class Notification(models.Model):
    """
    User notifications for mission and container events.

    Notifications are created when significant events occur:
    - Mission container starts/stops/errors
    - Conversation status changes
    - Task completions or failures
    - System alerts
    """

    class NotificationType(models.TextChoices):
        """Notification type choices."""
        MISSION_READY = "mission_ready", "Mission Ready"
        MISSION_ERROR = "mission_error", "Mission Error"
        CONTAINER_STARTED = "container_started", "Container Started"
        CONTAINER_STOPPED = "container_stopped", "Container Stopped"
        CONTAINER_ERROR = "container_error", "Container Error"
        CONVERSATION_COMPLETED = "conversation_completed", "Conversation Completed"
        CONVERSATION_ERROR = "conversation_error", "Conversation Error"
        MESSAGE_RECEIVED = "message_received", "Message Received"
        TASK_COMPLETED = "task_completed", "Task Completed"
        TASK_FAILED = "task_failed", "Task Failed"
        PR_CREATED = "pr_created", "Pull Request Created"
        PR_FAILED = "pr_failed", "Pull Request Failed"
        SYSTEM_ALERT = "system_alert", "System Alert"
        INFO = "info", "Information"

    class Priority(models.TextChoices):
        """Notification priority levels."""
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        help_text="User who receives this notification"
    )

    # Notification content
    type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        help_text="Type of notification"
    )
    title = models.CharField(
        max_length=255,
        help_text="Notification title"
    )
    message = models.TextField(
        help_text="Notification message content"
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.NORMAL,
        help_text="Notification priority level"
    )

    # Related objects (optional)
    mission_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="Related mission ID if applicable"
    )
    conversation_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="Related conversation ID if applicable"
    )

    # Additional data
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional JSON data for the notification"
    )

    # Status
    read = models.BooleanField(
        default=False,
        help_text="Whether the notification has been read"
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the notification was read"
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the notification was created"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the notification expires (optional)"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["user", "read", "-created_at"]),
            models.Index(fields=["mission_id"]),
            models.Index(fields=["conversation_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.type}: {self.title} for {self.user.email}"

    def mark_as_read(self) -> None:
        """Mark this notification as read."""
        from django.utils import timezone
        if not self.read:
            self.read = True
            self.read_at = timezone.now()
            self.save(update_fields=["read", "read_at"])
