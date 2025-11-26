"""Job model for tracking async Git operations."""

from datetime import datetime
import enum
from sqlalchemy import Column, String, JSON, DateTime, Enum as SQLEnum
from rest_mcp_client.database.database import Base


class JobStatus(str, enum.Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(Base):
    """Job model for async operations tracking."""
    
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True)  # UUID
    type = Column(String, nullable=False)  # clone, commit, push, pr, worktree
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    result = Column(JSON, nullable=True)  # Success result data
    error = Column(String, nullable=True)  # Error message if failed
    job_metadata = Column(JSON, default=dict, nullable=False)  # repo info, mission_id, etc.
    
    def to_dict(self):
        """Convert job to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "status": self.status.value if isinstance(self.status, JobStatus) else self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "result": self.result,
            "error": self.error,
            "metadata": self.job_metadata,
        }

