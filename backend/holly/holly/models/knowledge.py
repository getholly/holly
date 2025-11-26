from django.db import models
from django.utils.translation import gettext_lazy as _


class Knowledge(models.Model):
    """
    Model representing knowledge items that can be referenced by the MCP
    """

    name = models.CharField(_("Name"), max_length=64, help_text=_("The name of the knowledge item"))
    summary = models.CharField(
        ("Summary"), max_length=255, default="", blank=True, help_text=("Summary of the knowledge")
    )
    description = models.TextField(_("Description"), help_text=_("Description of this knowledge item"), blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Knowledge")
        verbose_name_plural = _("Knowledge Items")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
