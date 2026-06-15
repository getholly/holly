"""
Conversations API endpoints for the Holly app.
"""

import json
from collections.abc import AsyncGenerator
from functools import wraps
from typing import Any
from uuid import uuid4

import httpx
from asgiref.sync import async_to_sync, sync_to_async
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse, StreamingHttpResponse
from loguru import logger
from ninja import Router
from ninja_jwt.authentication import JWTAuth

from holly.holly.api.auth import AsyncJWTAuth
from holly.holly.api.proxy import MCPProxyClient, ModelConfig
from holly.holly.api.schemas import Conversation, ConversationSummary, MessageCreate
from holly.holly.api.schemas import Message as MessageSchema
from holly.holly.eventstream import send_conversation_event
from holly.holly.models import LLM, Mission
from holly.holly.models.conversations import Message as MessageModel
from holly.holly.models.mission_conversation import MissionConversation
from holly.holly.services.mission_service import MissionService

User = get_user_model()


# Helper function to handle async functions with Django Ninja
def sync_endpoint(async_func):
    @wraps(async_func)
    def wrapper(*args, **kwargs):
        return async_to_sync(async_func)(*args, **kwargs)

    return wrapper


router = Router(auth=JWTAuth())
mission_service = MissionService()


# Define error messages as constants (following CONVENTIONS.md TRY003)
CONVERSATION_NOT_FOUND_MSG = "Conversation not found"
MISSION_NOT_LINKED_MSG = "Conversation is not linked to a mission"
CONTAINER_START_FAILED_MSG = "Cannot send message to conversation: container failed to start"
SSE_STREAM_ERROR_MSG = "Error in SSE stream"
MESSAGE_SAVE_ERROR_MSG = "Error saving message to database"
JSON_PARSE_ERROR_MSG = "Error processing SSE message JSON"


def _mc_for_container_dict(mc: ModelConfig) -> dict:
    """Rewrite base_url for container to reach host services (e.g. Ollama).

    If base_url points to localhost/127.0.0.1, containers cannot reach it.
    Use host.docker.internal which works on Windows/Mac Docker to reach host.
    """
    d = mc.model_dump()
    bu = (d.get("base_url") or "").strip()
    if bu.startswith("http://localhost"):
        d["base_url"] = bu.replace("http://localhost", "http://host.docker.internal", 1)
    elif bu.startswith("http://127.0.0.1"):
        d["base_url"] = bu.replace("http://127.0.0.1", "http://host.docker.internal", 1)
    # Ensure a non-empty api_key for providers that our client validates, e.g. Ollama
    model_name = (d.get("model") or "").lower()
    if (not d.get("api_key")) and model_name.startswith("ollama/"):
        d["api_key"] = "ollama-placeholder"
    return d


async def get_model_config(user: User, llm_id: int, mcp_tools: dict | None = None) -> ModelConfig:
    """Return model configuration for the specified LLM and user."""

    from django.db.models import Q

    # Only allow system models or the user's own custom models — never another
    # user's private LLM config.
    allowed = Q(is_system=True)
    if getattr(user, "is_authenticated", False):
        allowed |= Q(user=user)

    try:
        llm_model = await LLM.objects.filter(allowed).aget(id=llm_id)
    except LLM.DoesNotExist:
        # Fall back to the default system model; guard against it being missing
        # or duplicated rather than surfacing a bare 500.
        try:
            llm_model = await LLM.objects.filter(is_system=True).aget(name="Holly")
        except (LLM.DoesNotExist, LLM.MultipleObjectsReturned) as exc:
            logger.error(f"Default 'Holly' system LLM is unavailable: {exc}")
            raise

    api_key = ""
    if user.is_authenticated:
        from holly.holly.models import UserLLMApiKey

        user_key = await UserLLMApiKey.objects.filter(user=user, llm=llm_model).afirst()
        if user_key:
            api_key = user_key.api_key

    return ModelConfig(
        model=llm_model.full_name,
        base_url=llm_model.base_url,
        api_key=api_key,
        temperature=llm_model.temperature,
        top_p=llm_model.top_p,
        top_k=llm_model.top_k,
        min_p=llm_model.min_p,
        mcp_tools=mcp_tools or {},
        system_prompt=llm_model.system_prompt,
    )


