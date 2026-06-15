import http
import json
from collections.abc import Iterator
from typing import Optional
from uuid import UUID

import redis
from asgiref.sync import async_to_sync, sync_to_async
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest, StreamingHttpResponse
from django.shortcuts import aget_object_or_404, get_object_or_404
from loguru import logger
from ninja import Router, Query
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.tokens import AccessToken

User = get_user_model()

from holly.holly.api.mission_schemas import (
    ContainerStartResponse,
    ConversationStartResponse,
    GenericResponse,
    LLMSummary,
    MissionCollaboratorSchema,
    MissionConversationCreate,
    MissionConversationUpdate,
    MissionCreate,
    MissionDetail,
    MissionKnowledgeSchema,
    MissionKnowledgeSetSchema,
    MissionRepositoryAddSchema,
    MissionRepositoryRemoveSchema,
    MissionRepositorySetSchema,
    MissionStateUpdate,
    MissionSummary,
    MissionToolSchema,
    MissionToolSetSchema,
    MissionUpdate,
)
from holly.holly.api.proxy import MCPProxyClient
from holly.holly.api.schemas import ConversationCreate, PRCreateRequest, PRCreateResponse
from holly.holly.api.auth import AsyncJWTAuth
from holly.holly.api.views.conversations import get_model_config
import httpx
from holly.holly.models import LLM
from holly.holly.models.mission import Mission
from holly.holly.services.mission_service import mission_service
from holly.holly.services.summary_service import agenerate_title_summary, generate_title_summary

router = Router(auth=JWTAuth())


def _mission_summary_from_mission(mission: Mission) -> MissionSummary:
    llm = None
    try:
        if mission.llm is not None:
            llm = LLMSummary(
                id=mission.llm.id,
                name=mission.llm.name,
            )
        else:
            logger.error(f"LLM not found for mission {mission.id}")
    except Exception as e:
        logger.error(f"Error getting LLM for mission {mission.id}: {e!s}")
    return MissionSummary(
        id=mission.id,
        title=mission.title,
        state=mission.state,
        created_at=mission.created_at,
        updated_at=mission.updated_at,
        owner=mission.owner.email,
        branch_name=mission.branch_name,
        repository_count=mission.repositories.count(),
        llm=llm,
    )


@router.get("/", response=list[MissionSummary])
def list_missions(request: HttpRequest) -> list[MissionSummary]:
    """
    Get a list of all missions accessible by the current user.

    Returns:
        list[MissionSummary]: A list of mission summaries
    """
    missions = mission_service.get_missions_for_user(request.user)
    return [_mission_summary_from_mission(mission) for mission in missions]


@router.get("/{mission_id}", response=MissionDetail)
def get_mission(request: HttpRequest, mission_id: UUID) -> MissionDetail:
    """
    Get detailed information about a mission.

    Args:
        request: The HTTP request
        mission_id: The UUID of the mission to retrieve

    Returns:
        MissionDetail: The mission details
    """
    mission = get_object_or_404(Mission, id=mission_id)

    # Check if user has access
    if not async_to_sync(mission.can_be_accessed_by)(request.user):
        raise http.HTTPStatus(403)
        # return {"detail": "You do not have permission to access this mission"}

    return mission


@router.post("/", response=MissionDetail)
def create_mission(request: HttpRequest, mission_data: MissionCreate) -> MissionDetail:
    """
    Create a new mission.

    Args:
        request: The HTTP request
        mission_data: The data for the new mission

    Returns:
        MissionDetail: The created mission details
    """
    try:
        llm = LLM.objects.get(id=mission_data.llm_id)
    except LLM.DoesNotExist:
        llm = LLM.objects.get(name="Holly")

    # generate_title_summary returns (title, branch_name)
    generated_title, branch_name = generate_title_summary(mission_data.description, request.user, llm)

    return mission_service.create_mission(
        owner=request.user,
        title=generated_title,
        description=mission_data.description,
        branch_name=branch_name,
        repositories=mission_data.repositories,
        knowledge_item_ids=mission_data.knowledge_item_ids,
        tool_ids=mission_data.tool_ids,
        requirements=mission_data.requirements,
        llm=llm,
    )



