"""Webhook handler service for processing container events."""

import hashlib
from typing import Dict, Any, Optional
from loguru import logger
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from holly.holly.models import Mission, MissionConversation, Notification
from holly.holly.utils.redis_client import redis_client

# Idempotency window for de-duplicating at-least-once webhook deliveries.
_WEBHOOK_DEDUP_TTL = 60 * 60  # 1 hour


class WebhookEventType:
    """Container webhook event types."""
    # Initialization events
    INIT_STARTED = "init.started"
    INIT_COMPLETED = "init.completed"
    INIT_FAILED = "init.failed"

    # Container lifecycle events
    CONTAINER_READY = "container.ready"
    CONTAINER_ERROR = "container.error"
    CONTAINER_STOPPED = "container.stopped"

    # Task events
    TASK_STARTED = "task.started"
    TASK_PROGRESS = "task.progress"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"

    # Conversation events
    CONVERSATION_CREATED = "conversation.created"
    CONVERSATION_STARTED = "conversation.started"
    CONVERSATION_UPDATED = "conversation.updated"
    CONVERSATION_COMPLETED = "conversation.completed"
    CONVERSATION_ERROR = "conversation.error"

    # Pull Request events
    PR_CREATED = "pr.created"
    PR_FAILED = "pr.failed"

    # Git auto-push events
    GIT_AUTO_PUSH_COMPLETED = "git.auto_push.completed"
    GIT_AUTO_PUSH_FAILED = "git.auto_push.failed"


