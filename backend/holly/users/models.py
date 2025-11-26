from typing import ClassVar, Optional

from django.contrib.auth.models import AbstractUser
from django.db.models import BooleanField, CharField, EmailField
from django.utils.translation import gettext_lazy as _
from loguru import logger

from .managers import UserManager


class User(AbstractUser):
    """
    Default custom user model for {{cookiecutter.project_name}}.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]
    email = EmailField(_("email address"), unique=True)
    username = None  # type: ignore[assignment]

    stripe_customer_id = CharField(max_length=255, blank=True, default="", help_text="Stripe customer ID")
    tour_completed = BooleanField(default=False, help_text="Whether the user has completed the onboarding tour")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = []

    objects: ClassVar[UserManager] = UserManager()

    def get_github_token(self) -> str:
        """Get the user's GitHub token using the new UserGitHubAccount model.

        Returns:
            str: GitHub token.

        """
        primary_account = self.get_primary_github_account()
        if not primary_account:
            logger.error("User does not have a GitHub account connected")
            raise ValueError("No GitHub account connected")

        token = primary_account.get_token()
        if not token:
            logger.error("User does not have a GitHub token")
            raise ValueError("No GitHub token available")

        return token

    def get_primary_github_account(self) -> Optional["UserGitHubAccount"]:
        """Get the user's primary GitHub account."""
        # Import here to avoid circular imports

        try:
            return self.github_accounts.filter(is_primary=True).first()
        except Exception:
            return None

    def get_github_accounts(self) -> list["UserGitHubAccount"]:
        """Get all active GitHub accounts for this user."""
        # Import here to avoid circular imports

        return list(self.github_accounts.filter(is_active=True))

    def has_github_account(self) -> bool:
        """Check if user has any GitHub accounts connected."""
        return self.github_accounts.filter(is_active=True).exists()

    def get_github_token_for_account(self, github_login: str) -> str | None:
        """Get GitHub token for a specific account."""
        github_account = self.github_accounts.filter(github_login=github_login, is_active=True).first()

        if github_account:
            return github_account.get_token()
        return None