@router.put("/{mission_id}", response=MissionDetail)
def update_mission(request: HttpRequest, mission_id: UUID, mission_data: MissionUpdate) -> MissionDetail:
    """
    Update an existing mission.

    Args:
        request: The HTTP request
        mission_id: The UUID of the mission to update
        mission_data: The updated mission data

    Returns:
        MissionDetail: The updated mission details
    """
    mission = get_object_or_404(Mission, id=mission_id)

    # Check if user has access
    if not async_to_sync(mission.can_be_accessed_by)(request.user):
        return {"detail": "You do not have permission to update this mission"}

    # Update the mission
    success, message, updated_mission = mission_service.update_mission(
        mission_id=mission_id,
        updates=mission_data.dict(exclude_unset=True),
    )

    if not success:
        return {"detail": message}

    return updated_mission


@router.delete("/{mission_id}", response=GenericResponse)
def delete_mission(request: HttpRequest, mission_id: UUID) -> GenericResponse:
    """
    Delete a mission.

    Args:
        request: The HTTP request
        mission_id: The UUID of the mission to delete

    Returns:
        GenericResponse: Response indicating success or failure
    """
    mission = get_object_or_404(Mission, id=mission_id)

    # Only the owner can delete the mission
    if request.user != mission.owner:
        return GenericResponse(success=False, message="Only the mission owner can delete this mission")

    try:
        # Delete the mission
        mission.delete()
        return GenericResponse(success=True, message="Mission deleted successfully")
    except Exception as e:
        logger.error(f"Error deleting mission {mission_id}: {e!s}")
        return GenericResponse(success=False, message=f"Failed to delete mission: {str(e)}")


@router.post("/{mission_id}/collaborators", response=GenericResponse)
def add_collaborators(request: HttpRequest, mission_id: UUID, data: MissionCollaboratorSchema) -> GenericResponse:
    """
    Add collaborators to a mission.

    Args:
        request: The HTTP request
        mission_id: The UUID of the mission
        data: The collaborator data containing user IDs to add

    Returns:
        GenericResponse: Response indicating success or failure
    """
    mission = get_object_or_404(Mission, id=mission_id)

    # Only the owner can add collaborators
    if request.user != mission.owner:
        return GenericResponse(success=False, message="Only the mission owner can add collaborators")

    # Add the collaborators
    success, message, _ = mission_service.add_collaborators(
        mission_id=mission_id,
        user_ids=data.user_ids,
    )

    return GenericResponse(success=success, message=message)


@router.delete("/{mission_id}/collaborators", response=GenericResponse)
def remove_collaborators(request: HttpRequest, mission_id: UUID, data: MissionCollaboratorSchema) -> GenericResponse:
    """
    Remove collaborators from a mission.

    Args:
        request: The HTTP request
        mission_id: The UUID of the mission
        data: The collaborator data containing user IDs to remove

    Returns:
        GenericResponse: Response indicating success or failure
    """
    mission = get_object_or_404(Mission, id=mission_id)

    # Only the owner can remove collaborators
    if request.user != mission.owner:
        return GenericResponse(success=False, message="Only the mission owner can remove collaborators")

    # Remove the collaborators
    success, message, _ = mission_service.remove_collaborators(
        mission_id=mission_id,
        user_ids=data.user_ids,
    )

    return GenericResponse(success=success, message=message)


@router.post("/{mission_id}/repositories", response=GenericResponse)
def add_repositories(request: HttpRequest, mission_id: UUID, data: MissionRepositoryAddSchema) -> GenericResponse:
    """
    Add repositories to a mission.

    Args:
        request: The HTTP request
        mission_id: The UUID of the mission
        data: The repository data containing repository IDs to add

    Returns:
        GenericResponse: Response indicating success or failure
    """
    mission = get_object_or_404(Mission, id=mission_id)

    # Check if user has access
    if not async_to_sync(mission.can_be_accessed_by)(request.user):
        return GenericResponse(success=False, message="You do not have permission to update this mission")

    # Add the repositories
    success, message, _ = mission_service.add_repositories(
        request.user,
        mission_id=mission_id,
        repos=data.repos,
    )

    return GenericResponse(success=success, message=message)


