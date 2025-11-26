"""
Git API endpoints for the Holly app that interact with REST MCP client git functionality.
"""

from collections.abc import Callable
from functools import wraps
from typing import Any
from uuid import UUID

import httpx
from asgiref.sync import async_to_sync, sync_to_async
from django.core.cache import cache
from django.http import HttpRequest
from django.shortcuts import aget_object_or_404, get_object_or_404
from loguru import logger
from ninja import Router, Schema
from ninja_jwt.authentication import JWTAuth
from pydantic import BaseModel

from holly.github_ext.auth_utils import create_auth_headers, get_best_github_auth, get_github_oauth_token
from holly.holly.api.schemas import (
    GitRepositoryClone,
    GitRepositoryResponse,
)
from holly.holly.models.mission import Mission
from holly.holly.services.mission_service import MissionService


class GitHubBranchCommit(BaseModel):
    """GitHub branch commit information"""

    sha: str
    url: str


class GitHubBranch(BaseModel):
    """GitHub branch information from API"""

    name: str
    commit: GitHubBranchCommit
    protected: bool


class GitHubBranchesResponse(BaseModel):
    """Response from GitHub API for branches"""

    branches: list[GitHubBranch]
    cached: bool = False
    cache_key: str | None = None


# Helper function to handle async functions with Django Ninja
def sync_endpoint(async_func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(async_func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return async_to_sync(async_func)(*args, **kwargs)

    return wrapper


router = Router(auth=JWTAuth())
mission_service = MissionService()


# Git Repository Operation Schemas
class WorktreeRequest(GitRepositoryClone):
    """Request model for creating a worktree"""

    branch: str
    base_branch: str = "main"


class CommitRequest(GitRepositoryClone):
    """Request model for committing changes"""

    branch: str
    commit_message: str
    files: list[str] | None = None


class PullRequest(GitRepositoryClone):
    """Request model for pulling changes"""

    branch: str


class PushRequest(GitRepositoryClone):
    """Request model for pushing changes"""

    branch: str
    force: bool = False


class RepositoryBranchesRequest(Schema):
    """Request model for getting repository branches"""

    repo_owner: str
    repo_name: str


class BranchesResponse(GitRepositoryResponse):
    """Response model for repository branches"""

    branches: list[str]
    current_branch: str | None = None


# async def _ensure_mission_container(mission_id: UUID, user) -> tuple[bool, Optional[str], Optional[str]]:
#     """
#     Ensure the mission container is running, start it if not.
#
#     Args:
#         mission_id: The UUID of the mission
#         user: The requesting user
#
#     Returns:
#         tuple[bool, Optional[str], Optional[str]]: (success, error_message, container_url)
#     """
#     try:
#         # Get the mission
#         mission = await sync_to_async(Mission.objects.get)(id=mission_id)
#
#         # Check if the mission has a container ID and it's running
#         if mission.container_id and await sync_to_async(container_service.is_container_running)(mission):
#             # Container is running, get its URL
#             container_ip = container_service._get_container_ip(mission.container_id)
#             if not container_ip:
#                 logger.error(f"Could not get IP address for container {mission.container_id}")
#                 return False, "Could not connect to mission container.", None
#
#             # Return the base URL with the container IP and the API port
#             return True, None, f"http://{container_ip}:{container_service.container_api_port}"
#
#         # Container is not running or doesn't exist, try to start it
#         success, message, container_id = await sync_to_async(mission_service.start_mission_container)(
#             mission_id=mission_id,
#             user=user
#         )
#
#         if not success or not container_id:
#             return False, message or "Failed to start mission container.", None
#
#         # Update mission with new container ID if not already updated
#         if mission.container_id != container_id:
#             mission.container_id = container_id
#             await sync_to_async(mission.save)(update_fields=["container_id"])
#
#         # Get the container IP
#         container_ip = container_service._get_container_ip(container_id)
#         if not container_ip:
#             logger.error(f"Could not get IP address for newly started container {container_id}")
#             return False, "Could not connect to mission container after starting it.", None
#
#         # Return the base URL with the container IP and the API port
#         return True, None, f"http://{container_ip}:{container_service.container_api_port}"
#
#     except Mission.DoesNotExist:
#         logger.error(f"Mission {mission_id} not found")
#         return False, f"Mission with ID {mission_id} not found", None
#     except Exception as e:
#         logger.error(f"Error ensuring mission container: {str(e)}")
#         return False, f"Error ensuring mission container: {str(e)}", None
#
# async def _get_mission_container_url(mission_id: UUID, user) -> Optional[str]:
#     """
#     Get the base URL for the REST MCP client in the mission container.
#     Ensures the container is running.
#
#     Args:
#         mission_id: The UUID of the mission
#         user: The requesting user
#
#     Returns:
#         Optional[str]: The base URL for the REST MCP client or None if not found
#     """
#     success, error_message, container_url = await _ensure_mission_container(mission_id, user)
#     if not success:
#         logger.error(f"Could not get container URL: {error_message}")
#         return None
#     return container_url


@router.post("/clone", response=GitRepositoryResponse)
@sync_endpoint
async def clone_repository(request: HttpRequest, mission_id: UUID) -> GitRepositoryResponse:
    """
    Clone a GitHub repository in the mission container.

    Args:
        request: The HTTP request
        mission_id: The UUID of the mission
        repo_data: Repository details including owner, name, and optional branch

    Returns:
        GitRepositoryResponse: Result of the clone operation
    """
    logger.info(f"Cloning repository in mission {mission_id}")

    # Get the mission
    mission = await aget_object_or_404(Mission, id=mission_id)

    # Check if the user has access to this mission
    if not await mission.can_be_accessed_by(request.user):
        return GitRepositoryResponse(success=False, message="You do not have permission to access this mission")

    # Check if the mission has a container ID
    if not mission.container_id:
        return GitRepositoryResponse(
            success=False, message="Mission container is not running. Please start the mission first."
        )

    # Get the container URL
    container_url = await mission.get_mission_container_url(request.user)
    if not container_url:
        return GitRepositoryResponse(
            success=False, message="Could not connect to mission container. Please ensure the mission is started."
        )

    try:
        # Get best available GitHub authentication
        auth_infos = await sync_to_async(get_best_github_auth)(request.user)

        if not auth_infos or auth_infos[0].get("type") == "none" or not auth_infos[0].get("token"):
            return GitRepositoryResponse(
                success=False, message="No GitHub authentication available"
            )

        auth_token = auth_infos[0]["token"]
        logger.info(f"Using {auth_infos[0]['type']} authentication for cloning")

        # Make the request to the container
        repos_cloned = 0
        repositories_queryset = mission.repositories.select_related('repository').all()
        # Convert queryset to list in async context
        mission_repositories: list[Any] = await sync_to_async(lambda: list(repositories_queryset))()
        for repo in mission_repositories:
            repo_data = GitRepositoryClone(
                repo_owner=repo.repository.username,
                repo_name=repo.repository.repo,
                branch=repo.repository.branch_name,
                auth_token=auth_token,
                create_branch=mission.branch_name,
            )
            logger.info(f"cloning with: {repo_data}")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{container_url}/api/git/clone",
                    json=repo_data.dict(),
                    timeout=120,  # Longer timeout for cloning operations
                )
                response.raise_for_status()
                repos_cloned += 1

        return GitRepositoryResponse(success=True, message=f"{repos_cloned} Repositories cloned successfully")
    except httpx.HTTPError as e:
        logger.error(f"HTTP error when cloning repository: {e!s}")
        return GitRepositoryResponse(success=False, message=f"Error cloning repository: {e!s}")
    except Exception as e:
        logger.error(f"Error cloning repository: {e!s}")
        return GitRepositoryResponse(success=False, message=f"Error cloning repository: {e!s}")


@router.post("/worktree", response=GitRepositoryResponse)
@sync_endpoint
async def create_worktree(request: HttpRequest, mission_id: UUID, repo_data: WorktreeRequest) -> GitRepositoryResponse:
    """
    Create a git worktree for a specific branch in the mission container.

    Args:
        request: The HTTP request
        mission_id: The UUID of the mission
        repo_data: Worktree details including repository and branch information

    Returns:
        GitRepositoryResponse: Result of the worktree creation operation
    """
    logger.info(f"Creating worktree for repository {repo_data.repo_name} in mission {mission_id}")

    # Get the mission
    mission = get_object_or_404(Mission, id=mission_id)

    # Check if the user has access to this mission
    if not await mission.can_be_accessed_by(request.user):
        return GitRepositoryResponse(success=False, message="You do not have permission to access this mission")

    # Get the container URL
    container_url = await mission.get_mission_container_url(request.user)
    if not container_url:
        return GitRepositoryResponse(
            success=False, message="Could not connect to mission container. Please ensure the mission is started."
        )

    try:
        # Make the request to the container
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{container_url}/api/git/worktree",
                json={
                    "repo_name": repo_data.repo_name,
                    "branch": repo_data.branch,
                    "base_branch": repo_data.base_branch,
                },
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"HTTP error when creating worktree: {e!s}")
        return GitRepositoryResponse(success=False, message=f"Error creating worktree: {e!s}")
    except Exception as e:
        logger.error(f"Error creating worktree: {e!s}")
        return GitRepositoryResponse(success=False, message=f"Error creating worktree: {e!s}")


