import uuid
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from .storage_service import StorageService
from models.tradeline_models import ProcessingJob, ProcessingStatus
import logging

logger = logging.getLogger(__name__)

class JobService:
    def __init__(self, storage_service: StorageService):
        self.storage_service = storage_service
        self.active_jobs: Dict[str, Dict[str, Any]] = {}
        self._job_lock = asyncio.Lock()

    async def create_processing_job(self, user_id: Optional[uuid.UUID], filename: str, 
                                   file_size: int) -> str:
        """Create a new processing job with coordination support"""
        async with self._job_lock:
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
                    'final_tradelines': None,
                    'services_used': [],
                    'processing_phases': {},
                    'coordination_metadata': {}
                }
                
                # Track active job
                self.active_jobs[job_id] = {
                    'status': ProcessingStatus.PENDING.value,
                    'started_at': datetime.now(),
                    'services_coordinated': [],
                    'current_phase': 'initialization'
                }
                
                await self.storage_service.store_job_data(job_id, job_data)
                
                logger.info(f"🎯 Created coordinated processing job {job_id} for file {filename}")
                return job_id
                
            except Exception as e:
                logger.error(f"❌ Failed to create processing job: {e}")
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

    async def update_job_coordination(self, job_id: str, service_name: str, 
                                    phase: str, metadata: Dict[str, Any] = None):
        """Update job coordination information"""
        async with self._job_lock:
            try:
                if job_id in self.active_jobs:
                    job_info = self.active_jobs[job_id]
                    job_info['current_phase'] = phase
                    
                    if service_name not in job_info['services_coordinated']:
                        job_info['services_coordinated'].append(service_name)
                    
                    # Update stored job data
                    job_data = await self.storage_service.get_job_data(job_id)
                    if job_data:
                        if service_name not in job_data.get('services_used', []):
                            job_data.setdefault('services_used', []).append(service_name)
                        
                        job_data.setdefault('processing_phases', {})[phase] = {
                            'service': service_name,
                            'timestamp': datetime.now().isoformat(),
                            'metadata': metadata or {}
                        }
                        
                        await self.storage_service.store_job_data(job_id, job_data)
                        
                        logger.info(f"🔄 Job {job_id} coordination updated: {service_name} -> {phase}")
                
            except Exception as e:
                logger.error(f"❌ Failed to update job coordination: {e}")

    async def complete_job_coordination(self, job_id: str, final_result: Any):
        """Complete job processing with coordination cleanup"""
        async with self._job_lock:
            try:
                if job_id in self.active_jobs:
                    job_info = self.active_jobs[job_id]
                    job_info['status'] = ProcessingStatus.COMPLETED.value
                    
                    # Update final job data
                    job_data = await self.storage_service.get_job_data(job_id)
                    if job_data:
                        job_data['status'] = ProcessingStatus.COMPLETED.value
                        job_data['completed_at'] = datetime.now().isoformat()
                        job_data['final_tradelines'] = final_result
                        
                        await self.storage_service.store_job_data(job_id, job_data)
                    
                    # Remove from active jobs after a delay
                    await asyncio.sleep(5)
                    if job_id in self.active_jobs:
                        del self.active_jobs[job_id]
                    
                    logger.info(f"✅ Job {job_id} coordination completed")
                
            except Exception as e:
                logger.error(f"❌ Failed to complete job coordination: {e}")

    async def get_active_jobs_summary(self) -> Dict[str, Any]:
        """Get summary of active coordinated jobs"""
        async with self._job_lock:
            return {
                'active_count': len(self.active_jobs),
                'jobs': {
                    job_id: {
                        'status': info['status'],
                        'current_phase': info['current_phase'],
                        'services_coordinated': info['services_coordinated'],
                        'duration_seconds': (datetime.now() - info['started_at']).total_seconds()
                    } for job_id, info in self.active_jobs.items()
                }
            }
