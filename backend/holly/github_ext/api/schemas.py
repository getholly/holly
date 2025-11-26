from typing import Any

from pydantic import BaseModel, Field
from pydantic_core import Url


class RepositorySchema(BaseModel):
    """Schema for GitHub repository data."""

    id: int = Field(..., description="GitHub ID")
    name: str = Field(..., description="Repository name")
    full_name: str = Field(..., description="Full name of repository (owner/name)")
    owner: dict[str, Any] = Field(..., description="Repository owner details")
    html_url: str = Field(..., description="Repository URL")
    description: str | None = Field(None, description="Repository description")
    private: bool = Field(..., description="Whether the repository is private")
    fork: bool = Field(..., description="Whether the repository is a fork")
    stargazers_count: int = Field(0, description="Number of stars")
    watchers_count: int = Field(0, description="Number of watchers")
    forks_count: int = Field(0, description="Number of forks")
    open_issues_count: int = Field(0, description="Number of open issues")
    default_branch: str = Field(..., description="Default branch name")
    created_at: str | None = Field(None, description="Repository creation date")
    updated_at: str | None = Field(None, description="Repository last update date")
    pushed_at: str | None = Field(None, description="Repository last push date")
    topics: list[str] | None = Field(None, description="Repository topics")


class RepositoryFilters(BaseModel):
    """Filters for GitHub repositories."""

    private_only: bool = Field(False, description="Filter to only private repositories")


class InstallationSchema(BaseModel):
    """Schema for GitHub App installation data."""

    installation_id: str = Field(..., description="GitHub App installation ID")
    account_name: str = Field(..., description="Account name (user or organization)")
    account_type: str = Field(..., description="Account type (user or organization)")
    installed_at: str = Field(..., description="Installation date")


class SocialAccountInfoSchema(BaseModel):
    """Schema for user's social account info."""

    login: str = Field(..., description="GitHub username")
    avatar_url: str = Field(..., description="GitHub avatar URL")


class InstallationsResponseSchema(BaseModel):
    """Schema for response to installations endpoint."""

    is_connected: bool = Field(..., description="Whether user is connected to GitHub")
    social_account: SocialAccountInfoSchema | None = Field(None, description="GitHub social account info if connected")
    installations: list[InstallationSchema] = Field([], description="List of GitHub App installations")


class Owner(BaseModel):
    login: str
    id: int
    node_id: str
    avatar_url: Url | None
    url: Url
    html_url: Url
    type: str
    site_admin: bool


class License(BaseModel):
    key: str
    name: str
    spdx_id: str
    url: Url | None
    node_id: str


class GitHubRepository(BaseModel):
    id: int
    node_id: str
    name: str
    full_name: str
    private: bool
    owner: Owner
    html_url: Url
    description: str | None
    fork: bool
    url: Url
    created_at: str
    updated_at: str
    pushed_at: str
    homepage: str | None
    size: int
    stargazers_count: int
    watchers_count: int
    language: str | None
    forks_count: int
    open_issues_count: int
    license: License | None
    default_branch: str
    visibility: str = Field(default="public")


class PullRequestResponseSchema(BaseModel):
    """Schema for pull request creation response."""

    url: Url = Field(..., description="Pull request URL")
    number: int = Field(..., description="Pull request number")


class InstallationUrlResponseSchema(BaseModel):
    """Schema for GitHub App installation URL response."""

    install_url: str = Field(..., description="GitHub App installation URL")
    state: str = Field(..., description="State parameter for CSRF protection")


class InstallationCallbackRequestSchema(BaseModel):
    """Schema for GitHub App installation callback request."""

    installation_id: str = Field(..., description="GitHub App installation ID")
    state: str = Field(..., description="State parameter for CSRF protection")


class InstallationCallbackResponseSchema(BaseModel):
    """Schema for GitHub App installation callback response."""

    success: bool = Field(..., description="Whether the installation was successful")
    message: str = Field(..., description="Success or error message")
    installation_id: str | None = Field(None, description="Installation ID if successful")


class InstallationStatusSchema(BaseModel):
    """Schema for GitHub App installation status."""

    installation_id: str = Field(..., description="GitHub App installation ID")
    status: str = Field(..., description="Installation status (active, suspended, deleted)")
    account_name: str = Field(..., description="Account name (user or organization)")
    account_type: str = Field(..., description="Account type (user or organization)")
    installed_at: str = Field(..., description="Installation date")
    permissions: dict[str, str] = Field(default_factory=dict, description="Installation permissions")
    repository_selection: str = Field(..., description="Repository selection (all or selected)")


class InstallationStatusResponseSchema(BaseModel):
    """Schema for GitHub App installation status response."""

    found: bool = Field(..., description="Whether the installation was found")
    installation: InstallationStatusSchema | None = Field(None, description="Installation details if found")
