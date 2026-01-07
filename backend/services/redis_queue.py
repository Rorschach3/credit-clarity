"""
Redis-backed job queue adapter for Credit Clarity
Provides production可靠的 job queue with priority, retries, and dead letter queue support
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    import redis.asyncio as redis
    from redis.asyncio import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from core.config import get_settings

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
    """Job priority levels (0-9, higher = more priority)."""
    LOWEST = 0
    LOW = 1
    BELOW_NORMAL = 2
    NORMAL = 3
    ABOVE_NORMAL = 4
    HIGH = 5
    HIGHEST = 6
    URGENT = 7
    CRITICAL = 8
    EMERGENCY = 9


class ProcessingStage(Enum):
    """Report processing stages for stage tracking."""
    UPLOAD = "upload"
    OCR = "ocr"
    PARSING = "parsing"
    TRADELINE_DETECTION = "tradeline_detection"
    VALIDATION = "validation"
    COMPLETE = "complete"


class RedisJobQueue:
    """
    Redis-backed job queue with priority support, retries, and dead letter queue.
    
    Uses sorted sets for priority queues and hashes for job storage.
    """
    
    # Redis key patterns
    PENDING_QUEUE_KEY = "job_queue:pending"
    RUNNING_JOBS_KEY = "job_queue:running"
    COMPLETED_JOBS_KEY = "job_queue:completed"
    FAILED_JOBS_KEY = "job_queue:failed"
    DEAD_LETTER_KEY = "job_queue:dead_letter"
    JOB_DATA_KEY_PREFIX = "job:data:"
    JOB_STATUS_KEY_PREFIX = "job:status:"
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        db: int = 0,
        max_retries: int = 3,
        retry_delay_seconds: int = 60,
        job_timeout_minutes: int = 30
    ):
        """
        Initialize Redis job queue.
        
        Args:
            redis_url: Redis connection URL
            db: Redis database number
            max_retries: Maximum retry attempts
            retry_delay_seconds: Base delay between retries
            job_timeout_minutes: Job timeout in minutes
        """
        self.redis_url = redis_url or settings.redis_url or "redis://localhost:6379"
        self.db = db
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self.job_timeout_minutes = job_timeout_minutes
        self._redis: Optional[Redis] = None
        self._connected = False
        
    async def connect(self) -> bool:
        """Establish connection to Redis."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis client not installed, falling back to memory")
            return False
            
        try:
            self._redis = redis.from_url(
                self.redis_url,
                db=self.db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            await self._redis.ping()
            self._connected = True
            logger.info(f"Connected to Redis at {self.redis_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._connected = False
            return False
    
    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            self._connected = False
            logger.info("Disconnected from Redis")
    
    async def is_connected(self) -> bool:
        """Check if connected to Redis."""
        if not self._connected or not self._redis:
            return False
        try:
            await self._redis.ping()
            return True
        except Exception:
            self._connected = False
            return False
    
    def _get_job_key(self, job_id: str) -> str:
        """Get Redis key for job data."""
        return f"{self.JOB_DATA_KEY_PREFIX}{job_id}"
    
    def _get_status_key(self, job_id: str) -> str:
        """Get Redis key for job status."""
        return f"{self.JOB_STATUS_KEY_PREFIX}{job_id}"
    
    async def enqueue(
        self,
        job_data: Dict[str, Any],
        priority: int = 3,
        job_id: Optional[str] = None
    ) -> str:
        """
        Add a job to the queue.
        
        Args:
            job_data: Job data dictionary
            priority: Priority level 0-9 (higher = more priority)
            job_id: Optional job ID (generated if not provided)
            
        Returns:
            Job ID
        """
        if not await self.is_connected():
            raise ConnectionError("Redis not connected")
        
        job_id = job_id or str(uuid.uuid4())
        
        # Clamp priority to 0-9
        priority = max(0, min(9, priority))
        
        # Create job record
        job_record = {
            'job_id': job_id,
            'task_name': job_data.get('task_name', 'unknown'),
            'task_args': job_data.get('task_args', {}),
            'user_id': job_data.get('user_id'),
            'priority': priority,
            'max_retries': job_data.get('max_retries', self.max_retries),
            'timeout': job_data.get('timeout', self.job_timeout_minutes * 60),
            'status': JobStatus.PENDING.value,
            'stage': ProcessingStage.UPLOAD.value,
            'progress': 0,
            'created_at': datetime.now().isoformat(),
            'started_at': None,
            'completed_at': None,
            'result': None,
            'error': None,
            'retry_count': 0,
            'progress_message': ''
        }
        
        # Store job data
        job_key = self._get_job_key(job_id)
        await self._redis.setex(
            job_key,
            timedelta(hours=24),  # TTL for job data
            json.dumps(job_record)
        )
        
        # Add to priority queue (score = -priority for descending order, +timestamp for FIFO)
        timestamp = datetime.now().timestamp()
        queue_score = -(priority * 1000) + (timestamp % 1)  # Priority first, then FIFO within priority
        await self._redis.zadd(self.PENDING_QUEUE_KEY, {job_id: queue_score})
        
        # Set job status
        status_key = self._get_status_key(job_id)
        await self._redis.setex(status_key, timedelta(hours=1), JobStatus.PENDING.value)
        
        logger.info(f"Enqueued job {job_id} with priority {priority}")
        return job_id
    
    async def dequeue(self) -> Optional[Dict[str, Any]]:
        """
        Get the next job from the queue.
        
        Returns:
            Job data dictionary or None if queue is empty
        """
        if not await self.is_connected():
            raise ConnectionError("Redis not connected")
        
        # Get highest priority job
        result = await self._redis.zpopmax(self.PENDING_QUEUE_KEY)
        
        if not result:
            return None
        
        job_id, score = result[0]
        
        # Get job data
        job_key = self._get_job_key(job_id)
        job_data = await self._redis.get(job_key)
        
        if not job_data:
            return None
        
        job_record = json.loads(job_data)
        
        # Update job status to running
        job_record['status'] = JobStatus.RUNNING.value
        job_record['started_at'] = datetime.now().isoformat()
        job_record['retry_count'] = job_record.get('retry_count', 0)
        
        # Store updated job data
        await self._redis.setex(
            job_key,
            timedelta(hours=24),
            json.dumps(job_record)
        )
        
        # Add to running jobs hash
        await self._redis.hset(self.RUNNING_JOBS_KEY, job_id, json.dumps(job_record))
        
        # Update status
        status_key = self._get_status_key(job_id)
        await self._redis.setex(status_key, timedelta(hours=1), JobStatus.RUNNING.value)
        
        logger.info(f"Dequeued job {job_id}")
        return job_record
    
    async def get_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status and details."""
        if not await self.is_connected():
            raise ConnectionError("Redis not connected")
        
        job_key = self._get_job_key(job_id)
        job_data = await self._redis.get(job_key)
        
        if not job_data:
            return None
        
        return json.loads(job_data)
    
    async def update_status(
        self,
        job_id: str,
        status: str,
        progress: Optional[int] = None,
        progress_message: Optional[str] = None,
        stage: Optional[str] = None
    ) -> bool:
        """
        Update job status.
        
        Args:
            job_id: Job ID
            status: New status
            progress: Progress percentage (0-100)
            progress_message: Progress message
            stage: Processing stage
            
        Returns:
            True if updated successfully
        """
        if not await self.is_connected():
            raise ConnectionError("Redis not connected")
        
        job_key = self._get_job_key(job_id)
        job_data = await self._redis.get(job_key)
        
        if not job_data:
            return False
        
        job_record = json.loads(job_data)
        job_record['status'] = status
        
        if progress is not None:
            job_record['progress'] = max(0, min(100, progress))
        if progress_message is not None:
            job_record['progress_message'] = progress_message
        if stage is not None:
            job_record['stage'] = stage
        
        # Store updated job data
        await self._redis.setex(
            job_key,
            timedelta(hours=24),
            json.dumps(job_record)
        )
        
        # Update running jobs hash if still running
        if status == JobStatus.RUNNING.value:
            await self._redis.hset(self.RUNNING_JOBS_KEY, job_id, json.dumps(job_record))
        
        # Update status key
        status_key = self._get_status_key(job_id)
        await self._redis.setex(status_key, timedelta(hours=1), status)
        
        return True
    
    async def mark_complete(self, job_id: str, result: Dict[str, Any]) -> bool:
        """Mark job as completed with result."""
        if not await self.is_connected():
            raise ConnectionError("Redis not connected")
        
        job_key = self._get_job_key(job_id)
        job_data = await self._redis.get(job_key)
        
        if not job_data:
            return False
        
        job_record = json.loads(job_data)
        job_record['status'] = JobStatus.COMPLETED.value
        job_record['completed_at'] = datetime.now().isoformat()
        job_record['result'] = result
        job_record['progress'] = 100
        job_record['stage'] = ProcessingStage.COMPLETE.value
        
        # Store completed job
        await self._redis.setex(
            job_key,
            timedelta(hours=24),
            json.dumps(job_record)
        )
        
        # Add to completed jobs
        await self._redis.hset(self.COMPLETED_JOBS_KEY, job_id, json.dumps(job_record))
        
        # Remove from running jobs
        await self._redis.hdel(self.RUNNING_JOBS_KEY, job_id)
        
        # Update status key
        status_key = self._get_status_key(job_id)
        await self._redis.setex(status_key, timedelta(hours=1), JobStatus.COMPLETED.value)
        
        logger.info(f"Job {job_id} completed")
        return True
    
    async def mark_failed(self, job_id: str, error: str) -> bool:
        """
        Mark job as failed.
        
        Returns:
            True if moved to retry, False if moved to dead letter
        """
        if not await self.is_connected():
            raise ConnectionError("Redis not connected")
        
        job_key = self._get_job_key(job_id)
        job_data = await self._redis.get(job_key)
        
        if not job_data:
            return False
        
        job_record = json.loads(job_data)
        job_record['error'] = error
        job_record['completed_at'] = datetime.now().isoformat()
        
        retry_count = job_record.get('retry_count', 0)
        max_retries = job_record.get('max_retries', self.max_retries)
        
        if retry_count < max_retries:
            # Schedule retry
            job_record['status'] = JobStatus.RETRY.value
            job_record['retry_count'] = retry_count + 1
            
            # Calculate backoff delay (exponential)
            delay = self.retry_delay_seconds * (2 ** retry_count)
            job_record['retry_at'] = (datetime.now() + timedelta(seconds=delay)).isoformat()
            
            # Store retry job
            await self._redis.setex(
                job_key,
                timedelta(hours=24),
                json.dumps(job_record)
            )
            
            # Re-add to pending queue with score for retry time
            retry_timestamp = (datetime.now() + timedelta(seconds=delay)).timestamp()
            queue_score = -(job_record['priority'] * 1000) + (retry_timestamp % 1)
            await self._redis.zadd(self.PENDING_QUEUE_KEY, {job_id: queue_score})
            
            # Remove from running
            await self._redis.hdel(self.RUNNING_JOBS_KEY, job_id)
            
            logger.warning(f"Job {job_id} failed, retry {retry_count + 1}/{max_retries} in {delay}s: {error}")
            return True
        else:
            # Max retries exceeded, move to dead letter
            job_record['status'] = JobStatus.FAILED.value
            
            # Store failed job
            await self._redis.setex(
                job_key,
                timedelta(hours=168),  # Keep for 7 days
                json.dumps(job_record)
            )
            
            # Add to dead letter queue
            await self._redis.lpush(self.DEAD_LETTER_KEY, json.dumps(job_record))
            
            # Remove from running
            await self._redis.hdel(self.RUNNING_JOBS_KEY, job_id)
            
            # Add to failed jobs
            await self._redis.hset(self.FAILED_JOBS_KEY, job_id, json.dumps(job_record))
            
            # Update status key
            status_key = self._get_status_key(job_id)
            await self._redis.setex(status_key, timedelta(hours=1), JobStatus.FAILED.value)
            
            logger.error(f"Job {job_id} failed permanently after {max_retries} retries: {error}")
            return False
    
    async def retry_job(self, job_id: str) -> bool:
        """
        Requeue a failed job for retry with reset retry count.
        
        Args:
            job_id: Job ID to retry
            
        Returns:
            True if successfully requeued
        """
        if not await self.is_connected():
            raise ConnectionError("Redis not connected")
        
        job_key = self._get_job_key(job_id)
        job_data = await self._redis.get(job_key)
        
        if not job_data:
            return False
        
        job_record = json.loads(job_data)
        job_record['status'] = JobStatus.PENDING.value
        job_record['retry_count'] = 0
        job_record['error'] = None
        job_record['started_at'] = None
        job_record['completed_at'] = None
        
        # Store updated job
        await self._redis.setex(
            job_key,
            timedelta(hours=24),
            json.dumps(job_record)
        )
        
        # Add back to pending queue
        timestamp = datetime.now().timestamp()
        queue_score = -(job_record['priority'] * 1000) + (timestamp % 1)
        await self._redis.zadd(self.PENDING_QUEUE_KEY, {job_id: queue_score})
        
        # Remove from failed jobs
        await self._redis.hdel(self.FAILED_JOBS_KEY, job_id)
        
        logger.info(f"Job {job_id} requeued for retry")
        return True
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        if not await self.is_connected():
            raise ConnectionError("Redis not connected")
        
        pending_count = await self._redis.zcard(self.PENDING_QUEUE_KEY)
        running_count = await self._redis.hlen(self.RUNNING_JOBS_KEY)
        completed_count = await self._redis.hlen(self.COMPLETED_JOBS_KEY)
        failed_count = await self._redis.hlen(self.FAILED_JOBS_KEY)
        dead_letter_count = await self._redis.llen(self.DEAD_LETTER_KEY)
        
        # Get jobs by priority distribution
        priority_distribution = {}
        for priority in range(10):
            count = await self._redis.zcount(
                self.PENDING_QUEUE_KEY,
                -(priority + 1) * 1000,
                -priority * 1000
            )
            if count > 0:
                priority_distribution[priority] = count
        
        # Get oldest job age
        oldest_job = await self._redis.zrange(self.PENDING_QUEUE_KEY, 0, 0, withscores=True)
        oldest_job_age = None
        if oldest_job:
            job_id, score = oldest_job[0]
            # Score is approximately timestamp, calculate age
            job_key = self._get_job_key(job_id)
            job_data = await self._redis.get(job_key)
            if job_data:
                job_record = json.loads(job_data)
                created_at = datetime.fromisoformat(job_record['created_at'])
                oldest_job_age = (datetime.now() - created_at).total_seconds()
        
        return {
            'pending': pending_count,
            'running': running_count,
            'completed': completed_count,
            'failed': failed_count,
            'dead_letter': dead_letter_count,
            'total': pending_count + running_count + completed_count + failed_count,
            'priority_distribution': priority_distribution,
            'oldest_job_age_seconds': oldest_job_age,
            'connected': self._connected
        }
    
    async def get_dead_letter_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get jobs from dead letter queue."""
        if not await self.is_connected():
            raise ConnectionError("Redis not connected")
        
        jobs = await self._redis.lrange(self.DEAD_LETTER_KEY, -limit, -1)
        return [json.loads(job) for job in jobs]
    
    async def clear_dead_letter(self, count: int = 0) -> int:
        """
        Clear jobs from dead letter queue.
        
        Args:
            count: Number of jobs to clear (0 = all)
            
        Returns:
            Number of jobs cleared
        """
        if not await self.is_connected():
            raise ConnectionError("Redis not connected")
        
        if count <= 0:
            # Clear all
            await self._redis.delete(self.DEAD_LETTER_KEY)
            return 0
        
        # Remove first 'count' items
        for _ in range(count):
            await self._redis.lpop(self.DEAD_LETTER_KEY)
        
        return count

    # ==================== PUB/SUB METHODS ====================

    async def publish_job_update(
        self,
        job_id: str,
        status: str,
        progress: int = 0,
        stage: str = "",
        message: str = "",
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish job status update to pub/sub channel.

        Args:
            job_id: Job ID
            status: Job status
            progress: Progress percentage (0-100)
            stage: Processing stage
            message: Progress message
            data: Additional data

        Returns:
            True if published successfully
        """
        if not await self.is_connected():
            return False

        try:
            channel = f"job_status:{job_id}"
            update_message = {
                "type": "job_status",
                "job_id": job_id,
                "status": status,
                "progress": progress,
                "stage": stage,
                "message": message,
                "data": data or {},
                "timestamp": datetime.now().isoformat()
            }
            await self._redis.publish(channel, json.dumps(update_message))
            return True
        except Exception as e:
            logger.error(f"Failed to publish job update: {e}")
            return False

    async def subscribe_to_job_updates(self, job_id: str):
        """
        Subscribe to job updates channel.

        Args:
            job_id: Job ID to subscribe to

        Returns:
            PubSub object or None if not connected
        """
        if not await self.is_connected():
            return None

        try:
            pubsub = self._redis.pubsub()
            channel = f"job_status:{job_id}"
            await pubsub.subscribe(channel)
            return pubsub
        except Exception as e:
            logger.error(f"Failed to subscribe to job updates: {e}")
            return None


class RedisRateLimiter:
    """
    Redis-based rate limiter using sliding window algorithm.
    """
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        db: int = 0
    ):
        """Initialize rate limiter."""
        self.redis_url = redis_url or settings.redis_url or "redis://localhost:6379"
        self.db = db
        self._redis: Optional[Redis] = None
        self._connected = False
    
    async def connect(self) -> bool:
        """Establish connection to Redis."""
        if not REDIS_AVAILABLE:
            return False
            
        try:
            self._redis = redis.from_url(
                self.redis_url,
                db=self.db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            await self._redis.ping()
            self._connected = True
            return True
        except Exception as e:
            logger.error(f"Failed to connect rate limiter to Redis: {e}")
            self._connected = False
            return False
    
    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            self._connected = False
    
    async def is_connected(self) -> bool:
        """Check if connected to Redis."""
        if not self._connected or not self._redis:
            return False
        try:
            await self._redis.ping()
            return True
        except Exception:
            self._connected = False
            return False
    
    def _get_limit_key(self, key: str) -> str:
        """Get Redis key for rate limit."""
        return f"ratelimit:{key}"
    
    async def check_rate_limit(
        self,
        key: str,
        max_requests: int = 10,
        window: int = 60
    ) -> Dict[str, Any]:
        """
        Check if request is within rate limit.
        
        Args:
            key: Rate limit key (e.g., user_id, api_key)
            max_requests: Maximum requests allowed in window
            window: Time window in seconds
            
        Returns:
            Dict with 'allowed', 'remaining', 'reset_at', 'limit'
        """
        if not await self.is_connected():
            # Fallback: allow request when Redis unavailable
            return {
                'allowed': True,
                'remaining': max_requests,
                'reset_at': None,
                'limit': max_requests,
                'window': window
            }
        
        limit_key = self._get_limit_key(key)
        now = datetime.now()
        window_start = now - timedelta(seconds=window)
        
        # Use pipeline for atomic operations
        pipe = self._redis.pipeline()
        
        # Remove old entries outside window
        pipe.zremrangebyscore(limit_key, 0, window_start.timestamp())
        
        # Count current requests
        pipe.zcard(limit_key)
        
        # Add current request
        pipe.zadd(limit_key, {f"{now.timestamp()}:{id(now)}": now.timestamp()})
        
        # Set TTL
        pipe.expire(limit_key, window)
        
        results = await pipe.execute()
        current_count = results[1]
        
        allowed = current_count <= max_requests
        remaining = max(0, max_requests - current_count)
        
        # Calculate reset time
        reset_at = now + timedelta(seconds=window)
        
        return {
            'allowed': allowed,
            'remaining': remaining,
            'reset_at': reset_at.isoformat(),
            'limit': max_requests,
            'window': window
        }
    
    async def get_remaining(self, key: str, max_requests: int = 10, window: int = 60) -> int:
        """Get remaining requests for a key."""
        if not await self.is_connected():
            return max_requests
        
        limit_key = self._get_limit_key(key)
        now = datetime.now()
        window_start = now - timedelta(seconds=window)
        
        # Clean old entries and count
        await self._redis.zremrangebyscore(limit_key, 0, window_start.timestamp())
        current_count = await self._redis.zcard(limit_key)
        
        return max(0, max_requests - current_count)
    
    async def reset_limit(self, key: str) -> bool:
        """Reset rate limit for a key."""
        if not await self.is_connected():
            return False
        
        limit_key = self._get_limit_key(key)
        await self._redis.delete(limit_key)
        return True


# Global instances
_redis_queue: Optional[RedisJobQueue] = None
_rate_limiter: Optional[RedisRateLimiter] = None


async def get_redis_queue() -> RedisJobQueue:
    """Get or create Redis job queue instance."""
    global _redis_queue
    if _redis_queue is None:
        _redis_queue = RedisJobQueue()
        await _redis_queue.connect()
    return _redis_queue


async def get_rate_limiter() -> RedisRateLimiter:
    """Get or create rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RedisRateLimiter()
        await _rate_limiter.connect()
    return _rate_limiter


async def shutdown_redis_queue() -> None:
    """Shutdown Redis queue connections."""
    global _redis_queue, _rate_limiter
    if _redis_queue:
        await _redis_queue.disconnect()
        _redis_queue = None
    if _rate_limiter:
        await _rate_limiter.disconnect()
        _rate_limiter = None
