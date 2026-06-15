"""Module for GitHub Apps integration with Django Allauth."""

import time
from pathlib import Path
from typing import Any

import jwt
import requests
from django.conf import settings
from loguru import logger


class GitHubAppError(Exception):
    """Base exception for GitHub App errors."""


class GitHubAppAuthError(GitHubAppError):
    """Exception for GitHub App authentication errors."""


class GitHubAppIntegration:
    """Helper class for GitHub App integration."""

    def __init__(self):
        """Initialize GitHub App integration with settings."""
        self.app_id = settings.GITHUB_APP_ID
        self.app_name = settings.GITHUB_APP_NAME
        key_path = Path(settings.GITHUB_APP_PRIVATE_KEY_PATH)
        self.private_key = key_path.read_text()

        if not all([self.app_id, self.app_name, self.private_key]):
            raise GitHubAppError("GitHub App settings are not properly configured.")

    def generate_jwt(self) -> str:
        """
        Generate a JWT for GitHub App authentication.

        Returns:
            str: JWT token for GitHub App authentication
        """
        now = int(time.time())
        # GitHub requires exp to be max 10 minutes in the future
        # Use 9 minutes to account for clock skew
        payload = {
            "iat": now - 60,  # Issued 1 minute ago to account for clock skew
            "exp": now + (9 * 60),  # Expires in 9 minutes
            "iss": int(self.app_id)
        }

        return jwt.encode(payload, self.private_key, algorithm="RS256")

    def get_installation_info(self, installation_id: str) -> dict[str, Any] | None:
        """
        Get information about a GitHub App installation.

        Args:
            installation_id: The GitHub App installation ID

        Returns:
            dict: Installation information or None if request failed
        """
        jwt_token = self.generate_jwt()

        headers = {"Authorization": f"Bearer {jwt_token}", "Accept": "application/vnd.github.v3+json"}

        response = requests.get(f"https://api.github.com/app/installations/{installation_id}", headers=headers,
                                timeout=30)

        if response.status_code == 200:
            return response.json()
        return None

    def get_installation_token(self, installation_id: str) -> str | None:
        """
        Get an installation access token for a specific installation.

        Args:
            installation_id: The GitHub App installation ID

        Returns:
            str: Installation token or None if request failed
        """
        jwt_token = self.generate_jwt()

        headers = {"Authorization": f"Bearer {jwt_token}", "Accept": "application/vnd.github.v3+json"}

        response = requests.post(
            f"https://api.github.com/app/installations/{installation_id}/access_tokens",
            headers=headers,
            timeout=30,
        )

        if response.status_code == 201:
            return response.json().get("token")
        # Do not log the raw response body of a token endpoint (may contain
        # sensitive material); log only the status code.
        logger.error(f"Failed to get installation token from github (status {response.status_code})")
        return None

    def get_installation_url(self, state: str) -> str:
        """
        Generate the URL for installing the GitHub App.

        Args:
            state: State parameter to prevent CSRF

        Returns:
            str: URL for GitHub App installation
        """
        return f"https://github.com/apps/{self.app_name}/installations/new?state={state}"
