"""
Service for interacting with GitHub App repositories.
"""

from http import HTTPStatus
from typing import Any

import requests
from django.contrib.auth import get_user_model
from loguru import logger

from holly.github_ext.api.schemas import GitHubRepository
from holly.github_ext.auth_utils import get_best_github_auth

User = get_user_model()


class GitHubAppService:
    """Service for interacting with GitHub App repositories."""

    def __init__(self, user: User):
        """
        Initialize the GitHub App service.

        Args:
            user: The Django user
        """
        self.user = user
        self.auth_infos = get_best_github_auth(user)

    def list_repositories(self) -> list[dict[str, Any]]:
        """
        List repositories via installation tokens. If we only have a user token,
        discover installations and mint installation tokens first.
        """
        repos: list[dict[str, Any]] = []

        # First pass: use any existing installation tokens
        for auth_info in self.auth_infos:
            token = auth_info.get("token")
            if not token:
                continue
            if auth_info.get("type") != "github_app":
                continue  # skip non-installation tokens in this pass

            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            try:
                r = requests.get("https://api.github.com/installation/repositories", headers=headers, timeout=30)
                if r.status_code == HTTPStatus.OK:
                    repos += r.json().get("repositories", [])
                else:
                    logger.error(f"[installation] list repos failed: {r.status_code} - {r.text}")
            except Exception as e:
                    logger.error(f"[installation] request exception: {e} ")

        # Second pass: if no installation tokens were present, but we have a user token,
        # discover installations and mint installation tokens using the App's JWT.
        if not repos:
            user_auth = next((a for a in self.auth_infos if a.get("type") == "oauth" and a.get("token")), None)
            if user_auth:
                user_headers = {
                    "Authorization": f"Bearer {user_auth['token']}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                }
                try:
                    insts = requests.get("https://api.github.com/user/installations", headers=user_headers, timeout=30)
                    if insts.status_code == HTTPStatus.OK:
                        from holly.github_ext.github_apps import GitHubAppIntegration
                        app = GitHubAppIntegration()
                        for inst in insts.json().get("installations", []):
                            inst_id = inst.get("id")
                            if not inst_id:
                                continue
                            try:
                                inst_token = app.get_installation_token(str(inst_id))
                                if not inst_token:
                                    logger.error(f"[user→installation] failed to mint token for installation {inst_id}")
                                    continue
                                inst_headers = {
                                    "Authorization": f"token {inst_token}",
                                    "Accept": "application/vnd.github+json",
                                    "X-GitHub-Api-Version": "2022-11-28",
                                }
                                r = requests.get(
                                    "https://api.github.com/installation/repositories",
                                    headers=inst_headers,
                                    timeout=30,
                                )
                                if r.status_code == HTTPStatus.OK:
                                    repos += r.json().get("repositories", [])
                                else:
                                    logger.error(
                                        f"[user→installation] list repos failed ({inst_id}): {r.status_code} - {r.text}"
                                    )
                            except Exception as e:  # noqa: BLE001
                                logger.error(f"[user→installation] exception ({inst_id}): {e}")
                    else:
                        logger.error(f"[oauth] list installations failed: {insts.status_code} - {insts.text}")
                except Exception as e:  # noqa: BLE001
                    logger.error(f"[oauth] request exception: {e}")

        # Final fallback: list repos directly via user OAuth token
        if not repos:
            oauth_auths = [a for a in self.auth_infos if a.get("type") == "oauth" and a.get("token")]
            for user_auth in oauth_auths:
                user_headers = {
                    "Authorization": f"Bearer {user_auth['token']}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                }
                try:
                    r = requests.get(
                        "https://api.github.com/user/repos?per_page=100&affiliation=owner,collaborator",
                        headers=user_headers,
                        timeout=30,
                    )
                    if r.status_code == HTTPStatus.OK:
                        repos += r.json()
                    else:
                        logger.error(f"[oauth-fallback] list user repos failed: {r.status_code} - {r.text}")
                except Exception as e:  # noqa: BLE001
                    logger.error(f"[oauth-fallback] request exception: {e}")

        return repos

    def get_repository_by_id(self, github_id: int) -> GitHubRepository | None:
        """
        Get information about a specific repository.

        Args:
            github_id: github id name

        Returns:
            Optional[GithubRepository]: Repository information or None if not accessible
        """
        for auth_info in self.auth_infos:
            if not auth_info["token"]:
                continue

            headers = {"Authorization": f"Bearer {auth_info['token']}", "Accept": "application/vnd.github.v3+json"}

            response = requests.get(f"https://api.github.com/repositories/{github_id}", headers=headers, timeout=30)

            if response.status_code == HTTPStatus.OK:
                return GitHubRepository.model_validate(response.json())
            logger.error(f"Failed to get repository: {response.status_code} - {response.text}")
        return None

    def get_repository(self, owner: str, repo: str) -> dict[str, Any] | None:
        """
        Get information about a specific repository.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Optional[Dict[str, Any]]: Repository information or None if not accessible
        """
        for auth_info in self.auth_infos:
            if not auth_info["token"]:
                continue

            headers = {"Authorization": f"Bearer {auth_info['token']}", "Accept": "application/vnd.github.v3+json"}

            response = requests.get(f"https://api.github.com/repos/{owner}/{repo}", headers=headers, timeout=30)

            if response.status_code == HTTPStatus.OK:
                return response.json()
            logger.error(f"Failed to get repository: {response.status_code} - {response.text}")
        return None

    def get_repository_contents(self, owner: str, repo: str, path: str = "") -> list[dict[str, Any]] | None:
        """
        Get contents of a repository directory.

        Args:
            owner: Repository owner
            repo: Repository name
            path: Path within repository, empty for root

        Returns:
            Optional[List[Dict[str, Any]]]: List of content items or None if not accessible
        """
        for auth_info in self.auth_infos:
            if not auth_info["token"]:
                continue

            headers = {"Authorization": f"Bearer {auth_info['token']}", "Accept": "application/vnd.github.v3+json"}

            response = requests.get(
                f"https://api.github.com/repos/{owner}/{repo}/contents/{path}", headers=headers, timeout=30
            )

            if response.status_code == HTTPStatus.OK:
                return response.json()
            logger.error(f"Failed to get repository contents: {response.status_code} - {response.text}")
        return None

    def get_file_content(self, owner: str, repo: str, path: str) -> str | None:
        """
        Get content of a specific file in the repository.

        Args:
            owner: Repository owner
            repo: Repository name
            path: Path to file within repository

        Returns:
            Optional[str]: File content or None if not accessible
        """
        for auth_info in self.auth_infos:
            if not auth_info["token"]:
                return None

            headers = {
                "Authorization": f"Bearer {auth_info['token']}",
                "Accept": "application/vnd.github.v3.raw",  # Get raw content
            }

            response = requests.get(
                f"https://api.github.com/repos/{owner}/{repo}/contents/{path}", headers=headers, timeout=30
            )

            if response.status_code == HTTPStatus.OK:
                return response.text
            logger.error(f"Failed to get file content: {response.status_code} - {response.text}")
        return None

    def create_pull_request(
        self,
        owner: str,
        repo: str,
        head_branch: str,
        base_branch: str,
        title: str,
        body: str = "",
    ) -> dict[str, Any] | None:
        """Create a pull request on GitHub."""
        payload = {"title": title, "head": head_branch, "base": base_branch, "body": body}
        for auth_info in self.auth_infos:
            if not auth_info["token"]:
                continue
            headers = {
                "Authorization": f"Bearer {auth_info['token']}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            response = requests.post(
                f"https://api.github.com/repos/{owner}/{repo}/pulls",
                headers=headers,
                json=payload,
                timeout=30,
            )
            if response.status_code == HTTPStatus.CREATED:
                return response.json()
            logger.error(f"Failed to create pull request: {response.status_code} - {response.text}")
        return None