@router.post("/commit", response=GitRepositoryResponse)
@sync_endpoint
async def commit_changes(request: HttpRequest, mission_id: UUID, repo_data: CommitRequest) -> GitRepositoryResponse:
    """
    Commit changes to a repository in the mission container.

    Args:
        request: The HTTP request
        mission_id: The UUID of the mission
        repo_data: Commit details including repository, branch, and message

    Returns:
        GitRepositoryResponse: Result of the commit operation
    """
    logger.info(f"Committing changes to repository {repo_data.repo_name} in mission {mission_id}")

    # Get the mission
    mission = get_object_or_404(Mission, id=mission_id)

    # Check if the user has access to this mission
    if not await mission.can_be_accessed_by(request.user):
        return GitRepositoryResponse(success=False, message="You do not have permission to access this mission")

    # Get the container URL
    container_url = await mission.get_mission_container_url(request.user)
    if not container_url:
        return GitRepositoryResponse(
            success=False, message="Could not connect to mission container. Please ensure the mission is started."
        )

    try:
        # Make the request to the container
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{container_url}/api/git/commit",
                json={
                    "repo_name": repo_data.repo_name,
                    "branch": repo_data.branch,
                    "commit_message": repo_data.commit_message,
                    "files": repo_data.files,
                },
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"HTTP error when committing changes: {e!s}")
        return GitRepositoryResponse(success=False, message=f"Error committing changes: {e!s}")
    except Exception as e:
        logger.error(f"Error committing changes: {e!s}")
        return GitRepositoryResponse(success=False, message=f"Error committing changes: {e!s}")


