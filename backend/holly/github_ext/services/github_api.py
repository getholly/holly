import datetime
import os
import time
from dataclasses import dataclass, fields
from pathlib import Path

import requests
from github import Github, Repository
from loguru import logger

from holly.github_ext.constants import IGNORE_FILE_TYPE_SEARCH, MAX_FILE_SIZE
from holly.github_ext.helpers import GitHubApiRepositoryDetailsDTO
from holly.github_ext.services.git_repo_mgr import GitRepositoryManager


@dataclass
class GithubGraphQLRepoData:
    id: str
    description: str
    isPrivate: bool  # noqa: N815
    createdAt: str  # noqa: N815
    updatedAt: str  # noqa: N815
    stargazerCount: int  # noqa: N815
    watchers: dict
    forkCount: int  # noqa: N815
    languages: list[str]


def fetch_repo_data_graphql(username: str, repo: str, token: str):
    url = "https://api.github.com/graphql"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    query = """
    query($owner: String!, $repo: String!) {
        repository(owner: $owner, name: $repo) {
            id
            description
            isPrivate
            createdAt
            updatedAt
            stargazerCount
            watchers {
                totalCount
            }
            forkCount
            # openIssuesCount
            # subscriberCount
            # size
            languages(first: 10) {
                nodes {
                    name
                }
            }
            # topics(first: 10) {
            #     nodes {
            #         topic {
            #             name
            #         }
            #     }
            # }
            object(expression: "HEAD:README.md") {
                ... on Blob {
                    text
                }
            }
        }
    }
    """
    variables = {"owner": username, "repo": repo}

    response = requests.post(url, json={"query": query, "variables": variables}, headers=headers, timeout=5)
    return response.json()


