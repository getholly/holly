"""Webhook receiver for container job updates."""

from django.conf import settings
from django.http import HttpRequest
from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel
from typing import Dict, Any
from loguru import logger

from holly.holly.models.mission import Mission
from holly.holly.utils.redis_client import redis_client
from holly.holly.utils.webhook_signing import SIGNATURE_HEADER, verify_signature

router = Router()


class WebhookPayload(BaseModel):
    """Webhook payload from container."""
    mission_id: str
    job_id: str
    status: str
    data: Dict[str, Any]
    timestamp: str


def publish_mission_update(mission_id: str, status: str, data: Dict[str, Any]) -> None:
    """
    Publish mission update to Redis for SSE streaming.

    Args:
        mission_id: Mission ID
        status: Job status
        data: Update data
    """
    channel = f"mission:{mission_id}:status"
    message = {
        "status": status,
        "data": data
    }
    success = redis_client.publish(channel, message)
    if success:
        logger.info(f"Published mission update for {mission_id}: {status}")
    else:
        logger.warning(f"Could not publish mission update (Redis unavailable): {mission_id}: {status}")


@router.post("/container-webhook", auth=None)  # No auth required for container callbacks
def receive_container_webhook(request: HttpRequest, payload: WebhookPayload) -> Dict[str, Any]:
    """
    Receive webhook from container about job status.

    This endpoint is called by the container when a job completes, fails,
    or has a significant status change.

    Args:
        request: HTTP request
        payload: Webhook payload with job info

    Returns:
        Success response
    """
    from holly.holly.services.webhook_handler import webhook_handler

    # Verify the HMAC signature over the raw body using the per-mission token.
    signature = request.headers.get(SIGNATURE_HEADER)
    if verify_signature(payload.mission_id, request.body, signature):
        pass
    elif settings.WEBHOOK_SIGNATURE_REQUIRED:
        logger.warning(f"Rejected unsigned/invalid webhook for mission {payload.mission_id}")
        raise HttpError(401, "Invalid webhook signature")
    else:
        logger.warning(
            f"Accepting webhook with missing/invalid signature for mission "
            f"{payload.mission_id} (WEBHOOK_SIGNATURE_REQUIRED is off)"
        )

    logger.info(
        f"Received webhook for mission {payload.mission_id}, "
        f"job {payload.job_id}, status: {payload.status}"
    )

    try:
        result = webhook_handler.process_webhook(
            mission_id=payload.mission_id,
            job_id=payload.job_id,
            status=payload.status,
            data=payload.data,
            timestamp=payload.timestamp
        )
        return result

    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        return {"success": False, "error": str(e)}

