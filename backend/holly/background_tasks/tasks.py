"""
Background tasks for holly application.

This module contains functions that handle potentially long-running operations
in a way that doesn't block the main request/response cycle.
"""

import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from django.core.cache import cache
from loguru import logger

# Task status constants
TASK_STATUS_PENDING = "pending"
TASK_STATUS_RUNNING = "running"
TASK_STATUS_COMPLETED = "completed"
TASK_STATUS_FAILED = "failed"


@dataclass
class TaskResult:
    """Store the result of a background task."""

    task_id: str
    status: str
    result: Any | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


# Dictionary to keep track of task results
# We'll use Django's cache instead of an in-memory variable for persistence
# between server restarts and for handling distributed environments
TASK_CACHE_PREFIX = "bg_task_"
TASK_CACHE_TIMEOUT = 60 * 60 * 24  # 24 hours


def run_background_task(func: Callable, *args, owner_id: int | None = None, **kwargs) -> str:
    """
    Run a function in a background thread and return a task ID.

    Args:
        func: The function to execute
        *args: Positional arguments to pass to the function
        owner_id: ID of the user who owns this task. Status/results are only
            returned to this user (see background_tasks.views.task_status).
        **kwargs: Keyword arguments to pass to the function

    Returns:
        str: A unique task ID that can be used to check the task status
    """
    task_id = str(uuid.uuid4())

    # Create initial task result with pending status

    # Store the initial task result in cache
    cache.set(
        f"{TASK_CACHE_PREFIX}{task_id}",
        {
            "task_id": task_id,
            "owner_id": owner_id,
            "status": TASK_STATUS_PENDING,
            "result": None,
            "error": None,
            "started_at": None,
            "completed_at": None,
        },
        TASK_CACHE_TIMEOUT,
    )

    # Start the task in a background thread
    thread = threading.Thread(target=_execute_task, args=(task_id, func, args, kwargs))
    thread.daemon = True
    thread.start()

    return task_id


def _execute_task(task_id: str, func: Callable, args, kwargs) -> None:
    """
    Execute a task and update its status in the cache.

    Args:
        task_id: The unique ID of the task
        func: The function to execute
        args: Positional arguments to pass to the function
        kwargs: Keyword arguments to pass to the function
    """
    # Update task status to running
    task_data = cache.get(f"{TASK_CACHE_PREFIX}{task_id}")
    if task_data:
        task_data["status"] = TASK_STATUS_RUNNING
        task_data["started_at"] = datetime.now(UTC).isoformat()
        cache.set(f"{TASK_CACHE_PREFIX}{task_id}", task_data, TASK_CACHE_TIMEOUT)

    try:
        # Execute the task function
        result = func(*args, **kwargs)

        # Update task status to completed
        task_data = cache.get(f"{TASK_CACHE_PREFIX}{task_id}")
        if task_data:
            task_data["status"] = TASK_STATUS_COMPLETED
            task_data["result"] = result
            task_data["completed_at"] = datetime.now(UTC).isoformat()
            cache.set(f"{TASK_CACHE_PREFIX}{task_id}", task_data, TASK_CACHE_TIMEOUT)

    except Exception as e:
        logger.exception(f"Task {task_id} failed with error: {e}")

        # Update task status to failed
        task_data = cache.get(f"{TASK_CACHE_PREFIX}{task_id}")
        if task_data:
            task_data["status"] = TASK_STATUS_FAILED
            task_data["error"] = str(e)
            task_data["completed_at"] = datetime.now(UTC).isoformat()
            cache.set(f"{TASK_CACHE_PREFIX}{task_id}", task_data, TASK_CACHE_TIMEOUT)


def get_task_status(task_id: str) -> dict[str, Any] | None:
    """
    Get the current status of a background task.

    Args:
        task_id: The task ID returned by run_background_task

    Returns:
        Dict with task status or None if task not found
    """
    return cache.get(f"{TASK_CACHE_PREFIX}{task_id}")
