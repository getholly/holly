"""Job service for managing async operations."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from loguru import logger

from rest_mcp_client.models.job import Job, JobStatus


class JobService:
    """Service for managing async jobs."""
    
    def create_job(self, db: Session, job_type: str, metadata: Dict[str, Any]) -> str:
        """
        Create a new job record.
        
        Args:
            db: Database session
            job_type: Type of job (clone, commit, push, pr, worktree)
            metadata: Job metadata (repo info, mission_id, etc.)
            
        Returns:
            Job ID (UUID string)
        """
        job_id = str(uuid.uuid4())
        
        job = Job(
            id=job_id,
            type=job_type,
            status=JobStatus.PENDING,
            job_metadata=metadata,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        db.add(job)
        db.commit()
        db.refresh(job)
        
        logger.info(f"Created job {job_id} of type {job_type}")
        return job_id
    
    def get_job(self, db: Session, job_id: str) -> Optional[Job]:
        """
        Get job by ID.
        
        Args:
            db: Database session
            job_id: Job ID
            
        Returns:
            Job object or None if not found
        """
        return db.query(Job).filter(Job.id == job_id).first()
    
    def get_job_status(self, db: Session, job_id: str) -> Dict[str, Any]:
        """
        Get job status as dictionary.
        
        Args:
            db: Database session
            job_id: Job ID
            
        Returns:
            Job status dictionary
        """
        job = self.get_job(db, job_id)
        
        if not job:
            return {
                "job_id": job_id,
                "error": "Job not found",
                "status": "not_found"
            }
        
        return job.to_dict()
    
    def update_job(
        self, 
        db: Session, 
        job_id: str, 
        status: JobStatus, 
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> bool:
        """
        Update job status and result.
        
        Args:
            db: Database session
            job_id: Job ID
            status: New job status
            result: Result data (for successful completion)
            error: Error message (for failures)
            
        Returns:
            True if updated, False if job not found
        """
        job = self.get_job(db, job_id)
        
        if not job:
            logger.error(f"Job {job_id} not found for update")
            return False
        
        job.status = status
        job.updated_at = datetime.utcnow()
        
        if result is not None:
            job.result = result
            
        if error is not None:
            job.error = error
        
        db.commit()
        db.refresh(job)
        
        logger.info(f"Updated job {job_id} to status {status.value}")
        return True
    
    def update_job_status(self, db: Session, job_id: str, status: JobStatus) -> bool:
        """
        Update only job status.
        
        Args:
            db: Database session
            job_id: Job ID
            status: New job status
            
        Returns:
            True if updated, False if job not found
        """
        return self.update_job(db, job_id, status)


# Singleton instance
job_service = JobService()

