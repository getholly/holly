"""
Unit tests for MCP configuration models supporting remote MCP servers.

Tests cover:
- Remote MCP server configuration with URL
- Auto-detection of remote vs stdio servers
- Transport protocol configuration
- Authentication configuration
- Mixed remote and stdio server configurations
"""

import pytest
from pydantic import ValidationError

from rest_mcp_client.models.conversation import MCPConfig, MCPServerConfig


class TestMCPServerConfig:
    """Test MCPServerConfig model for both stdio and remote servers."""

    def test_stdio_server_config(self):
        """Test traditional stdio MCP server configuration."""
        config = MCPServerConfig(
            command="uv",
            args=["--directory", "/path/to/server", "run", "server.py"],
            env={"ENV_VAR": "value"},
        )

        assert config.command == "uv"
        assert len(config.args) == 4
        assert config.env == {"ENV_VAR": "value"}
        assert not hasattr(config, "url") or config.url is None
        assert config.is_remote() is False

    def test_remote_server_config_with_url(self):
        """Test remote MCP server configuration with URL."""
        config = MCPServerConfig(
            url="https://mcp.linear.app/sse",
        )

        assert config.url == "https://mcp.linear.app/sse"
        assert config.is_remote() is True
        # Remote servers should use mcp-remote bridge
        assert config.command == "npx"
        assert "-y" in config.args
        assert "mcp-remote" in config.args

    def test_remote_server_config_with_transport(self):
        """Test remote MCP server with specific transport protocol."""
        config = MCPServerConfig(
            url="https://mcp.linear.app/sse", transport="sse-first"
        )

        assert config.url == "https://mcp.linear.app/sse"
        assert config.transport == "sse-first"
        assert config.is_remote() is True
        # Should include transport in args
        assert "--transport" in config.args
        assert "sse-first" in config.args

    def test_remote_server_with_sse_only_transport(self):
        """Test remote MCP server with SSE-only transport."""
        config = MCPServerConfig(url="https://example.com/mcp", transport="sse-only")

        assert config.transport == "sse-only"
        assert "--transport" in config.args
        assert "sse-only" in config.args

    def test_remote_server_with_http_first_transport(self):
        """Test remote MCP server with HTTP-first transport."""
        config = MCPServerConfig(url="https://example.com/mcp", transport="http-first")

        assert config.transport == "http-first"
        assert "--transport" in config.args
        assert "http-first" in config.args

    def test_remote_server_with_api_key_auth(self):
        """Test remote MCP server with static API key authentication."""
        config = MCPServerConfig(
            url="https://api.example.com/mcp",
            auth={"type": "api_key", "token": "sk-test-123"},
        )

        assert config.url == "https://api.example.com/mcp"
        assert config.auth["type"] == "api_key"
        assert config.auth["token"] == "sk-test-123"
        assert config.is_remote() is True
        # Should include header in args
        assert "--header" in config.args

    def test_remote_server_with_bearer_token_auth(self):
        """Test remote MCP server with bearer token authentication."""
        config = MCPServerConfig(
            url="https://api.example.com/mcp",
            auth={"type": "bearer", "token": "bearer-token-xyz"},
        )

        assert config.auth["type"] == "bearer"
        assert config.auth["token"] == "bearer-token-xyz"
        # Should include Authorization header
        assert "--header" in config.args

    def test_remote_server_with_oauth(self):
        """Test remote MCP server with OAuth configuration."""
        config = MCPServerConfig(
            url="https://mcp.linear.app/sse",
            auth={"type": "oauth", "client_id": "client-123", "scopes": ["read", "write"]},
        )

        assert config.auth["type"] == "oauth"
        assert config.auth["client_id"] == "client-123"
        assert config.auth["scopes"] == ["read", "write"]
        assert config.is_remote() is True

    def test_remote_server_default_transport_is_sse_first(self):
        """Test that remote servers default to SSE-first transport."""
        config = MCPServerConfig(url="https://example.com/mcp")

        # Default transport should be sse-first
        assert config.transport == "sse-first"

    def test_invalid_transport_raises_error(self):
        """Test that invalid transport values raise validation error."""
        with pytest.raises(ValidationError):
            MCPServerConfig(url="https://example.com/mcp", transport="invalid-transport")

    def test_remote_server_requires_url(self):
        """Test that remote server detection requires URL."""
        # Without URL, it's a stdio server and needs command
        with pytest.raises(ValidationError):
            MCPServerConfig()

    def test_stdio_server_requires_command(self):
        """Test that stdio servers require command field."""
        with pytest.raises(ValidationError):
            MCPServerConfig(args=["some", "args"])

    def test_remote_server_with_custom_headers(self):
        """Test remote MCP server with custom headers."""
        config = MCPServerConfig(
            url="https://example.com/mcp",
            headers={"X-Custom-Header": "value", "X-Api-Version": "v2"},
        )

        assert config.headers["X-Custom-Header"] == "value"
        assert config.headers["X-Api-Version"] == "v2"
        # Should include headers in args
        assert "--header" in config.args

    def test_remote_server_debug_mode(self):
        """Test remote MCP server with debug mode enabled."""
        config = MCPServerConfig(url="https://example.com/mcp", debug=True)

        assert config.debug is True
        # Should include --debug in args
        assert "--debug" in config.args

    def test_linear_example_config(self):
        """Test the Linear.app example configuration from the spec."""
        config = MCPServerConfig(url="https://mcp.linear.app/sse")

        assert config.url == "https://mcp.linear.app/sse"
        assert config.is_remote() is True
        assert config.command == "npx"
        assert config.args == ["-y", "mcp-remote", "https://mcp.linear.app/sse", "--transport", "sse-first"]


