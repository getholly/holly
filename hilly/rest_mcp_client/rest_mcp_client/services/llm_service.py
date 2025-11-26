from datetime import datetime
from typing import AsyncGenerator, List

from loguru import logger
from mcp_python_client import MCPClient
from sqlalchemy.orm import Session

from rest_mcp_client.models.conversation import (
    MODEL,
    MCPConfig,
    Message,
    ModelConfig,
    default_mcp_config,
)
from rest_mcp_client.repository.conversation_repository import ConversationRepository
from rest_mcp_client.services.prompts.agent import AGENT
from rest_mcp_client.services.prompts.claude import CLAUDE
from rest_mcp_client.services.prompts.gemini import GEMINI
from rest_mcp_client.services.prompts.general import GENERAL
from rest_mcp_client.services.prompts.slash_cmds import SLASH_CMD


def get_system_prompt(model: str = MODEL):
    llm = model.split("/")[0].lower()
    if llm == "gemini":
        SYSTEM_PROMPT = GEMINI + GENERAL + SLASH_CMD
        return SYSTEM_PROMPT
    elif llm in ("qwen", "openai"):
        SYSTEM_PROMPT = AGENT + GENERAL + SLASH_CMD
        return SYSTEM_PROMPT
    elif llm == "anthropic":
        SYSTEM_PROMPT = CLAUDE + GENERAL + SLASH_CMD
        return SYSTEM_PROMPT


def add_system_message(messages, system_message: str):
    for message in messages:
        if message["role"] == "system":
            logger.info(f"System message: {message['content']}")
            return messages
    logger.info(f"Added {system_message[:80]=}")
    messages.insert(0, {"role": "system", "content": system_message})
    return messages


async def generate_llm_response(
    conversation_id: str,
    messages: List[Message],
    mcp_servers: MCPConfig = default_mcp_config,
    model_config: ModelConfig = ModelConfig(),
) -> Message:
    """
    Process messages and get a response from the LLM.

    Args:
        conversation_id: The ID of the current conversation
        messages: The list of messages in the conversation so far
        mcp_servers: A dictionary of MCP server configurations
        model_config: A ModelConfig object

    Returns:
        Message: The LLM's response as a Message object
    """
    # add in the additional tools from the client
    mcp_servers.merge_servers(model_config.mcp_tools)

    logger.info(f"using llm: {model_config.model}")
    client = MCPClient(
        # Use default config path or set a specific one
        # config_path="path/to/config.json"
        model=model_config.model,
        base_url=model_config.base_url,
        api_key=model_config.api_key,
        debug=model_config.debug,
        mcp_servers=mcp_servers.model_dump(),
        show_thinking=model_config.show_thinking,
        temperature=model_config.temperature,
        top_p=model_config.top_p,
        top_k=model_config.top_k,
        min_p=model_config.min_p,
    )

    await client.connect_to_all_servers()
    tools = client.get_available_tools()
    logger.info(
        f"Connected to {len(client.sessions)} servers with {len(tools)} tools available"
    )
    client_messages = [
        {"role": message.role, "content": message.content} for message in messages
    ]

    client_messages = add_system_message(client_messages, model_config.system_prompt or get_system_prompt(MODEL))

    logger.info(f"client messages: {client_messages}")

    try:
        response = await client.complete(client_messages)
        await client.aclose()
        return Message(
            conversation_id=conversation_id,
            role="assistant",
            content=response,
            created_at=datetime.now(),
        )
    except Exception as ex:
        logger.error(f"error: {ex}")
        return Message(
            conversation_id=conversation_id,
            role="assistant",
            content=str(ex),
            created_at=datetime.now(),
        )


async def generate_llm_response_stream(
    conversation_id: str,
    messages: List[Message],
    db: Session,
    max_tokens: int | None = None,
    mcp_servers: MCPConfig = default_mcp_config,
    model_config: ModelConfig = ModelConfig(),
) -> AsyncGenerator[str, None]:
    """
    Process messages and get a streaming response from the LLM.

    Args:
        conversation_id: The ID of the current conversation
        messages: The list of messages in the conversation so far
        db: Database session
        max_tokens: The maximum number of tokens to generate
        mcp_servers: A dictionary of MCP server configurations
        model_config: A ModelConfig object

    Yields:
        Chunks of the LLM's response as they become available
    """
    if max_tokens is None:
        if "gemini" in model_config.model.lower():
            max_tokens = 900_000
        elif "anthropic" in model_config.model.lower():
            max_tokens = 8192
        elif "qwen" in model_config.model.lower():
            max_tokens = 30_000
        elif "deepseek" in model_config.model.lower():
            max_tokens = 8192
        else:
            max_tokens = 4096

    logger.info(f"using llm: {model_config.model}")
    # add in the additional tools from the client
    mcp_servers.merge_servers(model_config.mcp_tools)

    client = MCPClient(
        model=model_config.model,
        base_url=model_config.base_url,
        api_key=model_config.api_key,
        debug=False,
        mcp_servers=mcp_servers.model_dump(),
        max_tokens=max_tokens,
        show_thinking=True,
        temperature=model_config.temperature,
        top_p=model_config.top_p,
        top_k=model_config.top_k,
        min_p=model_config.min_p,
    )

    try:
        await client.connect_to_all_servers()
        tools = client.get_available_tools()
        logger.info(
            f"Connected to {len(client.sessions)} servers with {len(tools)} tools available"
        )
        client_messages = [
            {"role": message.role, "content": message.content} for message in messages
        ]

        logger.info(f"using {client.model}")
        client_messages = add_system_message(client_messages, model_config.system_prompt or get_system_prompt(client.model))

        logger.info(f"client messages: {client_messages}")

        # Stream response from the LLM
        assistant_message = ""
        async for chunk in client.stream_complete(client_messages):
            if chunk is None or (
                hasattr(chunk, "finish_reason") and chunk.finish_reason
            ):
                if chunk.finish_reason not in ("stop", "stopstop"):
                    logger.warning(
                        f"!!Conversation completed with: {chunk.finish_reason}"
                    )
                    assistant_message += (
                        "\n**conversation completed with:** {chunk.finish_reason}"
                    )
                break  # Stream ended
            if chunk:
                assistant_message += chunk
                yield f"{chunk}"
            else:
                logger.error(f"unknown chunk: {chunk}")
    except Exception as ex:
        logger.exception(f"Streaming error: {ex}")
        yield f"data: Error generating response: {str(ex)}\n\n"
    finally:
        logger.info(f"Finished streaming response: {assistant_message}")
        message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=assistant_message.strip(),
            created_at=datetime.now(),
        )
        ConversationRepository.add_message(db, message)
        # Update the conversation timestamp
        ConversationRepository.update_conversation_timestamp(db, conversation_id)
        await client.aclose()
