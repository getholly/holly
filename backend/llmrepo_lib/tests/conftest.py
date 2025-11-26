"""
Fixtures for testing ModelClientManager implementations.
"""

from unittest.mock import MagicMock

import pytest

from llmrepo_lib.enums import LLMModel
from llmrepo_lib.model_client_manager import (
    AnthropicClientManager,
    GeminiClientManager,
    OllamaClientManager,
    OpenAIClientManager,
)


@pytest.fixture
def common_test_texts():
    """Common test texts of different types and lengths."""
    return {
        "empty": "",
        "simple": "This is a simple test string.",
        "multiline": "This is a test\nwith multiple\nlines of text.",
        "code": """def hello_world():
    print("Hello, world!")
    return 42""",
        "long": "Long " * 100,  # 500 chars, should be >100 tokens
        "unicode": "こんにちは世界. Здравствуй, мир! 🌍🌎🌏",
        "whitespace": "   \t   \n   ",
        "special_chars": "!@#$%^&*()_+{}[]|\\:;\"'<>,.?/~`",
    }


@pytest.fixture
def openai_manager():
    """OpenAI client manager for testing."""
    return OpenAIClientManager(LLMModel.GPT_4o)


@pytest.fixture
def ollama_manager():
    """Ollama client manager for testing."""
    return OllamaClientManager(LLMModel.LLAMA3_3)


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client that approximates token counting."""
    mock_client = MagicMock()

    def mock_count_tokens(text):
        """Simple approximation of token counting."""
        if not text:
            return 0
        # Approximate tokens as words + punctuation
        words = text.split()
        return len(words) + len([c for c in text if c in ".,;:!?()[]{}\"'"])

    mock_client.count_tokens = mock_count_tokens
    return mock_client


@pytest.fixture
def anthropic_manager(mock_anthropic_client):
    """Anthropic client manager with mocked client."""
    manager = AnthropicClientManager(LLMModel.CLAUDE_SONNET)
    manager.get_client = lambda: mock_anthropic_client
    return manager


@pytest.fixture
def mock_gemini_model():
    """Mock Gemini model that approximates token counting."""
    mock_model = MagicMock()
    mock_result = MagicMock()

    def mock_count_tokens(text):
        """Simple approximation of token counting."""
        if not text:
            mock_result.total_tokens = 0
            return mock_result

        # Approximate tokens as words + punctuation
        words = text.split()
        mock_result.total_tokens = len(words) + len([c for c in text if c in ".,;:!?()[]{}\"'"])
        return mock_result

    mock_model.count_tokens = mock_count_tokens
    return mock_model


@pytest.fixture
def gemini_manager(mock_gemini_model):
    """Gemini client manager with mocked model."""
    manager = GeminiClientManager(LLMModel.GEMINI_2_FLASH)
    manager.get_model = lambda: mock_gemini_model
    return manager