class TestMCPConfig:
    """Test MCPConfig model for managing multiple MCP servers."""

    def test_mixed_stdio_and_remote_servers(self):
        """Test configuration with both stdio and remote servers."""
        config = MCPConfig(
            mcpServers={
                "shelltools": MCPServerConfig(
                    command="uv",
                    args=["--directory", "/path", "run", "server.py"],
                ),
                "linear": MCPServerConfig(url="https://mcp.linear.app/sse"),
            }
        )

        assert len(config.mcpServers) == 2
        assert config.mcpServers["shelltools"].is_remote() is False
        assert config.mcpServers["linear"].is_remote() is True

    def test_merge_remote_servers(self):
        """Test merging remote server configurations."""
        base_config = MCPConfig(
            mcpServers={
                "shelltools": MCPServerConfig(command="uv", args=["run", "server.py"])
            }
        )

        new_servers = {
            "linear": MCPServerConfig(url="https://mcp.linear.app/sse"),
            "atlassian": MCPServerConfig(url="https://mcp.atlassian.com/sse"),
        }

        base_config.merge_servers(new_servers)

        assert len(base_config.mcpServers) == 3
        assert "shelltools" in base_config.mcpServers
        assert "linear" in base_config.mcpServers
        assert "atlassian" in base_config.mcpServers

    def test_remote_server_overwrite_protection(self):
        """Test that existing servers are not overwritten by default."""
        config = MCPConfig(
            mcpServers={
                "linear": MCPServerConfig(url="https://old-url.com/mcp"),
            }
        )

        new_servers = {
            "linear": MCPServerConfig(url="https://new-url.com/mcp"),
        }

        config.merge_servers(new_servers, overwrite=False)

        # Original should be preserved
        assert config.mcpServers["linear"].url == "https://old-url.com/mcp"

    def test_remote_server_overwrite_allowed(self):
        """Test that servers can be overwritten when explicitly allowed."""
        config = MCPConfig(
            mcpServers={
                "linear": MCPServerConfig(url="https://old-url.com/mcp"),
            }
        )

        new_servers = {
            "linear": MCPServerConfig(url="https://new-url.com/mcp"),
        }

        config.merge_servers(new_servers, overwrite=True)

        # Should be updated
        assert config.mcpServers["linear"].url == "https://new-url.com/mcp"

    def test_all_remote_servers(self):
        """Test configuration with only remote servers."""
        config = MCPConfig(
            mcpServers={
                "linear": MCPServerConfig(url="https://mcp.linear.app/sse"),
                "atlassian": MCPServerConfig(
                    url="https://mcp.atlassian.com/sse", transport="http-first"
                ),
                "custom": MCPServerConfig(
                    url="https://api.custom.com/mcp",
                    auth={"type": "api_key", "token": "sk-123"},
                ),
            }
        )

        assert len(config.mcpServers) == 3
        # All should be remote
        for server in config.mcpServers.values():
            assert server.is_remote() is True

    def test_empty_mcpservers_allowed(self):
        """Test that empty server configuration is valid."""
        config = MCPConfig(mcpServers={})

        assert len(config.mcpServers) == 0

    def test_model_dump_includes_remote_fields(self):
        """Test that model_dump() includes remote-specific fields."""
        config = MCPConfig(
            mcpServers={
                "linear": MCPServerConfig(
                    url="https://mcp.linear.app/sse",
                    transport="sse-only",
                    auth={"type": "oauth"},
                )
            }
        )

        dumped = config.model_dump()

        assert "linear" in dumped["mcpServers"]
        linear_config = dumped["mcpServers"]["linear"]
        assert linear_config["url"] == "https://mcp.linear.app/sse"
        assert linear_config["transport"] == "sse-only"
        assert linear_config["auth"]["type"] == "oauth"
