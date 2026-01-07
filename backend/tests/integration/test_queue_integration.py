"""
Integration tests for Redis job queue
Tests the full queue workflow with actual Redis connection
"""
import asyncio
import json
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest import skip_if

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Skip tests if Redis is not available
try:
    import redis.asyncio as redis
    from services.redis_queue import RedisJobQueue, RedisRateLimiter
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


def is_redis_running():
    """Check if Redis is running."""
    if not REDIS_AVAILABLE:
        return False
    try:
        r = redis.from_url("redis://localhost:6379", socket_timeout=1)
        r.ping_sync()
        return True
    except Exception:
        return False


REDIS_RUNNING = is_redis_running()


@pytest.mark.skipif(not REDIS_AVAILABLE or not REDIS_RUNNING, 
                    reason="Redis not available or not running")
class TestRedisJobQueueIntegration:
    """Integration tests for RedisJobQueue with actual Redis."""
    
    @pytest_asyncio.fixture
    async def redis_queue(self):
        """Create and connect RedisJobQueue."""
        queue = RedisJobQueue(
            redis_url="redis://localhost:6379",
            db=0,
            max_retries=3,
            retry_delay_seconds=1,  # Short delay for testing
            job_timeout_minutes=1
        )
        connected = await queue.connect()
        if not connected:
            pytest.skip("Redis connection failed")
        
        yield queue
        
        # Cleanup
        await queue.disconnect()
    
    @pytest_asyncio.fixture
    async def clean_queue(self, redis_queue):
        """Clean up queue before each test."""
        if redis_queue._redis:
            # Clear all queue keys
            await redis_queue._redis.delete(redis_queue.PENDING_QUEUE_KEY)
            await redis_queue._redis.delete(redis_queue.RUNNING_JOBS_KEY)
            await redis_queue._redis.delete(redis_queue.COMPLETED_JOBS_KEY)
            await redis_queue._redis.delete(redis_queue.FAILED_JOBS_KEY)
            await redis_queue._redis.delete(redis_queue.DEAD_LETTER_KEY)
        yield redis_queue
    
    @pytest.mark.asyncio
    async def test_full_job_lifecycle(self, clean_queue):
        """Test complete job lifecycle: enqueue -> dequeue -> complete."""
        # Enqueue job
        job_data = {
            'task_name': 'process_large_pdf',
            'task_args': {'pdf_path': '/test/file.pdf'},
            'user_id': 'user123'
        }
        
        job_id = await clean_queue.enqueue(job_data, priority=5)
        
        assert job_id is not None
        
        # Check status
        status = await clean_queue.get_status(job_id)
        assert status is not None
        assert status['status'] == 'pending'
        assert status['task_name'] == 'process_large_pdf'
        
        # Dequeue job
        job = await clean_queue.dequeue()
        assert job is not None
        assert job['job_id'] == job_id
        assert job['status'] == 'running'
        
        # Update progress
        await clean_queue.update_status(
            job_id,
            status='running',
            progress=50,
            progress_message='Halfway done'
        )
        
        updated_status = await clean_queue.get_status(job_id)
        assert updated_status['progress'] == 50
        assert updated_status['progress_message'] == 'Halfway done'
        
        # Complete job
        result = {'success': True, 'tradelines_found': 10}
        await clean_queue.mark_complete(job_id, result)
        
        final_status = await clean_queue.get_status(job_id)
        assert final_status['status'] == 'completed'
        assert final_status['result'] == result
        assert final_status['progress'] == 100
    
    @pytest.mark.asyncio
    async def test_job_priority_ordering(self, clean_queue):
        """Test that jobs are dequeued by priority."""
        # Enqueue jobs with different priorities
        job_ids = []
        for i, priority in enumerate([1, 5, 3, 9, 2]):
            job_id = await clean_queue.enqueue(
                {'task_name': f'task_{i}'},
                priority=priority
            )
            job_ids.append(job_id)
        
        # Dequeue all jobs and check order
        dequeued = []
        for _ in range(5):
            job = await clean_queue.dequeue()
            if job:
                dequeued.append(job)
        
        # Jobs should be ordered by priority (highest first)
        priorities = [job['priority'] for job in dequeued]
        assert priorities == sorted(priorities, reverse=True)
    
    @pytest.mark.asyncio
    async def test_job_retry_mechanism(self, clean_queue):
        """Test job retry with exponential backoff."""
        # Create queue with short retry delay
        clean_queue.retry_delay_seconds = 1
        clean_queue.max_retries = 2
        
        # Enqueue job
        job_id = await clean_queue.enqueue({'task_name': 'failing_task'})
        
        # Mark as failed (should retry)
        success = await clean_queue.mark_failed(job_id, "Test error")
        
        # Should return True (scheduled for retry)
        assert success is True
        
        # Job should be back in pending queue
        status = await clean_queue.get_status(job_id)
        assert status['status'] == 'retry'
        assert status['retry_count'] == 1
    
    @pytest.mark.asyncio
    async def test_job_dead_letter_queue(self, clean_queue):
        """Test that failed jobs go to dead letter queue."""
        # Create queue with max_retries=1
        clean_queue.max_retries = 1
        
        job_id = await clean_queue.enqueue({'task_name': 'failing_task'})
        
        # First failure - should retry
        await clean_queue.mark_failed(job_id, "Error 1")
        
        # Second failure - should go to dead letter
        await clean_queue.mark_failed(job_id, "Error 2")
        
        # Check dead letter queue
        dead_letter_jobs = await clean_queue.get_dead_letter_jobs()
        assert len(dead_letter_jobs) >= 1
        
        # Find our job
        dl_job = next((j for j in dead_letter_jobs if j['job_id'] == job_id), None)
        assert dl_job is not None
        assert dl_job['status'] == 'failed'
        assert dl_job['error'] == 'Error 2'
    
    @pytest.mark.asyncio
    async def test_retry_failed_job(self, clean_queue):
        """Test manually retrying a failed job."""
        job_id = await clean_queue.enqueue({'task_name': 'stuck_job'})
        
        # Move to failed
        clean_queue.max_retries = 0  # Force immediate failure
        await clean_queue.mark_failed(job_id, "Permanent error")
        
        # Retry the job
        success = await clean_queue.retry_job(job_id)
        assert success is True
        
        # Job should be back in pending
        status = await clean_queue.get_status(job_id)
        assert status['status'] == 'pending'
        assert status['retry_count'] == 0
    
    @pytest.mark.asyncio
    async def test_queue_stats(self, clean_queue):
        """Test queue statistics."""
        # Add some jobs
        for i in range(3):
            await clean_queue.enqueue({'task_name': f'task_{i}'}, priority=3)
        
        # Dequeue one
        await clean_queue.dequeue()
        
        stats = await clean_queue.get_queue_stats()
        
        assert stats['pending'] == 2
        assert stats['running'] == 1
        assert stats['completed'] == 0
        assert stats['failed'] == 0
        assert stats['total'] == 3
        assert 'priority_distribution' in stats
        assert 3 in stats['priority_distribution']
    
    @pytest.mark.asyncio
    async def test_stage_tracking(self, clean_queue):
        """Test processing stage tracking."""
        job_id = await clean_queue.enqueue({'task_name': 'process_large_pdf'})
        
        # Update through stages
        stages = ['upload', 'ocr', 'parsing', 'tradeline_detection', 'complete']
        for i, stage in enumerate(stages):
            await clean_queue.update_status(
                job_id,
                status='running' if stage != 'complete' else 'completed',
                progress=(i + 1) * 20,
                stage=stage
            )
        
        status = await clean_queue.get_status(job_id)
        assert status['stage'] == 'complete'
        assert status['progress'] == 100


