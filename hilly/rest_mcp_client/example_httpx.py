#!/usr/bin/env python3
"""
Example script demonstrating how to make SSE requests with httpx and stream
the response to stdout in real-time.
"""

import asyncio
import json
import sys
from typing import AsyncGenerator, Dict, Optional

import httpx
from loguru import logger


async def sse_stream(conversation_id: str, headers: Optional[Dict[str, str]] = None) -> AsyncGenerator[Dict, None]:
    """
    Creates an async generator that yields parsed SSE events from the specified URL.

    Args:
        url: The URL endpoint that supports Server-Sent Events
        headers: Optional dictionary of HTTP headers to include in the request

    Yields:
        Parsed SSE events as dictionaries
    """
    if headers is None:
        headers = {}

    # Ensure we have the correct headers for SSE
    headers.update({
        "Accept": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive"
    })

    base_url = "http://localhost:8090"
    body = {
        "model": "ollama/qwen3:4b",
        "base_url": "http://localhost:11434/v1/",
        "api_key": "sk-test-example",
        "show_thinking": True,
        "debug": False,
        "temperature": 0.7,
        "mcp_tools": {},
        "system_prompt": "You are a helpful assistant.",
        "top_p": 0.7,
        "top_k": 20,
        "min_p": 0,
        "content": "hello"
    }
    start_url= f"{base_url}/api/conversations/sse/send_message/{conversation_id}"
    async with httpx.AsyncClient() as client:
        logger.info(f"sending request to: {start_url}")
        async with client.stream("POST", start_url, headers=headers, timeout=None, json=body) as response:
            response.raise_for_status()

            # Variables to store SSE components
            event_type = ""
            data_buffer = []
            event_id = ""

            async for line in response.aiter_lines():
                line = line.rstrip()

                # Empty line signals the end of an event
                if not line:
                    logger.info(f"line: {line}")
                    if data_buffer:
                        # Join the data buffer with newlines
                        data = "\n".join(data_buffer)

                        # Create the event object
                        event = {
                            "type": event_type if event_type else "message",
                            "data": data,
                        }

                        if event_id:
                            event["id"] = event_id

                        # Reset the state
                        event_type = ""
                        data_buffer = []
                        event_id = ""

                        yield event
                    continue

                # Parse SSE field
                if ":" in line:
                    field, value = line.split(":", 1)
                    value = value.lstrip()  # Remove leading space if present

                    if field == "event":
                        event_type = value
                    elif field == "data":
                        data_buffer.append(value)
                    elif field == "id" and not value.startswith("\u0000"):
                        event_id = value
                    elif field == "retry":
                        # You could handle retry timing here if needed
                        pass


async def main(conversation_id: str) -> None:
    """
    Main function that connects to an SSE endpoint and streams the output to stdout.

    Args:
        url: URL of the SSE endpoint
    """
    try:
        print("Streaming events (Press Ctrl+C to stop):", file=sys.stderr)
        print("-" * 50, file=sys.stderr)

        async for event in sse_stream(conversation_id):
            # Try to parse JSON data if possible
            try:
                event_data = json.loads(event["data"])
                formatted_data = json.dumps(event_data, indent=2)
            except (json.JSONDecodeError, TypeError):
                formatted_data = event["data"]

            # Print the event to stdout
            print(f"Event Type: {event['type']}", file=sys.stdout)
            if "id" in event:
                print(f"Event ID: {event['id']}", file=sys.stdout)
            print(f"Data:\n{formatted_data}", file=sys.stdout)
            print("-" * 50, file=sys.stdout)
            sys.stdout.flush()  # Ensure output is immediately visible

    except httpx.RequestError as e:
        print(f"Error connecting to {url}: {e}", file=sys.stderr)
    except KeyboardInterrupt:
        print("\nStream closed by user", file=sys.stderr)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Stream Server-Sent Events from a URL to stdout")
    parser.add_argument("conversation_id", help="conversation_id")
    parser.add_argument("--headers", help="JSON-formatted HTTP headers", default="{}")

    args = parser.parse_args()

    try:
        headers_dict = json.loads(args.headers)
        asyncio.run(main(args.conversation_id))
    except json.JSONDecodeError:
        print("Error: Headers must be valid JSON", file=sys.stderr)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)