@router.delete("/{mission_id}/repositories", response=GenericResponse)
def remove_repositories(request: HttpRequest, mission_id: UUID, data: MissionRepositoryRemoveSchema) -> GenericResponse:
    """
    Remove repositories from a mission.

    Args:
        request: The HTTP request
        mission_id: The UUID of the mission
        data: The repository data containing RepositoryDetail IDs to remove (not Github id)

    Returns:
        GenericResponse: Response indicating success or failure
    """
    mission = get_object_or_404(Mission, id=mission_id)

    # Check if user has access
    if not async_to_sync(mission.can_be_accessed_by)(request.user):
        return GenericResponse(success=False, message="You do not have permission to update this mission")

    # Remove the repositories
    success, message, _ = mission_service.remove_repositories(
        mission_id=mission_id,
        repository_ids=data.repository_ids,
    )

    return GenericResponse(success=success, message=message)


@router.post("/{mission_id}/knowledge", response=GenericResponse)
def add_knowledge_items(request: HttpRequest, mission_id: UUID, data: MissionKnowledgeSchema) -> GenericResponse:
    """
    Add knowledge items to a mission.

    Args:
        request: The HTTP request
        mission_id: The UUID of the mission
        data: The knowledge data containing knowledge item IDs to add

    Returns:
        GenericResponse: Response indicating success or failure
    """
    mission = get_object_or_404(Mission, id=mission_id)

    # Check if user has access
    if not async_to_sync(mission.can_be_accessed_by)(request.user):
        return GenericResponse(success=False, message="You do not have permission to update this mission")

    # Add the knowledge items
    success, message, _ = mission_service.add_knowledge_items(
        mission_id=mission_id,
        knowledge_item_ids=data.knowledge_item_ids,
    )

    return GenericResponse(success=success, message=message)


@router.delete("/{mission_id}/knowledge", response=GenericResponse)
def remove_knowledge_items(request: HttpRequest, mission_id: UUID, data: MissionKnowledgeSchema) -> GenericResponse:
    """
    Remove knowledge items from a mission.

    Args:
        request: The HTTP request
        mission_id: The UUID of the mission
        data: The knowledge data containing knowledge item IDs to remove

    Returns:
        GenericResponse: Response indicating success or failure
    """
    mission = get_object_or_404(Mission, id=mission_id)

    # Check if user has access
    if not async_to_sync(mission.can_be_accessed_by)(request.user):
        return GenericResponse(success=False, message="You do not have permission to update this mission")

    # Remove the knowledge items
    success, message, _ = mission_service.remove_knowledge_items(
        mission_id=mission_id,
        knowledge_item_ids=data.knowledge_item_ids,
    )

    return GenericResponse(success=success, message=message)


@router.put("/{mission_id}/repositories", response=GenericResponse)
def set_repositories(request: HttpRequest, mission_id: UUID, data: MissionRepositorySetSchema) -> GenericResponse:
    """
    Set repositories for a mission (replaces all existing repositories).

    Args:
        request: The HTTP request
        mission_id: The UUID of the mission
        data: The repository data containing complete list of repositories to set

    Returns:
        GenericResponse: Response indicating success or failure
    """
    mission = get_object_or_404(Mission, id=mission_id)

    # Check if user has access
    if not async_to_sync(mission.can_be_accessed_by)(request.user):
        return GenericResponse(success=False, message="You do not have permission to update this mission")

    # Set the repositories
    success, message, _ = mission_service.set_repositories(
        user=request.user,
        mission_id=mission_id,
        repos=data.repos,
    )

    return GenericResponse(success=success, message=message)


@router.put("/{mission_id}/knowledge", response=GenericResponse)
def set_knowledge_items(request: HttpRequest, mission_id: UUID, data: MissionKnowledgeSetSchema) -> GenericResponse:
    """
    Set knowledge items for a mission (replaces all existing knowledge items).

    Args:
        request: The HTTP request
        mission_id: The UUID of the mission
        data: The knowledge data containing complete list of knowledge item IDs to set

    Returns:
        GenericResponse: Response indicating success or failure
    """
    mission = get_object_or_404(Mission, id=mission_id)

    # Check if user has access
    if not async_to_sync(mission.can_be_accessed_by)(request.user):
        return GenericResponse(success=False, message="You do not have permission to update this mission")

    # Set the knowledge items
    success, message, _ = mission_service.set_knowledge_items(
        mission_id=mission_id,
        knowledge_item_ids=data.knowledge_item_ids,
    )

    return GenericResponse(success=success, message=message)


