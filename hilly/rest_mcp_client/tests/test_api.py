import sys
import os
import json
import requests
from typing import Dict, Any, List
import httpx

# Add the parent directory to sys.path to be able to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_start_conversation() -> Dict[str, Any]:
    """Test the start_conversation endpoint."""
    url = "http://localhost:8000/api/conversations/start"
    data = {
        "initial_message": "Hello, how are you today?",
        "title": "Test Conversation"
    }

    response = requests.post(url, json=data)
    if response.status_code == 200:
        print("✅ Start conversation test passed!")
        result = response.json()
        print(f"Conversation ID: {result['id']}")
        print(f"Title: {result['title']}")
        print(f"Created at: {result['created_at']}")
        print(f"Updated at: {result['updated_at']}")
        print(f"Messages: {json.dumps(result['messages'], indent=2)}")
        return result
    else:
        print(f"❌ Start conversation test failed with status {response.status_code}")
        print(response.text)
        return {}

def test_send_message(conversation_id: str) -> Dict[str, Any]:
    """Test the send_message endpoint."""
    url = f"http://localhost:8000/api/conversations/{conversation_id}/messages"
    data = {
        "content": "What's the weather like today?"
    }

    response = requests.post(url, json=data)
    if response.status_code == 200:
        print("✅ Send message test passed!")
        result = response.json()
        print(f"Response: {json.dumps(result['response'], indent=2)}")
        print(f"Updated at: {result['conversation']['updated_at']}")
        return result
    else:
        print(f"❌ Send message test failed with status {response.status_code}")
        print(response.text)
        return {}

def test_list_conversations() -> List[Dict[str, Any]]:
    """Test the list_conversations endpoint."""
    url = "http://localhost:8000/api/conversations"

    response = requests.get(url)
    if response.status_code == 200:
        print("✅ List conversations test passed!")
        result = response.json()
        print(f"Conversations: {json.dumps(result, indent=2)}")
        return result
    else:
        print(f"❌ List conversations test failed with status {response.status_code}")
        print(response.text)
        return []

def test_get_conversation(conversation_id: str) -> Dict[str, Any]:
    """Test the get_conversation endpoint."""
    url = f"http://localhost:8000/api/conversations/{conversation_id}"

    response = requests.get(url)
    if response.status_code == 200:
        print("✅ Get conversation test passed!")
        result = response.json()
        print(f"Conversation title: {result['title']}")
        print(f"Created at: {result['created_at']}")
        print(f"Updated at: {result['updated_at']}")
        print(f"Messages count: {len(result['messages'])}")
        return result
    else:
        print(f"❌ Get conversation test failed with status {response.status_code}")
        print(response.text)
        return {}

def test_tool_use():
    url = "http://localhost:8000/api/conversations/start"
    data = {
        "initial_message": "Hello, using execute_linux_shell_command what's in the /data folder?",
        "title": "Test Conversation"
    }

    response = requests.post(url, json=data)
    if response.status_code == 200:
        print("✅ Tool use test passed!")
        result = response.json()
        print(f"Conversation ID: {result['id']}")
        print(f"Title: {result['title']}")
        print(f"Created at: {result['created_at']}")
        print(f"Updated at: {result['updated_at']}")
        print(f"Messages: {json.dumps(result['messages'], indent=2)}")
        return result







if __name__ == "__main__":
    print("Testing the REST MCP Client API...")

    # First, test starting a conversation
    conversation = test_start_conversation()

    if conversation and 'id' in conversation:
        # Then, test sending a message to that conversation
        test_send_message(conversation['id'])

        # Test listing all conversations
        test_list_conversations()

        # Test getting a specific conversation
        test_get_conversation(conversation['id'])
