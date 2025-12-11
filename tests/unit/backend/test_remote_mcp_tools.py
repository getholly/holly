"""
Unit tests for remote MCP tools and authentication.

Tests cover:
- Remote MCP tool configuration
- Per-user tool authentication
- Tool auth token storage and retrieval
- Mixed stdio and remote tools in missions
"""

import pytest
from django.contrib.auth import get_user_model

from holly.holly.models.tools import Tools, ToolAuth
from tests.factories import UserFactory

User = get_user_model()


@pytest.mark.django_db
class TestRemoteMCPTools:
    """Test Tools model with remote MCP server support."""

    def test_create_stdio_tool(self):
        """Test creating a traditional stdio MCP tool."""
        tool = Tools.objects.create(
            name="shelltools",
            description="Execute shell commands",
            config={
                "command": "uv",
                "args": ["--directory", "/path", "run", "server.py"],
            },
        )

        assert tool.name == "shelltools"
        assert tool.is_remote is False
        assert tool.requires_auth is False
        assert tool.config["command"] == "uv"

    def test_create_remote_tool_without_auth(self):
        """Test creating a remote MCP tool that doesn't require authentication."""
        tool = Tools.objects.create(
            name="public-mcp",
            description="Public MCP server",
            config={"url": "https://api.example.com/mcp"},
            is_remote=True,
            requires_auth=False,
        )

        assert tool.is_remote is True
        assert tool.requires_auth is False
        assert tool.config["url"] == "https://api.example.com/mcp"

    def test_create_remote_tool_with_oauth(self):
        """Test creating a remote MCP tool with OAuth authentication."""
        tool = Tools.objects.create(
            name="linear",
            description="Linear.app MCP server",
            config={
                "url": "https://mcp.linear.app/sse",
                "transport": "sse-first",
                "auth": {"type": "oauth"},
            },
            is_remote=True,
            requires_auth=True,
        )

        assert tool.is_remote is True
        assert tool.requires_auth is True
        assert tool.config["url"] == "https://mcp.linear.app/sse"
        assert tool.config["auth"]["type"] == "oauth"

    def test_create_remote_tool_with_api_key(self):
        """Test creating a remote MCP tool with API key authentication."""
        tool = Tools.objects.create(
            name="custom-api",
            description="Custom API with API key",
            config={
                "url": "https://api.custom.com/mcp",
                "auth": {"type": "api_key"},
            },
            is_remote=True,
            requires_auth=True,
        )

        assert tool.is_remote is True
        assert tool.requires_auth is True
        assert tool.config["auth"]["type"] == "api_key"

    def test_tool_str_representation(self):
        """Test tool __str__ method."""
        tool = Tools.objects.create(
            name="linear",
            description="Linear MCP",
            config={"url": "https://mcp.linear.app/sse"},
            is_remote=True,
        )

        assert str(tool) == "linear"


