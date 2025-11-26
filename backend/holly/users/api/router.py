"""
Django-ninja API router for GitHub OAuth operations.
"""

from django.http import HttpRequest
from loguru import logger
from ninja import Router
from ninja_jwt.authentication import JWTAuth

from holly.users.api.schemas import (
    ConnectionStatusResponse,
    GitHubAccountActionRequest,
    GitHubAccountActionResponse,
    GitHubAccountInfo,
    GitHubAccountListResponse,
    GitHubOAuthCallbackRequest,
    GitHubOAuthCallbackResponse,
    GitHubOAuthInitiateRequest,
    GitHubOAuthInitiateResponse,
)
from holly.users.github_models import UserGitHubAccount
from holly.users.services.github_oauth_service import GitHubOAuthService

# Create router with JWT authentication
router = Router(auth=JWTAuth())


@router.post("/github/oauth/initiate", response=GitHubOAuthInitiateResponse)
def initiate_github_oauth(request: HttpRequest, data: GitHubOAuthInitiateRequest) -> GitHubOAuthInitiateResponse:
    """
    Initiate GitHub OAuth flow for the authenticated user.

    This endpoint generates a GitHub OAuth URL that the frontend can redirect to.
    The user will be redirected back to the frontend callback page after authorization.
    """
    try:
        oauth_service = GitHubOAuthService(request)

        oauth_url, state = oauth_service.generate_oauth_url(
            user=request.user, redirect_url=data.redirect_url, scopes=data.scopes
        )

        return GitHubOAuthInitiateResponse(oauth_url=oauth_url, state=state)

    except Exception as e:
        logger.error(f"Error initiating GitHub OAuth: {e}", exc_info=True)
        raise Exception("Failed to initiate GitHub OAuth")


@router.post("/github/oauth/callback", response=GitHubOAuthCallbackResponse)
def handle_github_oauth_callback(request: HttpRequest, data: GitHubOAuthCallbackRequest) -> GitHubOAuthCallbackResponse:
    """
    Handle GitHub OAuth callback.

    This endpoint processes the OAuth callback from GitHub and creates/updates
    the user's GitHub account connection.
    """
    try:
        oauth_service = GitHubOAuthService(request)

        success, message, github_account, redirect_url = oauth_service.handle_oauth_callback(
            code=data.code, state=data.state
        )

        account_info = None
        if github_account:
            account_info = GitHubAccountInfo(
                github_login=github_account.github_login,
                github_id=github_account.github_id,
                avatar_url=github_account.avatar_url,
                is_primary=github_account.is_primary,
                is_active=github_account.is_active,
                created_at=github_account.created_at.isoformat(),
            )

        return GitHubOAuthCallbackResponse(
            success=success, message=message, account_info=account_info, redirect_url=redirect_url
        )

    except Exception as e:
        logger.error(f"Error handling GitHub OAuth callback: {e}", exc_info=True)
        return GitHubOAuthCallbackResponse(success=False, message=f"OAuth callback error: {e!s}")


@router.get("/github/accounts", response=GitHubAccountListResponse)
def list_github_accounts(request: HttpRequest) -> GitHubAccountListResponse:
    """
    List all GitHub accounts connected to the authenticated user.
    """
    try:
        github_accounts = UserGitHubAccount.objects.filter(user=request.user, is_active=True).order_by(
            "-is_primary", "github_login"
        )

        accounts_data = []
        for account in github_accounts:
            accounts_data.append(
                GitHubAccountInfo(
                    github_login=account.github_login,
                    github_id=account.github_id,
                    avatar_url=account.avatar_url,
                    is_primary=account.is_primary,
                    is_active=account.is_active,
                    created_at=account.created_at.isoformat(),
                )
            )

        return GitHubAccountListResponse(accounts=accounts_data, total_count=len(accounts_data))

    except Exception as e:
        logger.error(f"Error listing GitHub accounts: {e}", exc_info=True)
        return GitHubAccountListResponse(accounts=[], total_count=0)


@router.get("/github/connection-status", response=ConnectionStatusResponse)
def get_github_connection_status(request: HttpRequest) -> ConnectionStatusResponse:
    """
    Get the current GitHub connection status for the authenticated user.
    """
    try:
        primary_account = request.user.get_primary_github_account()
        total_accounts = request.user.github_accounts.filter(is_active=True).count()

        primary_account_info = None
        if primary_account:
            primary_account_info = GitHubAccountInfo(
                github_login=primary_account.github_login,
                github_id=primary_account.github_id,
                avatar_url=primary_account.avatar_url,
                is_primary=primary_account.is_primary,
                is_active=primary_account.is_active,
                created_at=primary_account.created_at.isoformat(),
            )

        return ConnectionStatusResponse(
            is_connected=request.user.has_github_account(),
            primary_account=primary_account_info,
            total_accounts=total_accounts,
        )

    except Exception as e:
        logger.error(f"Error getting GitHub connection status: {e}", exc_info=True)
        return ConnectionStatusResponse(is_connected=False, primary_account=None, total_accounts=0)


@router.post("/github/disconnect", response=GitHubAccountActionResponse)
def disconnect_github_account(request: HttpRequest, data: GitHubAccountActionRequest) -> GitHubAccountActionResponse:
    """
    Disconnect a specific GitHub account from the authenticated user.
    """
    try:
        oauth_service = GitHubOAuthService(request)

        success, message = oauth_service.disconnect_github_account(user=request.user, github_login=data.github_login)

        return GitHubAccountActionResponse(success=success, message=message)

    except Exception as e:
        logger.error(f"Error disconnecting GitHub account: {e}", exc_info=True)
        return GitHubAccountActionResponse(success=False, message=f"Error disconnecting account: {e!s}")


@router.post("/github/set-primary", response=GitHubAccountActionResponse)
def set_primary_github_account(request: HttpRequest, data: GitHubAccountActionRequest) -> GitHubAccountActionResponse:
    """
    Set a specific GitHub account as the primary account for the authenticated user.
    """
    try:
        oauth_service = GitHubOAuthService(request)

        success, message = oauth_service.set_primary_account(user=request.user, github_login=data.github_login)

        return GitHubAccountActionResponse(success=success, message=message)

    except Exception as e:
        logger.error(f"Error setting primary GitHub account: {e}", exc_info=True)
        return GitHubAccountActionResponse(success=False, message=f"Error setting primary account: {e!s}")
