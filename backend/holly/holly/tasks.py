"""Celery tasks for Holly missions."""

import json
import time
from typing import Any

import redis
from celery import shared_task
from django.conf import settings
from loguru import logger

from holly.holly.models import Mission
from holly.holly.services.containers.holly_container_service import HollyContainerService

# Redis client for publishing SSE updates
redis_client = redis.StrictRedis.from_url(settings.CELERY_RESULT_BACKEND)


class CloneStatus:
    """Constants for clone status updates."""

    STARTED = "started"
    CLONING = "cloning"
    COMPLETED = "completed"
    FAILED = "failed"
    PROGRESS = "progress"


def publish_clone_update(mission_id: str, status: str, data: dict[str, Any]) -> None:
    """
    Publish a clone status update to Redis pub/sub for SSE.

    Args:
        mission_id: The mission UUID
        status: The status type (from CloneStatus)
        data: Additional data for the update
    """
    try:
        channel = f"mission:{mission_id}:clone_status"
        message = {"status": status, "timestamp": time.time(), **data}
        redis_client.publish(channel, json.dumps(message))
        logger.info(f"Published clone update for mission {mission_id}: {status}")
    except Exception as ex:
        logger.error(f"Failed to publish clone update message: {ex}")


# REMOVED: Helper functions for clone_repositories_task
# (retry_with_exponential_backoff, clone_repository_with_retry,
#  get_user_github_token, wait_for_container_api)
# Container now handles all cloning internally via async jobs


# REMOVED: clone_repositories_task - Container now self-initializes via init.py
# The container clones repositories asynchronously and reports back via webhooks


@shared_task
def cleanup_old_containers():
    """
    Periodic task to cleanup containers from missions that are completed/aborted.
    """
    try:
        container_service = HollyContainerService()

        # Find missions with containers that are in terminal states
        missions_to_cleanup = Mission.objects.filter(
            container_id__isnull=False, state__in=[Mission.State.COMPLETED, Mission.State.ABORTED]
        )

        cleaned_count = 0
        for mission in missions_to_cleanup:
            try:
                if container_service.stop_container(mission):
                    mission.container_id = None
                    mission.save(update_fields=["container_id"])
                    cleaned_count += 1
                    logger.info(f"Cleaned up container for mission {mission.id}")
            except Exception as e:
                logger.error(f"Failed to cleanup container for mission {mission.id}: {e!s}")

        return {"success": True, "cleaned_count": cleaned_count, "message": f"Cleaned up {cleaned_count} containers"}

    except Exception as e:
        logger.error(f"Error in cleanup task: {e!s}")
        return {"success": False, "error": str(e)}
