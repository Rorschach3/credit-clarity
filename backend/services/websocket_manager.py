"""
WebSocket connection manager for real-time job status updates.
Manages WebSocket connections per job_id and subscribes to Redis channels.
"""
import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class WebSocketMessage(BaseModel):
    """WebSocket message format."""
    type: str
    job_id: str
    status: Optional[str] = None
    progress: Optional[int] = None
    stage: Optional[str] = None
    message: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: str = datetime.now().isoformat()
    data: Optional[Dict[str, Any]] = None


class ConnectionManager:
    """
    Manages WebSocket connections for job status updates.

    Features:
    - Multiple connections per job_id (broadcast to all)
    - Automatic connection cleanup on disconnect
    - Thread-safe operations
    """

    def __init__(self):
        # Map job_id -> set of WebSocket connections
        self._connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        # Map WebSocket -> job_id (for reverse lookup)
        self._reverse_lookup: Dict[WebSocket, str] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def connect(self, job_id: str, websocket: WebSocket) -> None:
        """
        Accept and register a new WebSocket connection for a job.

        Args:
            job_id: Job ID to subscribe to
            websocket: WebSocket connection
        """
        await websocket.accept()

        async with self._lock:
            self._connections[job_id].add(websocket)
            self._reverse_lookup[websocket] = job_id

        logger.info(f"WebSocket connected for job {job_id}. Total connections: {len(self._connections[job_id])}")

    async def disconnect(self, job_id: str, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection.

        Args:
            job_id: Job ID
            websocket: WebSocket connection to remove
        """
        async with self._lock:
            if job_id in self._connections:
                self._connections[job_id].discard(websocket)
                if not self._connections[job_id]:
                    del self._connections[job_id]

            self._reverse_lookup.pop(websocket, None)

        logger.info(f"WebSocket disconnected for job {job_id}")

    async def broadcast(self, job_id: str, message: Dict[str, Any]) -> None:
        """
        Send a message to all connections for a job.

        Args:
            job_id: Job ID to broadcast to
            message: Message dict to send
        """
        connections_to_remove = []

        async with self._lock:
            connections = list(self._connections.get(job_id, set()))

        for websocket in connections:
            try:
                await websocket.send_json(message)
            except WebSocketDisconnect:
                connections_to_remove.append((job_id, websocket))
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")
                connections_to_remove.append((job_id, websocket))

        # Clean up disconnected websockets
        for jid, ws in connections_to_remove:
            await self.disconnect(jid, ws)

    async def get_connection_count(self, job_id: str) -> int:
        """Get number of connections for a job."""
        async with self._lock:
            return len(self._connections.get(job_id, set()))

    async def close_all_connections(self) -> None:
        """Close all WebSocket connections."""
        async with self._lock:
            all_connections = list(self._connections.keys())

        for job_id in all_connections:
            async with self._lock:
                connections = list(self._connections.get(job_id, set()))

            for websocket in connections:
                try:
                    await websocket.close()
                except Exception:
                    pass

            async with self._lock:
                if job_id in self._connections:
                    del self._connections[job_id]


class JobStatusPublisher:
    """
    Publishes job status updates to Redis pub/sub channel.
    Works with RedisJobQueue to broadcast status changes.
    """

    CHANNEL_PREFIX = "job_status:"

    def __init__(self):
        self._redis = None
        self._pubsub = None
        self._manager = None

    async def initialize(self, manager: ConnectionManager) -> None:
        """Initialize publisher with connection manager."""
        self._manager = manager

    async def publish_status(
        self,
        job_id: str,
        status: str,
        progress: int = 0,
        stage: str = "",
        message: str = "",
        request_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Publish job status update.

        Args:
            job_id: Job ID
            status: Job status (pending, running, completed, failed)
            progress: Progress percentage (0-100)
            stage: Processing stage
            message: Progress message
            request_id: Request ID for correlation
            data: Additional data
        """
        # Create WebSocket message
        ws_message = {
            "type": "job_status",
            "job_id": job_id,
            "status": status,
            "progress": progress,
            "stage": stage,
            "message": message,
            "request_id": request_id or "",
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        # Broadcast to local WebSocket connections
        if self._manager:
            await self._manager.broadcast(job_id, ws_message)

        # Publish to Redis for distributed systems
        await self._publish_to_redis(job_id, ws_message)

    async def _publish_to_redis(self, job_id: str, message: Dict[str, Any]) -> None:
        """Publish message to Redis pub/sub channel."""
        try:
            from services.redis_queue import get_redis_queue

            redis_queue = await get_redis_queue()
            if await redis_queue.is_connected():
                channel = f"{self.CHANNEL_PREFIX}{job_id}"
                await redis_queue._redis.publish(channel, json.dumps(message))
        except Exception as e:
            logger.debug(f"Could not publish to Redis: {e}")

    async def subscribe_to_job(self, job_id: str) -> None:
        """Subscribe to Redis channel for job updates."""
        try:
            from services.redis_queue import get_redis_queue

            redis_queue = await get_redis_queue()
            if not await redis_queue.is_connected():
                return

            pubsub = redis_queue._redis.pubsub()
            channel = f"{self.CHANNEL_PREFIX}{job_id}"
            await pubsub.subscribe(channel)

            # Start listening for messages
            asyncio.create_task(self._listen_for_updates(job_id, pubsub))
        except Exception as e:
            logger.error(f"Failed to subscribe to Redis channel: {e}")

    async def _listen_for_updates(self, job_id: str, pubsub) -> None:
        """Listen for Redis pub/sub messages."""
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        if self._manager:
                            await self._manager.broadcast(job_id, data)
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            logger.error(f"Error listening for updates: {e}")
        finally:
            await pubsub.unsubscribe()
            await pubsub.close()


# Global instances
websocket_manager = ConnectionManager()
job_status_publisher = JobStatusPublisher()


async def initialize_websocket_manager() -> None:
    """Initialize global WebSocket manager and publisher."""
    await job_status_publisher.initialize(websocket_manager)
    logger.info("WebSocket manager initialized")


async def shutdown_websocket_manager() -> None:
    """Shutdown WebSocket manager."""
    await websocket_manager.close_all_connections()
    logger.info("WebSocket manager shutdown")
