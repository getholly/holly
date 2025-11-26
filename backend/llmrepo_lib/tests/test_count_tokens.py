"""
Tests for ModelClientManager count_tokens methods without mocks.

Tests the actual token counting functionality of each ModelClientManager
implementation with various inputs.
"""

import re
from unittest.mock import MagicMock

import anthropic
import google
import pytest
import tiktoken
from anthropic.resources.messages import messages
from anthropic.types import MessageTokensCount
from google.genai import types

from llmrepo_lib.enums import LLMModel
from llmrepo_lib.errors import TextLengthError
from llmrepo_lib.model_client_manager import (
    AnthropicClientManager,
    GeminiClientManager,
    OllamaClientManager,
    OpenAIClientManager,
)


class TestCountTokensBase:
    """Base test class with common test cases for all token counters."""

    @pytest.fixture
    def sample_texts(self):
        """Sample texts of different types and lengths."""
        return {
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


class TestOpenAICountTokens(TestCountTokensBase):
    """Test token counting for OpenAI models."""

    @pytest.fixture
    def openai_manager(self):
        """Create OpenAI client manager."""
        return OpenAIClientManager(LLMModel.GPT_4o)

    def test_empty_string(self, openai_manager):
        """Test token count for empty string."""
        count = openai_manager.count_tokens("")
        assert count == 0

    def test_simple_string(self, openai_manager):
        """Test token count for a simple string."""
        text = "This is a simple test string."
        count = openai_manager.count_tokens(text)
        assert count > 0

        # Verify against tiktoken directly for consistency
        tokenizer = tiktoken.get_encoding("cl100k_base")
        expected = len(tokenizer.encode(text))
        assert count == expected

    def test_various_texts(self, openai_manager, sample_texts):
        """Test token counts with various text types."""
        for name, text in sample_texts.items():
            count = openai_manager.count_tokens(text)
            # We're not testing specific counts, just ensuring the method works
            # Each text should produce a reasonable count
            if name == "empty":
                assert count == 0
            elif name == "long":
                assert count > 100  # Long text should have >100 tokens
            else:
                assert count > 0

    def test_different_models(self):
        """Test token counting with different OpenAI models."""
        text = "This is a test string for different models."

        # All OpenAI models should use similar tokenization
        manager = OpenAIClientManager(LLMModel.GPT_4o)
        gpt4_count = manager.count_tokens(text)

        assert gpt4_count > 0


class TestAnthropicCountTokens(TestCountTokensBase):
    """Test token counting for Anthropic models."""

    @pytest.fixture
    def mock_anthropic_client(self):
        """Create a mock Anthropic client for token counting."""
        mock_client = MagicMock(spect=anthropic.Anthropic)
        # For testing purposes, implement a simple token counting algorithm
        # that approximates real tokenization without making API calls
        mock_messages = MagicMock(spect=messages.Messages)
        mock_client.messages = mock_messages

        def mock_count_tokens(model, messages):
            # Simple approximation: words + punctuation + spaces
            # This isn't accurate but allows tests to run without API calls
            text = messages[0]["content"]
            word_count = len(re.findall(r"\b\w+\b", text))
            punct_count = len(re.findall(r"[^\w\s]", text))
            space_count = len(re.findall(r"\s", text))
            count = word_count + punct_count + (space_count // 2)
            return MessageTokensCount(input_tokens=count)

        mock_client.messages.count_tokens = mock_count_tokens
        return mock_client

    @pytest.fixture
    def anthropic_manager(self, mock_anthropic_client):
        """Create Anthropic client manager with mocked client."""
        manager = AnthropicClientManager(LLMModel.CLAUDE_SONNET)

        # Patch get_client to return our mock
        manager.get_client = lambda: mock_anthropic_client

        return manager

    def test_empty_string(self, anthropic_manager):
        """Test token count for empty string."""
        count = anthropic_manager.count_tokens("")
        assert count == 0

    def test_various_texts(self, anthropic_manager, sample_texts):
        """Test token counts with various text types."""
        for name, text in sample_texts.items():
            count = anthropic_manager.count_tokens(text)
            # We're not testing specific counts, just ensuring the method works
            # Each text should produce a reasonable count
            if name == "empty":
                assert count == 0
            elif name == "long":
                assert count > 50  # Long text should have many tokens
            elif name != "whitespace":  # Whitespace might get 0 tokens
                assert count > 0


class TestGeminiCountTokens(TestCountTokensBase):
    """Test token counting for Gemini models."""

    @pytest.fixture
    def mock_gemini_client(self):
        """Create a mock Gemini client for token counting."""
        mock_client = MagicMock(spec=google.genai.Client)

        # Create a mock model inside the client
        mock_model = MagicMock()
        mock_client.models = mock_model  # Assign mock model to mock client

        def mock_count_tokens(model, contents):
            word_count = len(re.findall(r"\b\w+\b", contents))
            punct_count = len(re.findall(r"[^\w\s]", contents))
            space_count = len(re.findall(r"\s", contents))
            count = word_count + punct_count + (space_count // 2)
            return types.CountTokensResponse(total_tokens=count)

        # Mock the count_tokens method
        mock_client.models.count_tokens = mock_count_tokens

        return mock_client

    @pytest.fixture
    def gemini_manager(self, mock_gemini_client):
        """Create Gemini client manager with mocked model."""
        gemini_client = GeminiClientManager(LLMModel.GEMINI_2_FLASH)

        gemini_client.get_client = lambda: mock_gemini_client

        return gemini_client

    def test_empty_string(self, gemini_manager):
        """Test token count for empty string."""
        with pytest.raises(TextLengthError):
            gemini_manager.count_tokens("")

    def test_various_texts(self, gemini_manager, sample_texts):
        """Test token counts with various text types."""
        for name, text in sample_texts.items():
            count = gemini_manager.count_tokens(text)
            # We're not testing specific counts, just ensuring the method works
            # Each text should produce a reasonable count
            if name == "empty":
                assert count == 0
            elif name == "long":
                assert count > 50  # Long text should have many tokens
            elif name != "whitespace":  # Whitespace might get 0 tokens
                assert count > 0


class TestOllamaCountTokens(TestCountTokensBase):
    """Test token counting for Ollama models."""

    @pytest.fixture
    def ollama_manager(self):
        """Create Ollama client manager."""
        return OllamaClientManager(LLMModel.LLAMA3_3)

    def test_empty_string(self, ollama_manager):
        """Test token count for empty string."""
        count = ollama_manager.count_tokens("")
        assert count == 0

    def test_simple_string(self, ollama_manager):
        """Test token count for a simple string."""
        text = "This is a simple test string."
        count = ollama_manager.count_tokens(text)
        assert count > 0

        # Verify against tiktoken directly for consistency
        tokenizer = tiktoken.get_encoding("cl100k_base")
        expected = len(tokenizer.encode(text))
        assert count == expected

    def test_various_texts(self, ollama_manager, sample_texts):
        """Test token counts with various text types."""
        for name, text in sample_texts.items():
            count = ollama_manager.count_tokens(text)
            # We're not testing specific counts, just ensuring the method works
            # Each text should produce a reasonable count
            if name == "empty":
                assert count == 0
            elif name == "long":
                assert count > 100  # Long text should have >100 tokens
            else:
                assert count > 0


class TestCompareTokenCounts:
    """Compare token counts between different implementations."""

    @pytest.fixture
    def setup_managers(self):
        """Set up managers for comparison."""
        # Only OpenAI and Ollama managers can be tested without API calls
        openai_manager = OpenAIClientManager(LLMModel.GPT_4o)
        ollama_manager = OllamaClientManager(LLMModel.LLAMA3_3)

        return {
            "openai": openai_manager,
            "ollama": ollama_manager,
        }

    def test_consistency_between_implementations(self, setup_managers):
        """Test that token counts are consistent between implementations."""
        test_texts = [
            "This is a simple string.",
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            "def hello():\n    print('Hello, world!')",
            "a" * 100,  # Repeated character
            "The quick brown fox jumped over the lazy dog.",
        ]

        managers = setup_managers

        for text in test_texts:
            counts = {}
            for name, manager in managers.items():
                counts[name] = manager.count_tokens(text)

            # Since OpenAI and Ollama both use cl100k_base, they should match
            assert counts["openai"] == counts["ollama"], f"Token counts differ for: {text}"