@router.post("/{mission_id}/tools", response=GenericResponse)
def add_tools(request: HttpRequest, mission_id: UUID, data: MissionToolSchema) -> GenericResponse:
    """
    Add tools to a mission.

    Args:
        request: The HTTP request
        mission_id: The UUID of the mission
        data: The tool data containing tool IDs to add

    Returns:
        GenericResponse: Response indicating success or failure
    """
    mission = get_object_or_404(Mission, id=mission_id)

    # Check if user has access
    if not async_to_sync(mission.can_be_accessed_by)(request.user):
        return GenericResponse(success=False, message="You do not have permission to update this mission")

    # Add the tools
    success, message, _ = mission_service.add_tools(
        mission_id=mission_id,
        tool_ids=data.tool_ids,
    )

    return GenericResponse(success=success, message=message)


@router.delete("/{mission_id}/tools", response=GenericResponse)
def remove_tools(request: HttpRequest, mission_id: UUID, data: MissionToolSchema) -> GenericResponse:
    """
    Remove tools from a mission.

    Args:
        request: The HTTP request
        mission_id: The UUID of the mission
        data: The tool data containing tool IDs to remove

    Returns:
        GenericResponse: Response indicating success or failure
    """
    mission = get_object_or_404(Mission, id=mission_id)

    # Check if user has access
    if not async_to_sync(mission.can_be_accessed_by)(request.user):
        return GenericResponse(success=False, message="You do not have permission to update this mission")

    # Remove the tools
    success, message, _ = mission_service.remove_tools(
        mission_id=mission_id,
        tool_ids=data.tool_ids,
    )

    return GenericResponse(success=success, message=message)


@router.put("/{mission_id}/tools", response=GenericResponse)
def set_tools(request: HttpRequest, mission_id: UUID, data: MissionToolSetSchema) -> GenericResponse:
    """
    Set tools for a mission (replaces all existing tools).

    Args:
        request: The HTTP request
        mission_id: The UUID of the mission
        data: The tool data containing complete list of tool IDs to set

    Returns:
        GenericResponse: Response indicating success or failure
    """
    mission = get_object_or_404(Mission, id=mission_id)

    # Check if user has access
    if not async_to_sync(mission.can_be_accessed_by)(request.user):
        return GenericResponse(success=False, message="You do not have permission to update this mission")

    # Set the tools
    success, message, _ = mission_service.set_tools(
        mission_id=mission_id,
        tool_ids=data.tool_ids,
    )

    return GenericResponse(success=success, message=message)


@router.post("/{mission_id}/start", response=ContainerStartResponse)
def start_mission(request: HttpRequest, mission_id: UUID) -> ContainerStartResponse:
    """
    Start a mission by creating a container.

    Args:
        request: The HTTP request
        mission_id: The UUID of the mission to start

    Returns:
        ContainerStartResponse: Response with container information
    """
    mission = get_object_or_404(Mission, id=mission_id)

    # Check if user has access
    if not async_to_sync(mission.can_be_accessed_by)(request.user):
        return ContainerStartResponse(
            mission_id=mission_id,
            container_id=None,
            success=False,
            message="You do not have permission to start this mission",
        )

    # Check if container is already running
    if mission.container_id and mission_service.container_service.is_container_running(mission):
        return ContainerStartResponse(
            mission_id=mission_id,
            container_id=mission.container_id,
            success=True,
            message="Mission container is already running",
        )

    # Start the container
    success, message, container_id = mission_service.start_mission_container(
        mission_id=mission_id,
        user=request.user,
    )

    return ContainerStartResponse(mission_id=mission_id, container_id=container_id, success=success, message=message)


