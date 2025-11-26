"""
Utility module for handling GitHub authentication with both OAuth and GitHub Apps.
"""

from typing import Any

from django.contrib.auth import get_user_model
from loguru import logger

from holly.github_ext.github_apps import GitHubAppIntegration

User = get_user_model()


def get_github_oauth_token(user: User) -> str | None:
    """
    Get the GitHub OAuth token for a user using the new UserGitHubAccount model.

    Args:
        user: The Django user

    Returns:
        Optional[str]: The OAuth token if available, None otherwise
    """
    primary_account = user.get_primary_github_account()
    if not primary_account:
        return None

    return primary_account.get_token()


def get_github_app_installations(user: User) -> list:
    """
    Get all GitHub App installations for a user using the new UserGitHubAccount model.

    Args:
        user: The Django user

    Returns:
        List[GitHubAccountInstallation]: List of GitHub App installations
    """
    from holly.users.github_models import GitHubAccountInstallation

    installations = []

    # Get installations for all user's GitHub accounts via the new model
    for github_account in user.get_github_accounts():
        account_installations = GitHubAccountInstallation.objects.filter(
            user_github_account=github_account
        )
        installations.extend(account_installations)

    return installations


def get_github_app_token(user: User, repository: str | None = None) -> list[tuple[str, str]] | None:
    """
    Get a GitHub App installation token for a user, optionally for a specific repository.

    Args:
        user: The Django user
        repository: Optional repository in the format "owner/repo"

    Returns:
        list[tuple[str, str]] | None: A list of tuple of (token, installation_id) if available, None otherwise
    """
    installations = get_github_app_installations(user)

    if not installations:
        return None

    # If a specific repository is requested, we should find the correct installation
    # For simplicity, we'll just use the first installation
    # In a real-world scenario, you would check which installation has access to the specific repo
    tokens: list[tuple[str, str]] = []
    for installation in installations:
        try:
            github_app = GitHubAppIntegration()
            token = github_app.get_installation_token(installation.installation_id)
            if token:
                tokens.append((token, installation.installation_id))
        except Exception as e:  # noqa: BLE001
            logger.error(
                f"Failed to get token for installation {getattr(installation, 'installation_id', 'unknown')}: {e}"
            )
            # Continue trying other installations rather than failing all
            continue
    return tokens if tokens else None


def get_best_github_auth(user: User, repository: str | None = None) -> list[dict[str, Any]]:
    """
    Get the best available GitHub authentication method for a user.
    Tries GitHub App token first, falls back to OAuth token.

    Args:
        user: The Django user
        repository: Optional repository in the format "owner/repo"

    Returns:
        list[dict[str, Any]]: A list of Authentication info with type, token, and possibly installation_id
    """
    # Try GitHub App first
    app_auths = get_github_app_token(user, repository)

    if app_auths:
        auths = []
        for app_auth in app_auths:
            token, installation_id = app_auth
            auths.append({"type": "github_app", "token": token, "installation_id": installation_id})
        return auths

    # Fall back to OAuth
    oauth_token = get_github_oauth_token(user)

    if oauth_token:
        return [{"type": "oauth", "token": oauth_token}]

    # No auth available
    return [{"type": "none", "token": None}]


def create_auth_headers(auth_info: dict[str, Any]) -> dict[str, str]:
    """
    Create HTTP headers for GitHub API requests based on auth info.

    Args:
        auth_info: Authentication info from get_best_github_auth

    Returns:
        Dict[str, str]: HTTP headers for GitHub API
    """
    headers = {"Accept": "application/vnd.github.v3+json"}

    if auth_info["type"] == "oauth" or auth_info["type"] == "github_app":
        headers["Authorization"] = f"token {auth_info['token']}"

    return headers


def get_repository_url_with_auth(auth_info: dict[str, Any], owner: str, repo: str) -> str:
    """
    Create an authenticated URL for git operations.

    Args:
        auth_info: Authentication info from get_best_github_auth
        owner: Repository owner
        repo: Repository name

    Returns:
        str: Repository URL with authentication
    """
    if auth_info["type"] == "oauth":
        return f"https://{auth_info['token']}@github.com/{owner}/{repo}.git"
    if auth_info["type"] == "github_app":
        return f"https://x-access-token:{auth_info['token']}@github.com/{owner}/{repo}.git"
    return f"https://github.com/{owner}/{repo}.git"
