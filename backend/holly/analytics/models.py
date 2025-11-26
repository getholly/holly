from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Repository(models.Model):
    """
    Tracks the models of repositories that have been analysed.
    """

    username = models.CharField(_("Repository Owner"), max_length=100)
    repo_name = models.CharField(_("Repository Name"), max_length=100)
    private = models.BooleanField(_("Private"), default=True)
    timestamp = models.DateTimeField(_("Timestamp"), auto_now_add=True)

    class Meta:
        verbose_name = _("Repository Model")
        verbose_name_plural = _("Repository Models")
        unique_together = ("username", "repo_name")
        ordering = ("-timestamp",)
        indexes = (
            models.Index(fields=["username", "repo_name"]),
            models.Index(fields=["timestamp"]),
        )

    def __str__(self) -> str:
        return f"{self.username}/{self.repo_name}"


class RepoView(models.Model):
    """
    Tracks when a user views a repository through the analyse_repo view.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="repo_views",
    )
    repo = models.ForeignKey(
        Repository,
        on_delete=models.CASCADE,
        related_name="views",
    )
    timestamp = models.DateTimeField(_("Timestamp"), auto_now_add=True)

    class Meta:
        verbose_name = _("Repository View")
        verbose_name_plural = _("Repository Views")
        ordering = ("-timestamp",)
        indexes = (
            models.Index(fields=["repo"]),
            models.Index(fields=["user"]),
            models.Index(fields=["timestamp"]),
        )

    def __str__(self) -> str:
        user_info = self.user.email
        return f"{user_info} viewed {self.repo} at {self.timestamp}"


class LLMQuery(models.Model):
    """
    Tracks usage of LLM queries about GitHub repositories via the default_pipeline.run.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="llm_queries",
    )
    repo = models.ForeignKey(
        Repository,
        on_delete=models.CASCADE,
        related_name="queries",
    )
    query_text = models.TextField(_("Query Text"))
    model_name = models.CharField(_("Model Name"), max_length=250, blank=True, default="")
    timestamp = models.DateTimeField(_("Timestamp"), auto_now_add=True)

    class Meta:
        verbose_name = _("LLM Query")
        verbose_name_plural = _("LLM Queries")
        ordering = ("-timestamp",)
        indexes = (
            models.Index(fields=["repo"]),
            models.Index(fields=["user"]),
            models.Index(fields=["model_name"]),
            models.Index(fields=["timestamp"]),
        )

    def __str__(self) -> str:
        user_info = self.user.email
        return f"{user_info} queried about {self.repo} at {self.timestamp}"