class GithubApiClient:
    def __init__(self, client: Github, token: str = ""):
        self.github = client
        self.token = token

    def get_repo_info(self, username: str, repo: str) -> GitHubApiRepositoryDetailsDTO:
        repository = self.github.get_repo(f"{username}/{repo}", lazy=False)
        readme = self._get_readme(repository)
        graphql_data = self.get_graphql_repo_info(username, repo)
        return GitHubApiRepositoryDetailsDTO(
            github_id=graphql_data.id,
            description=graphql_data.description or "",
            private=graphql_data.isPrivate,
            created_at=datetime.datetime.strptime(graphql_data.createdAt, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=datetime.UTC
            ),
            updated_at=datetime.datetime.strptime(graphql_data.updatedAt, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=datetime.UTC
            ),
            stargazers_count=graphql_data.stargazerCount,
            watchers_count=graphql_data.watchers["totalCount"],
            forks_count=graphql_data.forkCount,
            open_issues_count=repository.open_issues_count,
            subscribers_count=repository.subscribers_count,
            size=repository.size,
            languages={i["name"]: 0 for i in graphql_data.languages["nodes"]},
            topics=repository.get_topics(),
            readme=readme,
        )

    def get_graphql_repo_info(self, username: str, repo: str) -> GithubGraphQLRepoData:
        data = fetch_repo_data_graphql(username, repo, self.token)

        return GithubGraphQLRepoData(
            **{
                k: v
                for k, v in data["data"]["repository"].items()
                if k in {field.name for field in fields(GithubGraphQLRepoData)}
            }
        )

    def get_repo_content(
        self, username: str, repo: str, filenames: list[str] | None = None, extensions: list[str] | None = None
    ) -> dict[str, str]:
        repository = self.github.get_repo(f"{username}/{repo}")
        return self._get_all_contents(
            repository, username=username, repo_name=repo, filenames=filenames, extensions=extensions
        )

    def get_repo_content_for_llm(
        self, username: str, repo: str, filenames: list[str] | None = None, extensions: list[str] | None = None
    ) -> str:
        content_dict = self.get_repo_content(username, repo, filenames, extensions)
        return "\n".join([f"// --- {path} ---\n{content}\n" for path, content in content_dict.items()])

    def _get_file_tree(self, repo: Repository) -> str:
        contents = repo.get_contents("")
        tree = []
        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                contents.extend(repo.get_contents(file_content.path))
            tree.append(file_content.path)
        return "\n".join(tree)

    def _get_all_contents(  # noqa: PLR0915 C901 PLR0912
        self,
        repo: Repository,
        username: str,
        repo_name: str,
        filenames: list[str] | None = None,
        extensions: list[str] | None = None,
    ) -> dict[str, str]:
        """
        Get all file contents from a repository with improved performance via local caching.

        Args:
            repo: GitHub Repository object
            username: GitHub username
            repo_name: Repository name
            filenames: Optional list of specific filenames to include
            extensions: Optional list of file extensions to include

        Returns:
            Dictionary mapping file paths to their contents
        """
        start_time = time.monotonic()
        files = {}

        # Set up filtering criteria
        filename_set = set(filenames) if filenames else None
        extension_set = set(extensions) if extensions else None
        binary_extensions = set(IGNORE_FILE_TYPE_SEARCH)

        try:
            # Get the current commit hash from the repository
            repo_commit_hash = repo.get_commits()[0].sha

            # Clone or update the repo locally
            repo_manager = GitRepositoryManager(username, repo_name, self.token)
            git_repo = repo_manager.get_repo()
            local_commit_hash = git_repo.head.commit.hexsha

            logger.info(f"Remote commit: {repo_commit_hash}, Local commit: {local_commit_hash}")

            # Use local files if commit hashes match
            if repo_commit_hash == local_commit_hash:
                logger.info(f"Using local files for {username}/{repo_name} (commit: {local_commit_hash})")
                repo_path = repo_manager.repo_path

                # Process files from local filesystem
                for root, _, file_list in os.walk(repo_path):
                    for filename in file_list:
                        file_path = Path(root) / filename
                        rel_path = file_path.relative_to(repo_path)
                        rel_path_str = str(rel_path)

                        # Skip .git directory files
                        if ".git/" in rel_path_str or rel_path_str.startswith(".git"):
                            continue

                        # Apply filename filter if specified
                        if filename_set and rel_path.name not in filename_set:
                            continue

                        # Apply extension filter if specified
                        file_ext = rel_path.suffix.lower()
                        if extension_set and file_ext not in extension_set:
                            continue

                        # Skip binary files
                        if file_ext in binary_extensions:
                            logger.debug(f"Skipping binary file: {rel_path_str}")
                            continue

                        # Skip files that are too large
                        if file_path.stat().st_size > MAX_FILE_SIZE:
                            logger.debug(f"Skipping large file: {rel_path_str}")
                            continue

                        # Try to read and decode the file
                        try:
                            with file_path.open(encoding="utf-8") as f:
                                content = f.read()
                                files[rel_path_str] = content
                        except UnicodeDecodeError:
                            logger.warning(f"Failed to decode {rel_path_str}. Skipping.")
                            continue
                        except Exception as e:  # noqa: BLE001
                            logger.warning(f"Error reading {rel_path_str}: {e}. Skipping.")
                            continue
            else:
                # Fallback to GitHub API if commit hashes don't match
                logger.info(f"Commit hashes don't match, using GitHub API for {username}/{repo_name}")
                contents = repo.get_contents("")

                while contents:
                    file_content = contents.pop(0)
                    if file_content.type == "dir":
                        contents.extend(repo.get_contents(file_content.path))
                    elif file_content.type == "file" and file_content.size < MAX_FILE_SIZE:
                        # Apply filename filter if specified
                        filename = Path(file_content.path).name
                        if filename_set and filename not in filename_set:
                            continue

                        # Apply extension filter if specified
                        file_ext = Path(file_content.path).suffix.lower()
                        if extension_set and file_ext not in extension_set:
                            continue

                        # Skip binary files
                        if file_ext in binary_extensions:
                            logger.debug(f"Skipping binary file: {file_content.path}")
                            continue

                        # Try to decode the file content
                        try:
                            files[file_content.path] = file_content.decoded_content.decode()
                        except Exception:  # noqa: BLE001
                            logger.warning(f"Failed to decode {file_content.path}. Skipping.")
                            continue
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error processing repository: {e}")
            # Fallback to the original implementation
            contents = repo.get_contents("")
            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    contents.extend(repo.get_contents(file_content.path))
                elif file_content.type == "file" and file_content.size < MAX_FILE_SIZE:
                    try:
                        files[file_content.path] = file_content.decoded_content.decode()
                    except Exception:  # noqa: BLE001
                        logger.warning(f"Failed to decode {file_content.path}. Skipping.")
                        continue

        logger.info(f"Processed {len(files)} files in {time.monotonic() - start_time:.2f} seconds")
        return files

    def _get_readme(self, repo: Repository) -> str:
        try:
            readme = repo.get_contents("README.md")
            return readme.decoded_content.decode()
        except Exception:  # noqa: BLE001
            logger.warning("No README.md found.")
            return ""
