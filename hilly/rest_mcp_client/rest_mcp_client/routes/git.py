from fastapi import APIRouter, Depends
from typing import Dict, Any
import os
from arq import create_pool
from arq.connections import RedisSettings
from sqlalchemy.orm import Session

from rest_mcp_client.routes.schema.git import CloneRepositoryRequest, WorktreeRequest, CommitRequest, PullRequest, \
    PushRequest, RepositoryBranchesRequest, GitOperationResponse, BranchesResponse
from rest_mcp_client.routes.schema.job_schemas import JobResponse, JobStatusResponse
from rest_mcp_client.routes.schema.pr_schemas import PRRequest
from rest_mcp_client.services.git_service import GitService
from rest_mcp_client.services.job_service import job_service
from rest_mcp_client.database.database import get_db

# Create a router
router = APIRouter(prefix="/api/git", tags=["git"])

# Initialize the Git service
git_service = GitService(base_dir=os.environ.get("BASE_DIR", "/data"))

# ARQ pool for job queue (will be initialized on first use)
_arq_pool = None

async def get_arq_pool():
    """Get or create ARQ connection pool."""
    global _arq_pool
    if _arq_pool is None:
        _arq_pool = await create_pool(
            RedisSettings(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379"))
            )
        )
    return _arq_pool

# Define request models

# Define response models

@router.post("/clone", response_model=GitOperationResponse)
async def clone_repository(request: CloneRepositoryRequest) -> Dict[str, Any]:
    """
    Clone a GitHub repository synchronously.

    Args:
        request: The repository details and authentication token

    Returns:
        GitOperationResponse: The result of the clone operation
    """
    result = git_service.clone_repository(
        repo_owner=request.repo_owner,
        repo_name=request.repo_name,
        auth_token=request.auth_token,
        branch=request.branch,
        create_branch=request.create_branch,
        auth_type=request.auth_type,
    )

    return result

@router.post("/worktree", response_model=GitOperationResponse)
async def create_worktree(request: WorktreeRequest) -> Dict[str, Any]:
    """
    Create a git worktree for a specific branch.

    Args:
        request: The worktree details

    Returns:
        GitOperationResponse: The result of the worktree creation operation
    """
    result = git_service.create_worktree(
        repo_name=request.repo_name,
        branch=request.branch,
        base_branch=request.base_branch,
    )

    return result

@router.post("/commit", response_model=GitOperationResponse)
async def commit_changes(request: CommitRequest) -> Dict[str, Any]:
    """
    Commit changes to a repository.

    Args:
        request: The commit details

    Returns:
        GitOperationResponse: The result of the commit operation
    """
    result = git_service.commit_changes(
        repo_name=request.repo_name,
        branch=request.branch,
        commit_message=request.commit_message,
        files=request.files,
    )

    return result

@router.post("/pull", response_model=GitOperationResponse)
async def pull_changes(request: PullRequest) -> Dict[str, Any]:
    """
    Pull latest changes from remote repository.

    Args:
        request: The pull details

    Returns:
        GitOperationResponse: The result of the pull operation
    """
    result = git_service.pull_changes(
        repo_name=request.repo_name,
        branch=request.branch,
    )

    return result

@router.post("/push", response_model=GitOperationResponse)
async def push_changes(request: PushRequest) -> Dict[str, Any]:
    """
    Push local changes to remote repository.

    Args:
        request: The push details

    Returns:
        GitOperationResponse: The result of the push operation
    """
    result = git_service.push_changes(
        repo_name=request.repo_name,
        branch=request.branch,
        force=request.force,
    )

    return result

@router.post("/branches", response_model=BranchesResponse)
async def list_branches(request: RepositoryBranchesRequest) -> Dict[str, Any]:
    """
    Get a list of branches for a cloned repository.

    Args:
        request: The repository details

    Returns:
        BranchesResponse: The list of branches and other details
    """
    result = git_service.get_repository_branches(
        repo_name=request.repo_name,
    )

    return result


# ==================== ASYNC JOB ENDPOINTS ====================