@router.get("/", response=list[ConversationSummary])
@sync_endpoint
async def list_conversations(request: HttpRequest) -> list[ConversationSummary]:
    """
    List all conversations for the authenticated user.

    Args:
        request: The HttpRequest

    Returns:
        list[ConversationSummary]: List of conversation summaries
    """
    logger.info(f"Getting conversations for user: {request.user}")

    # Get all mission conversations for the user
    mission_conversations = []
    async for mc in MissionConversation.objects.filter(mission__owner=request.user).select_related("mission"):
        mission_conversations.append(mc)

    # Convert to ConversationSummary objects
    summaries = []
    for mc in mission_conversations:
        # Get the first message content for title if available
        title = f"Conversation {mc.conversation_id[:8]}"
        try:
            first_message = await MessageModel.objects.filter(conversation=mc).afirst()
            if first_message:
                title = first_message.content[:50] + "..." if len(first_message.content) > 50 else first_message.content
        except MessageModel.DoesNotExist:
            pass

        summaries.append(
            ConversationSummary(
                id=mc.conversation_id,
                title=title,
                created_at=mc.created_at,
                updated_at=mc.updated_at,
                mission_id=mc.mission.id if mc.mission else None,
            )
        )

    return summaries


@router.get("/{conversation_id}", response=Conversation)
@sync_endpoint
async def get_conversation(request: HttpRequest, conversation_id: str) -> Conversation:
    """
    Get a conversation by ID for the authenticated user.

    Args:
        request: The HttpRequest
        conversation_id: The ID of the conversation

    Returns:
        Conversation: The conversation details
    """
    logger.info(f"Getting conversation {conversation_id} for user: {request.user}")

    try:
        mission_conversation = await MissionConversation.objects.aget(
            conversation_id=conversation_id, mission__owner=request.user
        )
    except MissionConversation.DoesNotExist as e:
        logger.error(f"Conversation {conversation_id} not found for user {request.user}")
        raise ValueError(CONVERSATION_NOT_FOUND_MSG) from e

    # Get all messages for this conversation
    messages = []
    async for message in MessageModel.objects.filter(conversation=mission_conversation).order_by("created_at"):
        messages.append(
            MessageSchema(
                id=message.id,
                conversation_id=conversation_id,
                role=message.role,
                content=message.content,
                created_at=message.created_at,
            )
        )

    @sync_to_async
    def get_mission_id():
        return mission_conversation.mission.id if mission_conversation.mission else None

    return Conversation(
        id=conversation_id,
        title=f"Conversation {conversation_id[:8]}",
        messages=messages,
        created_at=mission_conversation.created_at,
        updated_at=mission_conversation.updated_at,
        mission_id=await get_mission_id(),
    )


# @router.post("/start", response=Conversation)
# @sync_endpoint
# async def start_conversation(request: HttpRequest, message_create: MessageCreate) -> Conversation:
#     """
#     Start a new conversation.
#
#     Args:
#         request: The HttpRequest
#         message_create: The initial message
#
#     Returns:
#         Conversation: The created conversation
#     """
#     logger.info(f"Starting new conversation for user: {request.user}")
#
#     # Create a new conversation
#     conversation = await ConversationModel.objects.acreate(
#         id=str(uuid4()),
#         title=f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}",
#         owner=request.user,
#     )
#
#     # Create the initial message
#     message = await MessageModel.objects.acreate(
#         id=str(uuid4()),
#         conversation=conversation,
#         role="user",
#         content=message_create.content,
#     )
#
#     return Conversation(
#         id=conversation.id,
#         title=conversation.title,
#         messages=[
#             MessageSchema(
#                 id=message.id,
#                 conversation_id=conversation.id,
#                 role=message.role,
#                 content=message.content,
#                 created_at=message.created_at,
#             )
#         ],
#         updated_at=conversation.updated_at,
#     )