class WebhookHandler:
    """Service for handling container webhook events."""

    def __init__(self):
        """Initialize webhook handler."""
        self.event_handlers = {
            WebhookEventType.INIT_COMPLETED: self._handle_init_completed,
            WebhookEventType.INIT_FAILED: self._handle_init_failed,
            WebhookEventType.CONTAINER_READY: self._handle_container_ready,
            WebhookEventType.CONTAINER_ERROR: self._handle_container_error,
            WebhookEventType.TASK_STARTED: self._handle_task_started,
            WebhookEventType.TASK_COMPLETED: self._handle_task_completed,
            WebhookEventType.TASK_FAILED: self._handle_task_failed,
            WebhookEventType.CONVERSATION_STARTED: self._handle_conversation_started,
            WebhookEventType.CONVERSATION_UPDATED: self._handle_conversation_updated,
            WebhookEventType.CONVERSATION_COMPLETED: self._handle_conversation_completed,
            WebhookEventType.CONVERSATION_ERROR: self._handle_conversation_error,
            WebhookEventType.PR_CREATED: self._handle_pr_created,
            WebhookEventType.PR_FAILED: self._handle_pr_failed,
            WebhookEventType.GIT_AUTO_PUSH_COMPLETED: self._handle_git_auto_push_completed,
            WebhookEventType.GIT_AUTO_PUSH_FAILED: self._handle_git_auto_push_failed,
        }

    def process_webhook(
        self,
        mission_id: str,
        job_id: str,
        status: str,
        data: Dict[str, Any],
        timestamp: str
    ) -> Dict[str, Any]:
        """
        Process a webhook event from a container.

        Args:
            mission_id: Mission UUID
            job_id: Job identifier (e.g., "init", "clone_repo", etc.)
            status: Event status (completed, failed, processing)
            data: Event data dictionary
            timestamp: Event timestamp

        Returns:
            Processing result dictionary
        """
        # Idempotency: webhooks are delivered at-least-once. Short-circuit replays of
        # an identical event so we don't create duplicate notifications / PR entries
        # or re-trigger side effects like stop_container.
        dedup_key = "webhook:seen:" + hashlib.sha256(
            f"{mission_id}|{job_id}|{status}|{timestamp}".encode()
        ).hexdigest()
        if not cache.add(dedup_key, "1", _WEBHOOK_DEDUP_TTL):
            logger.info(f"Ignoring duplicate webhook delivery for mission={mission_id}, job={job_id}")
            return {"success": True, "duplicate": True, "mission_id": str(mission_id)}

        event_type = self._determine_event_type(job_id, status, data)
        logger.info(
            f"Processing webhook: mission={mission_id}, job={job_id}, "
            f"status={status}, event_type={event_type}"
        )

        try:
            # Lock the mission row for the duration so concurrent webhooks for the
            # same mission don't clobber each other's active_jobs / state writes.
            with transaction.atomic():
                try:
                    mission = Mission.objects.select_for_update().get(id=mission_id)
                except Mission.DoesNotExist:
                    error_msg = f"Mission {mission_id} not found"
                    logger.error(error_msg)
                    return {"success": False, "error": error_msg}

                self._update_active_jobs(mission, job_id, status, data, timestamp)

                handler = self.event_handlers.get(event_type)
                if handler:
                    # Let handler errors roll the transaction back rather than
                    # reporting success on a partially-applied event.
                    handler(mission, job_id, data)

                # Full save (not a narrow update_fields list) so a handler mutating a
                # field outside the previous hard-coded list is persisted.
                mission.save()

                # Only publish the real-time update after the DB commit succeeds.
                transaction.on_commit(
                    lambda: self._publish_update(mission_id, job_id, status, data)
                )
        except Exception:
            # The dedup key was claimed for a delivery that failed; release it so the
            # container's retry can be processed.
            cache.delete(dedup_key)
            raise

        return {
            "success": True,
            "mission_id": str(mission.id),
            "event_type": event_type
        }

    def _determine_event_type(
        self,
        job_id: str,
        status: str,
        data: Dict[str, Any]
    ) -> str:
        """
        Determine the event type from job_id, status, and data.

        Args:
            job_id: Job identifier
            status: Event status
            data: Event data

        Returns:
            Event type string
        """
        # Initialization events
        if job_id == "init" or job_id.startswith("init_"):
            if status == "completed":
                return WebhookEventType.INIT_COMPLETED
            elif status == "failed":
                return WebhookEventType.INIT_FAILED
            elif status == "started":
                return WebhookEventType.INIT_STARTED

        # Pull Request events - check data.type for job type
        job_type = data.get("type", "")
        if job_type == "create_pull_request":
            if status == "completed":
                return WebhookEventType.PR_CREATED
            elif status == "failed":
                return WebhookEventType.PR_FAILED

        # Git auto-push events - check data.event
        event = data.get("event", "")
        if event == "git.auto_push":
            if status == "completed":
                return WebhookEventType.GIT_AUTO_PUSH_COMPLETED
            elif status == "failed":
                return WebhookEventType.GIT_AUTO_PUSH_FAILED

        # Conversation events - check data.event for specific event type
        if "conversation_id" in data:
            event = data.get("event", "")
            if event == "conversation.started":
                return WebhookEventType.CONVERSATION_STARTED
            elif event == "conversation.completed":
                return WebhookEventType.CONVERSATION_COMPLETED
            elif event == "conversation.error":
                return WebhookEventType.CONVERSATION_ERROR
            # Fallback to status-based detection
            elif status == "completed":
                return WebhookEventType.CONVERSATION_UPDATED
            elif status == "failed":
                return WebhookEventType.CONVERSATION_ERROR
            elif status == "started":
                return WebhookEventType.CONVERSATION_STARTED

        # Generic task events
        if status == "completed":
            return WebhookEventType.TASK_COMPLETED
        elif status == "failed":
            return WebhookEventType.TASK_FAILED
        elif status == "started":
            return WebhookEventType.TASK_STARTED
        elif status == "processing":
            return WebhookEventType.TASK_PROGRESS

        # Default
        return f"unknown.{status}"

    def _update_active_jobs(
        self,
        mission: Mission,
        job_id: str,
        status: str,
        data: Dict[str, Any],
        timestamp: str
    ) -> None:
        """
        Update mission's active_jobs field.

        Args:
            mission: Mission instance
            job_id: Job identifier
            status: Job status
            data: Job data
            timestamp: Event timestamp
        """
        jobs = mission.active_jobs or []

        # Find existing job entry
        job_found = False
        for job in jobs:
            if job.get("job_id") == job_id:
                job["status"] = status
                job["timestamp"] = timestamp
                job["data"] = data
                job_found = True
                break

        # Add new job if not found
        if not job_found:
            jobs.append({
                "job_id": job_id,
                "status": status,
                "timestamp": timestamp,
                "data": data
            })

        mission.active_jobs = jobs

    def _publish_update(
        self,
        mission_id: str,
        job_id: str,
        status: str,
        data: Dict[str, Any]
    ) -> None:
        """
        Publish update to Redis for SSE streaming.

        Args:
            mission_id: Mission UUID
            job_id: Job identifier
            status: Job status
            data: Event data
        """
        channel = f"mission:{mission_id}:status"
        message = {
            "job_id": job_id,
            "status": status,
            "data": data
        }
        redis_client.publish(channel, message)

    def _create_notification(
        self,
        user,
        notification_type: str,
        title: str,
        message: str,
        mission_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        priority: str = Notification.Priority.NORMAL,
        data: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """
        Create a notification for a user.

        Args:
            user: User instance
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            mission_id: Optional mission ID
            conversation_id: Optional conversation ID
            priority: Notification priority
            data: Optional additional data

        Returns:
            Created Notification instance
        """
        return Notification.objects.create(
            user=user,
            type=notification_type,
            title=title,
            message=message,
            mission_id=mission_id,
            conversation_id=conversation_id,
            priority=priority,
            data=data or {}
        )

    # Event Handlers

    def _handle_init_completed(
        self,
        mission: Mission,
        job_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Handle successful initialization completion."""
        mission.state = Mission.State.READY
        mission.container_status = "ready"
        logger.info(f"Mission {mission.id} is now READY")

        # Create notification
        self._create_notification(
            user=mission.owner,
            notification_type=Notification.NotificationType.MISSION_READY,
            title=f"Mission Ready: {mission.title}",
            message=f"Your mission '{mission.title}' is now ready for conversations.",
            mission_id=str(mission.id),
            priority=Notification.Priority.NORMAL,
            data={"repositories": data.get("repositories", [])}
        )

    def _handle_init_failed(
        self,
        mission: Mission,
        job_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Handle initialization failure."""
        mission.state = Mission.State.ERROR
        mission.container_status = "error"
        error_message = data.get("error", "Unknown error during initialization")
        logger.error(f"Mission {mission.id} initialization failed: {error_message}")

        # Create notification
        self._create_notification(
            user=mission.owner,
            notification_type=Notification.NotificationType.MISSION_ERROR,
            title=f"Mission Error: {mission.title}",
            message=f"Failed to initialize mission: {error_message}",
            mission_id=str(mission.id),
            priority=Notification.Priority.HIGH,
            data={"error": error_message}
        )

    def _handle_container_ready(
        self,
        mission: Mission,
        job_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Handle container ready event."""
        mission.state = Mission.State.READY
        mission.container_status = "ready"
        logger.info(f"Container for mission {mission.id} is ready")

        self._create_notification(
            user=mission.owner,
            notification_type=Notification.NotificationType.CONTAINER_STARTED,
            title="Container Ready",
            message=f"Container for mission '{mission.title}' is ready.",
            mission_id=str(mission.id),
            data=data
        )

    def _handle_container_error(
        self,
        mission: Mission,
        job_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Handle container error event."""
        mission.state = Mission.State.ERROR
        mission.container_status = "error"
        error_message = data.get("error", "Container error")
        logger.error(f"Container error for mission {mission.id}: {error_message}")

        self._create_notification(
            user=mission.owner,
            notification_type=Notification.NotificationType.CONTAINER_ERROR,
            title="Container Error",
            message=f"Container error: {error_message}",
            mission_id=str(mission.id),
            priority=Notification.Priority.HIGH,
            data={"error": error_message}
        )

    def _handle_task_completed(
        self,
        mission: Mission,
        job_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Handle task completion."""
        task_name = data.get("task_name", job_id)
        logger.info(f"Task completed: {task_name} for mission {mission.id}")

        # Only notify for important tasks
        if data.get("notify", False):
            self._create_notification(
                user=mission.owner,
                notification_type=Notification.NotificationType.TASK_COMPLETED,
                title=f"Task Completed: {task_name}",
                message=data.get("message", f"Task '{task_name}' completed successfully."),
                mission_id=str(mission.id),
                data=data
            )

    def _handle_task_failed(
        self,
        mission: Mission,
        job_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Handle task failure."""
        task_name = data.get("task_name", job_id)
        error_message = data.get("error", "Task failed")
        logger.error(f"Task failed: {task_name} for mission {mission.id}: {error_message}")

        self._create_notification(
            user=mission.owner,
            notification_type=Notification.NotificationType.TASK_FAILED,
            title=f"Task Failed: {task_name}",
            message=f"Task '{task_name}' failed: {error_message}",
            mission_id=str(mission.id),
            priority=Notification.Priority.HIGH,
            data={"error": error_message}
        )

    def _handle_conversation_updated(
        self,
        mission: Mission,
        job_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Handle conversation update."""
        conversation_id = data.get("conversation_id")
        if not conversation_id:
            return

        try:
            conversation = MissionConversation.objects.get(conversation_id=conversation_id)

            # Update conversation title if provided
            new_title = data.get("title")
            if new_title and new_title != conversation.title:
                conversation.title = new_title
                conversation.save(update_fields=["title", "updated_at"])
                logger.info(f"Updated conversation {conversation_id} title: {new_title}")

        except MissionConversation.DoesNotExist:
            logger.error(f"Conversation {conversation_id} not found")

    def _handle_conversation_error(
        self,
        mission: Mission,
        job_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Handle conversation error."""
        conversation_id = data.get("conversation_id")
        error_message = data.get("error", "Conversation error")
        logger.error(f"Conversation {conversation_id} error: {error_message}")

        self._create_notification(
            user=mission.owner,
            notification_type=Notification.NotificationType.CONVERSATION_ERROR,
            title="Conversation Error",
            message=error_message,
            mission_id=str(mission.id),
            conversation_id=conversation_id,
            priority=Notification.Priority.NORMAL,
            data={"error": error_message}
        )

    def _handle_conversation_started(
        self,
        mission: Mission,
        job_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Handle conversation started event."""
        conversation_id = data.get("conversation_id")
        message = data.get("message", "Processing message...")
        logger.info(f"Conversation {conversation_id} started for mission {mission.id}")

        # Update mission state to show it's processing
        if mission.state == Mission.State.READY:
            mission.container_status = "processing"

    def _handle_conversation_completed(
        self,
        mission: Mission,
        job_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Handle conversation completed event."""
        conversation_id = data.get("conversation_id")
        logger.info(f"Conversation {conversation_id} completed for mission {mission.id}")

        # Update mission state back to ready
        if mission.state == Mission.State.READY:
            mission.container_status = "ready"

        # Optionally create a notification for the response
        response_preview = data.get("response_preview", "")
        if response_preview:
            self._create_notification(
                user=mission.owner,
                notification_type=Notification.NotificationType.MESSAGE_RECEIVED,
                title=f"Response Ready: {mission.title}",
                message=response_preview,
                mission_id=str(mission.id),
                conversation_id=conversation_id,
                priority=Notification.Priority.NORMAL,
                data=data
            )

    def _handle_task_started(
        self,
        mission: Mission,
        job_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Handle task started event."""
        task_name = data.get("task_name", job_id)
        logger.info(f"Task started: {task_name} for mission {mission.id}")

        # Update mission status to processing
        if mission.state == Mission.State.READY:
            mission.container_status = "processing"

    def _handle_pr_created(
        self,
        mission: Mission,
        job_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Handle pull request creation success."""
        result = data.get("result", {})
        pr_number = result.get("pr_number")
        pr_url = result.get("pr_url")
        pr_state = result.get("state", "open")

        logger.info(f"PR created for mission {mission.id}: #{pr_number} at {pr_url}")

        # Append PR information to the mission's metadata (now a real model field).
        if mission.metadata is None:
            mission.metadata = {}
        mission.metadata.setdefault("pull_requests", []).append({
            "pr_number": pr_number,
            "pr_url": pr_url,
            "state": pr_state,
            "created_at": timezone.now().isoformat(),
            "job_id": job_id,
        })

        # Store the most recent PR in dedicated fields.
        mission.pull_request_url = pr_url or ""
        mission.pull_request_number = pr_number

        # Auto-stop container after successful PR creation (pause/reset, not complete)
        if mission.container_id:
            # Import here to avoid circular imports
            from holly.holly.services.containers.holly_container_service import HollyContainerService

            try:
                container_service = HollyContainerService()
                success = container_service.stop_container(mission)

                if success:
                    logger.info(f"Successfully stopped container for mission {mission.id} after PR creation (pause/reset)")
                    # Clear container ID but keep mission state (pause, not complete)
                    mission.container_id = None
                    mission.container_status = "stopped"
                    # Note: Mission state is NOT changed to COMPLETED - this is a pause/reset
                else:
                    logger.warning(f"Failed to stop container for mission {mission.id} after PR creation")
            except Exception as e:
                logger.error(f"Error stopping container for mission {mission.id}: {e}")
                # Don't fail the PR creation if container stop fails
        else:
            # No container running, nothing to stop
            logger.info(f"No container to stop for mission {mission.id} after PR creation")

        # Create notification
        self._create_notification(
            user=mission.owner,
            notification_type=Notification.NotificationType.PR_CREATED,
            title=f"Pull Request Created: #{pr_number}",
            message=f"Pull request #{pr_number} created successfully for mission '{mission.title}'",
            mission_id=str(mission.id),
            priority=Notification.Priority.HIGH,
            data={
                "pr_number": pr_number,
                "pr_url": pr_url,
                "pr_state": pr_state
            }
        )

    def _handle_pr_failed(
        self,
        mission: Mission,
        job_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Handle pull request creation failure."""
        error_message = data.get("error", "Unknown error creating pull request")
        logger.error(f"PR creation failed for mission {mission.id}: {error_message}")

        # Create notification
        self._create_notification(
            user=mission.owner,
            notification_type=Notification.NotificationType.PR_FAILED,
            title="Pull Request Creation Failed",
            message=f"Failed to create pull request for mission '{mission.title}': {error_message}",
            mission_id=str(mission.id),
            priority=Notification.Priority.HIGH,
            data={"error": error_message}
        )

    def _handle_git_auto_push_completed(
        self,
        mission: Mission,
        job_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Handle successful git auto-push event."""
        repo = data.get("repo", "")
        branch = data.get("branch", "")
        commit_message = data.get("commit_message", "")
        conversation_id = data.get("conversation_id")

        logger.info(f"Git auto-push completed for mission {mission.id}: {repo}/{branch}")

        # Create notification
        self._create_notification(
            user=mission.owner,
            notification_type=Notification.NotificationType.TASK_COMPLETED,
            title="Changes Pushed to Remote",
            message=f"Changes pushed to {repo} on branch {branch}",
            mission_id=str(mission.id),
            conversation_id=conversation_id,
            priority=Notification.Priority.NORMAL,
            data={
                "repo": repo,
                "branch": branch,
                "commit_message": commit_message
            }
        )

    def _handle_git_auto_push_failed(
        self,
        mission: Mission,
        job_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Handle failed git auto-push event."""
        error_message = data.get("error", "Unknown error pushing changes")
        conversation_id = data.get("conversation_id")

        logger.error(f"Git auto-push failed for mission {mission.id}: {error_message}")

        # Create notification
        self._create_notification(
            user=mission.owner,
            notification_type=Notification.NotificationType.TASK_FAILED,
            title="Failed to Push Changes",
            message=f"Failed to push changes: {error_message}",
            mission_id=str(mission.id),
            conversation_id=conversation_id,
            priority=Notification.Priority.HIGH,
            data={"error": error_message}
        )


# Singleton instance
webhook_handler = WebhookHandler()