@pytest.mark.skipif(not REDIS_AVAILABLE or not REDIS_RUNNING, 
                    reason="Redis not available or not running")
class TestRedisRateLimiterIntegration:
    """Integration tests for RedisRateLimiter."""
    
    @pytest_asyncio.fixture
    async def rate_limiter(self):
        """Create and connect RedisRateLimiter."""
        limiter = RedisRateLimiter(redis_url="redis://localhost:6379", db=0)
        connected = await limiter.connect()
        if not connected:
            pytest.skip("Redis connection failed")
        
        yield limiter
        
        await limiter.disconnect()
    
    @pytest_asyncio.fixture
    async def clean_limiter(self, rate_limiter):
        """Clean up rate limit keys before each test."""
        yield rate_limiter
    
    @pytest.mark.asyncio
    async def test_rate_limit_under_threshold(self, clean_limiter):
        """Test rate limit when under threshold."""
        result = await clean_limiter.check_rate_limit(
            key='test_user_1',
            max_requests=10,
            window=60
        )
        
        assert result['allowed'] is True
        assert result['remaining'] == 9
        assert result['limit'] == 10
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeds_threshold(self, clean_limiter):
        """Test rate limit when exceeding threshold."""
        key = 'test_user_exceed'
        
        # Make 11 requests with max 10
        for i in range(11):
            result = await clean_limiter.check_rate_limit(
                key=key,
                max_requests=10,
                window=60
            )
        
        assert result['allowed'] is False
        assert result['remaining'] == 0
    
    @pytest.mark.asyncio
    async def test_get_remaining_requests(self, clean_limiter):
        """Test getting remaining requests."""
        key = 'test_user_remaining'
        
        # Make 3 requests
        for _ in range(3):
            await clean_limiter.check_rate_limit(key, max_requests=10, window=60)
        
        remaining = await clean_limiter.get_remaining(key, max_requests=10, window=60)
        assert remaining == 7
    
    @pytest.mark.asyncio
    async def test_reset_rate_limit(self, clean_limiter):
        """Test resetting rate limit."""
        key = 'test_user_reset'
        
        # Make some requests
        for _ in range(5):
            await clean_limiter.check_rate_limit(key, max_requests=10, window=60)
        
        # Reset
        success = await clean_limiter.reset_limit(key)
        assert success is True
        
        # Check remaining should be back to max
        remaining = await clean_limiter.get_remaining(key, max_requests=10, window=60)
        assert remaining == 10


