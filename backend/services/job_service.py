import uuid
from datetime import datetime
from typing import Optional
from .storage_service import StorageService
from ..models.tradeline_models import ProcessingJob, ProcessingStatus
import logging

logger = logging.getLogger(__name__)

class JobService:
    def __init__(self, storage_service: StorageService):
        self.storage_service = storage_service

    async def create_processing_job(self, user_id: Optional[uuid.UUID], filename: str, 
                                   file_size: int) -> str:
        """Create a new processing job"""
        try:
            job_id = str(uuid.uuid4())
            
            job_data = {
                'job_id': job_id,
                'user_id': str(user_id) if user_id else None,
                'status': ProcessingStatus.PENDING.value,
                'filename': filename,
                'file_size': file_size,
                'created_at': datetime.now().isoformat(),
                'completed_at': None,
                'error_message': None,
                'document_ai_result': None,
                'llm_result': None,
                'final_tradelines': None
            }
            
            await self.storage_service.store_job_data(job_id, job_data)
            
            logger.info(f"Created processing job {job_id} for file {filename}")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to create processing job: {e}")
            raise

    async def get_job_status(self, job_id: str) -> Optional[ProcessingJob]:
        """Get current job status"""
        try:
            job_data = await self.storage_service.get_job_data(job_id)
            if not job_data:
                return None
            
            return ProcessingJob(**job_data)
            
        except Exception as e:
            logger.error(f"Failed to get job status for {job_id}: {e}")
            return None

    async def update_job_status(self, job_id: str, status: ProcessingStatus, 
                               error_message: Optional[str] = None) -> None:
        """Update job processing status"""
        try:
            await self.storage_service.update_job_status(job_id, status, error_message)
            logger.info(f"Updated job {job_id} status to {status.value}")
            
        except Exception as e:
            logger.error(f"Failed to update job status for {job_id}: {e}")
            raise
