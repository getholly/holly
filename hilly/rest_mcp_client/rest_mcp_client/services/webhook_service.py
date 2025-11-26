"""Webhook service for reporting job status to Django."""

import os
from datetime import datetime
from typing import Dict, Any, Optional
import httpx
from loguru import logger


class WebhookService:
    """Service for sending webhooks to Django."""
    
    def __init__(self):
        self.django_webhook_url = os.getenv("DJANGO_WEBHOOK_URL")
        
    async def send_webhook(
        self, 
        mission_id: str, 
        job_id: str, 
        status: str, 
        data: Dict[str, Any],
        webhook_url: Optional[str] = None
    ) -> bool:
        """
        Send webhook to Django.
        
        Args:
            mission_id: Mission ID
            job_id: Job ID
            status: Job status (pending, running, completed, failed)
            data: Job data (result, error, metadata)
            webhook_url: Optional override webhook URL
            
        Returns:
            True if webhook sent successfully, False otherwise
        """
        url = webhook_url or self.django_webhook_url
        
        if not url:
            logger.warning("No webhook URL configured, skipping webhook")
            return False
        
        payload = {
            "mission_id": mission_id,
            "job_id": job_id,
            "status": status,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, 
                    json=payload, 
                    timeout=10.0
                )
                response.raise_for_status()
                logger.info(f"Webhook sent successfully for job {job_id}")
                return True
                
        except httpx.TimeoutException:
            logger.error(f"Webhook timeout for job {job_id} to {url}")
            return False
            
        except httpx.HTTPError as e:
            logger.error(f"Webhook HTTP error for job {job_id}: {e}")
            return False
            
        except Exception as e:
            logger.exception(f"Webhook failed for job {job_id}: {e}")
            return False


# Singleton instance
webhook_service = WebhookService()

