"""
Pydantic schemas for GitHub OAuth API endpoints.
"""

from pydantic import BaseModel, Field


class GitHubOAuthInitiateRequest(BaseModel):
    """Request schema for initiating GitHub OAuth flow."""

    redirect_url: str | None = Field(
        default=None, description="URL to redirect to after successful OAuth (defaults to frontend connect page)"
    )
    scopes: list[str] | None = Field(
        default=None, description="Additional GitHub scopes to request (defaults to configured scopes)"
    )


class GitHubOAuthInitiateResponse(BaseModel):
    """Response schema for GitHub OAuth initiation."""

    oauth_url: str = Field(description="GitHub OAuth URL to redirect user to")
    state: str = Field(description="OAuth state parameter for security")


class GitHubAccountInfo(BaseModel):
    """Schema for GitHub account information."""

    github_login: str = Field(description="GitHub username")
    github_id: str = Field(description="GitHub user ID")
    avatar_url: str = Field(description="GitHub avatar URL")
    is_primary: bool = Field(description="Whether this is the primary account")
    is_active: bool = Field(description="Whether this account is active")
    created_at: str = Field(description="When the account was connected (ISO format)")


class GitHubAccountListResponse(BaseModel):
    """Response schema for listing user's GitHub accounts."""

    accounts: list[GitHubAccountInfo] = Field(description="List of connected GitHub accounts")
    total_count: int = Field(description="Total number of connected accounts")


class GitHubAccountActionRequest(BaseModel):
    """Request schema for GitHub account actions."""

    github_login: str = Field(description="GitHub username to perform action on")


class GitHubAccountActionResponse(BaseModel):
    """Response schema for GitHub account actions."""

    success: bool = Field(description="Whether the action was successful")
    message: str = Field(description="Response message")


class GitHubOAuthCallbackRequest(BaseModel):
    """Request schema for OAuth callback handling."""

    code: str = Field(description="OAuth authorization code from GitHub")
    state: str = Field(description="OAuth state parameter for verification")


class GitHubOAuthCallbackResponse(BaseModel):
    """Response schema for OAuth callback."""

    success: bool = Field(description="Whether OAuth was successful")
    message: str = Field(description="Response message")
    account_info: GitHubAccountInfo | None = Field(default=None, description="Information about the connected account")
    redirect_url: str | None = Field(default=None, description="URL to redirect to after successful connection")


class ConnectionStatusResponse(BaseModel):
    """Response schema for GitHub connection status."""

    is_connected: bool = Field(description="Whether user has any GitHub accounts")
    primary_account: GitHubAccountInfo | None = Field(default=None, description="Primary GitHub account information")
    total_accounts: int = Field(description="Total number of connected accounts")
