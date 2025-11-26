from fastapi import APIRouter, Depends, HTTPException, Request
from loguru import logger
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import os

from rest_mcp_client.database.database import get_db
from rest_mcp_client.models.conversation import Conversation, ConversationCreate, MessageCreate, Message, \
    ConversationSummary, model_config_from_obj
from rest_mcp_client.repository.conversation_repository import ConversationRepository
from rest_mcp_client.services.llm_service import generate_llm_response, ModelConfig
from rest_mcp_client.services.sse_service import sse_stream
from rest_mcp_client.services.webhook_service import webhook_service
from rest_mcp_client.services.git_service import GitService

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("/", response_model=List[ConversationSummary])
async def list_conversations(db: Session = Depends(get_db)) -> List[ConversationSummary]:
    """
    Get a list of all conversations with their metadata.

    Returns:
        List[ConversationSummary]: A list of conversation summaries including id, title, created_at and updated_at
    """
    return ConversationRepository.get_all_conversations(db)


@router.get("/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str, db: Session = Depends(get_db)) -> Conversation:
    """
    Get a complete conversation by its ID.

    Args:
        conversation_id: The ID of the conversation to retrieve

    Returns:
        Conversation: The conversation object with all messages
    """
    conversation = ConversationRepository.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.post("/start", response_model=Conversation)
async def start_conversation(
    conversation_create: ConversationCreate = ConversationCreate(),
    db: Session = Depends(get_db)
) -> Conversation:
    """
    Start a new conversation.

    Args:
        conversation_create: Optional parameters including initial_message and title and model_config details
        db: Database session

    If an initial message is provided, it will be added to the conversation as a user message.

    Returns:
        Conversation: The newly created conversation
    """
    conversation = ConversationRepository.create_conversation(db, conversation_create)
    model_config = model_config_from_obj(conversation_create)
    # If there's an initial message, generate an assistant response
    if conversation_create.initial_message:
        # Fetch the conversation to get the initial message
        updated_conversation = ConversationRepository.get_conversation(db, conversation.id)
        if updated_conversation:
            # Generate LLM response
            assistant_message = await generate_llm_response(
                conversation_id=conversation.id,
                messages=updated_conversation.messages,
                model_config=model_config,
            )
            # Add the assistant message to the conversation
            ConversationRepository.add_message(db, assistant_message)
            # Get the updated conversation with all messages
            conversation = ConversationRepository.get_conversation(db, conversation.id)

    return conversation


@router.post("/{conversation_id}/messages", response_model=Dict[str, Any])
async def send_message(
    conversation_id: str,
    message_create: MessageCreate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Send a message to an existing conversation.

    The message will be added to the conversation and a response from the LLM will be generated.
    The conversation's updated_at timestamp will be updated.

    Args:
        conversation_id: The ID of the conversation
        message_create: The message to send
        db: Database session

    Returns:
        Dict[str, Any]: A dictionary containing the assistant's response and the updated conversation
    """
    mission_id = os.getenv("MISSION_ID")

    # Check if conversation exists
    conversation = ConversationRepository.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Add user message to the conversation
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=message_create.content
    )
    ConversationRepository.add_message(db, user_message)

    # Get the updated conversation with the new user message
    conversation = ConversationRepository.get_conversation(db, conversation_id)
    model_config = model_config_from_obj(message_create)

    # Send "started" webhook
    if mission_id:
        await webhook_service.send_webhook(
            mission_id=mission_id,
            job_id=f"conversation_{conversation_id}",
            status="started",
            data={
                "conversation_id": conversation_id,
                "event": "conversation.started",
                "message": "Processing message with LLM..."
            }
        )

    try:
        # Generate LLM response
        assistant_message = await generate_llm_response(
            conversation_id=conversation_id,
            messages=conversation.messages,
            model_config=model_config,
        )

        # Add the assistant message to the conversation
        ConversationRepository.add_message(db, assistant_message)

        # Update the conversation timestamp
        ConversationRepository.update_conversation_timestamp(db, conversation_id)

        # Get the final conversation with all messages
        updated_conversation = ConversationRepository.get_conversation(db, conversation_id)

        # Send "completed" webhook
        if mission_id:
            await webhook_service.send_webhook(
                mission_id=mission_id,
                job_id=f"conversation_{conversation_id}",
                status="completed",
                data={
                    "conversation_id": conversation_id,
                    "event": "conversation.completed",
                    "response_preview": assistant_message.content[:200] if assistant_message.content else ""
                }
            )

            # Auto-commit and push changes to remote
            try:
                # Get environment variables for git context
                repos_str = os.getenv("MISSION_REPOS", "")
                branch = os.getenv("MISSION_BRANCH", "")
                base_dir = os.getenv("BASE_DIR", "/data")

                if repos_str and branch:
                    # Parse first repo from MISSION_REPOS (format: "owner/repo:branch,...")
                    first_repo = repos_str.split(",")[0].split(":")[0]  # Get "owner/repo"

                    logger.info(f"Auto-pushing changes for repo {first_repo} on branch {branch}")

                    # Initialize git service
                    git_service = GitService(base_dir=base_dir)

                    # Commit all changes
                    commit_message = f"AI Assistant changes - conversation {conversation_id}"
                    commit_result = git_service.commit_changes(
                        repo_name=first_repo,
                        branch=branch,
                        commit_message=commit_message,
                        files=None  # None = commit all changes
                    )

                    if commit_result.get("success"):
                        logger.info(f"Committed changes: {commit_result.get('message')}")

                        # Push to remote
                        push_result = git_service.push_changes(
                            repo_name=first_repo,
                            branch=branch,
                            force=False
                        )

                        if push_result.get("success"):
                            logger.info(f"Pushed changes to remote: {push_result.get('message')}")

                            # Send webhook about successful git operations
                            await webhook_service.send_webhook(
                                mission_id=mission_id,
                                job_id=f"auto_push_{conversation_id}",
                                status="completed",
                                data={
                                    "event": "git.auto_push",
                                    "conversation_id": conversation_id,
                                    "repo": first_repo,
                                    "branch": branch,
                                    "commit_message": commit_message,
                                    "push_success": True
                                }
                            )
                        else:
                            logger.warning(f"Push failed: {push_result.get('message')}")
                            # Send webhook about push failure
                            await webhook_service.send_webhook(
                                mission_id=mission_id,
                                job_id=f"auto_push_{conversation_id}",
                                status="failed",
                                data={
                                    "event": "git.auto_push",
                                    "conversation_id": conversation_id,
                                    "error": push_result.get("message", "Push failed")
                                }
                            )
                    else:
                        # Nothing to commit or commit failed
                        logger.info(f"No changes to commit: {commit_result.get('message')}")
                else:
                    logger.info("Auto-push skipped: MISSION_REPOS or MISSION_BRANCH not set")

            except Exception as git_error:
                # Log error but don't fail the conversation
                logger.error(f"Auto-push failed for conversation {conversation_id}: {git_error}")
                # Send webhook about git error
                if mission_id:
                    try:
                        await webhook_service.send_webhook(
                            mission_id=mission_id,
                            job_id=f"auto_push_{conversation_id}",
                            status="failed",
                            data={
                                "event": "git.auto_push",
                                "conversation_id": conversation_id,
                                "error": str(git_error)
                            }
                        )
                    except Exception:
                        pass  # Silently fail webhook if it errors

        return {
            "response": assistant_message,
            "conversation": updated_conversation
        }
    except Exception as e:
        logger.error(f"Error processing message: {e}")

        # Send "error" webhook
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

        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


# New SSE endpoints


@router.post("/sse/send_message/{conversation_id}")
async def send_message_sse(
    request: Request,
    conversation_id: str,
    message_create: MessageCreate,
    db: Session = Depends(get_db)
):
    """
    Send a message to an existing conversation with SSE for streaming responses.

    Args:
        request: The FastAPI request
        conversation_id: The ID of the conversation
        message_create: The message to send
        db: Database session

    Returns:
        EventSourceResponse: An SSE stream of the assistant's response
    """
    mission_id = os.getenv("MISSION_ID")

    # Check if conversation exists
    conversation = ConversationRepository.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Add user message to the conversation
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=message_create.content
    )
    ConversationRepository.add_message(db, user_message)

    # Update the conversation timestamp
    ConversationRepository.update_conversation_timestamp(db, conversation_id)
    model_config = model_config_from_obj(message_create)
    logger.info(f"using {model_config}")

    # Send "started" webhook
    if mission_id:
        await webhook_service.send_webhook(
            mission_id=mission_id,
            job_id=f"conversation_{conversation_id}",
            status="started",
            data={
                "conversation_id": conversation_id,
                "event": "conversation.started",
                "message": "Processing message with LLM (streaming)..."
            }
        )

    # get updated conversation list
    conversation = ConversationRepository.get_conversation(db, conversation_id)
    # Start the SSE stream
    return await sse_stream(request, conversation_id, conversation.messages, db, model_config)

