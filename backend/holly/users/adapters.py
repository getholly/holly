from __future__ import annotations

import typing

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from loguru import logger

if typing.TYPE_CHECKING:
    from allauth.socialaccount.models import SocialLogin
    from django.http import HttpRequest

    from holly.users.models import User


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(
        self,
        request: HttpRequest,
        sociallogin: SocialLogin,
    ) -> bool:
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)

    def populate_user(
        self,
        request: HttpRequest,
        sociallogin: SocialLogin,
        data: dict[str, typing.Any],
    ) -> User:
        """
        Populates user information from social provider info.

        See: https://docs.allauth.org/en/latest/socialaccount/advanced.html#creating-and-populating-user-instances
        """
        user = super().populate_user(request, sociallogin, data)
        if not user.name:
            if name := data.get("name"):
                user.name = name
            elif first_name := data.get("first_name"):
                user.name = first_name
                if last_name := data.get("last_name"):
                    user.name += f" {last_name}"
        return user

    def pre_social_login(self, request: HttpRequest, sociallogin: SocialLogin) -> None:
        """
        Called when a user is about to sign in via a social account.
        This is called before the social account is connected to the user.
        """
        super().pre_social_login(request, sociallogin)

        # If this is a GitHub login and the user is already authenticated,
        # we don't need to do anything here as the OAuth service will handle
        # creating the UserGitHubAccount
        if sociallogin.account.provider == "github" and request.user.is_authenticated:
            logger.info(f"GitHub social login for authenticated user {request.user.id}")

    def save_user(self, request: HttpRequest, sociallogin: SocialLogin, form=None) -> User:
        """
        Called when a social account is connected to a user.
        This creates the UserGitHubAccount relationship.
        """
        user = super().save_user(request, sociallogin, form)

        # If this is a GitHub account, create the UserGitHubAccount
        if sociallogin.account.provider == "github":
            try:
                from holly.users.github_models import UserGitHubAccount

                # Check if UserGitHubAccount already exists
                if not UserGitHubAccount.objects.filter(user=user, social_account=sociallogin.account).exists():
                    # Determine if this should be the primary account
                    is_primary = not UserGitHubAccount.objects.filter(user=user, is_active=True).exists()

                    # Create UserGitHubAccount
                    UserGitHubAccount.create_from_social_account(
                        user=user, social_account=sociallogin.account, is_primary=is_primary
                    )

                    logger.info(
                        f"Created UserGitHubAccount for user {user.id} with GitHub login {sociallogin.account.extra_data.get('login', '')}"
                    )

            except Exception as e:
                logger.error(f"Error creating UserGitHubAccount: {e}", exc_info=True)

        return user