@router.post("/pull", response=GitRepositoryResponse)
@sync_endpoint
async def pull_changes(request: HttpRequest, mission_id: UUID, repo_data: PullRequest) -> GitRepositoryResponse:
    """
    Pull latest changes from remote repository in the mission container.

    Args:
        request: The HTTP request
        mission_id: The UUID of the mission
        repo_data: Pull details including repository and branch information

    Returns:
        GitRepositoryResponse: Result of the pull operation
    """
    logger.info(f"Pulling changes to repository {repo_data.repo_name} in mission {mission_id}")

    # Get the mission
    mission = get_object_or_404(Mission, id=mission_id)

    # Check if the user has access to this mission
    if not await mission.can_be_accessed_by(request.user):
        return GitRepositoryResponse(success=False, message="You do not have permission to access this mission")

    # Get the container URL
    container_url = await mission.get_mission_container_url(request.user)
    if not container_url:
        return GitRepositoryResponse(
            success=False, message="Could not connect to mission container. Please ensure the mission is started."
        )

    try:
        # Make the request to the container
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{container_url}/api/git/pull",
                json={"repo_name": repo_data.repo_name, "branch": repo_data.branch},
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"HTTP error when pulling changes: {e!s}")
        return GitRepositoryResponse(success=False, message=f"Error pulling changes: {e!s}")
    except Exception as e:
        logger.error(f"Error pulling changes: {e!s}")
        return GitRepositoryResponse(success=False, message=f"Error pulling changes: {e!s}")


