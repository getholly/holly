from datetime import datetime
from uuid import UUID

from ninja import Schema


class KnowledgeSchemaBase(Schema):
    """Base schema for Knowledge items"""

    name: str
    summary: str | None = None
    description: str | None = None


class KnowledgeSchema(KnowledgeSchemaBase):
    """Schema for Knowledge responses"""

    id: int


class ToolSchemaBase(Schema):
    """Base schema for Tools"""

    name: str


class ToolSchema(Schema):
    """Base schema for Tools"""

    name: str
    description: str | None = None
    id: int


class LLMSchemaBase(Schema):
    """Base schema for LLM operations."""

    name: str
    full_name: str
    base_url: str | None = None
    system_prompt: str | None = None
    top_p: float | None = None
    top_k: int | None = None
    min_p: float | None = None
    temperature: float | None = None
    max_tokens: int | None = None


class LLMCreate(Schema):
    """Schema for creating a new LLM."""

    name: str
    full_name: str
    base_url: str | None = None
    system_prompt: str | None = None
    top_p: float | None = None
    top_k: int | None = None
    min_p: float | None = None
    temperature: float | None = 0.0
    max_tokens: int | None = 4096


class LLMUpdate(Schema):
    """Schema for updating an existing LLM."""

    name: str | None = None
    full_name: str | None = None
    base_url: str | None = None
    system_prompt: str | None = None
    top_p: float | None = None
    top_k: int | None = None
    min_p: float | None = None
    temperature: float | None = None
    max_tokens: int | None = None


class LLMSchema(Schema):
    """Schema for LLM responses."""

    id: int
    name: str
    full_name: str
    base_url: str | None = None
    system_prompt: str | None = None
    top_p: float | None = None
    top_k: int | None = None
    min_p: float | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    is_system: bool = False
    user_id: int | None = None
    created_at: datetime
    updated_at: datetime


# Conversation Schemas
class MessageCreate(Schema):
    """Schema for creating a message."""

    content: str
    llm_id: int | None = None


class Message(Schema):
    """Schema for message responses."""

    id: str | UUID | None = None
    conversation_id: str
    role: str
    content: str
    created_at: datetime | None = None


class ConversationCreate(Schema):
    """Schema for creating a conversation."""

    initial_message: str | None = None
    title: str | None = None


class ConversationSummary(Schema):
    """Schema for conversation summary responses."""

    id: str
    title: str | None = None
    created_at: datetime
    updated_at: datetime


class Conversation(Schema):
    """Schema for conversation responses."""

    id: str | UUID
    title: str | None = None
    created_at: datetime
    updated_at: datetime
    messages: list[Message] = []


# Git Repository Schemas
class GitRepositoryClone(Schema):
    """Schema for cloning a Git repository."""

    repo_owner: str
    repo_name: str
    auth_token: str
    branch: str | None = None
    create_branch: str | None = None


class GitRepositoryResponse(Schema):
    """Schema for Git repository operation responses."""

    success: bool
    message: str
    path: str | None = None
    branch: str | None = None


class ErrorResponse(Schema):
    """Schema for general API error responses."""

    error: str


class ValidationError(Schema):
    """Schema for validation errors."""

    loc: list[str]
    msg: str
    type: str


class HTTPValidationError(Schema):
    """Schema for HTTP validation errors."""

    detail: list[ValidationError]


# Notification Schemas
class NotificationSchema(Schema):
    """Schema for notification response."""

    id: UUID
    type: str
    title: str
    message: str
    priority: str
    mission_id: UUID | None = None
    conversation_id: str | None = None
    data: dict = {}
    read: bool
    read_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(Schema):
    """Schema for list notifications response."""

    notifications: list[NotificationSchema]
    total: int
    unread_count: int


class UnreadCountResponse(Schema):
    """Schema for unread count response."""

    count: int


class MarkReadResponse(Schema):
    """Schema for mark read response."""

    success: bool
    message: str


# Pull Request Schemas
class PRCreateRequest(Schema):
    """Schema for creating a pull request."""

    owner: str
    repo: str
    head: str  # Source branch (e.g., mission branch)
    base: str  # Target branch (e.g., "main")
    title: str
    body: str | None = None


class PRCreateResponse(Schema):
    """Schema for pull request creation response."""

    success: bool
    message: str
    job_id: str | None = None  # For async PR creation
    pr_number: int | None = None
    pr_url: str | None = None
    pr_state: str | None = None


class PRStatusResponse(Schema):
    """Schema for pull request status check."""

    job_id: str
    status: str  # pending, completed, failed
    pr_number: int | None = None
    pr_url: str | None = None
    error: str | None = None


# Slash Command Schemas
class SlashCommandCreate(Schema):
    """Schema for creating a slash command."""

    name: str
    command_type: str  # 'replacement' or 'function'
    description: str | None = ""
    replacement_text: str | None = ""
    function_path: str | None = ""
    is_active: bool = True


class SlashCommandUpdate(Schema):
    """Schema for updating a slash command."""

    name: str | None = None
    command_type: str | None = None
    description: str | None = None
    replacement_text: str | None = None
    function_path: str | None = None
    is_active: bool | None = None


class SlashCommandSchema(Schema):
    """Schema for slash command responses."""

    id: str
    name: str
    command_type: str
    description: str | None = ""
    replacement_text: str | None = ""
    function_path: str | None = ""
    is_system: bool
    is_active: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime
