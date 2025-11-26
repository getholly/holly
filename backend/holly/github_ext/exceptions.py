class GitHubServiceError(Exception):
    """Base class for GitHub service exceptions."""


class GitHubService403Error(GitHubServiceError):
    """Exception raised when GitHub returns a 403 error."""


class GitHubServiceNotFoundError(GitHubServiceError):
    """Exception raised when a GitHub repository is not found (404)."""
