"""Pydantic schemas for notification API."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationSchema(BaseModel):
    """Schema for notification response."""

    id: UUID = Field(..., description="Notification UUID")
    type: str = Field(..., description="Notification type")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    priority: str = Field(..., description="Notification priority")
    mission_id: Optional[UUID] = Field(None, description="Related mission ID")
    conversation_id: Optional[str] = Field(None, description="Related conversation ID")
    data: dict = Field(default_factory=dict, description="Additional data")
    read: bool = Field(..., description="Whether notification is read")
    read_at: Optional[datetime] = Field(None, description="When notification was read")
    created_at: datetime = Field(..., description="When notification was created")

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Schema for list notifications response."""

    notifications: list[NotificationSchema]
    total: int = Field(..., description="Total number of notifications")
    unread_count: int = Field(..., description="Number of unread notifications")


class UnreadCountResponse(BaseModel):
    """Schema for unread count response."""

    count: int = Field(..., description="Number of unread notifications")


class MarkReadResponse(BaseModel):
    """Schema for mark read response."""

    success: bool = Field(..., description="Whether operation was successful")
    message: str = Field(..., description="Response message")
