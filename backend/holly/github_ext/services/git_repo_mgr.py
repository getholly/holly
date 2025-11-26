import shutil
from functools import cached_property
from pathlib import Path

import git
from django.conf import settings
from git import GitCommandError
from loguru import logger

from holly.github_ext.exceptions import GitHubService403Error
from holly.github_ext.helpers import authenticated_github_url, error_if_bare_repo, remove_readonly


class GitRepositoryManager:
    def __init__(self, username, repo, token: str, repo_base_path: str = settings.REPO_BASE_PATH):
        self.token = token
        self.username = username
        self.repo = repo
        self.repo_base_path = Path(repo_base_path)
        self.repo_base_path.mkdir(parents=True, exist_ok=True)

        self._repo: git.Repo | None = None

    def _clone_or_update_repo(self) -> git.Repo:
        clone_path = self.repo_path.resolve()

        if clone_path.exists():
            try:
                repo_obj = git.Repo(clone_path)
                error_if_bare_repo(repo_obj)
                self._fetch_latest_changes(repo_obj)
            except (git.exc.GitCommandError, git.exc.InvalidGitRepositoryError) as e:
                logger.error(f"Failed to update repo at {clone_path}: {e}. Deleting and re-cloning.")
                try:
                    repo_obj = self._clone_repo()
                except GitCommandError as e:
                    if "403" in str(e):
                        error_string = "Access denied. Please check your GitHub token."
                        raise GitHubService403Error(error_string) from e
                    raise
        else:
            try:
                repo_obj = self._clone_repo()
            except GitCommandError as e:
                if "403" in str(e):
                    error_string = "Access denied. Please check your GitHub token."
                    raise GitHubService403Error(error_string) from e
                raise
        return repo_obj

    def _fetch_latest_changes(self, repo_obj: git.Repo):
        """Fetches the latest changes from the remote repository."""
        logger.info(f"Fetching latest changes for {self.username}/{self.repo} in {repo_obj.working_dir}")
        origin = repo_obj.remotes.origin
        origin.fetch()
        logger.info("Repository successfully updated.")

    def _clone_repo(self) -> git.Repo:
        clone_path = self.repo_path.resolve()
        repo_url = authenticated_github_url(self.username, self.repo, self.token)
        shutil.rmtree(str(clone_path), ignore_errors=True, onerror=remove_readonly)
        logger.info(f"Cloning repository from {self.username}/{self.repo} to {clone_path}")
        return git.Repo.clone_from(repo_url, str(clone_path), multi_options=["--depth=1"])

    def delete_repo(self):
        """Delete the local repository."""
        if self._repo:
            del self._repo  # Ensure the repo object is deleted
            self._repo = None  # Prevent reuse

        if self.repo_path.exists():
            shutil.rmtree(str(self.repo_path), ignore_errors=False, onerror=remove_readonly)
            logger.info(f"Deleted local repository at {self.repo_path}")

    def get_repo(self) -> git.Repo:
        """Lazy-load repository instance to avoid keeping it open unnecessarily."""
        if self._repo is None:
            self._repo = self._clone_or_update_repo()
        return self._repo

    @cached_property
    def get_file_count(self) -> int:
        """Returns the number of files in the repository."""
        repo = self.get_repo()  # Ensure repo is initialized
        return len(repo.git.ls_files().splitlines())

    @cached_property
    def repo_path(self) -> Path:
        return self.repo_base_path / self.username / self.repo

    def _get_file_content(self, file_path: Path) -> str | None:
        """
        Retrieve the content of a file from the repository.

        Args:
            file_path: The path of the file relative to the repository root

        Returns:
            The file content as a string, or None if the file doesn't exist
        """
        try:
            full_path = self.repo_path / file_path
            if not full_path.exists() or not full_path.is_file():
                logger.error(f"File not found: {full_path}")
                return None

            return full_path.read_text(errors="replace")
        except FileNotFoundError as e:
            logger.exception(f"Error reading file {file_path}: {e!s}")
            return None

    def get_multiple_file_contents(self, file_paths: list[Path]) -> dict[Path, str]:
        """
        Retrieve the content of multiple files from the repository.

        Args:
            repo_path: The path to the repository root
            file_paths: A list of file paths relative to the repository root

        Returns:
            A dictionary mapping file paths to their content
        """
        result = {}
        for file_path in file_paths:
            content = self._get_file_content(file_path)
            if content is not None:
                result[file_path] = content
        return result
