from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class LLM(models.Model):
    """
    Model representing a Language Learning Model (LLM) configuration
    Can be either a system-wide LLM or user-specific custom LLM
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="custom_llms",
        null=True,
        blank=True,
        help_text=_("User who owns this LLM. Null for system LLMs."),
    )
    is_system = models.BooleanField(
        _("Is System LLM"),
        default=False,
        help_text=_("Whether this is a system-wide LLM or user-specific"),
    )
    name = models.CharField(_("Name"), max_length=255, help_text=_("The name of the language learning model"))
    full_name = models.CharField(
        _("Full Name"),
        max_length=255,
        help_text=_("The full name of the language learning model, eg openai/qwen3:32b"),
        default="openai/qwen3:32b",
    )
    base_url = models.URLField(
        _("Base URL"),
        help_text=_("The base URL to use with this LLM"),
        blank=True,
        null=True,
        default="http://10.13.1.11:30000/v1",
    )
    system_prompt = models.TextField(
        _("System Prompt"), help_text=_("The system prompt to use with this LLM"), blank=True
    )
    top_p = models.FloatField(
        _("Top P"),
        help_text=_("The top p value to use with this LLM"),
        blank=True,
        null=True,
        default=None,
    )
    top_k = models.PositiveIntegerField(
        _("Top K"),
        help_text=_("The top k value to use with this LLM"),
        blank=True,
        null=True,
        default=None,
    )
    min_p = models.FloatField(
        _("Min P"), help_text=_("The min p value to use with this LLM"), blank=True, null=True, default=None
    )
    temperature = models.FloatField(
        _("Temperature"), help_text=_("The temperature value to use with this LLM"), blank=True, default=0.0
    )
    max_tokens = models.IntegerField(
        _("MaxTokens"), help_text=_("The max output tokens for this model"), blank=True, null=True, default=4096
    )

    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("LLM")
        verbose_name_plural = _("LLMs")
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"],
                condition=models.Q(user__isnull=False),
                name="unique_user_llm_name",
            )
        ]

    def __str__(self) -> str:
        if self.is_system:
            return f"{self.name} (System)"
        elif self.user:
            return f"{self.name} ({self.user.username})"
        return self.name

    def get_absolute_url(self) -> str:
        """Return the URL to access a detail record for this LLM."""
        from django.urls import reverse

        return reverse("holly:llm_detail", kwargs={"pk": self.pk})