@router.post("/push", response=GitRepositoryResponse)
@sync_endpoint
async def push_changes(request: HttpRequest, mission_id: UUID, repo_data: PushRequest) -> GitRepositoryResponse:
    """
    Push local changes to remote repository from the mission container.

    Args:
        request: The HTTP request
        mission_id: The UUID of the mission
        repo_data: Push details including repository, branch, and force option

    Returns:
        GitRepositoryResponse: Result of the push operation
    """
    logger.info(f"Pushing changes to repository {repo_data.repo_name} in mission {mission_id}")

    # Get the mission
    mission = get_object_or_404(Mission, id=mission_id)

    # Check if the user has access to this mission
    if not await mission.can_be_accessed_by(request.user):
        return GitRepositoryResponse(success=False, message="You do not have permission to access this mission")

    # Get the container URL
    container_url = await mission.get_mission_container_url(request.user)
    if not container_url:
        return GitRepositoryResponse(
            success=False, message="Could not connect to mission container. Please ensure the mission is started."
        )

    try:
        # Make the request to the container
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{container_url}/api/git/push",
                json={"repo_name": repo_data.repo_name, "branch": repo_data.branch, "force": repo_data.force},
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"HTTP error when pushing changes: {e!s}")
        return GitRepositoryResponse(success=False, message=f"Error pushing changes: {e!s}")
    except Exception as e:
        logger.error(f"Error pushing changes: {e!s}")
        return GitRepositoryResponse(success=False, message=f"Error pushing changes: {e!s}")


@router.post("/branches", response=BranchesResponse)
@sync_endpoint
async def list_branches(
    request: HttpRequest, mission_id: UUID, repo_data: RepositoryBranchesRequest
) -> BranchesResponse:
    """
    Get a list of branches for a cloned repository in the mission container.

    Args:
        request: The HTTP request
        mission_id: The UUID of the mission
        repo_data: Repository details

    Returns:
        BranchesResponse: The list of branches and other details
    """
    logger.info(f"Listing branches for repository {repo_data.repo_name} in mission {mission_id}")

    # Get the mission
    mission = get_object_or_404(Mission, id=mission_id)

    # Check if the user has access to this mission
    if not await mission.can_be_accessed_by(request.user):
        return BranchesResponse(success=False, message="You do not have permission to access this mission", branches=[])

    # Get the container URL
    container_url = await mission.get_mission_container_url(request.user)
    if not container_url:
        return BranchesResponse(
            success=False,
            message="Could not connect to mission container. Please ensure the mission is started.",
            branches=[],
        )

    try:
        # Make the request to the container
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{container_url}/api/git/branches", json={"repo_name": repo_data.repo_name}, timeout=30
            )
            response.raise_for_status()
            response_data = response.json()
            return BranchesResponse(
                success=response_data.get("success", True),
                message=response_data.get("message", "Branches retrieved successfully"),
                branches=response_data.get("branches", []),
                current_branch=response_data.get("current_branch"),
            )
    except httpx.HTTPError as e:
        logger.error(f"HTTP error when listing branches: {e!s}")
        return BranchesResponse(success=False, message=f"Error listing branches: {e!s}", branches=[])
    except Exception as e:
        logger.error(f"Error listing branches: {e!s}")
        return BranchesResponse(success=False, message=f"Error listing branches: {e!s}", branches=[])


