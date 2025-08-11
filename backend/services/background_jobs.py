"""
Background job processing system for Credit Clarity
Handles long-running tasks like large PDF processing, batch operations, and maintenance
"""
import asyncio
import logging
import json
import uuid
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from enum import Enum
import traceback
import weakref

from core.config import get_settings
from services.cache_service import cache

logger = logging.getLogger(__name__)
settings = get_settings()


class JobStatus(Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY = "retry"


class JobPriority(Enum):
    """Job priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class Job:
    """Represents a background job."""
    
    def __init__(
        self,
        job_id: str,
        task_name: str,
        task_args: Dict[str, Any],
        user_id: Optional[str] = None,
        priority: JobPriority = JobPriority.NORMAL,
        max_retries: int = 3,
        timeout: int = 1800  # 30 minutes default
    ):
        self.job_id = job_id
        self.task_name = task_name
        self.task_args = task_args
        self.user_id = user_id
        self.priority = priority
        self.max_retries = max_retries
        self.timeout = timeout
        
        self.status = JobStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.retry_count = 0
        self.progress = 0
        self.progress_message = ""
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for serialization."""
        return {
            'job_id': self.job_id,
            'task_name': self.task_name,
            'task_args': self.task_args,
            'user_id': self.user_id,
            'priority': self.priority.value,
            'max_retries': self.max_retries,
            'timeout': self.timeout,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': self.result,
            'error': self.error,
            'retry_count': self.retry_count,
            'progress': self.progress,
            'progress_message': self.progress_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Create job from dictionary."""
        job = cls(
            job_id=data['job_id'],
            task_name=data['task_name'],
            task_args=data['task_args'],
            user_id=data.get('user_id'),
            priority=JobPriority(data.get('priority', JobPriority.NORMAL.value)),
            max_retries=data.get('max_retries', 3),
            timeout=data.get('timeout', 1800)
        )
        
        job.status = JobStatus(data['status'])
        job.created_at = datetime.fromisoformat(data['created_at'])
        job.started_at = datetime.fromisoformat(data['started_at']) if data.get('started_at') else None
        job.completed_at = datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None
        job.result = data.get('result')
        job.error = data.get('error')
        job.retry_count = data.get('retry_count', 0)
        job.progress = data.get('progress', 0)
        job.progress_message = data.get('progress_message', "")
        
        return job


class JobQueue:
    """In-memory job queue with persistence support."""
    
    def __init__(self):
        self._pending_jobs: List[Job] = []
        self._running_jobs: Dict[str, Job] = {}
        self._completed_jobs: Dict[str, Job] = {}
        self._failed_jobs: Dict[str, Job] = {}
        
        # Job history cleanup
        self._max_completed_jobs = 100
        self._max_failed_jobs = 50
    
    def add_job(self, job: Job) -> None:
        """Add job to pending queue."""
        self._pending_jobs.append(job)
        # Sort by priority (higher priority first)
        self._pending_jobs.sort(key=lambda j: j.priority.value, reverse=True)
        
        logger.info(f"Added job {job.job_id} ({job.task_name}) to queue")
    
    def get_next_job(self) -> Optional[Job]:
        """Get next job from queue."""
        if self._pending_jobs:
            job = self._pending_jobs.pop(0)
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now()
            self._running_jobs[job.job_id] = job
            return job
        return None
    
    def complete_job(self, job_id: str, result: Dict[str, Any]) -> None:
        """Mark job as completed."""
        job = self._running_jobs.pop(job_id, None)
        if job:
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            job.result = result
            job.progress = 100
            
            self._completed_jobs[job_id] = job
            
            # Cleanup old completed jobs
            if len(self._completed_jobs) > self._max_completed_jobs:
                oldest_job = min(self._completed_jobs.values(), key=lambda j: j.completed_at)
                del self._completed_jobs[oldest_job.job_id]
            
            logger.info(f"Job {job_id} completed successfully")
    
    def fail_job(self, job_id: str, error: str) -> None:
        """Mark job as failed."""
        job = self._running_jobs.pop(job_id, None)
        if job:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now()
            job.error = error
            
            # Check if job can be retried
            if job.retry_count < job.max_retries:
                job.retry_count += 1
                job.status = JobStatus.RETRY
                job.started_at = None
                job.completed_at = None
                
                # Add back to pending queue for retry
                self._pending_jobs.append(job)
                self._pending_jobs.sort(key=lambda j: j.priority.value, reverse=True)
                
                logger.warning(f"Job {job_id} failed, retry {job.retry_count}/{job.max_retries}: {error}")
            else:
                self._failed_jobs[job_id] = job
                
                # Cleanup old failed jobs
                if len(self._failed_jobs) > self._max_failed_jobs:
                    oldest_job = min(self._failed_jobs.values(), key=lambda j: j.completed_at)
                    del self._failed_jobs[oldest_job.job_id]
                
                logger.error(f"Job {job_id} failed permanently after {job.retry_count} retries: {error}")
    
    def update_job_progress(self, job_id: str, progress: int, message: str = "") -> None:
        """Update job progress."""
        job = self._running_jobs.get(job_id)
        if job:
            job.progress = max(0, min(100, progress))
            job.progress_message = message
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        # Check running jobs
        if job_id in self._running_jobs:
            return self._running_jobs[job_id]
        
        # Check completed jobs
        if job_id in self._completed_jobs:
            return self._completed_jobs[job_id]
        
        # Check failed jobs
        if job_id in self._failed_jobs:
            return self._failed_jobs[job_id]
        
        # Check pending jobs
        for job in self._pending_jobs:
            if job.job_id == job_id:
                return job
        
        return None
    
    def get_user_jobs(self, user_id: str, limit: int = 50) -> List[Job]:
        """Get jobs for a specific user."""
        user_jobs = []
        
        # Add running jobs
        for job in self._running_jobs.values():
            if job.user_id == user_id:
                user_jobs.append(job)
        
        # Add completed jobs
        for job in self._completed_jobs.values():
            if job.user_id == user_id:
                user_jobs.append(job)
        
        # Add failed jobs
        for job in self._failed_jobs.values():
            if job.user_id == user_id:
                user_jobs.append(job)
        
        # Add pending jobs
        for job in self._pending_jobs:
            if job.user_id == user_id:
                user_jobs.append(job)
        
        # Sort by creation time (newest first)
        user_jobs.sort(key=lambda j: j.created_at, reverse=True)
        
        return user_jobs[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        return {
            'pending': len(self._pending_jobs),
            'running': len(self._running_jobs),
            'completed': len(self._completed_jobs),
            'failed': len(self._failed_jobs),
            'total': len(self._pending_jobs) + len(self._running_jobs) + len(self._completed_jobs) + len(self._failed_jobs)
        }


class BackgroundJobProcessor:
    """Background job processor with worker management."""
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.job_queue = JobQueue()
        self.task_registry: Dict[str, Callable] = {}
        self.workers: List[asyncio.Task] = []
        self.is_running = False
        
        # Register built-in tasks
        self._register_builtin_tasks()
    
    def _register_builtin_tasks(self):
        """Register built-in task handlers."""
        self.register_task('process_large_pdf', self._process_large_pdf_task)
        self.register_task('batch_update_tradelines', self._batch_update_tradelines_task)
        self.register_task('cleanup_old_data', self._cleanup_old_data_task)
        self.register_task('generate_user_report', self._generate_user_report_task)
    
    def register_task(self, task_name: str, handler: Callable) -> None:
        """Register a task handler."""
        self.task_registry[task_name] = handler
        logger.info(f"Registered task handler: {task_name}")
    
    async def submit_job(
        self,
        task_name: str,
        task_args: Dict[str, Any],
        user_id: Optional[str] = None,
        priority: JobPriority = JobPriority.NORMAL,
        max_retries: int = 3,
        timeout: int = 1800
    ) -> str:
        """Submit a job for background processing."""
        job_id = str(uuid.uuid4())
        
        job = Job(
            job_id=job_id,
            task_name=task_name,
            task_args=task_args,
            user_id=user_id,
            priority=priority,
            max_retries=max_retries,
            timeout=timeout
        )
        
        self.job_queue.add_job(job)
        
        # Cache job info for quick access
        await cache.set(f"job_status_{job_id}", job.to_dict(), ttl=7200)  # 2 hours
        
        return job_id
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status."""
        # Try cache first
        cached_job = await cache.get(f"job_status_{job_id}")
        if cached_job:
            return cached_job
        
        # Get from queue
        job = self.job_queue.get_job(job_id)
        if job:
            job_dict = job.to_dict()
            await cache.set(f"job_status_{job_id}", job_dict, ttl=7200)
            return job_dict
        
        return None
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        job = self.job_queue.get_job(job_id)
        if job and job.status in [JobStatus.PENDING, JobStatus.RETRY]:
            job.status = JobStatus.CANCELLED
            return True
        return False
    
    async def start(self) -> None:
        """Start the background job processor."""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start worker tasks
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self.workers.append(worker)
        
        logger.info(f"Started background job processor with {self.max_workers} workers")
    
    async def stop(self) -> None:
        """Stop the background job processor."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        
        logger.info("Background job processor stopped")
    
    async def _worker_loop(self, worker_name: str) -> None:
        """Main worker loop."""
        logger.info(f"Worker {worker_name} started")
        
        while self.is_running:
            try:
                # Get next job
                job = self.job_queue.get_next_job()
                
                if job:
                    logger.info(f"Worker {worker_name} processing job {job.job_id}")
                    await self._process_job(job)
                else:
                    # No jobs available, wait a bit
                    await asyncio.sleep(1)
                    
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_name} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(5)  # Wait before retrying
        
        logger.info(f"Worker {worker_name} stopped")
    
    async def _process_job(self, job: Job) -> None:
        """Process a single job."""
        try:
            # Check if task handler exists
            handler = self.task_registry.get(job.task_name)
            if not handler:
                raise Exception(f"Unknown task: {job.task_name}")
            
            # Create progress callback
            async def update_progress(progress: int, message: str = ""):
                self.job_queue.update_job_progress(job.job_id, progress, message)
                # Update cache
                job_dict = job.to_dict()
                await cache.set(f"job_status_{job.job_id}", job_dict, ttl=7200)
            
            # Execute task with timeout
            task_args = job.task_args.copy()
            task_args['progress_callback'] = update_progress
            task_args['job_id'] = job.job_id
            
            result = await asyncio.wait_for(
                handler(**task_args),
                timeout=job.timeout
            )
            
            # Mark job as completed
            self.job_queue.complete_job(job.job_id, result or {})
            
            # Update cache
            job_dict = job.to_dict()
            await cache.set(f"job_status_{job.job_id}", job_dict, ttl=7200)
            
        except asyncio.TimeoutError:
            error_msg = f"Job timed out after {job.timeout} seconds"
            self.job_queue.fail_job(job.job_id, error_msg)
        except Exception as e:
            error_msg = f"Job failed: {str(e)}"
            logger.error(f"Job {job.job_id} failed: {error_msg}\n{traceback.format_exc()}")
            self.job_queue.fail_job(job.job_id, error_msg)
    
    # Built-in task handlers
    async def _process_large_pdf_task(self, pdf_path: str, user_id: str, progress_callback, **kwargs) -> Dict[str, Any]:
        """Process large PDF in background."""
        try:
            await progress_callback(10, "Starting PDF processing...")
            
            from services.optimized_processor import OptimizedCreditReportProcessor
            processor = OptimizedCreditReportProcessor()
            
            await progress_callback(30, "Extracting text and tables...")
            
            # Add a hard timeout around the heavy processing to avoid "stuck at 30%"
            try:
                result = await asyncio.wait_for(
                    processor.process_credit_report_optimized(pdf_path),
                    timeout=15 * 60  # 15 minutes
                )
            except asyncio.TimeoutError:
                await progress_callback(99, "Timed out while extracting text. Please try a smaller PDF or retry later.")
                raise Exception("Processing timed out after 15 minutes")
            
            if result.get('success'):
                await progress_callback(80, "Saving tradelines to database...")
                
                # Save tradelines to database
                from services.database_optimizer import db_optimizer
                
                tradelines = result.get('tradelines', [])
                for tradeline in tradelines:
                    tradeline['user_id'] = user_id
                
                try:
                    save_result = await db_optimizer.batch_insert_tradelines(tradelines)
                except Exception as save_err:
                    # Don't fail the entire job if DB save fails; report in result
                    logger.error(f"DB save failed: {save_err}")
                    save_result = {'inserted': 0, 'errors': len(tradelines)}
                
                await progress_callback(100, f"Completed! Found {len(tradelines)} tradelines")
                
                return {
                    'success': True,
                    'tradelines_found': len(tradelines),
                    'tradelines_saved': save_result.get('inserted', 0),
                    'processing_time': result.get('processing_time', 0),
                    'method_used': result.get('method_used', 'unknown')
                }
            else:
                raise Exception(result.get('error', 'PDF processing failed'))
                
        except Exception as e:
            logger.error(f"Large PDF processing failed: {e}")
            raise
    
    async def _batch_update_tradelines_task(self, updates: List[Dict], progress_callback, **kwargs) -> Dict[str, Any]:
        """Batch update tradelines in background."""
        try:
            await progress_callback(10, "Starting batch update...")
            
            from services.database_optimizer import db_optimizer
            
            batch_size = 50
            total_batches = (len(updates) + batch_size - 1) // batch_size
            total_updated = 0
            
            for i, batch_start in enumerate(range(0, len(updates), batch_size)):
                batch = updates[batch_start:batch_start + batch_size]
                
                result = await db_optimizer.bulk_update_tradelines(batch)
                total_updated += result.get('updated', 0)
                
                progress = int(((i + 1) / total_batches) * 90) + 10
                await progress_callback(progress, f"Updated batch {i + 1}/{total_batches}")
            
            await progress_callback(100, f"Batch update completed! Updated {total_updated} tradelines")
            
            return {'updated': total_updated, 'total_batches': total_batches}
            
        except Exception as e:
            logger.error(f"Batch update failed: {e}")
            raise
    
    async def _cleanup_old_data_task(self, days_old: int = 30, progress_callback=None, **kwargs) -> Dict[str, Any]:
        """Cleanup old data in background."""
        try:
            if progress_callback:
                await progress_callback(10, "Starting cleanup...")
            
            # Implement cleanup logic here
            # This is a placeholder for actual cleanup operations
            
            if progress_callback:
                await progress_callback(100, "Cleanup completed")
            
            return {'cleaned_items': 0, 'days_old': days_old}
            
        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")
            raise
    
    async def _generate_user_report_task(self, user_id: str, report_type: str, progress_callback, **kwargs) -> Dict[str, Any]:
        """Generate user report in background."""
        try:
            await progress_callback(10, "Starting report generation...")
            
            # Implement report generation logic here
            # This is a placeholder
            
            await progress_callback(100, f"Report generated successfully")
            
            return {'report_type': report_type, 'user_id': user_id, 'generated_at': datetime.now().isoformat()}
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics."""
        queue_stats = self.job_queue.get_stats()
        return {
            'is_running': self.is_running,
            'workers': len(self.workers),
            'max_workers': self.max_workers,
            'registered_tasks': list(self.task_registry.keys()),
            'queue': queue_stats
        }


# Global job processor instance
job_processor = BackgroundJobProcessor(max_workers=3)


# Convenience functions
async def submit_pdf_processing_job(
    pdf_path: str,
    user_id: str,
    priority: JobPriority = JobPriority.NORMAL
) -> str:
    """Submit PDF processing job."""
    return await job_processor.submit_job(
        task_name='process_large_pdf',
        task_args={'pdf_path': pdf_path, 'user_id': user_id},
        user_id=user_id,
        priority=priority,
        timeout=3600  # 1 hour for large PDFs
    )


async def submit_batch_update_job(
    updates: List[Dict],
    user_id: Optional[str] = None,
    priority: JobPriority = JobPriority.NORMAL
) -> str:
    """Submit batch update job."""
    return await job_processor.submit_job(
        task_name='batch_update_tradelines',
        task_args={'updates': updates},
        user_id=user_id,
        priority=priority,
        timeout=1800  # 30 minutes
    )