@pytest.mark.django_db
class TestToolAuth:
    """Test ToolAuth model for per-user authentication tokens."""

    def test_create_oauth_token(self):
        """Test storing OAuth tokens for a user."""
        user = UserFactory()
        tool = Tools.objects.create(
            name="linear",
            description="Linear MCP",
            config={"url": "https://mcp.linear.app/sse"},
            is_remote=True,
            requires_auth=True,
        )

        auth = ToolAuth.objects.create(
            user=user,
            tool=tool,
            auth_type=ToolAuth.AuthType.OAUTH,
            auth_data={
                "access_token": "oauth_access_token_xyz",
                "refresh_token": "oauth_refresh_token_abc",
                "expires_at": "2025-12-31T23:59:59Z",
            },
        )

        assert auth.user == user
        assert auth.tool == tool
        assert auth.auth_type == ToolAuth.AuthType.OAUTH
        assert auth.auth_data["access_token"] == "oauth_access_token_xyz"
        assert auth.is_valid() is True

    def test_create_api_key_token(self):
        """Test storing API key for a user."""
        user = UserFactory()
        tool = Tools.objects.create(
            name="custom-api",
            description="Custom API",
            config={"url": "https://api.custom.com/mcp"},
            is_remote=True,
            requires_auth=True,
        )

        auth = ToolAuth.objects.create(
            user=user,
            tool=tool,
            auth_type=ToolAuth.AuthType.API_KEY,
            auth_data={"token": "sk-test-123456"},
        )

        assert auth.auth_type == ToolAuth.AuthType.API_KEY
        assert auth.auth_data["token"] == "sk-test-123456"

    def test_create_bearer_token(self):
        """Test storing bearer token for a user."""
        user = UserFactory()
        tool = Tools.objects.create(
            name="bearer-api",
            description="Bearer token API",
            config={"url": "https://api.bearer.com/mcp"},
            is_remote=True,
            requires_auth=True,
        )

        auth = ToolAuth.objects.create(
            user=user,
            tool=tool,
            auth_type=ToolAuth.AuthType.BEARER,
            auth_data={"token": "bearer_token_xyz"},
        )

        assert auth.auth_type == ToolAuth.AuthType.BEARER
        assert auth.auth_data["token"] == "bearer_token_xyz"

    def test_unique_user_tool_constraint(self):
        """Test that a user can only have one auth per tool."""
        user = UserFactory()
        tool = Tools.objects.create(
            name="linear",
            description="Linear MCP",
            config={"url": "https://mcp.linear.app/sse"},
            is_remote=True,
            requires_auth=True,
        )

        # Create first auth
        ToolAuth.objects.create(
            user=user,
            tool=tool,
            auth_type=ToolAuth.AuthType.OAUTH,
            auth_data={"access_token": "token1"},
        )

        # Try to create duplicate - should raise error
        with pytest.raises(Exception):  # Django IntegrityError
            ToolAuth.objects.create(
                user=user,
                tool=tool,
                auth_type=ToolAuth.AuthType.OAUTH,
                auth_data={"access_token": "token2"},
            )

    def test_different_users_same_tool(self):
        """Test that different users can have auth for the same tool."""
        user1 = UserFactory()
        user2 = UserFactory()
        tool = Tools.objects.create(
            name="linear",
            description="Linear MCP",
            config={"url": "https://mcp.linear.app/sse"},
            is_remote=True,
            requires_auth=True,
        )

        auth1 = ToolAuth.objects.create(
            user=user1,
            tool=tool,
            auth_type=ToolAuth.AuthType.OAUTH,
            auth_data={"access_token": "user1_token"},
        )

        auth2 = ToolAuth.objects.create(
            user=user2,
            tool=tool,
            auth_type=ToolAuth.AuthType.OAUTH,
            auth_data={"access_token": "user2_token"},
        )

        assert auth1.user != auth2.user
        assert auth1.tool == auth2.tool
        assert auth1.auth_data["access_token"] != auth2.auth_data["access_token"]

    def test_get_auth_for_user_and_tool(self):
        """Test retrieving auth token for a specific user and tool."""
        user = UserFactory()
        tool = Tools.objects.create(
            name="linear",
            description="Linear MCP",
            config={"url": "https://mcp.linear.app/sse"},
            is_remote=True,
            requires_auth=True,
        )

        ToolAuth.objects.create(
            user=user,
            tool=tool,
            auth_type=ToolAuth.AuthType.OAUTH,
            auth_data={"access_token": "my_token"},
        )

        # Retrieve the auth
        auth = ToolAuth.objects.get(user=user, tool=tool)

        assert auth.auth_data["access_token"] == "my_token"

    def test_update_auth_token(self):
        """Test updating auth token (e.g., OAuth refresh)."""
        user = UserFactory()
        tool = Tools.objects.create(
            name="linear",
            description="Linear MCP",
            config={"url": "https://mcp.linear.app/sse"},
            is_remote=True,
            requires_auth=True,
        )

        auth = ToolAuth.objects.create(
            user=user,
            tool=tool,
            auth_type=ToolAuth.AuthType.OAUTH,
            auth_data={"access_token": "old_token"},
        )

        # Update token
        auth.auth_data = {"access_token": "new_token"}
        auth.save()

        # Verify update
        auth.refresh_from_db()
        assert auth.auth_data["access_token"] == "new_token"

    def test_delete_auth_token(self):
        """Test deleting auth token (e.g., user disconnects tool)."""
        user = UserFactory()
        tool = Tools.objects.create(
            name="linear",
            description="Linear MCP",
            config={"url": "https://mcp.linear.app/sse"},
            is_remote=True,
            requires_auth=True,
        )

        auth = ToolAuth.objects.create(
            user=user,
            tool=tool,
            auth_type=ToolAuth.AuthType.OAUTH,
            auth_data={"access_token": "token"},
        )

        auth_id = auth.id
        auth.delete()

        # Verify deletion
        assert not ToolAuth.objects.filter(id=auth_id).exists()

    def test_tool_auth_str_representation(self):
        """Test ToolAuth __str__ method."""
        user = UserFactory(username="testuser")
        tool = Tools.objects.create(
            name="linear",
            description="Linear MCP",
            config={"url": "https://mcp.linear.app/sse"},
            is_remote=True,
            requires_auth=True,
        )

        auth = ToolAuth.objects.create(
            user=user,
            tool=tool,
            auth_type=ToolAuth.AuthType.OAUTH,
            auth_data={"access_token": "token"},
        )

        assert str(auth) == "testuser - linear (oauth)"

    def test_get_auth_config_for_mcp(self):
        """Test getting auth configuration in MCP format."""
        user = UserFactory()
        tool = Tools.objects.create(
            name="linear",
            description="Linear MCP",
            config={
                "url": "https://mcp.linear.app/sse",
                "auth": {"type": "oauth"},
            },
            is_remote=True,
            requires_auth=True,
        )

        auth = ToolAuth.objects.create(
            user=user,
            tool=tool,
            auth_type=ToolAuth.AuthType.OAUTH,
            auth_data={
                "access_token": "oauth_token",
                "refresh_token": "refresh_token",
            },
        )

        # Get auth config in MCP format
        mcp_auth = auth.get_mcp_auth_config()

        assert mcp_auth["type"] == "oauth"
        assert "access_token" in mcp_auth or "token" in mcp_auth