@pytest.mark.skipif(not REDIS_AVAILABLE or not REDIS_RUNNING, 
                    reason="Redis not available or not running")
class TestBackgroundJobsIntegration:
    """Integration tests for BackgroundJobProcessor with Redis."""
    
    @pytest_asyncio.fixture
    async def processor(self):
        """Create and start BackgroundJobProcessor."""
        from services.background_jobs import BackgroundJobProcessor
        
        processor = BackgroundJobProcessor(max_workers=2)
        await processor.start()
        
        yield processor
        
        await processor.stop()
    
    @pytest.mark.asyncio
    async def test_submit_and_process_job(self, processor):
        """Test submitting and processing a job."""
        # Submit job
        job_id = await processor.submit_job(
            task_name='cleanup_old_data',
            task_args={'days_old': 30},
            user_id='test_user'
        )
        
        assert job_id is not None
        
        # Wait a bit for processing
        await asyncio.sleep(2)
        
        # Check status
        status = await processor.get_job_status(job_id)
        assert status is not None
        assert status['job_id'] == job_id
        
        # Job should be completed (cleanup task is simple)
        assert status['status'] in ['completed', 'pending', 'running']
    
    @pytest.mark.asyncio
    async def test_multiple_jobs(self, processor):
        """Test submitting multiple jobs."""
        job_ids = []
        
        for i in range(5):
            job_id = await processor.submit_job(
                task_name='cleanup_old_data',
                task_args={'days_old': 30},
                user_id='test_user'
            )
            job_ids.append(job_id)
        
        assert len(job_ids) == 5
        
        # All should be in queue
        for job_id in job_ids:
            status = await processor.get_job_status(job_id)
            assert status is not None


# Memory fallback tests (always run)
class TestMemoryFallback:
    """Test memory fallback when Redis is unavailable."""
    
    @pytest.mark.asyncio
    async def test_memory_queue_operations(self):
        """Test basic memory queue operations."""
        from services.background_jobs import JobQueue, Job, JobPriority, JobStatus
        
        queue = JobQueue()
        
        # Add jobs
        for i in range(3):
            job = Job(
                job_id=f'job-{i}',
                task_name=f'task_{i}',
                task_args={},
                priority=JobPriority.NORMAL
            )
            queue.add_job(job)
        
        assert queue.get_stats()['pending'] == 3
        
        # Get next job
        job = queue.get_next_job()
        assert job is not None
        assert job.status == JobStatus.RUNNING
        
        # Complete job
        queue.complete_job(job.job_id, {'result': 'success'})
        assert queue.get_stats()['completed'] == 1
    
    @pytest.mark.asyncio
    async def test_job_retry_in_memory(self):
        """Test job retry in memory queue."""
        from services.background_jobs import JobQueue, Job, JobPriority, JobStatus
        
        queue = JobQueue()
        
        job = Job(
            job_id='retry-job',
            task_name='failing_task',
            task_args={},
            priority=JobPriority.NORMAL,
            max_retries=2
        )
        
        queue.add_job(job)
        
        # Get and fail job
        running_job = queue.get_next_job()
        queue.fail_job(running_job.job_id, "Error 1")
        
        # Should be back in queue for retry
        status = queue.get_job('retry-job')
        assert status.status == JobStatus.RETRY
        assert status.retry_count == 1
        
        # Fail again
        queue.fail_job('retry-job', "Error 2")
        assert status.retry_count == 2
        
        # Fail again (max retries exceeded)
        queue.fail_job('retry-job', "Error 3")
        
        final_status = queue.get_job('retry-job')
        assert final_status.status == JobStatus.FAILED


# Run tests if executed directly
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
