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
