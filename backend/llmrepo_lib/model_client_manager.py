import random
from abc import ABC, abstractmethod
from typing import Any

import anthropic
import google
import openai
import tiktoken
from django.conf import settings
from loguru import logger

from llmrepo_lib.enums import LLMModel
from llmrepo_lib.errors import TextLengthError, UnsupportedModelError


class ModelClientManager(ABC):
    """
    Abstract base class for managing model clients and API connections.
    Provides consistent interface for different model providers.
    """

    @abstractmethod
    def get_client(self) -> Any:
        """Get the client for this model type."""

    @abstractmethod
    def get_model(self) -> str:
        """Get the model name"""

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens for the given text."""

    @staticmethod
    def create(model: LLMModel, api_key: str | None = None) -> "ModelClientManager":
        """
        Factory method to create appropriate client manager.

        Args:
            model: Model identifier (LLMModel enum)
            api_key: Optional API key

        Returns:
            ModelClientManager implementation

        Raises:
            UnsupportedModelError: If model is not supported
        """
        # Select manager based on model type
        if model in (LLMModel.GPT_4o,):
            return OpenAIClientManager(model, api_key)
        if model in (LLMModel.CLAUDE_SONNET,):
            return AnthropicClientManager(model, api_key)
        if model in (
            LLMModel.GEMINI_2_5,
            LLMModel.GEMINI_2,
            LLMModel.GEMINI_2_FLASH,
            LLMModel.GEMINI_2_FLASH_THINKING,
            LLMModel.GEMINI_2_PRO_EXP,
            LLMModel.GEMINI_1_5,
            LLMModel.GEMINI_1_5_PRO,
        ):
            return GeminiClientManager(model, api_key)
        if model in (LLMModel.LLAMA3_3, LLMModel.MISTRAL7B):
            return OllamaClientManager(model, api_key)

        raise UnsupportedModelError


class OpenAIClientManager(ModelClientManager):
    """Client manager for OpenAI models."""

    def __init__(self, model: LLMModel, api_key: str | None = None):
        """
        Initialize OpenAI client manager.

        Args:
            model: LLMModel enum value
            api_key: Optional API key
        """
        self.model_enum = model
        self.model_name = model.value
        self.api_key = api_key
        self._client = None
        self._tokenizer = None

    def get_client(self) -> Any:
        """
        Get OpenAI client.

        Returns:
            OpenAI client or None if not available
        """
        if self._client is None:
            self._client = openai.Client(api_key=self.api_key) if self.api_key else openai.Client()

        return self._client

    def get_model(self) -> str:
        return self.model_name

    def _get_tokenizer(self) -> Any:
        """
        Get tiktoken tokenizer for the model.

        Returns:
            Tokenizer or None if not available
        """
        if self._tokenizer is None:
            # Map model name to encoding
            if "gpt-4" in self.model_name:
                self._tokenizer = tiktoken.encoding_for_model("gpt-4")
            elif "gpt-3.5" in self.model_name:
                self._tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
            else:
                # Default to cl100k_base for other models
                self._tokenizer = tiktoken.get_encoding("cl100k_base")
        return self._tokenizer

    def count_tokens(self, text: str) -> int:
        """
        Count tokens using tiktoken.

        Args:
            text: Text to tokenize

        Returns:
            Token count or word-based estimate if tiktoken unavailable
        """
        return len(self._get_tokenizer().encode(text))


class AnthropicClientManager(ModelClientManager):
    """Client manager for Anthropic Claude models."""

    def __init__(self, model: LLMModel, api_key: str | None = None):
        """
        Initialize Anthropic client manager.

        Args:
            model: LLMModel enum value
            api_key: Optional API key
        """
        self.model_enum = model
        self.model_name = model.value
        self.api_key = api_key
        self._client = None

    def get_client(self) -> anthropic.Anthropic:
        """
        Get Anthropic client.

        Returns:
            Anthropic client or None if not available
        """
        self._client = anthropic.Anthropic(api_key=self.api_key) if self.api_key else anthropic.Anthropic()

        return self._client

    def get_model(self) -> str:
        return self.model_name

    def count_tokens(self, text: str) -> int:
        """
        Count tokens using Anthropic's counter.

        Args:
            text: Text to tokenize
            system: Optional system name

        Returns:
            Token count or word-based estimate if Anthropic unavailable
        """
        client = self.get_client()
        response = client.messages.count_tokens(model=self.get_model(), messages=[{"role": "user", "content": text}])
        return response.input_tokens


class GeminiClientManager(ModelClientManager):
    """Client manager for Google Gemini models."""

    def __init__(self, model: LLMModel, api_key: str | None = None):
        """
        Initialize Gemini client manager.

        Args:
            model: LLMModel enum value
            api_key: Optional API key
        """
        self.model_enum = model
        self.model_name = model.value
        self.api_key = api_key
        self._client = None
        self._model = None

    def _get_api_key(self) -> str | None:
        """
        Get API key from various sources.

        Returns:
            API key or None if not available
        """
        # Use provided API key if available
        if self.api_key:
            return self.api_key

        # Try to get from settings
        if hasattr(settings, "GEMINI_API_KEY") and settings.GEMINI_API_KEY:
            return settings.GEMINI_API_KEY

        # Try to get from API keys list
        if hasattr(settings, "GEMINI_API_KEYS") and settings.GEMINI_API_KEYS:
            keys = settings.GEMINI_API_KEYS
            if len(keys) > 0:
                # Pick a random key from the list
                return keys[random.randint(0, len(keys) - 1)]  # noqa: S311

        logger.error("No Gemini API key available")
        return ""

    def get_client(self) -> google.genai.Client:
        """
        Get Gemini client.

        Returns:
            Gemini client or None if not available
        """
        if self._client is None:
            api_key = self._get_api_key()
            self._client = google.genai.Client(api_key=api_key)
        return self._client

    def get_model(self) -> str:
        return self.model_name

    def count_tokens(self, text: str) -> int:
        """
        Count tokens using Gemini's counter.

        Args:
            text: Text to tokenize

        Returns:
            Token count or word-based estimate if Gemini unavailable

        Raises:
            TextLengthError: If text is empty
        """
        if len(text) == 0:
            raise TextLengthError
        response = self.get_client().models.count_tokens(model=self.get_model(), contents=text)
        return response.total_tokens


class OllamaClientManager(ModelClientManager):
    """Client manager for Ollama models (Llama, Mistral, etc.)."""

    def __init__(self, model: LLMModel, api_key: str | None = None):
        """
        Initialize Ollama client manager.

        Args:
            model: LLMModel enum value
            api_key: Optional API key (used as base URL)
        """
        self.model_enum = model
        self.model_name = model.value
        # For Ollama, the "api_key" is used as base URL
        self.api_key = api_key
        self.base_url = "http://localhost:11434/v1"  # assuming you are running ollama on your local machine
        self._client = None

    def get_client(self) -> Any:
        """
        Get Ollama client (using OpenAI client with custom base URL).

        Returns:
            OpenAI client configured for Ollama or None if not available
        """
        if self._client is None:
            self._client = openai.Client(base_url=self.base_url, api_key=self.api_key)
        return self._client

    def get_model(self) -> str:
        return self.model_name

    def count_tokens(self, text: str) -> int:
        """
        Estimate tokens for Ollama models.
        Currently uses tiktoken cl100k_base or falls back to word count.

        Args:
            text: Text to tokenize

        Returns:
            Estimated token count
        """

        tokenizer = tiktoken.get_encoding("cl100k_base")
        return len(tokenizer.encode(text))
