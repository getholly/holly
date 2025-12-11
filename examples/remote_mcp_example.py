"""
Example: Using Remote MCP Servers with Holly

This example demonstrates how to:
1. Create remote MCP tools (Linear.app)
2. Create stdio MCP tools (shelltools)
3. Use both in a mixed configuration
4. Store per-user authentication
"""

from django.contrib.auth import get_user_model
from holly.holly.models import LLM, Mission, Tools, ToolAuth

User = get_user_model()


def create_remote_tool_example():
    """Create a remote MCP tool configuration for Linear.app"""

    linear_tool = Tools.objects.create(
        name="linear",
        description="Linear.app remote MCP server for issue tracking and project management",
        config={
            "url": "https://mcp.linear.app/sse",
            "transport": "sse-first",
            "auth": {"type": "oauth"},
        },
        is_remote=True,
        requires_auth=True,
    )

    print(f"✅ Created remote tool: {linear_tool.name}")
    print(f"   URL: {linear_tool.config['url']}")
    print(f"   Requires auth: {linear_tool.requires_auth}")

    return linear_tool


def create_stdio_tool_example():
    """Create a traditional stdio MCP tool"""

    shell_tool = Tools.objects.create(
        name="shelltools",
        description="Execute shell commands in the container",
        config={
            "command": "uv",
            "args": ["--directory", "/app/aiagents", "run", "mcp_server.py"],
        },
        is_remote=False,
        requires_auth=False,
    )

    print(f"✅ Created stdio tool: {shell_tool.name}")
    print(f"   Command: {shell_tool.config['command']}")
    print(f"   Is remote: {shell_tool.is_remote}")

    return shell_tool


def store_user_oauth_token(user, tool):
    """
    Store OAuth tokens for a user after OAuth flow completes.

    In a real application, this would be called after the OAuth
    callback with actual tokens from the OAuth provider.
    """

    auth = ToolAuth.objects.create(
        user=user,
        tool=tool,
        auth_type=ToolAuth.AuthType.OAUTH,
        auth_data={
            "access_token": "oauth_access_token_example",
            "refresh_token": "oauth_refresh_token_example",
            "expires_at": "2025-12-31T23:59:59Z",
        },
    )

    print(f"✅ Stored OAuth token for user: {user.username}")
    print(f"   Tool: {tool.name}")
    print(f"   Auth type: {auth.auth_type}")
    print(f"   Valid: {auth.is_valid()}")

    return auth


def create_mission_with_mixed_tools(user, llm, tools):
    """Create a mission using both stdio and remote MCP tools"""

    mission = Mission.objects.create(
        title="Implement GitHub Issue Sync",
        description="Sync GitHub issues with Linear using both shelltools and Linear MCP",
        owner=user,
        llm=llm,
        branch_name="claude/github-linear-sync",
    )

    # Add all tools to the mission
    mission.tools.add(*tools)

    print(f"✅ Created mission: {mission.title}")
    print(f"   Tools: {[t.name for t in mission.tools.all()]}")
    print(f"   Mixed remote + stdio: {any(t.is_remote for t in mission.tools.all())}")

    return mission


def demonstrate_mcp_config_generation(mission):
    """
    Demonstrate how the MCP configuration is generated for the container.

    This shows what the container receives after merging tool configs
    with user authentication.
    """

    from holly.holly.api.proxy import MCPServerConfig, MCPConfig

    print("\n📋 Generated MCP Configuration for Container:")
    print("=" * 60)

    # This is what the mission service does when starting a container
    mcp_servers = {}

    for tool in mission.tools.all():
        config_data = tool.config.copy()

        # If tool requires auth, merge user's auth tokens
        if tool.requires_auth:
            try:
                auth = ToolAuth.objects.get(user=mission.owner, tool=tool)
                config_data["auth"] = auth.get_mcp_auth_config()
                print(f"\n🔐 Added auth for {tool.name} (user: {mission.owner.username})")
            except ToolAuth.DoesNotExist:
                print(f"\n⚠️  Warning: {tool.name} requires auth but user has no tokens")
                continue

        # Create MCPServerConfig (this auto-configures mcp-remote for remote servers)
        server_config = MCPServerConfig(**config_data)

        print(f"\n📦 {tool.name}:")
        print(f"   Type: {'Remote (HTTP/SSE)' if server_config.is_remote() else 'Stdio (subprocess)'}")
        print(f"   Command: {server_config.command}")
        print(f"   Args: {' '.join(server_config.args)}")

        mcp_servers[tool.name] = server_config

    # Create the full MCP config
    mcp_config = MCPConfig(mcpServers=mcp_servers)

    print("\n✅ Final MCP Config JSON:")
    print("=" * 60)
    import json
    print(json.dumps(mcp_config.model_dump(), indent=2))

    return mcp_config


def main():
    """Run the complete example"""

    print("\n" + "=" * 60)
    print("Remote MCP Server Example")
    print("=" * 60 + "\n")

    # Get or create a user
    user, _ = User.objects.get_or_create(
        username="demo_user",
        defaults={"email": "demo@example.com"}
    )

    # Get or create an LLM
    llm, _ = LLM.objects.get_or_create(
        name="Claude Sonnet",
        defaults={
            "full_name": "anthropic/claude-3-5-sonnet",
            "base_url": "https://api.anthropic.com/v1",
        }
    )

    # Step 1: Create tools
    print("\n1️⃣  Creating MCP Tools...")
    print("-" * 60)

    linear_tool = create_remote_tool_example()
    shell_tool = create_stdio_tool_example()

    # Step 2: Store user authentication for remote tool
    print("\n2️⃣  Storing User Authentication...")
    print("-" * 60)

    store_user_oauth_token(user, linear_tool)

    # Step 3: Create mission with both tools
    print("\n3️⃣  Creating Mission with Mixed Tools...")
    print("-" * 60)

    mission = create_mission_with_mixed_tools(
        user=user,
        llm=llm,
        tools=[shell_tool, linear_tool]
    )

    # Step 4: Show how MCP config is generated
    print("\n4️⃣  Generating MCP Configuration...")
    print("-" * 60)

    mcp_config = demonstrate_mcp_config_generation(mission)

    print("\n" + "=" * 60)
    print("✅ Example Complete!")
    print("=" * 60)

    print("\nKey Takeaways:")
    print("- Remote servers use 'url' field and auto-configure mcp-remote bridge")
    print("- Stdio servers use 'command' field and spawn subprocesses")
    print("- Both can be mixed in the same mission seamlessly")
    print("- Per-user auth tokens are merged into configuration")
    print("- The container receives a unified MCP config with all servers")


if __name__ == "__main__":
    # This would be run in a Django shell or management command
    print("Run this in Django shell:")
    print("  cd /home/user/holly/backend")
    print("  uv run python manage.py shell < examples/remote_mcp_example.py")