@router.get("/sse/start/{mission_id}", auth=None)
def start_mission_sse(request: HttpRequest, mission_id: str, token: Optional[str] = Query(None)) -> StreamingHttpResponse:
    """Stream mission start progress via SSE.

    Accepts authentication via query parameter 'token' since EventSource cannot send custom headers.
    """

    # Authenticate using token query parameter if provided
    user = request.user
    if token:
        try:
            access_token = AccessToken(token)
            user_id = access_token.get("user_id")
            if user_id:
                user = User.objects.get(id=user_id)
                # Set the authenticated user on the request
                request.user = user
                logger.info(f"Successfully authenticated user {user.id} via token for mission {mission_id}")
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Token validation failed for mission {mission_id}: {error_type} - {e}")
            return StreamingHttpResponse(
                f'data: {{"error": "Invalid or expired token", "detail": "{error_type}"}}\n\n',
                content_type="text/event-stream",
                status=http.HTTPStatus.UNAUTHORIZED,
            )

    # Check if user is authenticated (either from session or token)
    if not user or not user.is_authenticated:
        logger.warning(f"Unauthenticated access attempt to mission {mission_id}")
        return StreamingHttpResponse(
            'data: {"error": "Authentication required"}\n\n',
            content_type="text/event-stream",
            status=http.HTTPStatus.UNAUTHORIZED,
        )

    mission = get_object_or_404(Mission, id=mission_id)

    if not async_to_sync(mission.can_be_accessed_by)(request.user):
        return StreamingHttpResponse(
            'data: {"error": "Unauthorized"}\n\n',
            content_type="text/event-stream",
            status=http.HTTPStatus.FORBIDDEN,
        )

    def event_stream() -> Iterator[str]:
        yield f"data: {json.dumps({'status': 'container_starting'})}\n\n"

        success, message, container_id = mission_service.start_mission_container(
            mission_id=mission_id,
            user=request.user,
        )

        if not success or not container_id:
            yield f"data: {json.dumps({'status': 'error', 'message': message})}\n\n"
            yield "data: [DONE]\n\n"
            return

        yield (
            f"data: {json.dumps({'status': 'container_started', 'container_id': container_id, 'message': message})}\n\n"
        )

        redis_client = redis.StrictRedis.from_url(settings.CELERY_RESULT_BACKEND)
        pubsub = redis_client.pubsub()
        channel = f"mission:{mission_id}:status"
        pubsub.subscribe(channel)

        try:
            for msg in pubsub.listen():
                if msg.get("type") != "message":
                    continue
                try:
                    data = json.loads(msg["data"])
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON in Redis message: {msg['data']}")
                    continue

                yield f"data: {json.dumps(data)}\n\n"

                if data.get("status") in ["completed", "failed"]:
                    break
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Error in SSE stream for mission {mission_id}: {exc!s}")
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        finally:
            pubsub.unsubscribe(channel)
            pubsub.close()

        yield "data: [DONE]\n\n"

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


@router.post("/{mission_id}/end", response=GenericResponse)
def end_mission(request: HttpRequest, mission_id: UUID, data: MissionStateUpdate) -> GenericResponse:
    """
    End a mission (mark as completed or aborted).

    Args:
        request: The HTTP request
        mission_id: The UUID of the mission to end
        data: The state update data

    Returns:
        GenericResponse: Response indicating success or failure
    """
    mission = get_object_or_404(Mission, id=mission_id)

    # Check if user has access
    if not async_to_sync(mission.can_be_accessed_by)(request.user):
        return GenericResponse(success=False, message="You do not have permission to end this mission")

    # Determine if marking as completed or aborted
    complete = data.state == Mission.State.COMPLETED

    # Stop the container if running
    if mission.container_id:
        stop_success, stop_message = mission_service.stop_mission_container(mission_id=mission_id, user=request.user)

        if not stop_success:
            logger.warning(f"Could not stop container for mission {mission_id}: {stop_message}")
            # Continue with ending mission even if container stop fails

    # End the mission
    success, message = mission_service.end_mission(
        mission_id=mission_id,
        user=request.user,
        complete=complete,
    )

    # Clear container_id if it hasn't been done already
    if success and mission.container_id:
        mission.container_id = None
        mission.save(update_fields=["container_id"])

    return GenericResponse(success=success, message=message)


