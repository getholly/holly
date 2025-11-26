from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DiagramsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "holly.github_ext"
    verbose_name = _("Github Extension")

    class Meta:
        app_label = "github_ext"
