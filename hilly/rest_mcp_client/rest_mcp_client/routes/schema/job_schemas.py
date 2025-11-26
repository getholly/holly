"""Pydantic schemas for job responses."""

from pydantic import BaseModel
from typing import Optional, Dict, Any


class JobResponse(BaseModel):
    """Response for job creation."""
    job_id: str
    status: str
    message: Optional[str] = None


class JobStatusResponse(BaseModel):
    """Response for job status query."""
    id: str
    type: str
    status: str
    created_at: str
    updated_at: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any]

