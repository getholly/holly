"""
Tests to improve code coverage for ModelClientManager implementations.

Specifically targets areas with lower coverage in the existing tests.
"""

from unittest.mock import MagicMock, patch

from llmrepo_lib.enums import LLMModel
from llmrepo_lib.model_client_manager import (
    AnthropicClientManager,
    GeminiClientManager,
    OllamaClientManager,
    OpenAIClientManager,
)


class TestOpenAITokenizer:
    """Tests for OpenAI's tokenizer functionality."""

    def test_get_tokenizer_gpt4(self):
        """Test tokenizer initialization for GPT-4 models."""
        # Create manager with GPT-4 model
        manager = OpenAIClientManager(LLMModel.GPT_4o)

        # Access tokenizer to trigger initialization
        tokenizer = manager._get_tokenizer()

        # Verify
        assert tokenizer is not None
        # Test that the tokenizer works
        tokens = tokenizer.encode("Test")
        assert len(tokens) > 0

    def test_get_tokenizer_other_model(self):
        """Test tokenizer initialization for other models."""

        # Create a mock model for a custom model
        class MockModel:
            value = "custom-model"

        # Create manager with custom model
        manager = OpenAIClientManager(MockModel())

        # Access tokenizer to trigger initialization
        tokenizer = manager._get_tokenizer()

        # Verify
        assert tokenizer is not None
        # Test that the tokenizer works
        tokens = tokenizer.encode("Test")
        assert len(tokens) > 0


class TestGeminiApiKey:
    """Tests for Gemini's API key handling."""

    def test_provided_api_key(self):
        """Test using a provided API key."""
        manager = GeminiClientManager(LLMModel.GEMINI_2_FLASH, api_key="test_key")

        # Call the method
        api_key = manager._get_api_key()

        # Verify
        assert api_key == "test_key"

    @patch("llmrepo_lib.model_client_manager.settings")
    def test_settings_api_key(self, mock_settings):
        """Test using API key from settings."""
        # We need to mock settings as it's an external dependency
        mock_settings.GEMINI_API_KEY = "settings_key"

        # Create manager with no API key
        manager = GeminiClientManager(LLMModel.GEMINI_2_FLASH)

        # Call the method
        api_key = manager._get_api_key()

        # Verify
        assert api_key == "settings_key"

    @patch("llmrepo_lib.model_client_manager.settings")
    @patch("llmrepo_lib.model_client_manager.random.randint")
    def test_settings_api_keys_list(self, mock_randint, mock_settings):
        """Test using API key from settings list."""
        # We need to mock settings as it's an external dependency
        mock_settings.GEMINI_API_KEY = None
        mock_settings.GEMINI_API_KEYS = ["key1", "key2", "key3"]
        mock_randint.return_value = 1  # Pick the second key

        # Create manager with no API key
        manager = GeminiClientManager(LLMModel.GEMINI_2_FLASH)

        # Call the method
        api_key = manager._get_api_key()

        # Verify
        assert api_key == "key2"
        mock_randint.assert_called_once_with(0, 2)

    @patch("llmrepo_lib.model_client_manager.settings")
    @patch("llmrepo_lib.model_client_manager.logger")
    def test_no_api_key_available(self, mock_logger, mock_settings):
        """Test fallback when no API key is available."""
        # We need to mock settings as it's an external dependency
        mock_settings.GEMINI_API_KEY = None
        mock_settings.GEMINI_API_KEYS = []

        # Create manager with no API key
        manager = GeminiClientManager(LLMModel.GEMINI_2_FLASH)

        # Call the method
        api_key = manager._get_api_key()

        # Verify
        assert api_key == ""
        mock_logger.error.assert_called_once_with("No Gemini API key available")


class TestOllamaManager:
    """Tests for Ollama manager."""

    @patch("openai.Client")
    def test_base_url_initialization(self, mock_client):
        """Test Ollama client initialization with base URL."""
        # We need to mock the OpenAI client as it makes HTTP requests
        mock_client.return_value = MagicMock()

        # Create manager and get client to trigger initialization
        manager = OllamaClientManager(LLMModel.LLAMA3_3)
        manager.get_client()

        # Verify the base URL is set correctly
        assert manager.base_url == "http://10.13.1.11:11434/v1"
        mock_client.assert_called_once_with(base_url="http://10.13.1.11:11434/v1", api_key=None)

    @patch("openai.Client")
    def test_client_with_api_key(self, mock_client):
        """Test Ollama client initialization with API key."""
        # We need to mock the OpenAI client as it makes HTTP requests
        mock_client.return_value = MagicMock()

        # Create manager with API key
        manager = OllamaClientManager(LLMModel.LLAMA3_3, api_key="test_key")
        manager.get_client()

        # Verify
        mock_client.assert_called_once_with(base_url="http://10.13.1.11:11434/v1", api_key="test_key")

    def test_get_model(self):
        """Test get_model returns the correct model name."""
        manager = OllamaClientManager(LLMModel.LLAMA3_3)
        model_name = manager.get_model()

        assert model_name == "llama3.3:latest"


class TestManagerGetModel:
    """Tests for get_model method across different managers."""

    def test_openai_get_model(self):
        """Test OpenAI get_model method."""
        manager = OpenAIClientManager(LLMModel.GPT_4o)
        model_name = manager.get_model()
        assert model_name == "gpt-4o"

    def test_anthropic_get_model(self):
        """Test Anthropic get_model method."""
        manager = AnthropicClientManager(LLMModel.CLAUDE_SONNET)
        model_name = manager.get_model()
        assert model_name == "claude-3-7-sonnet"

    def test_gemini_get_model(self):
        """Test Gemini get_model method."""
        manager = GeminiClientManager(LLMModel.GEMINI_2_FLASH)
        model_name = manager.get_model()
        assert model_name == "gemini-2.0-flash"

    @patch("google.genai.Client")
    def test_gemini_get_client(self, mock_client):
        """Test Gemini get_client method."""
        # We need to mock the Google client as it makes HTTP requests
        mock_client.return_value = MagicMock()

        # Create manager with API key and get client
        manager = GeminiClientManager(LLMModel.GEMINI_2_FLASH, api_key="test_key")
        manager._get_api_key = MagicMock(return_value="test_key")  # Mock to avoid settings dependency

        client = manager.get_client()

        # Verify
        assert client is not None
        mock_client.assert_called_once_with(api_key="test_key")
