from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from encrypted_fields.fields import EncryptedTextField

from .llms import LLM


class UserLLMApiKey(models.Model):
    """Store per-user API keys for LLM models."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="llm_api_keys",
    )
    llm = models.ForeignKey(
        LLM,
        on_delete=models.CASCADE,
        related_name="user_api_keys",
    )
    api_key = EncryptedTextField(_("API Key"))
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        unique_together = ("user", "llm")
        verbose_name = _("User LLM API Key")
        verbose_name_plural = _("User LLM API Keys")

    def __str__(self) -> str:
        return f"{self.user} - {self.llm}"
