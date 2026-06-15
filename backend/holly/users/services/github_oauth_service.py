"""
Service for handling GitHub OAuth flow with multiple account support.
"""

import secrets
from typing import Any
from urllib.parse import urlencode

from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from allauth.socialaccount.providers.github.provider import GitHubProvider
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from loguru import logger
from pydantic import BaseModel

from holly.github_ext.models import GitHubAppInstallation
from holly.users.github_models import GitHubAccountInstallation, UserGitHubAccount
from holly.users.models import User


class GitHubOAuthState(BaseModel):
    """OAuth state data stored temporarily."""

    user_id: int
    redirect_url: str | None = None
    timestamp: int


class GitHubOAuthService:
    """Service for handling GitHub OAuth operations."""

    def __init__(self, request):
        try:
            self.request = request
            # Get the GitHub social application
            self.client_id = settings.GITHUB_CLIENT_ID
            self.client_secret = settings.GITHUB_CLIENT_SECRET
            social_app, _ = SocialApp.objects.get_or_create(
                provider="github",
                defaults={
                    "name": "GitHub",
                    "client_id": self.client_id,
                    "secret": self.client_secret,
                },
            )

            self.provider = GitHubProvider(request, app=social_app)
            self.base_oauth_url = "https://github.com/login/oauth/authorize"
            self.token_url = "https://github.com/login/oauth/access_token"
            self.user_api_url = "https://api.github.com/user"
        except SocialApp.DoesNotExist:
            logger.error("GitHub social application not found", exc_info=True)
            raise Exception("GitHub social application not found")
        except Exception as e:
            logger.error(f"Error initializing GitHub OAuth service: {e}", exc_info=True)
            raise Exception("Failed to initialize GitHub OAuth service")

    def generate_oauth_url(
        self, user: User, redirect_url: str | None = None, scopes: list[str] | None = None
    ) -> tuple[str, str]:
        """
        Generate GitHub OAuth URL for user authentication.

        Returns:
            tuple: (oauth_url, state)
        """
        # Generate secure state
        state = secrets.token_urlsafe(32)

        # Store state data in cache (expires in 10 minutes)
        state_data = GitHubOAuthState(
            user_id=user.id,
            redirect_url=redirect_url,
            timestamp=int(__import__("time").time()),  # Current timestamp
        )

        cache_key = f"github_oauth_state:{state}"
        cache.set(cache_key, state_data.dict(), timeout=600)  # 10 minutes

        # Use configured scopes or defaults
        if scopes is None:
            scopes = settings.SOCIALACCOUNT_PROVIDERS.get("github", {}).get("SCOPE", ["user", "repo"])

        # Build OAuth URL
        params = {
            "client_id": self.client_id,
            "redirect_uri": self._get_callback_url(),
            "scope": " ".join(scopes),
            "state": state,
            "allow_signup": "true",
        }

        oauth_url = f"{self.base_oauth_url}?{urlencode(params)}"

        logger.info(f"Generated OAuth URL for user {user.id} with state {state}/{oauth_url}")
        return oauth_url, state

    def handle_oauth_callback(self, code: str, state: str) -> tuple[bool, str, UserGitHubAccount | None, str | None]:
        """
        Handle GitHub OAuth callback.

        Returns:
            tuple: (success, message, account_info, redirect_url)
        """
        try:
            # Verify and retrieve state data
            cache_key = f"github_oauth_state:{state}"
            state_data_dict = cache.get(cache_key)

            if not state_data_dict:
                return False, "Invalid or expired OAuth state", None, None

            state_data = GitHubOAuthState(**state_data_dict)

            # Clear state from cache
            cache.delete(cache_key)

            # Bind the OAuth state to the authenticated caller: the user who
            # initiated the flow must be the one completing it. Without this an
            # attacker could complete a flow against another user's session and
            # link their GitHub account to the victim (account takeover surface).
            request_user = getattr(self.request, "user", None)
            if request_user is not None and getattr(request_user, "is_authenticated", False):
                if str(request_user.id) != str(state_data.user_id):
                    logger.warning(
                        f"OAuth state user mismatch: state={state_data.user_id} request={request_user.id}"
                    )
                    return False, "OAuth state does not match the authenticated user", None, None

            # Get user
            try:
                user = User.objects.get(id=state_data.user_id)
            except User.DoesNotExist:
                return False, "User not found", None, None

            # Exchange code for access token
            token_data = self._exchange_code_for_token(code)
            if not token_data:
                return False, "Failed to exchange code for token", None, None

            access_token = token_data.get("access_token")
            if not access_token:
                return False, "No access token received", None, None

            # Get GitHub user info
            github_user_data = self._get_github_user_info(access_token)
            if not github_user_data:
                return False, "Failed to retrieve GitHub user information", None, None

            # Create or update social account and user GitHub account
            try:
                github_account = self._create_or_update_github_account(
                    user, access_token, github_user_data, token_data
                )
            except ValueError as err:
                return False, str(err), None, None

            if not github_account:
                return False, "Failed to create GitHub account connection", None, None

            logger.info(f"Successfully connected GitHub account {github_account.github_login} for user {user.id}")

            return True, "GitHub account connected successfully", github_account, state_data.redirect_url

        except Exception as e:
            logger.error(f"Error handling OAuth callback: {e}", exc_info=True)
            return False, f"OAuth callback error: {e!s}", None, None

    def disconnect_github_account(self, user: User, github_login: str) -> tuple[bool, str]:
        """Disconnect a specific GitHub account."""
        try:
            github_account = UserGitHubAccount.objects.get(user=user, github_login=github_login, is_active=True)

            # Mark as inactive instead of deleting to preserve history
            github_account.is_active = False
            github_account.save()

            # If this was the primary account, make another account primary
            if github_account.is_primary:
                next_account = UserGitHubAccount.objects.filter(user=user, is_active=True).first()
                if next_account:
                    next_account.is_primary = True
                    next_account.save()

            logger.info(f"Disconnected GitHub account {github_login} for user {user.id}")
            return True, f"GitHub account {github_login} disconnected successfully"

        except UserGitHubAccount.DoesNotExist:
            return False, "GitHub account not found"
        except Exception as e:
            logger.error(f"Error disconnecting GitHub account: {e}", exc_info=True)
            return False, f"Error disconnecting account: {e!s}"

    def set_primary_account(self, user: User, github_login: str) -> tuple[bool, str]:
        """Set a GitHub account as primary."""
        try:
            github_account = UserGitHubAccount.objects.get(user=user, github_login=github_login, is_active=True)

            # The save method will automatically handle making this primary
            # and removing primary status from other accounts
            github_account.is_primary = True
            github_account.save()

            logger.info(f"Set GitHub account {github_login} as primary for user {user.id}")
            return True, f"GitHub account {github_login} set as primary"

        except UserGitHubAccount.DoesNotExist:
            return False, "GitHub account not found"
        except Exception as e:
            logger.error(f"Error setting primary GitHub account: {e}", exc_info=True)
            return False, f"Error setting primary account: {e!s}"

    def _get_callback_url(self) -> str:
        """Get the OAuth callback URL."""
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
        return f"{frontend_url}/github/oauth/callback"

    def _exchange_code_for_token(self, code: str) -> dict[str, Any] | None:
        """Exchange OAuth code for access token."""
        import requests

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
        }

        headers = {
            "Accept": "application/json",
        }

        try:
            response = requests.post(self.token_url, data=data, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}")
            return None

    def _get_github_user_info(self, access_token: str) -> dict[str, Any] | None:
        """Get GitHub user information using access token."""
        import requests

        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/json",
        }

        try:
            response = requests.get(self.user_api_url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting GitHub user info: {e}")
            return None

    def _ensure_primary_account(self, user: User) -> None:
        """Ensure the given user still has a primary GitHub account."""
        remaining = UserGitHubAccount.objects.filter(user=user, is_active=True)
        if remaining and not remaining.filter(is_primary=True).exists():
            account = remaining.first()
            account.is_primary = True
            account.save(update_fields=["is_primary"])

    def _create_or_update_github_account(
        self, user: User, access_token: str, github_user_data: dict[str, Any], token_data: dict[str, Any]
    ) -> UserGitHubAccount | None:
        """Create or update GitHub account and social account."""
        try:
            github_login = github_user_data.get("login")
            github_id = str(github_user_data.get("id"))

            if not github_login or not github_id:
                logger.error("Missing GitHub login or ID in user data")
                return None

            # Perform all related writes (social account/token reassignment,
            # installation cleanup, primary-account bookkeeping) atomically so a
            # mid-flow failure cannot leave a half-linked account.
            with transaction.atomic():
                return self._persist_github_account(user, access_token, github_user_data, token_data)

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error creating/updating GitHub account: {e}", exc_info=True)
            return None

    def _persist_github_account(
        self,
        user: User,
        access_token: str,
        github_user_data: dict[str, Any],
        token_data: dict[str, Any],
    ) -> UserGitHubAccount | None:
        github_login = github_user_data.get("login")
        github_id = str(github_user_data.get("id"))
        # Get or create SocialApp for GitHub
        social_app, _ = SocialApp.objects.get_or_create(
            provider="github",
            defaults={
                "name": "GitHub",
                "client_id": self.client_id,
                "secret": self.client_secret,
            },
        )

        # Get or create SocialAccount
        social_account, created = SocialAccount.objects.get_or_create(
            provider="github",
            uid=github_id,
            defaults={
                "user": user,
                "extra_data": github_user_data,
            },
        )

        previous_owner = None
        if social_account.user and social_account.user != user:
            previous_owner = social_account.user
            logger.info(
                "Reassigning GitHub social account %s from user %s to user %s",
                github_id,
                social_account.user_id,
                user.id,
            )

        social_account.user = user
        social_account.extra_data = github_user_data
        social_account.save(update_fields=["user", "extra_data"])

        # Create or update SocialToken
        social_token, _ = SocialToken.objects.update_or_create(
            account=social_account,
            app=social_app,
            defaults={
                "token": access_token,
                "token_secret": token_data.get("refresh_token", ""),
            },
        )

        # Create or update UserGitHubAccount

        existing_account = UserGitHubAccount.objects.filter(social_account=social_account).first()

        if previous_owner and existing_account:
            GitHubAccountInstallation.objects.filter(user_github_account=existing_account).delete()
            GitHubAppInstallation.objects.filter(social_account=social_account).delete()
        active_accounts = UserGitHubAccount.objects.filter(user=user, is_active=True)
        if existing_account and existing_account.user == user:
            active_accounts_excluding_current = active_accounts.exclude(pk=existing_account.pk)
        else:
            active_accounts_excluding_current = active_accounts

        should_be_primary = not active_accounts_excluding_current.exists()

        if existing_account:
            old_owner = existing_account.user if existing_account.user != user else None
            existing_account.user = user
            existing_account.github_login = github_login
            existing_account.github_id = github_id
            existing_account.avatar_url = github_user_data.get("avatar_url", "")
            existing_account.is_active = True
            existing_account.is_primary = should_be_primary
            existing_account.save()

            if old_owner:
                self._ensure_primary_account(old_owner)

            github_account = existing_account
        else:
            defaults = {
                "github_login": github_login,
                "github_id": github_id,
                "avatar_url": github_user_data.get("avatar_url", ""),
                "is_active": True,
                "is_primary": should_be_primary,
            }

            github_account = UserGitHubAccount.objects.create(
                user=user,
                social_account=social_account,
                **defaults,
            )

        return github_account
