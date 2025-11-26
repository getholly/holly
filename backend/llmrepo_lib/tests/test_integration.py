"""
Integration tests for ModelClientManager implementations.

Tests the ModelClientManager implementations together.
"""

from unittest.mock import MagicMock

import pytest

from llmrepo_lib.enums import LLMModel
from llmrepo_lib.errors import UnsupportedModelError
from llmrepo_lib.model_client_manager import (
    AnthropicClientManager,
    GeminiClientManager,
    ModelClientManager,
    OllamaClientManager,
    OpenAIClientManager,
)


class TestModelClientManagerIntegration:
    """Integration tests for ModelClientManager implementations."""

    @pytest.fixture
    def sample_text(self):
        """A sample text for testing."""
        return """
        This is a sample text for testing token counting.
        It has multiple lines and some special characters: !@#$%^&*().
        It also includes some code:

        def hello_world():
            print("Hello, world!")
            return 42

        The token count should be consistent across implementations.
        """

    def test_factory_method_with_enum(self):
        """Test the factory method with LLMModel enum."""
        # Test OpenAI client
        manager = ModelClientManager.create(LLMModel.GPT_4o)
        assert isinstance(manager, OpenAIClientManager)
        assert manager.model_enum == LLMModel.GPT_4o
        assert manager.model_name == LLMModel.GPT_4o.value

        # Test Anthropic client
        manager = ModelClientManager.create(LLMModel.CLAUDE_SONNET)
        assert isinstance(manager, AnthropicClientManager)
        assert manager.model_enum == LLMModel.CLAUDE_SONNET
        assert manager.model_name == LLMModel.CLAUDE_SONNET.value

        # Test Gemini client
        manager = ModelClientManager.create(LLMModel.GEMINI_2)
        assert isinstance(manager, GeminiClientManager)
        assert manager.model_enum == LLMModel.GEMINI_2
        assert manager.model_name == LLMModel.GEMINI_2.value

        manager = ModelClientManager.create(LLMModel.GEMINI_2_FLASH)
        assert isinstance(manager, GeminiClientManager)
        assert manager.model_enum == LLMModel.GEMINI_2_FLASH
        assert manager.model_name == LLMModel.GEMINI_2_FLASH.value

        # Test Llama client
        manager = ModelClientManager.create(LLMModel.LLAMA3_3)
        assert isinstance(manager, OllamaClientManager)
        assert manager.model_enum == LLMModel.LLAMA3_3
        assert manager.model_name == LLMModel.LLAMA3_3.value

        manager = ModelClientManager.create(LLMModel.MISTRAL7B)
        assert isinstance(manager, OllamaClientManager)
        assert manager.model_enum == LLMModel.MISTRAL7B
        assert manager.model_name == LLMModel.MISTRAL7B.value

    def test_raise_error_or_unknown_model(self):
        """Test raising an error for an unknown model."""
        some_enum = MagicMock(spec=LLMModel)
        some_enum.value = "unknown-model"

        with pytest.raises(UnsupportedModelError):
            ModelClientManager.create(some_enum)

    def test_api_key_is_passed_correctly(self):
        """Test that API keys are passed correctly to the managers."""
        api_key = "test_api_key"

        openai_manager = ModelClientManager.create(LLMModel.GPT_4o, api_key=api_key)
        assert openai_manager.api_key == api_key

        anthropic_manager = ModelClientManager.create(LLMModel.CLAUDE_SONNET, api_key=api_key)
        assert anthropic_manager.api_key == api_key

        gemini_manager = ModelClientManager.create(LLMModel.GEMINI_2_FLASH, api_key=api_key)
        assert gemini_manager.api_key == api_key

        ollama_manager = ModelClientManager.create(LLMModel.LLAMA3_3, api_key=api_key)
        assert ollama_manager.api_key == api_key
