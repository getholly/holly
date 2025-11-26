from datetime import datetime
from typing import Any
from uuid import UUID

from ninja import Schema
from pydantic import Field

from holly.holly.models.mission import Mission


class MissionBase(Schema):
    """Base schema for mission data"""

    title: str | None = None
    description: str | None = "Mission description"
    branch_name: str | None = None  # base branch to clone from


class MissionRepoAdd(Schema):
    github_id: int = Field(description="GitHub id")
    branch_name: str = Field(description="Branch from which to fork from")


class MissionCreate(MissionBase):
    """Schema for creating a new mission"""

    repositories: list[MissionRepoAdd] | None = None
    knowledge_item_ids: list[int] | None = None
    tool_ids: list[int] | None = None
    requirements: dict[str, Any] | None = None
    llm_id: int | None = None


class MissionUpdate(Schema):
    """Schema for updating an existing mission"""

    title: str | None = None
    description: str | None = None
    branch_name: str | None = None
    state: Mission.State | None = None
    requirements: dict[str, Any] | None = None


class MissionCollaboratorSchema(Schema):
    """Schema for adding or removing collaborators"""

    user_ids: list[int]


class MissionRepositoryAddSchema(Schema):
    """Schema for adding github repositories"""

    repos: list[MissionRepoAdd] = Field(description="List of repos to add")


class MissionRepositoryRemoveSchema(Schema):
    """Schema for removing repositories"""

    repository_ids: list[int] = Field(description="list of RepositoryDetail ids")


class MissionRepositoryResponseSchema(Schema):
    """Schema for repository information in mission responses"""

    id: int


class MissionKnowledgeSchema(Schema):
    """Schema for adding or removing knowledge items"""

    knowledge_item_ids: list[int]


class MissionRepositorySetSchema(Schema):
    """Schema for setting/replacing all repositories in a mission"""

    repos: list[MissionRepoAdd] = Field(description="Complete list of repos to set (replaces all existing)")


class MissionKnowledgeSetSchema(Schema):
    """Schema for setting/replacing all knowledge items in a mission"""

    knowledge_item_ids: list[int] = Field(
        description="Complete list of knowledge item IDs to set (replaces all existing)"
    )


class MissionToolSetSchema(Schema):
    """Schema for setting/replacing all tools in a mission"""

    tool_ids: list[int] = Field(description="Complete list of tool IDs to set (replaces all existing)")


class MissionToolSchema(Schema):
    """Schema for adding or removing tools"""

    tool_ids: list[int]


class MissionUserSchema(Schema):
    """Schema for user information in mission responses"""

    id: int
    email: str


class MissionKnowledgeItemSchema(Schema):
    """Schema for knowledge items in mission responses"""

    id: int
    name: str


class MissionToolItemSchema(Schema):
    """Schema for tools in mission responses"""

    id: int
    name: str


class MissionConversationSchema(Schema):
    """Schema for conversations in mission responses"""

    id: UUID
    conversation_id: str
    title: str | None = None
    created_at: datetime
    updated_at: datetime
    is_summarized: bool
    summary: str | None = None
    remaining_tasks: list[str] | None = None


class LLMSummary(Schema):
    """Summary schema for LLM responses"""

    id: int
    name: str


class MissionDetail(Schema):
    """Detailed schema for mission responses"""

    id: UUID
    title: str
    description: str | None = ""
    state: str
    created_at: datetime
    updated_at: datetime
    branch_name: str
    container_id: str | None = None
    container_ip_address: str | None = None
    owner: MissionUserSchema
    collaborators: list[MissionUserSchema]
    repositories: list[MissionRepositoryResponseSchema]
    knowledge_items: list[MissionKnowledgeItemSchema]
    tools: list[MissionToolItemSchema]
    conversations: list[MissionConversationSchema]
    requirements: dict[str, Any]
    llm: LLMSummary | None = None


class MissionSummary(Schema):
    """Summary schema for mission list responses"""

    id: UUID
    title: str
    state: str
    created_at: datetime
    updated_at: datetime
    owner: str
    branch_name: str
    repository_count: int
    llm: LLMSummary | None = None


class MissionStateUpdate(Schema):
    """Schema for updating mission state"""

    state: str


class MissionConversationCreate(Schema):
    """Schema for creating a new conversation in a mission"""

    title: str | None = None
    initial_message: str | None = None
    llm_id: str | None = None


class MissionConversationUpdate(Schema):
    """Schema for updating a conversation in a mission"""

    title: str | None = None
    is_summarized: bool | None = None
    summary: str | None = None
    remaining_tasks: list[str] | None = None


class ContainerStartResponse(Schema):
    """Response schema for starting a container"""

    mission_id: UUID
    container_id: str | None = None
    success: bool
    message: str


class GenericResponse(Schema):
    """Generic response schema"""

    success: bool
    message: str


class ConversationStartResponse(GenericResponse):
    conversation_id: str | None = Field(default=None)
    job_id: str | None = Field(default=None, description="Job ID for tracking async conversation creation")
    reply: str | None = Field(default=None, description="Deprecated - will be empty for async conversations")