@router.post("/{mission_id}/conversation", response=ConversationStartResponse, auth=AsyncJWTAuth())
async def create_conversation(
    request: HttpRequest, mission_id: UUID, data: MissionConversationCreate
) -> ConversationStartResponse:
    """
    Create a new conversation for a mission (async/event-driven).

    This endpoint immediately returns a job_id and starts the conversation
    processing in the background. The container will send webhooks with updates.

    Args:
        request: The HTTP request
        mission_id: The UUID of the mission
        data: The conversation data

    Returns:
        ConversationStartResponse: Response with job_id for tracking
    """
    from uuid import uuid4
    from holly.holly.models.mission_conversation import MissionConversation

    mission: Mission = await aget_object_or_404(Mission.objects.select_related('llm'), id=mission_id)

    # Check if user has access
    if not await mission.can_be_accessed_by(request.user):
        return ConversationStartResponse(
            success=False,
            message="You do not have permission to access this mission"
        )

    try:
        # Generate IDs
        conversation_id = str(uuid4())
        job_id = str(uuid4())

        # Generate title asynchronously (robust to return shape and failures)
        generated_title: str | None = None
        try:
            title_result = await agenerate_title_summary(
                data.title or data.initial_message or "New Conversation",
                request.user,
                mission.llm,
            )
            if isinstance(title_result, tuple) and len(title_result) >= 1:
                generated_title = title_result[0]
            elif isinstance(title_result, str):
                generated_title = title_result
        except Exception as _e:  # noqa: BLE001
            # Fallback handled below
            generated_title = None

        if not generated_title:
            fallback = (data.title or data.initial_message or "New Conversation").strip()
            generated_title = fallback[:80]

        # Create conversation record
        await MissionConversation.objects.acreate(
            mission=mission,
            conversation_id=conversation_id,
            title=generated_title,
            status="pending",
        )

        # Ensure mission container is ready (one container per mission)
        container_success, container_error, container_url = await mission_service.ensure_mission_container(
            mission_id, request.user
        )

        if not container_success:
            return ConversationStartResponse(
                success=False,
                message=f"Failed to start mission container: {container_error}"
            )

        # Container is ready, conversation created in Django
        # The container will create the conversation when first message is sent
        return ConversationStartResponse(
            success=True,
            conversation_id=conversation_id,
            job_id=job_id,
            message="Conversation created successfully"
        )

    except Exception as e:
        logger.error(f"Error creating conversation for mission {mission_id}: {e!s}")
        return ConversationStartResponse(
            success=False,
            message=f"Error creating conversation: {e!s}"
        )


@router.put("/{mission_id}/conversation/{conversation_id}/summary", response=GenericResponse)
def update_conversation_summary(
    request: HttpRequest, mission_id: UUID, conversation_id: str, data: MissionConversationUpdate
) -> GenericResponse:
    """
    Update a mission conversation with a summary.

    Args:
        request: The HTTP request
        mission_id: The UUID of the mission
        conversation_id: The ID of the conversation
        data: The updated conversation data

    Returns:
        GenericResponse: Response indicating success or failure
    """
    mission = get_object_or_404(Mission, id=mission_id)

    # Check if user has access
    if not async_to_sync(mission.can_be_accessed_by)(request.user):
        return GenericResponse(success=False, message="You do not have permission to access this mission")

    # Update the conversation summary
    success, message = mission_service.update_conversation_summary(
        mission_id=mission_id,
        conversation_id=conversation_id,
        summary=data.summary or "",
        remaining_tasks=data.remaining_tasks or [],
    )

    return GenericResponse(success=success, message=message)


@router.get("/{mission_id}/jobs/{job_id}", response=dict)
def get_mission_job_status(request: HttpRequest, mission_id: UUID, job_id: str) -> dict:
    """
    Get job status for a mission.

    This endpoint polls the container for job status.

    Args:
        request: HTTP request
        mission_id: Mission ID
        job_id: Job ID to query

    Returns:
        Job status dictionary
    """
    mission = get_object_or_404(Mission, id=mission_id)

    # Check if user has access
    if not async_to_sync(mission.can_be_accessed_by)(request.user):
        return {"error": "Unauthorized", "job_id": job_id}

    return mission.get_job_status(job_id)


