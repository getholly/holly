import asyncio
import httpx
import json
import pytest
from fastapi.testclient import TestClient

pytest_plugins = ('pytest_asyncio',)

@pytest.mark.asyncio
async def test_sse_stream(monkeypatch):
    """
    Test the SSE streaming functionality with mocks.
    """
    from rest_mcp_client.services.sse_service import sse_stream
    from starlette.responses import Response
    
    # Create a mock for the request
    class MockRequest:
        def __init__(self):
            self.headers = {}
    
    # Create a mock for the generator function
    async def mock_generator():
        yield "Test message 1"
        yield "Test message 2"
        yield "Test message 3"
    
    # Mock the generate_llm_response_stream function
    from rest_mcp_client.services import llm_service
    monkeypatch.setattr(llm_service, "generate_llm_response_stream", lambda *args, **kwargs: mock_generator())
    
    # Call the sse_stream function
    request = MockRequest()
    conversation_id = "test-conversation"
    messages = []
    
    # Get the SSE response
    response = await sse_stream(request, conversation_id, messages)
    
    # Verify the response is an instance of EventSourceResponse
    assert response is not None
    assert hasattr(response, 'send_events')

@pytest.mark.skip(reason="This test requires a running server and is for manual testing")
@pytest.mark.asyncio
async def test_sse_client():
    """
    Connects to an SSE endpoint and processes incoming events.
    This test is meant for manual testing with a running server.
    """
    try:
        url = "http://localhost:8000/api/conversations/start"
        print(f"Connecting to SSE endpoint: {url}")
        response = httpx.post(url, json={})
        conversation_id = response.json()['id']
        sse_url = f"http://localhost:8000/api/conversations/sse/send_message/{conversation_id}"
        httpx.post(sse_url, json={"content": "What's in the /data folder ? /no_think"})
        
        # Use stream=True to handle the response incrementally
        url = f"http://localhost:8000/api/conversations/sse/start_conversation/{conversation_id}"
        async with httpx.AsyncClient(timeout=None) as client: # No timeout for long-lived streams
            async with client.stream("GET", url) as response:
                # Check if the server responded successfully for streaming
                response.raise_for_status()
                print(f"Connected successfully (Status: {response.status_code})")
                print("Waiting for events...")

                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        try:
                            # Remove "data: " prefix and strip whitespace
                            data_content = line[len("data:"):].strip()
                            if data_content:
                                print(f"Received data: {data_content}")
                                # If data is JSON, uncomment the line below:
                                # parsed_data = json.loads(data_content)
                                # print(f"Parsed JSON: {parsed_data}")
                        except json.JSONDecodeError:
                            print(f"Received non-JSON data or malformed JSON: {data_content}")
                        except Exception as e:
                            print(f"Error processing data line: {line} - {e}")
                    elif line.strip(): # Log other non-empty lines (e.g., comments, event types)
                        print(f"Received other line: {line}")

    except httpx.RequestError as e:
        print(f"An error occurred while requesting {e.request.url!r}: {e}")
    except httpx.HTTPStatusError as e:
        print(f"Server returned an error status: {e.response.status_code} - {e.response.text}")
    except KeyboardInterrupt:
        print("\nClient stopped by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        print("Client finished.")

