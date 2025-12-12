# Remote MCP Server Support

Holly now supports both local (stdio) and remote (HTTP/SSE) MCP servers, following the [MCP specification 2025-03-26](https://modelcontextprotocol.io/specification/2025-03-26).

## Overview

Remote MCP servers allow you to connect to MCP services hosted on external servers via HTTP and Server-Sent Events (SSE). This enables integration with cloud-hosted MCP servers like Linear.app, Atlassian, and custom remote services.

## Features

- ✅ **Auto-detection**: Automatically detects remote vs stdio servers based on configuration
- ✅ **Multiple transports**: Supports SSE, HTTP, with configurable fallback strategies
- ✅ **Authentication**: OAuth 2.0, API keys, and bearer tokens
- ✅ **Per-user credentials**: Each user can have their own authentication tokens
- ✅ **Mixed servers**: Use both local and remote servers in the same mission
- ✅ **mcp-remote bridge**: Uses `mcp-remote` to bridge stdio clients to remote servers

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Django Backend (Tools Model)                                │
│  - Stores tool configurations                                │
│  - Stores per-user authentication (ToolAuth)                 │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Hilly Container (MCP Python Client)                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  MCPServerConfig (Pydantic)                          │   │
│  │  - Auto-configures mcp-remote bridge for remote URLs │   │
│  └──────────────────────────────────────────────────────┘   │
│                        │                                     │
│  ┌─────────────────────┼────────────────────────┐           │
│  │ Stdio Server        │ Remote Server          │           │
│  │ (subprocess)        │ (npx mcp-remote)       │           │
│  └──────────────────────┴────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │  Remote MCP Server            │
         │  (Linear, Atlassian, etc.)    │
         └──────────────────────────────┘
```

## Configuration

### Remote Server Configuration

Remote MCP servers are configured by providing a `url` field instead of `command`:

```json
{
  "mcpServers": {
    "linear": {
      "url": "https://mcp.linear.app/sse",
      "transport": "sse-first",
      "auth": {"type": "oauth"}
    }
  }
}
```

The system automatically:
1. Detects this is a remote server (because of `url` field)
2. Configures `mcp-remote` as a bridge
3. Sets up appropriate transport and authentication

### Stdio Server Configuration (Traditional)

```json
{
  "mcpServers": {
    "shelltools": {
      "command": "uv",
      "args": ["--directory", "/path", "run", "server.py"],
      "env": {"ENV_VAR": "value"}
    }
  }
}
```

### Mixed Configuration

You can use both stdio and remote servers together:

```json
{
  "mcpServers": {
    "shelltools": {
      "command": "uv",
      "args": ["run", "server.py"]
    },
    "linear": {
      "url": "https://mcp.linear.app/sse"
    },
    "atlassian": {
      "url": "https://mcp.atlassian.com/sse",
      "transport": "http-first"
    }
  }
}
```

## Transport Protocols

Remote MCP servers support multiple transport protocols:

| Transport | Description |
|-----------|-------------|
| `sse-first` (default) | Try SSE first, fallback to HTTP on 405 error |
| `http-first` | Try HTTP first, fallback to SSE on 404 error |
| `sse-only` | Use only SSE, fail if unavailable |
| `http-only` | Use only HTTP, fail if unavailable |

Example:

```python
MCPServerConfig(
    url="https://api.example.com/mcp",
    transport="sse-first"  # Default if not specified
)
```

## Authentication

### OAuth 2.0

OAuth is handled automatically by `mcp-remote`. The user will be prompted to authenticate via their browser on first use.

```python
# Tools model configuration
Tools.objects.create(
    name="linear",
    description="Linear.app MCP server",
    config={
        "url": "https://mcp.linear.app/sse",
        "auth": {"type": "oauth"}
    },
    is_remote=True,
    requires_auth=True
)

# Per-user authentication (stored after OAuth flow)
ToolAuth.objects.create(
    user=user,
    tool=linear_tool,
    auth_type=ToolAuth.AuthType.OAUTH,
    auth_data={
        "access_token": "oauth_access_token",
        "refresh_token": "oauth_refresh_token",
        "expires_at": "2025-12-31T23:59:59Z"
    }
)
```

### API Key

For services that use API keys:

```python
MCPServerConfig(
    url="https://api.custom.com/mcp",
    auth={
        "type": "api_key",
        "token": "sk-test-123"
    }
)
```

This automatically adds the header: `X-API-Key: sk-test-123`

### Bearer Token

For services that use bearer authentication:

```python
MCPServerConfig(
    url="https://api.custom.com/mcp",
    auth={
        "type": "bearer",
        "token": "bearer_token_xyz"
    }
)
```

This automatically adds the header: `Authorization: Bearer bearer_token_xyz`

### Custom Headers

You can also specify custom headers:

```python
MCPServerConfig(
    url="https://api.custom.com/mcp",
    headers={
        "X-Custom-Header": "value",
        "X-API-Version": "v2"
    }
)
```

## Adding Remote Tools via Django Admin

1. **Create a Tool**:
   ```python
   from holly.holly.models import Tools

   Tools.objects.create(
       name="linear",
       description="Linear.app remote MCP server for issue tracking",
       config={
           "url": "https://mcp.linear.app/sse",
           "transport": "sse-first",
           "auth": {"type": "oauth"}
       },
       is_remote=True,
       requires_auth=True
   )
   ```

2. **Users Authenticate** (for tools requiring auth):
   - User visits authentication page
   - OAuth flow redirects to service
   - Service redirects back with tokens
   - Tokens stored in `ToolAuth` model

3. **Use in Mission**:
   - Select the tool when creating a mission
   - System automatically merges user's auth tokens
   - mcp-remote handles connection

## Using the populate_tools Command

The Linear MCP server is included in the default tools:

```bash
cd /home/user/holly/backend
uv run python manage.py populate_tools

# To force update existing tools:
uv run python manage.py populate_tools --force
```

This creates:
- **stdio tools**: FileSystem, browser, graphiti, context7
- **remote tools**: linear (with OAuth)

## Example: Linear.app Integration

### 1. Tool Configuration

Linear is pre-configured in `populate_tools.py`:

```python
{
    "name": "linear",
    "description": "Linear.app remote MCP server for issue tracking and project management",
    "config": {
        "url": "https://mcp.linear.app/sse",
        "transport": "sse-first",
        "auth": {"type": "oauth"}
    },
    "is_remote": True,
    "requires_auth": True
}
```

### 2. User Workflow

1. User creates a mission and selects "linear" tool
2. On first use, user is prompted to authenticate
3. OAuth flow completes, tokens stored in database
4. Container receives merged configuration:

```json
{
  "mcpServers": {
    "shelltools": {
      "command": "uv",
      "args": ["run", "mcp_server.py"]
    },
    "linear": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://mcp.linear.app/sse",
        "--transport",
        "sse-first"
      ]
    }
  }
}
```

### 3. Container Execution

The `mcp-python-client` in the container:
1. Spawns subprocess for `shelltools` (stdio)
2. Spawns subprocess for `linear` via `npx mcp-remote` (remote bridge)
3. Both servers appear identical to the LLM client
4. LLM can use tools from both servers seamlessly

## Database Models

### Tools Model

```python
class Tools(models.Model):
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField()
    config = models.JSONField()  # MCP server config
    is_remote = models.BooleanField(default=False)
    requires_auth = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### ToolAuth Model

