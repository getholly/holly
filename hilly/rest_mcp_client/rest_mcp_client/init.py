"""Container self-initialization script."""

import os
import asyncio
import sys
from typing import List, Tuple, Dict, Any
import httpx
from loguru import logger


async def wait_for_api_ready(max_retries: int = 30, delay: float = 1.0) -> bool:
    """
    Wait for the local API to be ready.
    
    Args:
        max_retries: Maximum number of retries
        delay: Delay between retries in seconds
        
    Returns:
        True if API is ready, False otherwise
    """
    api_url = "http://localhost:8090/"
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(api_url, timeout=2.0)
                if response.status_code == 200:
                    logger.info(f"API ready after {attempt + 1} attempts")
                    return True
        except Exception as e:
            logger.debug(f"Attempt {attempt + 1}/{max_retries}: API not ready - {e}")
            await asyncio.sleep(delay)
    
    logger.error(f"API not ready after {max_retries} attempts")
    return False


async def clone_repositories(
    repos_str: str,
    auth_token: str,
    mission_branch: str,
    auth_type: str = "oauth"
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Clone all repositories SYNCHRONOUSLY.
    
    Args:
        repos_str: Comma-separated list of "owner/repo:branch" specs
        auth_token: GitHub auth token
        mission_branch: Mission branch name
        auth_type: Type of authentication ('github_app' or 'oauth')
        
    Returns:
        Tuple of (success, results)
    """
    if not repos_str:
        logger.warning("No repositories to clone")
        return True, []
    
    repos = [r.strip() for r in repos_str.split(",") if r.strip()]
    results = []
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        for repo_spec in repos:
            try:
                # Parse repo spec: "owner/repo:branch" or "owner/repo"
                if ":" in repo_spec:
                    owner_repo, branch = repo_spec.split(":", 1)
                else:
                    owner_repo = repo_spec
                    branch = "main"  # Default branch
                
                owner, repo = owner_repo.split("/", 1)
                
                logger.info(f"Cloning {owner}/{repo} (branch: {branch}) with {auth_type} auth")
                
                # Call SYNCHRONOUS clone endpoint (not /repos)
                response = await client.post(
                    "http://localhost:8090/api/git/clone",
                    json={
                        "repo_owner": owner,
                        "repo_name": repo,
                        "branch": branch,
                        "auth_token": auth_token,
                        "auth_type": auth_type,
                        "create_branch": mission_branch if mission_branch != branch else None,
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                if result.get("success"):
                    logger.info(f"✅ Cloned {owner}/{repo} to {result.get('path')}")
                    results.append(result)
                else:
                    logger.error(f"❌ Failed to clone {owner}/{repo}: {result.get('message')}")
                    return False, results  # Fail fast on first error
                    
            except Exception as e:
                logger.error(f"❌ Failed to clone {repo_spec}: {e}")
                return False, results  # Fail fast
    
    return True, results


async def send_init_webhook(
    mission_id: str,
    webhook_url: str,
    job_ids: List[str],
    total_repos: int
) -> bool:
    """
    Send initialization webhook to Django.
    
    Args:
        mission_id: Mission ID
        webhook_url: Django webhook URL
        job_ids: List of clone job IDs
        total_repos: Total number of repositories
        
    Returns:
        True if webhook sent successfully
    """
    if not webhook_url:
        logger.warning("No webhook URL configured")
        return False
    
    # Use first job_id as the init job
    init_job_id = job_ids[0] if job_ids else "no-jobs"
    
    payload = {
        "mission_id": mission_id,
        "job_id": init_job_id,
        "status": "initializing",
        "data": {
            "total_repos": total_repos,
            "job_ids": job_ids,
            "message": f"Started cloning {total_repos} repositories"
        },
        "timestamp": None  # Will be set by webhook service
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                json=payload,
                timeout=10.0
            )
            response.raise_for_status()
            logger.info(f"Init webhook sent successfully for mission {mission_id}")
            return True
            
    except httpx.HTTPError as e:
        logger.error(f"Failed to send init webhook: {e}")
        return False


async def send_webhook(
    mission_id: str,
    job_id: str,
    status: str,
    webhook_url: str,
    data: dict = None
) -> bool:
    """
    Send webhook to Django.
    
    Args:
        mission_id: Mission ID
        job_id: Job ID
        status: Job status
        webhook_url: Django webhook URL
        data: Additional data
        
    Returns:
        True if webhook sent successfully
    """
    from datetime import datetime
    
    if not webhook_url:
        logger.warning("No webhook URL configured")
        return False
    
    payload = {
        "mission_id": mission_id,
        "job_id": job_id,
        "status": status,
        "data": data or {},
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                json=payload,
                timeout=10.0
            )
            response.raise_for_status()
            logger.info(f"Webhook sent: {status} for job {job_id}")
            return True
            
    except httpx.HTTPError as e:
        logger.error(f"Failed to send webhook: {e}")
        return False


async def process_initial_message(
    conversation_id: str,
    initial_message: str,
    mission_id: str,
    job_id: str,
    webhook_url: str,
    llm_id: str = None
) -> bool:
    """
    Process initial conversation message with LLM.
    
    Args:
        conversation_id: Conversation ID
        initial_message: User's initial message
        mission_id: Mission ID
        job_id: Job ID for tracking
        webhook_url: Django webhook URL
        llm_id: Optional LLM ID to use
        
    Returns:
        True if successful
    """
    try:
        # Send processing status
        await send_webhook(
            mission_id=mission_id,
            job_id=job_id,
            status="processing",
            webhook_url=webhook_url,
            data={
                "conversation_id": conversation_id,
                "progress": "Processing initial message with LLM..."
            }
        )
        
        # Call conversation API
        request_data = {
            "id": conversation_id,
            "initial_message": initial_message,
            "title": "Auto-generated"
        }
        
        # Add LLM config if provided
        if llm_id:
            request_data["llm_id"] = llm_id
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8090/api/conversations/start",
                json=request_data,
                timeout=120.0
            )
            response.raise_for_status()
            result = response.json()
        
        # Extract response message
        messages = result.get("messages", [])
        reply = messages[-1].get("content", "") if messages else ""
        
        # Send completion webhook
        await send_webhook(
            mission_id=mission_id,
            job_id=job_id,
            status="completed",
            webhook_url=webhook_url,
            data={
                "conversation_id": conversation_id,
                "title": result.get("title", "Conversation"),
                "response": reply,
                "result": result
            }
        )
        
        logger.info(f"Initial message processed for conversation {conversation_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to process initial message: {e}")
        
        # Send failure webhook
        await send_webhook(
            mission_id=mission_id,
            job_id=job_id,
            status="failed",
            webhook_url=webhook_url,
            data={
                "conversation_id": conversation_id,
                "error": str(e)
            }
        )
        return False


async def initialize_container():
    """Synchronous container initialization."""
    
    logger.info("=== Container Initialization Started ===")
    
    # Get environment variables
    mission_id = os.getenv("MISSION_ID")
    repos_str = os.getenv("MISSION_REPOS", "")
    mission_branch = os.getenv("MISSION_BRANCH", "main")
    auth_token = os.getenv("AUTH_TOKEN", "")
    auth_type = os.getenv("AUTH_TYPE", "oauth")
    webhook_url = os.getenv("DJANGO_WEBHOOK_URL")
    
    # Get conversation context (if provided)
    conversation_id = os.getenv("CONVERSATION_ID")
    initial_message = os.getenv("INITIAL_MESSAGE")
    job_id = os.getenv("JOB_ID")
    llm_id = os.getenv("LLM_ID")
    
    # Check if initialization is needed
    if not mission_id:
        logger.info("No MISSION_ID set, skipping initialization")
        return
    
    logger.info(f"Mission: {mission_id}, Auth: {auth_type}")
    
    # Wait for API to be ready
    logger.info("Waiting for API to be ready...")
    if not await wait_for_api_ready():
        logger.error("API failed to start")
        if webhook_url:
            await send_webhook(
                mission_id, "init", "failed", webhook_url,
                {"error": "API failed to start"}
            )
        sys.exit(1)
    
    # Clone repositories synchronously
    if repos_str:
        logger.info(f"Cloning repositories: {repos_str}")
        success, results = await clone_repositories(
            repos_str, auth_token, mission_branch, auth_type
        )
        
        if not success:
            logger.error("❌ Repository cloning failed")
            if webhook_url:
                await send_webhook(
                    mission_id, "init", "failed", webhook_url,
                    {"error": "Failed to clone repositories", "results": results}
                )
            sys.exit(1)
        
        logger.info(f"✅ Cloned {len(results)} repositories successfully")
    
    # Process initial message if provided
    if conversation_id and initial_message and job_id:
        logger.info(f"Processing initial message for conversation {conversation_id}")
        await process_initial_message(
            conversation_id=conversation_id,
            initial_message=initial_message,
            mission_id=mission_id,
            job_id=job_id,
            webhook_url=webhook_url,
            llm_id=llm_id
        )
    
    # Execute coding task end-to-end only when explicitly enabled
    if os.getenv("AUTO_IMPLEMENT", "false").lower() == "true" and initial_message:
        logger.info("Executing task based on initial message")
        # Parse repos into tuples
        repo_specs = [r.strip() for r in repos_str.split(",") if r.strip()]
        repos: list[tuple[str, str]] = []
        for spec in repo_specs:
            owner_repo = spec.split(":", 1)[0]
            if "/" in owner_repo:
                owner, repo = owner_repo.split("/", 1)
                repos.append((owner, repo))

        from rest_mcp_client.services.task_executor import execute_task
        await execute_task(
            task_text=initial_message,
            mission_branch=mission_branch,
            repos=repos,
            webhook_url=webhook_url,
        )

    # Send success webhook
    if webhook_url:
        await send_webhook(
            mission_id, "init", "completed", webhook_url,
            {
                "message": "Container initialized successfully",
                "repos_cloned": len(repos_str.split(",")) if repos_str else 0
            }
        )
    
    logger.info("=== Container Initialization Complete ===")


if __name__ == "__main__":
    # Run initialization
    try:
        asyncio.run(initialize_container())
    except KeyboardInterrupt:
        logger.info("Initialization interrupted")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Initialization failed: {e}")
        sys.exit(1)

