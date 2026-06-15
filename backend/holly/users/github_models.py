"""
Models for managing multiple GitHub accounts per user.
"""

from allauth.socialaccount.models import SocialAccount, SocialToken
from django.db import models
from django.utils.translation import gettext_lazy as _
from loguru import logger

from .models import User


class UserGitHubAccount(models.Model):
    """
    Model to track multiple GitHub accounts associated with a user.
    Each user can have multiple GitHub accounts connected.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="github_accounts")
    social_account = models.OneToOneField(SocialAccount, on_delete=models.CASCADE, related_name="user_github_account")

    # GitHub account details
    github_login = models.CharField(max_length=255, help_text="GitHub username")
    github_id = models.CharField(max_length=50, help_text="GitHub user ID")
    avatar_url = models.URLField(blank=True, help_text="GitHub avatar URL")

    # Account preferences
    is_primary = models.BooleanField(default=False, help_text="Whether this is the user's primary GitHub account")
    is_active = models.BooleanField(default=True, help_text="Whether this GitHub account is active for the user")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [
            ("user", "github_login"),
            ("user", "social_account"),
        ]
        constraints = [
            # Enforce at most one primary GitHub account per user at the DB level
            # (the save() override alone is racy).
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(is_primary=True),
                name="unique_primary_github_account_per_user",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "is_active"], name="ugha_user_active_idx"),
            models.Index(fields=["user", "is_primary"], name="ugha_user_primary_idx"),
        ]
        verbose_name = _("User GitHub Account")
        verbose_name_plural = _("User GitHub Accounts")

    def __str__(self) -> str:
        primary_indicator = " (Primary)" if self.is_primary else ""
        return f"{self.user.email} -> {self.github_login}{primary_indicator}"

    def get_token(self) -> str | None:
        """Get the OAuth token for this GitHub account."""
        try:
            social_token = SocialToken.objects.get(account=self.social_account, account__provider="github")
            return social_token.token
        except SocialToken.DoesNotExist:
            logger.warning(f"No token found for GitHub account {self.github_login}")
            return None

    def refresh_account_data(self) -> None:
        """Refresh GitHub account data from the social account."""
        if self.social_account and self.social_account.extra_data:
            extra_data = self.social_account.extra_data
            self.github_login = extra_data.get("login", self.github_login)
            self.github_id = str(extra_data.get("id", self.github_id))
            self.avatar_url = extra_data.get("avatar_url", self.avatar_url)
            self.save()

    @classmethod
    def create_from_social_account(
        cls, user: User, social_account: SocialAccount, is_primary: bool = False
    ) -> "UserGitHubAccount":
        """Create a UserGitHubAccount from a SocialAccount."""
        extra_data = social_account.extra_data or {}

        github_account = cls.objects.create(
            user=user,
            social_account=social_account,
            github_login=extra_data.get("login", ""),
            github_id=str(extra_data.get("id", "")),
            avatar_url=extra_data.get("avatar_url", ""),
            is_primary=is_primary,
        )

        # If this is the first GitHub account, make it primary
        if not user.github_accounts.filter(is_primary=True).exists():
            github_account.is_primary = True
            github_account.save()

        return github_account

    def save(self, *args, **kwargs):
        """Override save to ensure only one primary account per user."""
        if self.is_primary:
            # Ensure only one primary account per user
            UserGitHubAccount.objects.filter(user=self.user, is_primary=True).exclude(pk=self.pk).update(
                is_primary=False
            )

        super().save(*args, **kwargs)


class GitHubAccountInstallation(models.Model):
    """
    Model to track GitHub App installations for specific GitHub accounts.
    Links GitHubAppInstallation to UserGitHubAccount for better organization.
    """

    user_github_account = models.ForeignKey(
        UserGitHubAccount, on_delete=models.CASCADE, related_name="app_installations"
    )
    installation_id = models.CharField(max_length=100)
    account_name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=50, choices=[("user", "User"), ("organization", "Organization")])

    # Permissions and scope information
    permissions = models.JSONField(default=dict, help_text="GitHub App permissions")
    repository_selection = models.CharField(
        max_length=50, choices=[("all", "All"), ("selected", "Selected")], default="selected"
    )

    # Metadata
    installed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("user_github_account", "installation_id")]
        verbose_name = _("GitHub Account Installation")
        verbose_name_plural = _("GitHub Account Installations")

    def __str__(self) -> str:
        return f"{self.user_github_account.github_login} - {self.account_name} ({self.installation_id})"