```python
class ToolAuth(models.Model):
    class AuthType(models.TextChoices):
        OAUTH = "oauth"
        API_KEY = "api_key"
        BEARER = "bearer"

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tool = models.ForeignKey(Tools, on_delete=models.CASCADE)
    auth_type = models.CharField(max_length=20, choices=AuthType.choices)
    auth_data = models.JSONField()  # Tokens, keys, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["user", "tool"]]
```

## Python API Examples

### Creating a Remote Tool

```python
from holly.holly.models import Tools

# Public remote server (no auth)
Tools.objects.create(
    name="public-mcp",
    description="Public MCP server",
    config={"url": "https://api.example.com/mcp"},
    is_remote=True,
    requires_auth=False
)

# Private remote server (OAuth)
linear = Tools.objects.create(
    name="linear",
    description="Linear.app MCP server",
    config={
        "url": "https://mcp.linear.app/sse",
        "auth": {"type": "oauth"}
    },
    is_remote=True,
    requires_auth=True
)
```

### Storing User Authentication

```python
from holly.holly.models import ToolAuth

# After OAuth flow completes
ToolAuth.objects.create(
    user=request.user,
    tool=linear,
    auth_type=ToolAuth.AuthType.OAUTH,
    auth_data={
        "access_token": oauth_response["access_token"],
        "refresh_token": oauth_response["refresh_token"],
        "expires_at": oauth_response["expires_at"]
    }
)
```

