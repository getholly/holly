"""ARQ worker for async Git operations."""

import os
from typing import Dict, Any
from arq.connections import RedisSettings
from loguru import logger

from rest_mcp_client.services.git_service import GitService
from rest_mcp_client.models.job import JobStatus
from rest_mcp_client.database.database import SessionLocal
from rest_mcp_client.services.job_service import job_service


async def clone_repository(
    ctx: Dict[str, Any],
    job_id: str,
    repo_owner: str,
    repo_name: str,
    auth_token: str,
    branch: str,
    create_branch: str = None,
) -> Dict[str, Any]:
    """
    Clone a repository asynchronously.
    
    Args:
        ctx: ARQ context
        job_id: Job ID
        repo_owner: Repository owner
        repo_name: Repository name
        auth_token: GitHub auth token
        branch: Branch to clone
        create_branch: Optional branch to create
        
    Returns:
        Result dictionary
    """
    db = SessionLocal()
    git_service = GitService()
    
    try:
        # Update job to running
        job_service.update_job_status(db, job_id, JobStatus.RUNNING)
        
        logger.info(f"Cloning {repo_owner}/{repo_name} (branch: {branch})")
        
        # Perform clone operation
        result = git_service.clone_repository(
            repo_owner=repo_owner,
            repo_name=repo_name,
            auth_token=auth_token,
            branch=branch,
            create_branch=create_branch,
        )
        
        if result.get("success"):
            job_service.update_job(db, job_id, JobStatus.COMPLETED, result=result)
            logger.info(f"Clone job {job_id} completed successfully")
        else:
            error_msg = result.get("message", "Unknown error")
            job_service.update_job(db, job_id, JobStatus.FAILED, error=error_msg)
            logger.error(f"Clone job {job_id} failed: {error_msg}")
        
        # Send webhook if we have mission_id in job metadata
        job = job_service.get_job(db, job_id)
        if job and job.job_metadata.get("mission_id"):
            await send_job_webhook(job)
        
        return result
        
    except Exception as e:
        logger.exception(f"Error in clone job {job_id}: {e}")
        job_service.update_job(db, job_id, JobStatus.FAILED, error=str(e))
        
        # Send webhook on failure
        job = job_service.get_job(db, job_id)
        if job and job.job_metadata.get("mission_id"):
            await send_job_webhook(job)
        
        return {"success": False, "error": str(e)}
    finally:
        db.close()


async def create_worktree(
    ctx: Dict[str, Any],
    job_id: str,
    repo_name: str,
    branch: str,
    base_branch: str = "main",
) -> Dict[str, Any]:
    """
    Create a worktree asynchronously.
    
    Args:
        ctx: ARQ context
        job_id: Job ID
        repo_name: Repository name
        branch: Branch name for worktree
        base_branch: Base branch
        
    Returns:
        Result dictionary
    """
    db = SessionLocal()
    git_service = GitService()
    
    try:
        job_service.update_job_status(db, job_id, JobStatus.RUNNING)
        
        logger.info(f"Creating worktree for {repo_name}/{branch}")
        
        result = git_service.create_worktree(
            repo_name=repo_name,
            branch=branch,
            base_branch=base_branch,
        )
        
        if result.get("success"):
            job_service.update_job(db, job_id, JobStatus.COMPLETED, result=result)
        else:
            error_msg = result.get("message", "Unknown error")
            job_service.update_job(db, job_id, JobStatus.FAILED, error=error_msg)
        
        # Send webhook if we have mission_id
        job = job_service.get_job(db, job_id)
        if job and job.job_metadata.get("mission_id"):
            await send_job_webhook(job)
        
        return result
        
    except Exception as e:
        logger.exception(f"Error in worktree job {job_id}: {e}")
        job_service.update_job(db, job_id, JobStatus.FAILED, error=str(e))
        
        job = job_service.get_job(db, job_id)
        if job and job.job_metadata.get("mission_id"):
            await send_job_webhook(job)
        
        return {"success": False, "error": str(e)}
    finally:
        db.close()


async def commit_changes(
    ctx: Dict[str, Any],
    job_id: str,
    repo_name: str,
    branch: str,
    commit_message: str,
    files: list = None,
) -> Dict[str, Any]:
    """
    Commit changes asynchronously.
    
    Args:
        ctx: ARQ context
        job_id: Job ID
        repo_name: Repository name
        branch: Branch name
        commit_message: Commit message
        files: Optional list of files to commit
        
    Returns:
        Result dictionary
    """
    db = SessionLocal()
    git_service = GitService()
    
    try:
        job_service.update_job_status(db, job_id, JobStatus.RUNNING)
        
        logger.info(f"Committing changes to {repo_name}/{branch}")
        
        result = git_service.commit_changes(
            repo_name=repo_name,
            branch=branch,
            commit_message=commit_message,
            files=files,
        )
        
        if result.get("success"):
            job_service.update_job(db, job_id, JobStatus.COMPLETED, result=result)
        else:
            error_msg = result.get("message", "Unknown error")
            job_service.update_job(db, job_id, JobStatus.FAILED, error=error_msg)
        
        job = job_service.get_job(db, job_id)
        if job and job.job_metadata.get("mission_id"):
            await send_job_webhook(job)
        
        return result
        
    except Exception as e:
        logger.exception(f"Error in commit job {job_id}: {e}")
        job_service.update_job(db, job_id, JobStatus.FAILED, error=str(e))
        
        job = job_service.get_job(db, job_id)
        if job and job.job_metadata.get("mission_id"):
            await send_job_webhook(job)
        
        return {"success": False, "error": str(e)}
    finally:
        db.close()


