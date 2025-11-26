"""Pydantic schemas for pull request operations."""

from pydantic import BaseModel
from typing import Optional


class PRRequest(BaseModel):
    """Request schema for creating a pull request."""
    head: str
    base: str
    title: str
    body: Optional[str] = ""
    auth_token: Optional[str] = None


class AutoPRRequest(BaseModel):
    """
    Simplified request schema for auto PR creation.
    Uses mission context from environment variables.
    All fields are optional - container auto-populates from MISSION_REPOS, MISSION_BRANCH, etc.
    """
    title: Optional[str] = None
    body: Optional[str] = None