### Using in Mission

```python
# Mission automatically merges tool configs with user auth
mission = Mission.objects.create(
    title="Implement feature",
    owner=user,
    llm=llm
)
mission.tools.add(shelltools_tool, linear_tool)

# Container receives merged config with user's auth tokens
```

## Testing

### Unit Tests

```python
# Test remote server configuration
def test_remote_server_config_with_url():
    config = MCPServerConfig(url="https://mcp.linear.app/sse")

    assert config.is_remote() is True
    assert config.command == "npx"
    assert "mcp-remote" in config.args
    assert "https://mcp.linear.app/sse" in config.args

# Test mixed servers
def test_mixed_stdio_and_remote_servers():
    mcp_config = MCPConfig(
        mcpServers={
            "shelltools": MCPServerConfig(
                command="uv",
                args=["run", "server.py"]
            ),
            "linear": MCPServerConfig(
                url="https://mcp.linear.app/sse"
            )
        }
    )

    assert mcp_config.mcpServers["shelltools"].is_remote() is False
    assert mcp_config.mcpServers["linear"].is_remote() is True
```

Run tests:

```bash
# Hilly container tests
cd /home/user/holly/hilly/rest_mcp_client
uv run pytest tests/test_mcp_config.py -v

# Django backend tests
cd /home/user/holly/backend
uv run pytest tests/unit/backend/test_remote_mcp_tools.py -v
```

## Security Considerations

1. **Token Storage**: OAuth tokens and API keys are stored in the database. Consider:
   - Using Django's encryption for `auth_data` field
   - Implementing token rotation
   - Setting appropriate database permissions

2. **SSL/TLS**: All remote connections use HTTPS by default

3. **Validation**: URLs are validated before connection

4. **Per-User Isolation**: Each user's authentication is isolated

## Troubleshooting

### Remote server not connecting

1. Check Node.js is available: `node --version`
2. Check npx is available: `npx --version`
3. Check network connectivity: `curl https://mcp.linear.app/sse`
4. Enable debug mode: `MCPServerConfig(url="...", debug=True)`

### OAuth flow failing

1. Verify OAuth configuration in tool config
2. Check redirect URLs are correct
3. Review `~/.mcp-auth/` directory for stored tokens
4. Check ToolAuth record exists for user

### Mixed servers not working

1. Verify stdio servers have `command` field
2. Verify remote servers have `url` field
3. Check logs for connection errors
4. Ensure both server types are in merged config

## Future Enhancements

- [ ] Token encryption at rest
- [ ] Automatic OAuth token refresh
- [ ] WebSocket transport support
- [ ] Admin UI for managing user tool auth
- [ ] Tool marketplace for discovering remote servers

## References

- [MCP Specification 2025-03-26](https://modelcontextprotocol.io/specification/2025-03-26)
- [mcp-remote GitHub](https://github.com/geelen/mcp-remote)
- [Linear MCP Documentation](https://linear.app/docs/mcp)
- [Atlassian MCP Server](https://community.atlassian.com/forums/Atlassian-Platform-articles/Atlassian-Remote-MCP-Server-beta-now-available-for-desktop/ba-p/3022084)