@router.post("/branch", response=BranchesResponse)
@sync_endpoint
async def get_branches(request: HttpRequest, repo_data: RepositoryBranchesRequest) -> BranchesResponse:
    """
    Get a list of branches for a repository using GitHub REST API with caching.

    Args:
        request: The HTTP request
        repo_data: Repository details including owner and name

    Returns:
        BranchesResponse: The list of branches and other details
    """
    logger.info(f"Getting branches for repository {repo_data.repo_owner}/{repo_data.repo_name}")

    user = request.user

    # Ensure user is authenticated and has an ID
    if not user.is_authenticated:
        return BranchesResponse(
            success=False, message="Authentication required to access GitHub repositories", branches=[]
        )

    # Type guard to ensure user has id attribute (authenticated users will have this)
    user_id = getattr(user, "id", None)
    if user_id is None:
        return BranchesResponse(success=False, message="User authentication error - no user ID found", branches=[])

    # Create cache key based on repo and user
    cache_key = f"github_branches:{repo_data.repo_owner}:{repo_data.repo_name}:{user_id}"
    cache_timeout = 300  # 5 minutes cache

    # Check cache first
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.info(f"Returning cached branches for {repo_data.repo_owner}/{repo_data.repo_name}")
        return BranchesResponse(
            success=True,
            message="Branches retrieved from cache",
            branches=cached_result.get("branches", []),
            current_branch=cached_result.get("current_branch"),
        )

    try:
        # Get best available GitHub authentication (tries GitHub App first, then OAuth)
        auth_infos = await sync_to_async(get_best_github_auth)(user, f"{repo_data.repo_owner}/{repo_data.repo_name}")

        if not auth_infos or auth_infos[0].get("type") == "none":
            error_msg = "No GitHub authentication available for user"
            logger.error(error_msg)
            return BranchesResponse(success=False, message=error_msg, branches=[])

        # Try each authentication method until one works
        last_error = None
        for auth_info in auth_infos:
            if not auth_info.get("token"):
                continue

            logger.debug(f"Trying auth type: {auth_info.get('type')} for user {user.id}")

            # Call GitHub API to get branches
            github_api_url = f"https://api.github.com/repos/{repo_data.repo_owner}/{repo_data.repo_name}/branches"
            headers = create_auth_headers(auth_info)
            headers["User-Agent"] = "GitHubMe-App"

            async with httpx.AsyncClient() as client:
                response = await client.get(github_api_url, headers=headers, timeout=30)

                logger.debug(f"GitHub API response status: {response.status_code} for auth type: {auth_info.get('type')}")
                logger.debug(f"GitHub API response headers: {dict(response.headers)}")
                if response.status_code != 200:
                    logger.debug(f"GitHub API response body: {response.text}")

                if response.status_code == 401:
                    last_error = "GitHub authentication failed - invalid or expired token"
                    logger.warning(f"{last_error} for auth type: {auth_info.get('type')}, trying next auth method")
                    continue  # Try next auth method
                if response.status_code == 404:
                    error_msg = f"Repository {repo_data.repo_owner}/{repo_data.repo_name} not found or not accessible"
                    logger.error(error_msg)
                    return BranchesResponse(success=False, message=error_msg, branches=[])
                if response.status_code == 403:
                    last_error = "GitHub API rate limit exceeded or insufficient permissions"
                    logger.warning(f"{last_error} for auth type: {auth_info.get('type')}, trying next auth method")
                    continue  # Try next auth method

                # If we get here, the request was successful
                response.raise_for_status()
                github_branches_data = response.json()
                break  # Success! Exit the loop
        else:
            # All auth methods failed
            error_msg = last_error or "All authentication methods failed"
            logger.error(error_msg)
            return BranchesResponse(success=False, message=error_msg, branches=[])

        # Parse GitHub response
        branch_names = [branch["name"] for branch in github_branches_data]

        # Get current branch (default branch info if available) - use same auth
        current_branch = None
        try:
            # Make additional call to get repository info for default branch
            repo_info_url = f"https://api.github.com/repos/{repo_data.repo_owner}/{repo_data.repo_name}"
            # auth_info is still in scope from the successful branch fetch above
            headers_for_default = create_auth_headers(auth_info)
            headers_for_default["User-Agent"] = "GitHubMe-App"
            async with httpx.AsyncClient() as client:
                repo_response = await client.get(repo_info_url, headers=headers_for_default, timeout=15)
                if repo_response.status_code == 200:
                    repo_info = repo_response.json()
                    current_branch = repo_info.get("default_branch")
        except (httpx.HTTPError, KeyError, ValueError) as e:
            logger.warning(f"Could not get default branch info: {e!s}")

        # Cache the result
        cache_data = {"branches": branch_names, "current_branch": current_branch}
        cache.set(cache_key, cache_data, cache_timeout)

        logger.info(
            f"Successfully retrieved and cached {len(branch_names)} branches for {repo_data.repo_owner}/{repo_data.repo_name}"
        )

        return BranchesResponse(
            success=True,
            message=f"Successfully retrieved {len(branch_names)} branches",
            branches=branch_names,
            current_branch=current_branch,
        )

    except httpx.ConnectError as e:
        error_msg = f"Network connection error when accessing GitHub API: {e!s}"
        logger.error(error_msg)
        return BranchesResponse(success=False, message=error_msg, branches=[])
    except httpx.TimeoutException as e:
        error_msg = f"Timeout when accessing GitHub API: {e!s}"
        logger.error(error_msg)
        return BranchesResponse(success=False, message=error_msg, branches=[])
    except httpx.HTTPStatusError as e:
        error_msg = f"GitHub API returned error status {e.response.status_code}: {e!s}"
        logger.error(error_msg)
        return BranchesResponse(success=False, message=error_msg, branches=[])
    except ValueError as e:
        error_msg = f"Invalid JSON response from GitHub API: {e!s}"
        logger.error(error_msg)
        return BranchesResponse(success=False, message=error_msg, branches=[])
    except Exception as e:
        error_msg = f"Unexpected error when retrieving branches: {e!s}"
        logger.error(error_msg)
        return BranchesResponse(success=False, message=error_msg, branches=[])