@router.post("/repos", response_model=JobResponse)
async def clone_repository_async(
    request: CloneRepositoryRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Clone a repository asynchronously (returns job_id).
    
    This is the Git-Flow V1.1 async endpoint that immediately returns
    a job ID. Use GET /jobs/{job_id} to check status.

    Args:
        request: Clone repository request
        db: Database session

    Returns:
        JobResponse with job_id and initial status
    """
    # Create job record
    job_id = job_service.create_job(
        db=db,
        job_type="clone",
        metadata={
            "repo_owner": request.repo_owner,
            "repo_name": request.repo_name,
            "branch": request.branch,
            "mission_id": os.getenv("MISSION_ID"),  # From environment
        }
    )
    
    # Enqueue job to ARQ
    pool = await get_arq_pool()
    await pool.enqueue_job(
        'clone_repository',
        job_id=job_id,
        repo_owner=request.repo_owner,
        repo_name=request.repo_name,
        auth_token=request.auth_token,
        branch=request.branch,
        create_branch=request.create_branch,
    )
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": f"Clone job enqueued for {request.repo_owner}/{request.repo_name}"
    }


@router.post("/repos/{repo_name}/worktrees", response_model=JobResponse)
async def create_worktree_async(
    repo_name: str,
    request: WorktreeRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create a worktree asynchronously (returns job_id).

    Args:
        repo_name: Repository name
        request: Worktree request
        db: Database session

    Returns:
        JobResponse with job_id and initial status
    """
    job_id = job_service.create_job(
        db=db,
        job_type="worktree",
        metadata={
            "repo_name": repo_name,
            "branch": request.branch,
            "base_branch": request.base_branch,
            "mission_id": os.getenv("MISSION_ID"),
        }
    )
    
    pool = await get_arq_pool()
    await pool.enqueue_job(
        'create_worktree',
        job_id=job_id,
        repo_name=repo_name,
        branch=request.branch,
        base_branch=request.base_branch,
    )
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": f"Worktree creation job enqueued for {repo_name}/{request.branch}"
    }


@router.post("/repos/{repo_name}/commits", response_model=JobResponse)
async def commit_changes_async(
    repo_name: str,
    request: CommitRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Commit changes asynchronously (returns job_id).

    Args:
        repo_name: Repository name
        request: Commit request
        db: Database session

    Returns:
        JobResponse with job_id and initial status
    """
    job_id = job_service.create_job(
        db=db,
        job_type="commit",
        metadata={
            "repo_name": repo_name,
            "branch": request.branch,
            "mission_id": os.getenv("MISSION_ID"),
        }
    )
    
    pool = await get_arq_pool()
    await pool.enqueue_job(
        'commit_changes',
        job_id=job_id,
        repo_name=repo_name,
        branch=request.branch,
        commit_message=request.commit_message,
        files=request.files,
    )
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": f"Commit job enqueued for {repo_name}/{request.branch}"
    }


@router.post("/repos/{repo_name}/push", response_model=JobResponse)
async def push_changes_async(
    repo_name: str,
    request: PushRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Push changes asynchronously (returns job_id).

    Args:
        repo_name: Repository name
        request: Push request
        db: Database session

    Returns:
        JobResponse with job_id and initial status
    """
    job_id = job_service.create_job(
        db=db,
        job_type="push",
        metadata={
            "repo_name": repo_name,
            "branch": request.branch,
            "force": request.force,
            "mission_id": os.getenv("MISSION_ID"),
        }
    )
    
    pool = await get_arq_pool()
    await pool.enqueue_job(
        'push_changes',
        job_id=job_id,
        repo_name=repo_name,
        branch=request.branch,
        force=request.force,
    )
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": f"Push job enqueued for {repo_name}/{request.branch}"
    }


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get job status by ID.
    
    This endpoint allows polling for job status. Jobs are created
    by async endpoints like POST /repos.

    Args:
        job_id: Job ID (UUID)
        db: Database session

    Returns:
        Job status with result/error information
    """
    return job_service.get_job_status(db, job_id)


@router.post("/repos/{owner}/{repo}/pull-requests", response_model=JobResponse)
async def create_pull_request_async(
    owner: str,
    repo: str,
    request: PRRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create a pull request asynchronously (returns job_id).
    
    Uses the GitHub provider to create a PR from head branch to base branch.

    Args:
        owner: Repository owner
        repo: Repository name
        request: PR request with head, base, title, body
        db: Database session

    Returns:
        JobResponse with job_id and initial status
    """
    job_id = job_service.create_job(
        db=db,
        job_type="create_pr",
        metadata={
            "owner": owner,
            "repo": repo,
            "head": request.head,
            "base": request.base,
            "title": request.title,
            "mission_id": os.getenv("MISSION_ID"),
        }
    )
    
    pool = await get_arq_pool()
    await pool.enqueue_job(
        'create_pull_request',
        job_id=job_id,
        owner=owner,
        repo=repo,
        head=request.head,
        base=request.base,
        title=request.title,
        body=request.body or "",
        auth_token=request.auth_token or os.getenv("AUTH_TOKEN"),
    )
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": f"PR creation job enqueued for {owner}/{repo}"
    }


