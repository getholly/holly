import os
from datetime import datetime
from typing import Any, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

MODEL = os.environ.get("MODEL") or "openai/qwen3:32b"
BASE_URL = os.environ.get("BASE_URL")
API_KEY = os.environ.get("OPENAI_API_KEY") or os.environ.get("API_KEY")
SHELLTOOLS_DIR = os.environ.get("SHELLTOOLS_DIR") or ""

from pathlib import Path
from typing import Dict, Union


class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server."""

    command: str = Field(..., description="The command to run the server")
    args: list[str] = Field(
        default_factory=list, description="Arguments to pass to the command"
    )
    env: dict[str, str] | None = Field(
        default=None, description="Environment variables for the server"
    )


class MCPConfig(BaseModel):
    """Top-level MCP configuration."""

    mcpServers: dict[str, MCPServerConfig | None] = Field(
        ..., description="Dictionary mapping server names to their configurations"
    )

    def merge_servers(
        self, servers: Dict[str, MCPServerConfig], overwrite: bool = False
    ) -> "MCPConfig":
        """
        Merge additional server configurations into the existing configuration.

        Args:
            servers: Dictionary of server configurations to merge
            overwrite: If True, existing servers with the same name will be overwritten.
                      If False, existing servers will be preserved.

        Returns:
            Self for method chaining
        """
        if servers:
            for name, config in servers.items():
                # Skip if server exists and we don't want to overwrite
                if not overwrite and name in self.mcpServers:
                    continue

                # Add or update the server configuration
                self.mcpServers[name] = config

        return self

    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> "MCPConfig":
        """Load configuration from a JSON file."""
        import json

        with open(file_path, "r") as f:
            config_data = json.load(f)

        return cls.model_validate(config_data)

    def to_file(self, file_path: Union[str, Path]) -> None:
        """Save configuration to a JSON file."""
        import json

        with open(file_path, "w") as f:
            json.dump(self.model_dump(), f, indent=4)

    def get_server_config(self, server_name: str) -> Optional[MCPServerConfig]:
        """Get the configuration for a specific server by name."""
        return self.mcpServers.get(server_name)


DEFAULT_MCP_SERVERS = {
    "mcpServers": {
        "shelltools": {
            "command": "uv",
            "args": ["--directory", SHELLTOOLS_DIR, "run", "mcp_server.py"],
        }
    }
}
default_mcp_config = MCPConfig.model_validate(DEFAULT_MCP_SERVERS)


class ModelConfig(BaseModel):
    model: str = Field(default=MODEL)
    base_url: str | None = Field(default=BASE_URL)
    api_key: str = Field(default=API_KEY)
    show_thinking: bool = Field(default=True)
    debug: bool = Field(default=False)
    temperature: float = Field(default=0.0)
    mcp_tools: dict[str, MCPServerConfig] | None = Field(default=None)
    system_prompt: str = Field(default="You are a helpful assistant.")
    top_p: float | None = Field(default=None)
    top_k: int | None = Field(default=None)
    min_p: float | None = Field(default=None)


class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    conversation_id: str
    role: str  # "user" or "assistant"
    content: str
    created_at: datetime = Field(default_factory=datetime.now)


class Conversation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    messages: List[Message] = []


class ConversationCreate(ModelConfig):
    id: Optional[str] = Field(default=None)
    initial_message: Optional[str] = Field(default="")
    title: Optional[str] = Field(default="")


class MessageCreate(ModelConfig):
    content: str


class ConversationSummary(BaseModel):
    id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime


def model_config_from_obj(obj: Any):
    return ModelConfig(
        model=obj.model,
        base_url=obj.base_url,
        api_key=obj.api_key,
        show_thinking=obj.show_thinking,
        debug=obj.debug,
        temperature=obj.temperature,
        system_prompt=obj.system_prompt,
        mcp_tools=obj.mcp_tools,
    )
