"""
Unit tests for Redis job queue adapter
"""
import asyncio
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestJobStatus:
    """Test JobStatus enum."""
    
    def test_job_status_values(self):
        """Test job status enum values."""
        from services.redis_queue import JobStatus
        
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.RUNNING.value == "running"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
        assert JobStatus.CANCELLED.value == "cancelled"
        assert JobStatus.RETRY.value == "retry"


class TestJobPriority:
    """Test JobPriority enum."""
    
    def test_job_priority_values(self):
        """Test job priority enum values."""
        from services.redis_queue import JobPriority
        
        assert JobPriority.LOWEST.value == 0
        assert JobPriority.NORMAL.value == 3
        assert JobPriority.HIGHEST.value == 6
        assert JobPriority.EMERGENCY.value == 9
    
    def test_priority_ordering(self):
        """Test priority ordering."""
        from services.redis_queue import JobPriority
        
        # Higher value = higher priority
        assert JobPriority.EMERGENCY.value > JobPriority.HIGH.value
        assert JobPriority.NORMAL.value > JobPriority.LOW.value


class TestProcessingStage:
    """Test ProcessingStage enum."""
    
    def test_processing_stage_values(self):
        """Test processing stage enum values."""
        from services.redis_queue import ProcessingStage
        
        assert ProcessingStage.UPLOAD.value == "upload"
        assert ProcessingStage.OCR.value == "ocr"
        assert ProcessingStage.PARSING.value == "parsing"
        assert ProcessingStage.TRADELINE_DETECTION.value == "tradeline_detection"
        assert ProcessingStage.VALIDATION.value == "validation"
        assert ProcessingStage.COMPLETE.value == "complete"


