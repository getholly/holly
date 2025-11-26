"""
API router for GitHub extensions.
"""

from typing import Any

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from loguru import logger
from ninja import Query, Router
from ninja_jwt.authentication import JWTAuth

from holly.github_ext.api.schemas import (
    GitHubRepository,
    InstallationCallbackRequestSchema,
    InstallationCallbackResponseSchema,
    InstallationsResponseSchema,
    InstallationStatusResponseSchema,
    InstallationUrlResponseSchema,
    PullRequestResponseSchema,
    RepositoryFilters,
    RepositorySchema,
)
from holly.github_ext.services.github_app_service import GitHubAppService
from holly.holly.models.mission_conversation import MissionConversation

# Create router
router = Router(auth=JWTAuth())


@router.get("/repositories", response=list[RepositorySchema], summary="List GitHub repositories")
def list_repositories(request: HttpRequest, filters: RepositoryFilters = Query(...)) -> list[dict[str, Any]]:
    """
    List GitHub repositories that the authenticated user has access to.

    Returns a list of repositories from GitHub App installations.

    Parameters:
        - private_only: Filter to only return private repositories if set to true
    """
    app_service = GitHubAppService(request.user)
    try:
        repositories = app_service.list_repositories()

        # Filter repositories based on the private_only flag
        if filters.private_only:
            repositories = [repo for repo in repositories if repo.get("private", False)]

        return repositories
    except Exception as e:
        logger.error(f"Error listing repositories: {e}")
        return []


@router.get("/repository/{github_id}", response=GitHubRepository, summary="Get a Github repo")
def get_repository(request: HttpRequest, github_id: int) -> GitHubRepository | None:
    app_service = GitHubAppService(request.user)
    try:
        repo: GitHubRepository = app_service.get_repository_by_id(github_id)

        return repo
    except Exception as e:
        logger.error(f"Error listing repositories: {e}")
        return None


@router.get("/installations", response=InstallationsResponseSchema, summary="List GitHub App installations")
def list_installations(request: HttpRequest) -> dict[str, Any]:
    """
    List all GitHub App installations for the authenticated user.

    Returns information about the user's GitHub connection status and App installations.
    Now supports multiple GitHub accounts per user.
    """
    try:
        # Import here to avoid circular imports

        # Get the primary GitHub account
        primary_account = request.user.get_primary_github_account()

        if not primary_account:
            return {
                "is_connected": False,
                "social_account": None,
                "installations": [],
            }

        # Get social account info from primary account
        social_info = {
            "login": primary_account.github_login,
            "avatar_url": primary_account.avatar_url,
        }

        # Get installations for all user's GitHub accounts from the new model
        from holly.users.github_models import GitHubAccountInstallation

        all_installations = []
        for github_account in request.user.get_github_accounts():
            installations = GitHubAccountInstallation.objects.filter(user_github_account=github_account)

            for install in installations:
                all_installations.append(
                    {
                        "installation_id": install.installation_id,
                        "account_name": install.account_name,
                        "account_type": install.account_type,
                        "installed_at": install.installed_at.isoformat(),
                        "github_login": github_account.github_login,  # Add which account this belongs to
                    }
                )

        return {
            "is_connected": True,
            "social_account": social_info,
            "installations": all_installations,
        }

    except Exception as e:
        logger.error(f"Error listing installations: {e}")
        return {
            "is_connected": False,
            "social_account": None,
            "installations": [],
        }


@router.post(
    "/pull-request/{mission_conversation_id}", response=PullRequestResponseSchema, summary="Create pull request"
)
def create_pull_request(request: HttpRequest, mission_conversation_id: str) -> dict[str, Any]:
    """Create a pull request for a mission conversation."""
    conversation = get_object_or_404(MissionConversation, id=mission_conversation_id)
    mission = conversation.mission
    repo_detail = mission.repositories.first()
    if repo_detail is None:
        logger.error("No repository associated with mission")
        return {"url": "", "number": 0}

    app_service = GitHubAppService(request.user)
    pr = app_service.create_pull_request(
        owner=repo_detail.username,
        repo=repo_detail.repo,
        head_branch=conversation.title,
        base_branch=repo_detail.branch_name,
        title=f"Auto PR for {conversation.title}",
    )
    if pr is None:
        return {"url": "", "number": 0}
    return {"url": pr.get("html_url", ""), "number": pr.get("number", 0)}


@router.get("/install-url", response=InstallationUrlResponseSchema, summary="Get GitHub App installation URL")
def get_installation_url(request: HttpRequest) -> dict[str, Any]:
    """
    Generate a GitHub App installation URL with CSRF protection.

    Returns the installation URL and state parameter for the authenticated user.
    """
    import time

    from holly.github_ext.github_apps import GitHubAppIntegration

    try:
        # Check if user has a GitHub account using the new UserGitHubAccount model
        primary_account = request.user.get_primary_github_account()
        if not primary_account:
            logger.error("User does not have a GitHub account connected")
            return {"install_url": "", "state": ""}

        # Generate state parameter to prevent CSRF
        state = f"{request.user.id}_{int(time.time())}"

        # Store state in session for validation (if session is available)
        if hasattr(request, "session"):
            request.session["github_app_install_state"] = state

        # Build the installation URL
        github_app = GitHubAppIntegration()
        install_url = github_app.get_installation_url(state)

        return {"install_url": install_url, "state": state}

    except Exception as e:
        logger.error(f"Error generating installation URL: {e}")
        return {"install_url": "", "state": ""}