@router.get("/{mission_id}/clone-status/stream")
def stream_clone_status(request: HttpRequest, mission_id: str):
    """
    Server-Sent Events endpoint for streaming clone status updates.

    Args:
        request: The HTTP request
        mission_id: The UUID of the mission

    Returns:
        StreamingHttpResponse: SSE stream of clone status updates
    """
    mission = get_object_or_404(Mission, id=mission_id)

    # Check if user has access
    if not async_to_sync(mission.can_be_accessed_by)(request.user):
        return StreamingHttpResponse(
            'data: {"error": "Unauthorized"}\n\n', content_type="text/event-stream", status=403
        )

    def event_stream():
        """Generate SSE events from Redis pub/sub."""
        # Connect to Redis
        redis_client = redis.StrictRedis.from_url(settings.CELERY_RESULT_BACKEND)
        pubsub = redis_client.pubsub()
        channel = f"mission:{mission_id}:clone_status"

        # Subscribe to the channel
        pubsub.subscribe(channel)

        # Send initial connection message
        yield f"data: {json.dumps({'status': 'connected', 'mission_id': str(mission_id)})}\n\n"

        try:
            # Listen for messages
            for message in pubsub.listen():
                if message["type"] == "message":
                    # Parse and forward the message
                    try:
                        data = json.loads(message["data"])
                        yield f"data: {json.dumps(data)}\n\n"

                        # If status is completed or failed, close the stream
                        if data.get("status") in ["completed", "failed"]:
                            break
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON in Redis message: {message['data']}")

        except Exception as e:
            logger.error(f"Error in SSE stream for mission {mission_id}: {e!s}")
            # Do not leak internal exception text to the client.
            yield f"data: {json.dumps({'error': 'stream error'})}\n\n"
        finally:
            # Clean up
            pubsub.unsubscribe(channel)
            pubsub.close()

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"  # Disable nginx buffering
    return response


@router.get("/{mission_id}/jobs/{job_id}/stream")
def stream_job_status(request: HttpRequest, mission_id: UUID, job_id: str):
    """
    SSE stream for real-time job updates.

    Client connects to this endpoint and receives real-time updates
    as the container processes the job.

    Args:
        request: The HTTP request
        mission_id: The UUID of the mission
        job_id: The job ID to track

    Returns:
        StreamingHttpResponse: SSE stream of job status updates
    """
    mission = get_object_or_404(Mission, id=mission_id)

    # Check if user has access
    if not async_to_sync(mission.can_be_accessed_by)(request.user):
        return StreamingHttpResponse(
            'data: {"error": "Unauthorized"}\n\n',
            content_type="text/event-stream",
            status=403
        )

    def event_stream():
        """Generate SSE events from Redis pub/sub."""
        # Connect to Redis
        redis_client = redis.StrictRedis.from_url(settings.CELERY_RESULT_BACKEND)
        pubsub = redis_client.pubsub()
        channel = f"mission:{mission_id}:status"

        # Subscribe to the channel
        pubsub.subscribe(channel)

        # Send initial connection message
        yield f"data: {json.dumps({'status': 'connected', 'job_id': job_id})}\n\n"

        try:
            # Listen for messages
            for message in pubsub.listen():
                if message["type"] == "message":
                    # Parse and forward the message
                    try:
                        data = json.loads(message["data"])

                        # Filter for this specific job
                        job_data = data.get("data", {})
                        if (job_data.get("job_id") == job_id or
                            job_data.get("conversation_id") and
                            any(j.get("job_id") == job_id for j in mission.active_jobs or [])):

                            yield f"data: {json.dumps(data)}\n\n"

                            # End stream on completion/failure
                            if data.get("status") in ["completed", "failed"]:
                                yield "data: [DONE]\n\n"
                                break

                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON in Redis message: {message['data']}")

        except Exception as e:
            logger.error(f"Error in SSE stream for job {job_id}: {e!s}")
            # Generic, JSON-encoded message: never interpolate raw exception text
            # (avoids event-stream/JSON injection and internal-detail disclosure).
            yield f"data: {json.dumps({'error': 'stream error'})}\n\n"
        finally:
            # Clean up
            pubsub.unsubscribe(channel)
            pubsub.close()

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"  # Disable nginx buffering
    return response