@router.post("/{conversation_id}/messages", response=dict[str, Any])
@sync_endpoint
async def send_message(request: HttpRequest, conversation_id: str, message_create: MessageCreate) -> dict[str, Any]:
    """
    Send a message to an existing conversation.

    Args:
        request: The HttpRequest
        conversation_id: The ID of the conversation
        message_create: The message to send

    Returns:
        dict: Status of the message sending
    """
    logger.info(f"Sending message to conversation {conversation_id} for user: {request.user}")

    try:
        mission_conversation = await MissionConversation.objects.aget(
            conversation_id=conversation_id, mission__owner=request.user
        )
    except MissionConversation.DoesNotExist as e:
        logger.error(f"Conversation {conversation_id} not found for user {request.user}")
        raise ValueError(CONVERSATION_NOT_FOUND_MSG) from e

    @sync_to_async
    def get_mission_id():
        if mission_conversation.mission:
            return mission_conversation.mission.id
        raise ValueError(MISSION_NOT_LINKED_MSG)

    mission_id = await get_mission_id()

    # Do not allow messages until mission/container initialization completes
    mission = await Mission.objects.aget(id=mission_id)
    if mission.state == Mission.State.PROVISIONING:
        error_msg = "Container is still initializing. Please wait and try again."
        logger.warning(error_msg)
        raise RuntimeError(error_msg)
    if mission.state == Mission.State.ERROR:
        error_msg = "Container failed to initialize. Please restart the mission."
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # Ensure container is running
    container_success, container_error, container_url = await mission_service.ensure_mission_container(
        mission_id, request.user
    )
    if not container_success:
        error_msg = f"{CONTAINER_START_FAILED_MSG}: {container_error}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # Verify container REST API is responsive before sending message
    health_url = f"{container_url}/api/health"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(health_url, timeout=settings.REST_MCP_HEALTH_CHECK_TIMEOUT)
            response.raise_for_status()
            logger.info(f"Container REST API health check passed for mission {mission_id}")
    except (httpx.HTTPError, httpx.RequestError) as e:
        error_msg = f"Container REST API is not ready: {e!s}"
        logger.warning(error_msg)
        raise RuntimeError("Container REST API is not ready. Please wait and retry.") from e

    try:
        # Get repository context for the mission
        @sync_to_async
        def get_repo_context():
            repos_info = []
            # Use mission's branch name (e.g., "holly/feature-name"), not the repo's base branch
            mission_branch = mission_conversation.mission.branch_name
            for mission_repo in mission_conversation.mission.repositories.all():
                repo = mission_repo.repository
                repos_info.append({
                    "owner": repo.username,
                    "name": repo.repo,
                    "branch": mission_branch,  # Use mission branch, not repo branch
                    "path": f"/data/{repo.username}/{repo.repo}/{mission_branch}"
                })
            return repos_info

        repos_context = await get_repo_context()

        # Build repository context to send to container
        repo_context_text = ""
        if repos_context:
            repo_context_text = "\n\n---REPOSITORY CONTEXT---\n"
            repo_context_text += "You are working with the following cloned repositories:\n"
            for repo in repos_context:
                repo_context_text += f"- {repo['owner']}/{repo['name']} (branch: {repo['branch']})\n"
                repo_context_text += f"  Location: {repo['path']}\n"
            repo_context_text += "\nWhen creating or modifying files, use the full repository path.\n"
            repo_context_text += "Your current working directory is /data\n"
            repo_context_text += "---END CONTEXT---\n\n"

        # Save the original user message to Django database (without context spam)
        user_message = await MessageModel.objects.acreate(
            id=str(uuid4()), conversation=mission_conversation, role="user", content=message_create.content
        )

        # Enhanced content for container (with repository context)
        enhanced_content = repo_context_text + message_create.content

        # Get the correct model configuration using the LLM ID from the mission
        @sync_to_async
        def get_llm_id():
            return mission_conversation.mission.llm.id

        model_config = await get_model_config(request.user, await get_llm_id())
        adjusted_model_config = ModelConfig(**_mc_for_container_dict(model_config))
        mcp_client = MCPProxyClient(url=container_url, timeout=settings.REST_MCP_REQUEST_TIMEOUT, model_config=adjusted_model_config)

        # Send the message to the external API; if conversation is missing remotely, create and retry once
        endpoint = f"/api/conversations/{conversation_id}/messages"
        # Use enhanced content with repository context
        message_data = message_create.dict()
        message_data['content'] = enhanced_content
        try:
            response = await mcp_client.post(endpoint, data=message_data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Create the conversation remotely then retry
                await mcp_client.post(
                    "/api/conversations/start",
                    data={
                        "id": conversation_id,
                        "initial_message": enhanced_content,
                        "title": f"Conversation {conversation_id[:8]}",
                    },
                )
                response = await mcp_client.post(endpoint, data=message_data)
            else:
                raise

        # Save the assistant response
        # Container returns {"response": message_obj, "conversation": ...}
        response_message = response.get("response", {})
        assistant_message = await MessageModel.objects.acreate(
            id=str(uuid4()),
            conversation=mission_conversation,
            role="assistant",
            content=response_message.get("content", ""),
        )

        return {
            "status": "success",
            "user_message_id": user_message.id,
            "assistant_message_id": assistant_message.id,
        }

    except (httpx.HTTPError, httpx.RequestError) as e:
        error_msg = f"HTTP error sending message: {e!s}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e
    except Exception as e:
        error_msg = f"Error sending message to conversation {conversation_id}: {e!s}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


@router.get("/sse/start_conversation/{conversation_id}", auth=AsyncJWTAuth())
async def start_conversation_sse(request: HttpRequest, conversation_id: str) -> HttpResponse:
    """
    Start an SSE stream for an existing conversation.

    Args:
        request: The HttpRequest
        conversation_id: The ID of the conversation

    Returns:
        HttpResponse: SSE streaming response
    """
    logger.info(f"Starting SSE stream for conversation {conversation_id} for user: {request.user}")

    try:
        mission_conversation = await MissionConversation.objects.aget(
            conversation_id=conversation_id, mission__owner=request.user
        )
    except MissionConversation.DoesNotExist as e:
        logger.error(f"Conversation {conversation_id} not found for user {request.user}")
        raise ValueError(CONVERSATION_NOT_FOUND_MSG) from e

    @sync_to_async
    def get_mission_id():
        if mission_conversation.mission:
            return mission_conversation.mission.id
        raise ValueError(MISSION_NOT_LINKED_MSG)

    mission_id = await get_mission_id()

    # Ensure container is running
    container_success, container_error, container_url = await mission_service.ensure_mission_container(
        mission_id, request.user
    )
    if not container_success:
        error_msg = f"{CONTAINER_START_FAILED_MSG}: {container_error}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    async def sse_event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events for conversation start."""
        try:
            # Get model config
            @sync_to_async
            def get_llm_id():
                return mission_conversation.mission.llm.id

            model_config = await get_model_config(request.user, await get_llm_id())
            adjusted_model_config = ModelConfig(**_mc_for_container_dict(model_config))
            mcp_client = MCPProxyClient(url=container_url, timeout=settings.REST_MCP_REQUEST_TIMEOUT, model_config=adjusted_model_config)

            # Start the SSE stream to the external API
            async with httpx.AsyncClient(verify=mcp_client.verify_ssl, timeout=mcp_client.timeout) as client:
                url = f"{container_url}/api/conversations/sse/start_conversation/{conversation_id}"
                headers = {
                    "Accept": "text/event-stream",
                    "Content-Type": "application/json",
                }

                async with client.stream("GET", url, headers=headers, timeout=None) as response:
                    if response.status_code == 404:
                        # Create the conversation remotely then retry stream once
                        await client.post(
                            f"{container_url}/api/conversations/start",
                            json={
                                "id": conversation_id,
                                "initial_message": "",
                                "title": f"Conversation {conversation_id[:8]}",
                                **adjusted_model_config.model_dump(),
                            },
                            timeout=30,
                        )
                        # Reopen the stream after creation
                        await response.aclose()
                        async with client.stream("GET", url, headers=headers, timeout=None) as response2:
                            response2.raise_for_status()
                            async for line in response2.aiter_lines():
                                if line.strip():
                                    send_conversation_event(conversation_id, "start", {"text": line})
                                    yield f"{line}\n"
                        return
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if line.strip():
                            # Send event to django-eventstream for any listening clients
                            send_conversation_event(conversation_id, "start", {"text": line})

                            # Forward the SSE line to the client
                            yield f"{line}\n"

        except (httpx.HTTPError, httpx.RequestError) as e:
            error_msg = f"HTTP error in SSE stream: {e!s}"
            logger.error(error_msg)
            yield f'data: {{"error": "Stream interrupted: {error_msg}"}}\n\n'
            yield "data: [DONE]\n\n"
        except (json.JSONDecodeError, ValueError) as e:
            error_msg = f"Data processing error in SSE stream: {e!s}"
            logger.error(error_msg)
            yield f'data: {{"error": "Data processing error: {error_msg}"}}\n\n'
            yield "data: [DONE]\n\n"
        except Exception as e:
            error_msg = f"{SSE_STREAM_ERROR_MSG}: {e!s}"
            logger.error(error_msg)
            yield f'data: {{"error": "Stream interrupted: {error_msg}"}}\n\n'
            yield "data: [DONE]\n\n"

    # Return the SSE response with proper content type and headers
    response = StreamingHttpResponse(sse_event_generator(), content_type="text/event-stream", status=200)
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"  # Disable Nginx buffering if using Nginx
    return response


@router.post("/sse/send_message/{conversation_id}", auth=AsyncJWTAuth())
async def send_message_sse(
    request: HttpRequest, conversation_id: str, message_create: MessageCreate
) -> StreamingHttpResponse:
    """
    Send a message to an existing conversation with SSE for streaming responses.

    Args:
        request: The HttpRequest
        conversation_id: The ID of the conversation
        message_create: The message to send

    Returns:
        StreamingHttpResponse: SSE streaming response
    """
    logger.info(f"Sending SSE message to conversation {conversation_id} for user: {request.user}")

    try:
        mission_conversation = await MissionConversation.objects.aget(
            conversation_id=conversation_id, mission__owner=request.user
        )
    except MissionConversation.DoesNotExist as e:
        logger.error(f"Conversation {conversation_id} not found for user {request.user}")
        raise ValueError(CONVERSATION_NOT_FOUND_MSG) from e

    @sync_to_async
    def get_mission_id():
        if mission_conversation.mission:
            return mission_conversation.mission.id
        raise ValueError(MISSION_NOT_LINKED_MSG)

    mission_id = await get_mission_id()

    # Ensure container is running
    container_success, container_error, container_url = await mission_service.ensure_mission_container(
        mission_id, request.user
    )
    if not container_success:
        error_msg = f"{CONTAINER_START_FAILED_MSG}: {container_error}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    try:
        # Save the user message to local database
        await MessageModel.objects.acreate(
            id=str(uuid4()), conversation=mission_conversation, role="user", content=message_create.content
        )

        # Get the correct model configuration using the LLM ID from the mission
        @sync_to_async
        def get_llm_id():
            return mission_conversation.mission.llm.id

        logger.info(f"using llm id: {message_create.id}")
        mission = await Mission.objects.aget(id=mission_id)
        tools = await mission.aget_tools()
        model_config = await get_model_config(request.user, message_create.id or await get_llm_id(), mcp_tools=tools)
        adjusted_model_config = ModelConfig(**_mc_for_container_dict(model_config))
        logger.info(f"using model config: {adjusted_model_config}")
        mcp_client = MCPProxyClient(url=container_url, timeout=settings.REST_MCP_REQUEST_TIMEOUT, model_config=adjusted_model_config)

        async def sse_event_generator() -> AsyncGenerator[str, None]:
            """
            Generator that streams SSE events from the external API to the client,
            while also processing them for database storage and event stream notifications.
            """
            full_content = ""
            saved = False

            async def _persist_assistant_message() -> None:
                """Persist the streamed assistant message exactly once (also used on
                client disconnect so partial output isn't lost)."""
                nonlocal saved
                if saved or not full_content.strip():
                    return
                try:
                    await MessageModel.objects.acreate(
                        id=str(uuid4()),
                        conversation=mission_conversation,
                        role="assistant",
                        content=full_content,
                    )
                    mission_conversation.updated_at = timezone.now()
                    await sync_to_async(mission_conversation.save)()
                    saved = True
                except Exception as e:
                    logger.error(f"{MESSAGE_SAVE_ERROR_MSG}: {e!s}")

            try:
                # Direct streaming to external API without intermediate proxy layer
                async with httpx.AsyncClient(verify=mcp_client.verify_ssl, timeout=mcp_client.timeout) as client:
                    url = f"{mcp_client.base_url}/api/conversations/sse/send_message/{conversation_id}"
                    headers = {
                        "Accept": "text/event-stream",
                        "Content-Type": "application/json",
                    }

                    # Add adjusted model config to request data
                    request_data = message_create.dict()
                    request_data.update(adjusted_model_config.model_dump())

                    async with client.stream("POST", url, headers=headers, json=request_data, timeout=None) as response:
                        if response.status_code == 404:
                            # Create the conversation remotely then retry once
                            await client.post(
                                f"{mcp_client.base_url}/api/conversations/start",
                                json={
                                    "id": conversation_id,
                                    "initial_message": message_create.content,
                                    "title": f"Conversation {conversation_id[:8]}",
                                    **adjusted_model_config.model_dump(),
                                },
                                timeout=30,
                            )
                            await response.aclose()
                            async with client.stream("POST", url, headers=headers, json=request_data, timeout=None) as response2:
                                response2.raise_for_status()
                                async for line in response2.aiter_lines():
                                    if not line.strip():
                                        continue
                                    send_conversation_event(conversation_id, "message", {"text": line})
                                    if line.startswith("data: [DONE]") and full_content:
                                        await _persist_assistant_message()
                                    else:
                                        full_content += line[6:]
                                    yield f"{line}\n"
                            return
                        response.raise_for_status()

                        async for line in response.aiter_lines():
                            if not line.strip():
                                continue

                            # Send event to django-eventstream for any listening clients
                            send_conversation_event(conversation_id, "message", {"text": line})
                            # TODO: move to multiplex

                            # Save completed message to database
                            if line.startswith("data: [DONE]") and full_content:
                                await _persist_assistant_message()
                            else:
                                full_content += line[6:]

                            # Forward the SSE line to the client
                            yield f"{line}\n"

            except (httpx.HTTPError, httpx.RequestError) as e:
                logger.error(f"HTTP error in SSE stream: {e!s}")
                yield f"data: {json.dumps({'error': 'Stream interrupted'})}\n\n"
                yield "data: [DONE]\n\n"
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Data processing error in SSE stream: {e!s}")
                yield f"data: {json.dumps({'error': 'Data processing error'})}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                logger.exception(f"{SSE_STREAM_ERROR_MSG}: {e!s}")
                yield f"data: {json.dumps({'error': 'Stream interrupted'})}\n\n"
                yield "data: [DONE]\n\n"
            finally:
                # On normal completion or client disconnect (GeneratorExit), make
                # sure any streamed-but-unsaved assistant content is persisted.
                await _persist_assistant_message()

        # Return the SSE response with proper content type and headers
        return StreamingHttpResponse(sse_event_generator(), content_type="text/event-stream", status=200)
        # response["Cache-Control"] = "no-cache"
        # response["X-Accel-Buffering"] = "no"  # Disable Nginx buffering if using Nginx

    except (httpx.HTTPError, httpx.RequestError) as e:
        error_msg = f"HTTP error sending SSE message to conversation {conversation_id}: {e!s}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e
    except Exception as e:
        error_msg = f"Error sending SSE message to conversation {conversation_id}: {e!s}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


# @router.post("/clone-repository", response=GitRepositoryResponse)