@router.post(
    "/handle-callback", response=InstallationCallbackResponseSchema, summary="Handle GitHub App installation callback"
)
def handle_installation_callback(request: HttpRequest, payload: InstallationCallbackRequestSchema) -> dict[str, Any]:
    """
    Handle the GitHub App installation callback.

    Processes the installation callback and saves the installation to the database.
    """
    from holly.github_ext.github_apps import GitHubAppIntegration

    try:
        # Verify state to prevent CSRF
        session_state = getattr(request, "session", {}).get("github_app_install_state")
        if session_state and payload.state != session_state:
            logger.warning(f"Invalid state parameter: {payload.state} != {session_state}")
            return {"success": False, "message": "Invalid state parameter", "installation_id": None}

        # Basic state validation (check if it contains user ID)
        try:
            user_id_from_state = payload.state.split("_")[0]
            if str(request.user.id) != user_id_from_state:
                logger.warning(f"State user ID mismatch: {user_id_from_state} != {request.user.id}")
                return {"success": False, "message": "Invalid state parameter", "installation_id": None}
        except (IndexError, ValueError):
            logger.warning(f"Invalid state format: {payload.state}")
            return {"success": False, "message": "Invalid state parameter", "installation_id": None}

        # Get the user's primary GitHub account using the new model
        primary_account = request.user.get_primary_github_account()
        if not primary_account:
            logger.error("GitHub account not connected")
            return {"success": False, "message": "GitHub account not connected", "installation_id": None}

        social_account = primary_account.social_account

        # Get installation info using GitHub App credentials
        github_app = GitHubAppIntegration()
        installation_info = github_app.get_installation_info(payload.installation_id)

        # Save the installation even if we couldn't fetch full info (network issues)
        # We can update the details later when network is stable
        if installation_info:
            account_name = installation_info.get("account", {}).get("login", "")
            account_type = installation_info.get("account", {}).get("type", "").lower()
            permissions = installation_info.get("permissions", {})
            repository_selection = installation_info.get("repository_selection", "selected")
        else:
            logger.warning(
                f"Could not fetch installation info for {payload.installation_id}, saving with minimal data"
            )
            account_name = primary_account.github_login  # Use the connected account name as fallback
            account_type = "user"  # Default assumption
            permissions = {}
            repository_selection = "selected"

        # Save to the new user-centric model
        from holly.users.github_models import GitHubAccountInstallation

        GitHubAccountInstallation.objects.update_or_create(
            user_github_account=primary_account,
            installation_id=payload.installation_id,
            defaults={
                "account_name": account_name,
                "account_type": account_type,
                "permissions": permissions,
                "repository_selection": repository_selection,
            },
        )

        # Clear the state from session
        if hasattr(request, "session") and "github_app_install_state" in request.session:
            del request.session["github_app_install_state"]

        logger.info(
            f"Successfully installed GitHub App for user {request.user.id}, installation {payload.installation_id}"
        )

        return {
            "success": True,
            "message": "GitHub App installed successfully",
            "installation_id": payload.installation_id,
        }

    except Exception as e:
        logger.error(f"Error handling installation callback: {e}")
        return {"success": False, "message": f"An error occurred: {e!s}", "installation_id": None}


@router.get(
    "/installation-status/{installation_id}",
    response=InstallationStatusResponseSchema,
    summary="Get GitHub App installation status",
)
def get_installation_status(request: HttpRequest, installation_id: str) -> dict[str, Any]:
    """
    Get the status of a specific GitHub App installation.

    Returns detailed information about the installation if it exists and is accessible to the user.
    """
    from holly.github_ext.github_apps import GitHubAppIntegration

    try:
        from holly.users.github_models import GitHubAccountInstallation

        # Check if user has access to this installation across all their GitHub accounts
        accounts = request.user.get_github_accounts()
        if not accounts:
            logger.warning(f"User {request.user.id} does not have a GitHub account connected")
            return {"found": False, "installation": None}

        installation = None
        for account in accounts:
            try:
                installation = GitHubAccountInstallation.objects.get(
                    user_github_account=account, installation_id=installation_id
                )
                break
            except GitHubAccountInstallation.DoesNotExist:
                continue

        if not installation:
            logger.warning(f"Installation {installation_id} not found for user {request.user.id} on any account")
            return {"found": False, "installation": None}

        # Get current installation info from GitHub
        github_app = GitHubAppIntegration()
        installation_info = github_app.get_installation_info(installation_id)

        if not installation_info:
            logger.warning(f"Installation {installation_id} not found on GitHub")
            return {"found": False, "installation": None}

        # Extract installation details
        account_info = installation_info.get("account", {})
        permissions = installation_info.get("permissions", {})
        repository_selection = installation_info.get("repository_selection", "unknown")

        installation_details = {
            "installation_id": installation_id,
            "status": "active",  # If we can fetch it, it's active
            "account_name": account_info.get("login", installation.account_name),
            "account_type": account_info.get("type", installation.account_type).lower(),
            "installed_at": installation.installed_at.isoformat(),
            "permissions": permissions,
            "repository_selection": repository_selection,
        }

        return {"found": True, "installation": installation_details}

    except Exception as e:
        logger.error(f"Error getting installation status: {e}")
        return {"found": False, "installation": None}
