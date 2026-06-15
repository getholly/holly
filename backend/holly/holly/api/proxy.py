"""
Proxy utility for REST MCP Client.
"""

import json
from pathlib import Path
from typing import Any

import httpx
from django.conf import settings
from loguru import logger
from pydantic import BaseModel, Field


###########################################################################################
# taken from the rest_mcp_client, TODO: create shared library for this
###########################################################################################
class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server."""

    command: str = Field(..., description="The command to run the server")
    args: list[str] = Field(default_factory=list, description="Arguments to pass to the command")
    env: dict[str, str] | None = Field(default=None, description="Environment variables for the server")


class MCPConfig(BaseModel):
    """Top-level MCP configuration."""

    mcpServers: dict[str, MCPServerConfig] = Field(
        ..., description="Dictionary mapping server names to their configurations"
    )

    def merge_servers(self, servers: dict[str, MCPServerConfig], overwrite: bool = False) -> "MCPConfig":
        """
        Merge additional server configurations into the existing configuration.

        Args:
            servers: Dictionary of server configurations to merge
            overwrite: If True, existing servers with the same name will be overwritten.
                      If False, existing servers will be preserved.

        Returns:
            Self for method chaining
        """
        for name, config in servers.items():
            # Skip if server exists and we don't want to overwrite
            if not overwrite and name in self.mcpServers:
                continue

            # Add or update the server configuration
            self.mcpServers[name] = config

        return self

    @classmethod
    def from_file(cls, file_path: str | Path) -> "MCPConfig":
        """Load configuration from a JSON file."""
        import json

        with open(file_path) as f:
            config_data = json.load(f)

        return cls.model_validate(config_data)

    def to_file(self, file_path: str | Path) -> None:
        """Save configuration to a JSON file."""
        import json

        with open(file_path, "w") as f:
            json.dump(self.model_dump(), f, indent=4)

    def get_server_config(self, server_name: str) -> MCPServerConfig | None:
        """Get the configuration for a specific server by name."""
        return self.mcpServers.get(server_name)


class ModelConfig(BaseModel):
    model: str = Field(default="openai/qwen3:32b")
    base_url: str | None = Field(default="http://10.13.1.11:30000/v1")
    api_key: str = Field(default="sk-test")
    show_thinking: bool = Field(default=True)
    debug: bool = Field(default=False)
    temperature: float | None = Field(default=0.0)
    mcp_tools: dict[str, MCPServerConfig] | None = Field(default=None)
    system_prompt: str = Field(default="You are a helpful assistant.")
    top_p: float | None = Field(default=None)
    top_k: int | None = Field(default=None)
    min_p: float | None = Field(default=None)


###########################################################################################


class MCPProxyClient:
    """
    Client for proxying requests to the REST MCP server.
    """

    def __init__(self, url: str | None = None, timeout: int | None = None, model_config: ModelConfig = ModelConfig()):
        """
        Initialize the MCP Proxy Client.

        Args:
            url: The base URL for the REST MCP server. If not provided, uses settings.REST_MCP_BASE_URL.
            timeout: The timeout for requests in seconds. If not provided, uses settings.REST_MCP_REQUEST_TIMEOUT.
        """
        if settings.REST_MCP_SERVER_LOCAL:
            self.base_url = settings.REST_MCP_BASE_URL
        else:
            self.base_url = url or settings.REST_MCP_BASE_URL
        self.timeout = timeout or settings.REST_MCP_REQUEST_TIMEOUT
        self.verify_ssl = settings.REST_MCP_VERIFY_SSL
        self.model_config = model_config

        # Ensure base_url doesn't end with a slash
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]

        logger.debug(f"Initialized MCP Proxy Client with base URL: {self.base_url}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        stream: bool = False,
    ) -> Any:
        """
        Make a request to the REST MCP server.

        Args:
            method: The HTTP method to use (GET, POST, PUT, DELETE).
            endpoint: The endpoint to call, relative to the base URL.
            data: Optional data to send in the request body.
            params: Optional query parameters.
            headers: Optional headers to include in the request.
            stream: Whether to stream the response.

        Returns:
            The response from the REST MCP server or a streaming response.

        Raises:
            httpx.HTTPError: If the request fails.
        """
        url = f"{self.base_url}{endpoint}"

        default_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # For SSE requests, set the proper headers
        if stream:
            default_headers["Accept"] = "text/event-stream"

        if headers:
            default_headers.update(headers)

        logger.debug(f"Making {method} request to {url}")
        logger.debug(f"Request params: {params}")
        if data:
            logger.debug(f"Request data: {json.dumps(data, default=str)}")

        try:
            async with httpx.AsyncClient(verify=self.verify_ssl, timeout=self.timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(
                        url, params=params, headers=default_headers, timeout=None if stream else self.timeout
                    )
                elif method.upper() == "POST":
                    response = await client.post(
                        url, json=data, params=params, headers=default_headers, timeout=None if stream else self.timeout
                    )
                elif method.upper() == "PUT":
                    response = await client.put(url, json=data, params=params, headers=default_headers)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, params=params, headers=default_headers)
                else:
                    msg = f"Unsupported HTTP method: {method}"
                    raise ValueError(msg)

                response.raise_for_status()

                # For streaming requests, return the response object
                if stream:
                    return response

                # For JSON responses, parse and return the JSON
                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"HTTP error when calling {url}: {e!s}")
            raise
        except Exception as e:
            logger.error(f"Error when calling {url}: {e!s}")
            raise

    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        """Make a GET request to the REST MCP server."""
        # TODO: add model_config to the request
        return await self._make_request("GET", endpoint, params=params)

    def _merge_model_config(self, data: dict[str, Any]) -> dict[str, Any]:
        """Return a new dict combining the caller's data with the model config.

        Builds a copy rather than mutating the caller's dict (which previously
        leaked the api_key back into caller-owned data).
        """
        return {**data, **self.model_config.model_dump()}

    @staticmethod
    def _redacted(data: dict[str, Any]) -> dict[str, Any]:
        """Copy of ``data`` with secret-ish fields masked for logging."""
        redacted = dict(data)
        for key in ("api_key", "apikey", "token", "auth_token", "password"):
            if key in redacted:
                redacted[key] = "***"
        return redacted

    async def post(self, endpoint: str, data: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
        """Make a POST request to the REST MCP server."""
        payload = self._merge_model_config(data)
        logger.info(f"POSTING {endpoint} with: {self._redacted(payload)}")
        return await self._make_request("POST", endpoint, data=payload, params=params)

    async def get_sse(self, endpoint: str, params: dict[str, Any] | None = None) -> httpx.Response:
        """
        Make a GET request with SSE for streaming responses.

        Args:
            endpoint: The endpoint to call, relative to the base URL.
            params: Optional query parameters.

        Returns:
            httpx.Response: The streaming response that can be used with aiter_lines().
        """
        return await self._make_request("GET", endpoint, params=params, stream=True)

    async def post_sse(
        self, endpoint: str, data: dict[str, Any], params: dict[str, Any] | None = None
    ) -> httpx.Response:
        """
        Make a POST request with SSE for streaming responses.

        Args:
            endpoint: The endpoint to call, relative to the base URL.
            data: The data to send in the request body.
            params: Optional query parameters.

        Returns:
            httpx.Response: The streaming response that can be used with aiter_lines().
        """
        payload = self._merge_model_config(data)
        return await self._make_request("POST", endpoint, data=payload, params=params, stream=True)
