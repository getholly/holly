import stat
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import git

from holly.github_ext.utils import FileNode


@dataclass
class RepositoryDetailsDTO:
    username: str
    repo: str
    github_id: str
    commit_hash: str
    languages: dict
    description: str
    stargazers_count: int
    watchers_count: int
    forks_count: int
    open_issues_count: int
    subscribers_count: int
    size: int
    topics: list[str]
    file_tree: list[FileNode]
    file_count: int
    readme: str
    diagram: str
    explanation: str
    private: bool


@dataclass
class GitHubApiRepositoryDetailsDTO:
    github_id: str
    description: str
    private: bool
    created_at: datetime
    updated_at: datetime
    stargazers_count: int
    watchers_count: int
    forks_count: int
    open_issues_count: int
    subscribers_count: int
    size: int
    languages: dict
    topics: list[str]
    readme: str


@dataclass
class FilteredFileTreeDTO:
    filtered_tree: list[FileNode]


# Utility Functions
def error_if_bare_repo(repo: git.Repo):
    if repo.bare:
        error_string = "Repository is bare or invalid."
        raise git.exc.InvalidGitRepositoryError(error_string)


def remove_readonly(func, path: str, excinfo):
    path_obj = Path(path)
    path_obj.chmod(stat.S_IWRITE)
    func(path)


def authenticated_github_url(username: str, repo: str, token: str):
    return f"https://{token}@github.com/{username}/{repo}.git"


# Path to the askpass helper used to supply the token via GIT_ASKPASS rather than
# embedding it in the clone URL / .git/config.
GIT_ASKPASS_SCRIPT = str(Path(__file__).resolve().parent / "git_askpass.sh")


def github_auth_env(token: str) -> dict[str, str]:
    """Build a git environment that authenticates via GIT_ASKPASS.

    Using GIT_ASKPASS keeps the token out of the remote URL and the persisted
    .git/config (and out of process args/logs), while still working for the
    initial clone and subsequent fetch/pull operations.
    """
    return {
        "GIT_ASKPASS": GIT_ASKPASS_SCRIPT,
        "GIT_PASSWORD": token,
        "GIT_TERMINAL_PROMPT": "0",
    }


def tokenless_github_url(username: str, repo: str) -> str:
    """HTTPS URL with only the username component (no secret) for the origin."""
    return f"https://x-access-token@github.com/{username}/{repo}.git"
