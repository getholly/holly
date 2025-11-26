from django.db import models
from django.utils.translation import gettext_lazy as _


class Tools(models.Model):
    """
    Model representing MCP Tools configuration
    """

    name = models.CharField(_("Name"), max_length=64, help_text=_("The name of the MCP tool"))
    description = models.TextField(help_text="Description of this MCP tool")
    config = models.JSONField()

    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Tool")
        verbose_name_plural = _("Tools")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