async def push_changes(
    ctx: Dict[str, Any],
    job_id: str,
    repo_name: str,
    branch: str,
    force: bool = False,
) -> Dict[str, Any]:
    """
    Push changes asynchronously.
    
    Args:
        ctx: ARQ context
        job_id: Job ID
        repo_name: Repository name
        branch: Branch name
        force: Force push flag
        
    Returns:
        Result dictionary
    """
    db = SessionLocal()
    git_service = GitService()
    
    try:
        job_service.update_job_status(db, job_id, JobStatus.RUNNING)
        
        logger.info(f"Pushing changes to {repo_name}/{branch}")
        
        result = git_service.push_changes(
            repo_name=repo_name,
            branch=branch,
            force=force,
        )
        
        if result.get("success"):
            job_service.update_job(db, job_id, JobStatus.COMPLETED, result=result)
        else:
            error_msg = result.get("message", "Unknown error")
            job_service.update_job(db, job_id, JobStatus.FAILED, error=error_msg)
        
        job = job_service.get_job(db, job_id)
        if job and job.job_metadata.get("mission_id"):
            await send_job_webhook(job)
        
        return result
        
    except Exception as e:
        logger.exception(f"Error in push job {job_id}: {e}")
        job_service.update_job(db, job_id, JobStatus.FAILED, error=str(e))
        
        job = job_service.get_job(db, job_id)
        if job and job.job_metadata.get("mission_id"):
            await send_job_webhook(job)
        
        return {"success": False, "error": str(e)}
    finally:
        db.close()


async def send_job_webhook(job):
    """Send webhook for job completion/failure."""
    from rest_mcp_client.services.webhook_service import webhook_service
    
    mission_id = job.job_metadata.get("mission_id")
    if not mission_id:
        return
    
    await webhook_service.send_webhook(
        mission_id=mission_id,
        job_id=job.id,
        status=job.status.value if isinstance(job.status, JobStatus) else job.status,
        data={
            "type": job.type,
            "result": job.result,
            "error": job.error,
            "metadata": job.job_metadata,
        }
    )


async def create_pull_request(
    ctx: Dict[str, Any],
    job_id: str,
    owner: str,
    repo: str,
    head: str,
    base: str,
    title: str,
    body: str = "",
    auth_token: str = None,
) -> Dict[str, Any]:
    """
    Create a pull request asynchronously.
    
    Args:
        ctx: ARQ context
        job_id: Job ID
        owner: Repository owner
        repo: Repository name
        head: Head branch
        base: Base branch
        title: PR title
        body: PR body
        auth_token: GitHub auth token
        
    Returns:
        Result dictionary
    """
    db = SessionLocal()
    
    try:
        job_service.update_job_status(db, job_id, JobStatus.RUNNING)
        
        logger.info(f"Creating PR for {owner}/{repo}: {head} -> {base}")
        
        # Import provider
        from rest_mcp_client.providers.github import GitHubProvider
        
        if not auth_token:
            auth_token = os.getenv("AUTH_TOKEN", "")
        
        provider = GitHubProvider(auth_token)
        
        result = await provider.create_pull_request(
            owner=owner,
            repo=repo,
            head=head,
            base=base,
            title=title,
            body=body,
        )
        
        if result.get("success"):
            job_service.update_job(db, job_id, JobStatus.COMPLETED, result=result)
            logger.info(f"PR creation job {job_id} completed")
        else:
            error_msg = result.get("error", "Unknown error")
            job_service.update_job(db, job_id, JobStatus.FAILED, error=error_msg)
            logger.error(f"PR creation job {job_id} failed: {error_msg}")
        
        job = job_service.get_job(db, job_id)
        if job and job.job_metadata.get("mission_id"):
            await send_job_webhook(job)
        
        return result
        
    except Exception as e:
        logger.exception(f"Error in PR creation job {job_id}: {e}")
        job_service.update_job(db, job_id, JobStatus.FAILED, error=str(e))
        
        job = job_service.get_job(db, job_id)
        if job and job.job_metadata.get("mission_id"):
            await send_job_webhook(job)
        
        return {"success": False, "error": str(e)}
    finally:
        db.close()


# ARQ Worker Settings
class WorkerSettings:
    """ARQ worker configuration."""
    
    functions = [
        clone_repository,
        create_worktree,
        commit_changes,
        push_changes,
        create_pull_request,
    ]
    
    redis_settings = RedisSettings(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
    )
    
    # Job timeout (5 minutes)
    job_timeout = 300
    
    # Max retries for failed jobs
    max_tries = 3
    
    # Keep jobs for 24 hours
    keep_result = 86400

