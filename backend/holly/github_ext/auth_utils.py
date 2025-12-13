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


def get_github_app_installations(user: User, installation_id: str | None = None) -> list:
    """
    Get all GitHub App installations for a user using the new UserGitHubAccount model.

    Args:
        user: The Django user
        installation_id: Optional specific installation ID to look for

    Returns:
        List[GitHubAccountInstallation]: List of GitHub App installations
    """
    from holly.users.github_models import GitHubAccountInstallation

    installations = []

    # If a specific installation_id is provided, try to find it directly first
    if installation_id:
        # Try to find by installation_id across all user's accounts
        github_accounts = user.get_github_accounts()
        account_ids = [acc.id for acc in github_accounts]
        if account_ids:
            # Try both string and int versions of installation_id
            direct_installations = GitHubAccountInstallation.objects.filter(
                user_github_account__id__in=account_ids,
                installation_id=str(installation_id)
            )
            if direct_installations.exists():
                return list(direct_installations)
            # Also try as int if it's numeric
            try:
                int_id = int(installation_id)
                direct_installations = GitHubAccountInstallation.objects.filter(
                    user_github_account__id__in=account_ids,
                    installation_id=str(int_id)
                )
                if direct_installations.exists():
                    return list(direct_installations)
            except ValueError:
                pass

    # Get installations for all user's GitHub accounts via the new model
    github_accounts = user.get_github_accounts()
    
    for github_account in github_accounts:
        account_installations = GitHubAccountInstallation.objects.filter(
            user_github_account=github_account
        )
        installations.extend(account_installations)

    # Also check if there are any installations linked to any of the user's accounts
    # This is a fallback in case the installation was saved but the account relationship is wrong
    if not installations:
        # Get all UserGitHubAccount IDs for this user
        account_ids = [acc.id for acc in github_accounts]
        if account_ids:
            all_installations = GitHubAccountInstallation.objects.filter(
                user_github_account__id__in=account_ids
            )
            installations = list(all_installations)

    return installations


def sync_installations_from_github(user: User) -> list:
    """
    Discover and sync GitHub App installations from GitHub API to the database.
    This is useful when installations exist on GitHub but aren't in our database.

    Args:
        user: The Django user

    Returns:
        List[GitHubAccountInstallation]: List of synced installations
    """
    from holly.users.github_models import GitHubAccountInstallation

    github_app = GitHubAppIntegration()
    all_installations = github_app.list_all_installations()
    
    if not all_installations:
        return []

    # Get user's GitHub accounts
    github_accounts = user.get_github_accounts()
    account_logins = {acc.github_login.lower(): acc for acc in github_accounts}
    account_ids = {acc.github_id: acc for acc in github_accounts}
    
    synced_installations = []
    
    for inst in all_installations:
        inst_id = str(inst.get("id"))
        account_info = inst.get("account", {})
        account_login = account_info.get("login", "").lower()
        account_id = str(account_info.get("id", ""))
        
        # Try to match by login or ID
        matched_account = None
        if account_login in account_logins:
            matched_account = account_logins[account_login]
        elif account_id in account_ids:
            matched_account = account_ids[account_id]
        
        if matched_account:
            installation, created = GitHubAccountInstallation.objects.update_or_create(
                user_github_account=matched_account,
                installation_id=inst_id,
                defaults={
                    "account_name": account_info.get("login", ""),
                    "account_type": account_info.get("type", "user").lower(),
                    "permissions": inst.get("permissions", {}),
                    "repository_selection": inst.get("repository_selection", "selected"),
                },
            )
            synced_installations.append(installation)
    
    if synced_installations:
        logger.info(f"[sync_installations_from_github] Synced {len(synced_installations)} installation(s) from GitHub")
    
    return synced_installations


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

    # If no installations found in database, try to sync from GitHub
    if not installations:
        try:
            synced = sync_installations_from_github(user)
            if synced:
                installations = get_github_app_installations(user)
        except Exception as e:
            logger.error(f"[get_github_app_token] Failed to sync installations from GitHub: {e}", exc_info=True)

    if not installations:
        return None

    # If a specific repository is requested, we should find the correct installation
    # For simplicity, we'll just use the first installation
    # In a real-world scenario, you would check which installation has access to the specific repo
    tokens: list[tuple[str, str]] = []
    for installation in installations:
        try:
            github_app = GitHubAppIntegration()
            token = github_app.get_installation_token(str(installation.installation_id))
            if token:
                tokens.append((token, str(installation.installation_id)))
            else:
                logger.error(
                    f"[get_github_app_token] Failed to get token for installation {installation.installation_id}"
                )
        except Exception as e:  # noqa: BLE001
            logger.error(
                f"[get_github_app_token] Exception getting token for installation {installation.installation_id}: {e}",
                exc_info=True
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
    logger.warning(f"[get_best_github_auth] No authentication available for user {user.id}")
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