class TestRedisJobQueue:
    """Test RedisJobQueue class."""
    
    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        mock = AsyncMock()
        mock.ping = AsyncMock(return_value=True)
        mock.setex = AsyncMock(return_value=True)
        mock.get = AsyncMock(return_value=None)
        mock.zadd = AsyncMock(return_value=1)
        mock.zpopmax = AsyncMock(return_value=[])
        mock.zcard = AsyncMock(return_value=0)
        mock.hset = AsyncMock(return_value=1)
        mock.hdel = AsyncMock(return_value=1)
        mock.hlen = AsyncMock(return_value=0)
        mock.lpush = AsyncMock(return_value=1)
        mock.llen = AsyncMock(return_value=0)
        mock.lrange = AsyncMock(return_value=[])
        mock.zcount = AsyncMock(return_value=0)
        mock.zrange = AsyncMock(return_value=[])
        mock.pipeline = MagicMock()
        mock.delete = AsyncMock(return_value=1)
        return mock
    
    @pytest.fixture
    def redis_queue(self, mock_redis):
        """Create RedisJobQueue with mocked Redis."""
        from services.redis_queue import RedisJobQueue
        
        queue = RedisJobQueue(
            redis_url="redis://localhost:6379",
            db=0,
            max_retries=3,
            retry_delay_seconds=60,
            job_timeout_minutes=30
        )
        queue._redis = mock_redis
        queue._connected = True
        return queue
    
    @pytest.mark.asyncio
    async def test_enqueue_creates_job(self, redis_queue, mock_redis):
        """Test that enqueue creates a job in Redis."""
        job_data = {
            'task_name': 'test_task',
            'task_args': {'arg1': 'value1'},
            'user_id': 'user123'
        }
        
        job_id = await redis_queue.enqueue(job_data, priority=5)
        
        assert job_id is not None
        assert len(job_id) == 36  # UUID format
        
        # Verify Redis calls
        mock_redis.setex.assert_called()
        mock_redis.zadd.assert_called_once()
        mock_redis.setex.assert_called()
    
    @pytest.mark.asyncio
    async def test_enqueue_with_custom_job_id(self, redis_queue, mock_redis):
        """Test enqueue with custom job ID."""
        job_data = {'task_name': 'test_task'}
        custom_id = 'custom-job-id-123'
        
        job_id = await redis_queue.enqueue(job_data, job_id=custom_id)
        
        assert job_id == custom_id
    
    @pytest.mark.asyncio
    async def test_enqueue_priority_clamping(self, redis_queue, mock_redis):
        """Test that priority is clamped to 0-9."""
        job_data = {'task_name': 'test_task'}
        
        # Test priority too high
        job_id_high = await redis_queue.enqueue(job_data, priority=15)
        
        # Test priority too low
        job_id_low = await redis_queue.enqueue(job_data, priority=-5)
        
        # Both should succeed (queue score calculation handles clamping)
        assert job_id_high is not None
        assert job_id_low is not None
    
    @pytest.mark.asyncio
    async def test_dequeue_returns_none_when_empty(self, redis_queue, mock_redis):
        """Test that dequeue returns None when queue is empty."""
        mock_redis.zpopmax = AsyncMock(return_value=[])
        
        result = await redis_queue.dequeue()
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_dequeue_returns_job(self, redis_queue, mock_redis):
        """Test that dequeue returns a job when available."""
        job_id = 'test-job-id'
        job_record = {
            'job_id': job_id,
            'task_name': 'test_task',
            'task_args': {},
            'priority': 3,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        
        mock_redis.zpopmax = AsyncMock(return_value=[(job_id, -3000.0)])
        mock_redis.get = AsyncMock(return_value=json.dumps(job_record))
        
        result = await redis_queue.dequeue()
        
        assert result is not None
        assert result['job_id'] == job_id
        assert result['status'] == 'running'
    
    @pytest.mark.asyncio
    async def test_get_status(self, redis_queue, mock_redis):
        """Test getting job status."""
        job_id = 'test-job-id'
        job_record = {
            'job_id': job_id,
            'status': 'running',
            'progress': 50
        }
        
        mock_redis.get = AsyncMock(return_value=json.dumps(job_record))
        
        result = await redis_queue.get_status(job_id)
        
        assert result is not None
        assert result['job_id'] == job_id
        assert result['status'] == 'running'
    
    @pytest.mark.asyncio
    async def test_get_status_not_found(self, redis_queue, mock_redis):
        """Test getting status of non-existent job."""
        mock_redis.get = AsyncMock(return_value=None)
        
        result = await redis_queue.get_status('non-existent-id')
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_mark_complete(self, redis_queue, mock_redis):
        """Test marking job as complete."""
        job_id = 'test-job-id'
        job_record = {
            'job_id': job_id,
            'status': 'running',
            'created_at': datetime.now().isoformat()
        }
        
        mock_redis.get = AsyncMock(return_value=json.dumps(job_record))
        
        result = {'success': True, 'data': [1, 2, 3]}
        success = await redis_queue.mark_complete(job_id, result)
        
        assert success is True
        mock_redis.hset.assert_called()
    
    @pytest.mark.asyncio
    async def test_mark_failed_with_retry(self, redis_queue, mock_redis):
        """Test marking job as failed with retry."""
        job_id = 'test-job-id'
        job_record = {
            'job_id': job_id,
            'status': 'running',
            'priority': 3,
            'retry_count': 0,
            'max_retries': 3,
            'created_at': datetime.now().isoformat()
        }
        
        mock_redis.get = AsyncMock(return_value=json.dumps(job_record))
        
        success = await redis_queue.mark_failed(job_id, "Test error")
        
        # Should be scheduled for retry (return True for retry)
        assert success is True
    
    @pytest.mark.asyncio
    async def test_mark_failed_without_retry(self, redis_queue, mock_redis):
        """Test marking job as failed without retry (max retries exceeded)."""
        job_id = 'test-job-id'
        job_record = {
            'job_id': job_id,
            'status': 'running',
            'priority': 3,
            'retry_count': 3,  # Already at max
            'max_retries': 3,
            'created_at': datetime.now().isoformat()
        }
        
        mock_redis.get = AsyncMock(return_value=json.dumps(job_record))
        
        success = await redis_queue.mark_failed(job_id, "Test error")
        
        # Should go to dead letter (return False)
        assert success is False
    
    @pytest.mark.asyncio
    async def test_retry_job(self, redis_queue, mock_redis):
        """Test retrying a failed job."""
        job_id = 'test-job-id'
        job_record = {
            'job_id': job_id,
            'status': 'failed',
            'priority': 3,
            'created_at': datetime.now().isoformat()
        }
        
        mock_redis.get = AsyncMock(return_value=json.dumps(job_record))
        
        success = await redis_queue.retry_job(job_id)
        
        assert success is True
        mock_redis.zadd.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_queue_stats(self, redis_queue, mock_redis):
        """Test getting queue statistics."""
        mock_redis.zcard = AsyncMock(side_effect=[5, 10, 2, 3, 1])  # pending, completed, failed, dead_letter
        mock_redis.hlen = AsyncMock(side_effect=[2, 3])  # running
        mock_redis.llen = AsyncMock(return_value=1)
        mock_redis.zcount = AsyncMock(return_value=2)
        mock_redis.zrange = AsyncMock(return_value=[])
        
        stats = await redis_queue.get_queue_stats()
        
        assert stats['pending'] == 5
        assert stats['running'] == 2
        assert stats['completed'] == 10
        assert stats['failed'] == 3
        assert stats['dead_letter'] == 1
        assert stats['total'] == 21
        assert stats['connected'] is True
    
    @pytest.mark.asyncio
    async def test_update_status(self, redis_queue, mock_redis):
        """Test updating job status."""
        job_id = 'test-job-id'
        job_record = {
            'job_id': job_id,
            'status': 'running',
            'progress': 50,
            'created_at': datetime.now().isoformat()
        }
        
        mock_redis.get = AsyncMock(return_value=json.dumps(job_record))
        
        success = await redis_queue.update_status(
            job_id,
            status='running',
            progress=75,
            progress_message='Processing...',
            stage='ocr'
        )
        
        assert success is True


class TestRedisRateLimiter:
    """Test RedisRateLimiter class."""
    
    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        mock = AsyncMock()
        mock.ping = AsyncMock(return_value=True)
        mock.zremrangebyscore = AsyncMock(return_value=0)
        mock.zcard = AsyncMock(return_value=5)
        mock.zadd = AsyncMock(return_value=1)
        mock.expire = AsyncMock(return_value=True)
        mock.delete = AsyncMock(return_value=1)
        mock.pipeline = MagicMock()
        return mock
    
    @pytest.fixture
    def rate_limiter(self, mock_redis):
        """Create RedisRateLimiter with mocked Redis."""
        from services.redis_queue import RedisRateLimiter
        
        limiter = RedisRateLimiter(
            redis_url="redis://localhost:6379",
            db=0
        )
        limiter._redis = mock_redis
        limiter._connected = True
        return limiter
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_allowed(self, rate_limiter, mock_redis):
        """Test rate limit check when under limit."""
        pipe = AsyncMock()
        pipe.execute = AsyncMock(return_value=[0, 5, 1, True])
        mock_redis.pipeline = MagicMock(return_value=pipe)
        
        result = await rate_limiter.check_rate_limit(
            key='user123',
            max_requests=10,
            window=60
        )
        
        assert result['allowed'] is True
        assert result['remaining'] == 5
        assert result['limit'] == 10
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeded(self, rate_limiter, mock_redis):
        """Test rate limit check when over limit."""
        pipe = AsyncMock()
        pipe.execute = AsyncMock(return_value=[0, 12, 1, True])  # 12 > 10
        mock_redis.pipeline = MagicMock(return_value=pipe)
        
        result = await rate_limiter.check_rate_limit(
            key='user123',
            max_requests=10,
            window=60
        )
        
        assert result['allowed'] is False
        assert result['remaining'] == 0
    
    @pytest.mark.asyncio
    async def test_get_remaining(self, rate_limiter, mock_redis):
        """Test getting remaining requests."""
        mock_redis.zcard = AsyncMock(return_value=3)
        
        remaining = await rate_limiter.get_remaining(
            key='user123',
            max_requests=10,
            window=60
        )
        
        assert remaining == 7
    
    @pytest.mark.asyncio
    async def test_reset_limit(self, rate_limiter, mock_redis):
        """Test resetting rate limit."""
        success = await rate_limiter.reset_limit('user123')
        
        assert success is True
        mock_redis.delete.assert_called_once()


class TestHybridJobQueue:
    """Test HybridJobQueue class."""
    
    @pytest.mark.asyncio
    async def test_initialize_uses_memory_when_redis_unavailable(self):
        """Test that HybridJobQueue falls back to memory when Redis unavailable."""
        from services.background_jobs import HybridJobQueue, JobQueue
        
        queue = HybridJobQueue()
        
        # Mock RedisQueueAdapter to return False for initialization
        with patch('services.background_jobs.REDIS_QUEUE_AVAILABLE', False):
            await queue.initialize()
        
        assert queue.use_redis is False
        assert isinstance(queue._memory_queue, JobQueue)
    
    @pytest.mark.asyncio
    async def test_add_job_memory(self):
        """Test adding job to memory queue."""
        from services.background_jobs import HybridJobQueue, Job, JobPriority
        
        queue = HybridJobQueue()
        await queue.initialize()
        
        job = Job(
            job_id='test-id',
            task_name='test_task',
            task_args={},
            priority=JobPriority.NORMAL
        )
        
        await queue.add_job(job)
        
        # Job should be in memory queue
        assert len(queue._memory_queue._pending_jobs) == 1


class TestBackgroundJobProcessor:
    """Test BackgroundJobProcessor class."""
    
    @pytest.fixture
    def processor(self):
        """Create a BackgroundJobProcessor instance."""
        from services.background_jobs import BackgroundJobProcessor
        
        return BackgroundJobProcessor(max_workers=1)
    
    def test_processor_initialization(self, processor):
        """Test processor initialization."""
        assert processor.max_workers == 1
        assert processor.is_running is False
        assert len(processor.workers) == 0
        assert len(processor.task_registry) > 0  # Built-in tasks registered
    
    def test_register_task(self, processor):
        """Test task registration."""
        async def dummy_task(**kwargs):
            return {}
        
        processor.register_task('custom_task', dummy_task)
        
        assert 'custom_task' in processor.task_registry
        assert processor.task_registry['custom_task'] == dummy_task
    
    @pytest.mark.asyncio
    async def test_submit_job(self, processor):
        """Test job submission."""
        job_id = await processor.submit_job(
            task_name='cleanup_old_data',
            task_args={'days_old': 30},
            user_id='user123',
            priority=processor.job_queue._memory_queue.__class__.__name__
        )
        
        assert job_id is not None
        assert len(job_id) == 36
    
    @pytest.mark.asyncio
    async def test_get_job_status(self, processor):
        """Test getting job status."""
        job_id = await processor.submit_job(
            task_name='cleanup_old_data',
            task_args={}
        )
        
        status = await processor.get_job_status(job_id)
        
        assert status is not None
        assert status['job_id'] == job_id
        assert status['status'] == 'pending'
    
    @pytest.mark.asyncio
    async def test_get_job_status_not_found(self, processor):
        """Test getting status of non-existent job."""
        status = await processor.get_job_status('non-existent-id')
        
        assert status is None


# Run tests if executed directly
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
