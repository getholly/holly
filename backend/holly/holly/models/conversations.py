from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import models

from holly.holly.models.mission_conversation import MissionConversation

User = get_user_model()


class Message(models.Model):
    """
    Model for storing messages within a conversation.
    """

    ROLE_CHOICES = (
        ("user", "User"),
        ("assistant", "Assistant"),
    )

    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    conversation = models.ForeignKey(MissionConversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self):
        # Convert UUID to string before slicing
        id_str = str(self.id)
        return f"{self.role} message in {self.conversation.title or 'Untitled'} ({id_str[:8]})"
