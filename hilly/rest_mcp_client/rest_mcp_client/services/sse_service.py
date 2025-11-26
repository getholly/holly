import asyncio
import os

from loguru import logger
from typing import AsyncGenerator, List

from fastapi import Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from sse_starlette.sse import EventSourceResponse

from rest_mcp_client.models.conversation import Message, ModelConfig
from rest_mcp_client.services.llm_service import generate_llm_response_stream
from rest_mcp_client.services.webhook_service import webhook_service

DEBUG_SSE = os.environ.get("DEBUG_SSE", False)


async def sse_generator(request: Request, conversation_id: str, messages: List[Message], db: Session,
                        model_config: ModelConfig = ModelConfig()) -> AsyncGenerator[str, None]:
    """
    Generate a stream of SSE events for the LLM response.

    Args:
        request: Request the http one
        conversation_id: The ID of the conversation
        messages: The list of messages in the conversation
        db: The database session
        model_config: ModelConfig settings

    Yields:
        SSE events containing chunks of the assistant's response
    """
    mission_id = os.environ.get("MISSION_ID")
    assistant_message = ""
    error_occurred = False

    try:
        if DEBUG_SSE:
            i = 0
            while True and i < 10:
                i += 1
                if await request.is_disconnected():
                    logger.info("client disconnected")
                    break
                logger.info(f"sending hello{i}")
                yield f'data: {i}:hello\n\n'
                await asyncio.sleep(2)
        else:
            async for chunk in generate_llm_response_stream(conversation_id, messages, db, model_config=model_config):
                if chunk:
                    assistant_message += chunk
                    yield f"data: {chunk}\n\n"  # Send the chunk
                else:
                    yield "data: [DONE]\n\n"
                    break
                if await request.is_disconnected():
                    logger.info('client disconnected')
                    break
    except Exception as e:
        error_occurred = True
        logger.error(f"Error in SSE generator: {str(e)}")
        yield f"data: {{'error': '{str(e)}'}}\n\n"

        # Send error webhook
        if mission_id:
            await webhook_service.send_webhook(
                mission_id=mission_id,
                job_id=f"conversation_{conversation_id}",
                status="failed",
                data={
                    "conversation_id": conversation_id,
                    "event": "conversation.error",
                    "error": str(e)
                }
            )
    finally:
        logger.info('client disconnected/streaming is done')
        yield "data: [DONE]\n\n"

        # Send completion webhook if no error occurred
        if mission_id and not error_occurred:
            await webhook_service.send_webhook(
                mission_id=mission_id,
                job_id=f"conversation_{conversation_id}",
                status="completed",
                data={
                    "conversation_id": conversation_id,
                    "event": "conversation.completed",
                    "response_preview": assistant_message[:200] if assistant_message else ""
                }
            )

        await request.close()


# async def sse_stream(request: Request, conversation_id: str, messages: List[Message]) -> EventSourceResponse:
async def sse_stream(request: Request, conversation_id: str, messages: List[Message], db: Session,
                     model_config: ModelConfig) -> StreamingResponse:
    """
    Create an SSE stream for the LLM response.

    Args:
        request: The FastAPI request
        conversation_id: The ID of the conversation
        messages: The list of messages in the conversation
        db: the database session
        model_config: ModelConfig

    Returns:
        EventSourceResponse: An SSE response that can be returned from a FastAPI endpoint
    """
    # The StreamingResponse takes our async generator and the correct media type
    return StreamingResponse(
        sse_generator(request, conversation_id, messages, db, model_config),
        media_type="text/event-stream"
    )
