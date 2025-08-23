"""
Real-time WebSocket service for Credit Clarity
Provides real-time updates for job progress, credit score changes, and notifications
"""
import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from core.jwt_auth import jwt_validator, JWTValidationError
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EventType(Enum):
    """Real-time event types."""
    JOB_PROGRESS = "job:progress"
    JOB_COMPLETED = "job:completed"
    JOB_FAILED = "job:failed"
    CREDIT_SCORE_UPDATED = "credit:score_updated"
    TRADELINES_UPDATED = "tradelines:updated"
    NOTIFICATION = "notification"
    SYSTEM_STATUS = "system:status"


@dataclass
class RealtimeEvent:
    """Real-time event data structure."""
    event_type: EventType
    user_id: str
    data: Dict[str, Any]
    timestamp: datetime
    event_id: str = None
    
    def __post_init__(self):
        if self.event_id is None:
            self.event_id = str(uuid.uuid4())
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps({
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "event_id": self.event_id
        })


@dataclass
class JobProgressEvent:
    """Job progress update event."""
    job_id: str
    progress: int
    message: str
    estimated_time_remaining: Optional[int] = None
    stage: Optional[str] = None
    tradelines_found: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CreditScoreUpdate:
    """Credit score update event."""
    old_score: int
    new_score: int
    change: int
    bureau: str
    factors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ConnectionManager:
    """Manages WebSocket connections for real-time communication."""
    
    def __init__(self):
        # Map of user_id -> set of WebSocket connections
        self.user_connections: Dict[str, Set[WebSocket]] = {}
        # Map of WebSocket -> user_id for cleanup
        self.connection_users: Dict[WebSocket, str] = {}
        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str, metadata: Dict[str, Any] = None):
        """Accept new WebSocket connection."""
        await websocket.accept()
        
        # Initialize user connections if needed
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        
        # Add connection
        self.user_connections[user_id].add(websocket)
        self.connection_users[websocket] = user_id
        self.connection_metadata[websocket] = metadata or {}
        
        logger.info(f"✅ WebSocket connected for user {user_id}")
        
        # Send connection confirmation
        await self.send_to_connection(websocket, RealtimeEvent(
            event_type=EventType.SYSTEM_STATUS,
            user_id=user_id,
            data={"status": "connected", "message": "Real-time connection established"},
            timestamp=datetime.now()
        ))
    
    async def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection."""
        user_id = self.connection_users.get(websocket)
        
        if user_id:
            # Remove from user connections
            if user_id in self.user_connections:
                self.user_connections[user_id].discard(websocket)
                
                # Clean up empty user entry
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Remove from connection mappings
            del self.connection_users[websocket]
            del self.connection_metadata[websocket]
            
            logger.info(f"🔌 WebSocket disconnected for user {user_id}")
    
    async def send_to_user(self, user_id: str, event: RealtimeEvent):
        """Send event to all connections for a specific user."""
        if user_id not in self.user_connections:
            logger.debug(f"No connections found for user {user_id}")
            return
        
        connections = list(self.user_connections[user_id])  # Create copy to avoid modification during iteration
        disconnected = []
        
        for connection in connections:
            try:
                await self.send_to_connection(connection, event)
            except Exception as e:
                logger.warning(f"Failed to send to connection: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            await self.disconnect(connection)
    
    async def send_to_connection(self, websocket: WebSocket, event: RealtimeEvent):
        """Send event to specific WebSocket connection."""
        try:
            await websocket.send_text(event.to_json())
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            raise
    
    async def broadcast(self, event: RealtimeEvent, exclude_user: Optional[str] = None):
        """Broadcast event to all connected users."""
        for user_id in list(self.user_connections.keys()):
            if exclude_user and user_id == exclude_user:
                continue
            await self.send_to_user(user_id, event)
    
    def get_connection_count(self, user_id: Optional[str] = None) -> int:
        """Get total connection count or count for specific user."""
        if user_id:
            return len(self.user_connections.get(user_id, set()))
        return sum(len(connections) for connections in self.user_connections.values())
    
    def get_connected_users(self) -> List[str]:
        """Get list of all connected user IDs."""
        return list(self.user_connections.keys())


class RealtimeService:
    """Service for managing real-time events and WebSocket connections."""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.event_history: Dict[str, List[RealtimeEvent]] = {}
        self.max_history_per_user = 100
        
    async def authenticate_websocket(self, websocket: WebSocket, token: str) -> Optional[str]:
        """Authenticate WebSocket connection using JWT token."""
        try:
            user_info = await jwt_validator.extract_user_info(token)
            return user_info.get('id')
        except JWTValidationError as e:
            logger.warning(f"WebSocket authentication failed: {e}")
            await websocket.close(code=4001, reason="Authentication failed")
            return None
        except Exception as e:
            logger.error(f"WebSocket authentication error: {e}")
            await websocket.close(code=4000, reason="Authentication error")
            return None
    
    async def handle_connection(self, websocket: WebSocket, token: str, metadata: Dict[str, Any] = None):
        """Handle new WebSocket connection with authentication."""
        user_id = await self.authenticate_websocket(websocket, token)
        if not user_id:
            return
        
        try:
            await self.connection_manager.connect(websocket, user_id, metadata)
            
            # Send recent event history
            await self.send_recent_events(user_id, websocket)
            
            # Keep connection alive
            await self.connection_loop(websocket, user_id)
            
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {user_id}")
        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {e}")
        finally:
            await self.connection_manager.disconnect(websocket)
    
    async def connection_loop(self, websocket: WebSocket, user_id: str):
        """Keep WebSocket connection alive and handle incoming messages."""
        try:
            while True:
                # Wait for messages from client (like heartbeat)
                message = await websocket.receive_text()
                await self.handle_client_message(websocket, user_id, message)
        except WebSocketDisconnect:
            raise
        except Exception as e:
            logger.error(f"Connection loop error: {e}")
            raise
    
    async def handle_client_message(self, websocket: WebSocket, user_id: str, message: str):
        """Handle incoming message from client."""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'heartbeat':
                await self.connection_manager.send_to_connection(websocket, RealtimeEvent(
                    event_type=EventType.SYSTEM_STATUS,
                    user_id=user_id,
                    data={"type": "heartbeat_ack", "timestamp": time.time()},
                    timestamp=datetime.now()
                ))
            elif message_type == 'subscribe':
                # Handle subscription to specific events
                await self.handle_subscription(websocket, user_id, data.get('events', []))
            
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON message from user {user_id}")
        except Exception as e:
            logger.error(f"Error handling client message: {e}")
    
    async def handle_subscription(self, websocket: WebSocket, user_id: str, event_types: List[str]):
        """Handle client subscription to specific event types."""
        # Store subscription preferences in connection metadata
        self.connection_manager.connection_metadata[websocket]['subscriptions'] = event_types
        
        await self.connection_manager.send_to_connection(websocket, RealtimeEvent(
            event_type=EventType.SYSTEM_STATUS,
            user_id=user_id,
            data={"type": "subscription_confirmed", "events": event_types},
            timestamp=datetime.now()
        ))
    
    async def send_recent_events(self, user_id: str, websocket: WebSocket):
        """Send recent events to newly connected user."""
        if user_id in self.event_history:
            recent_events = self.event_history[user_id][-10:]  # Last 10 events
            for event in recent_events:
                await self.connection_manager.send_to_connection(websocket, event)
    
    async def emit_job_progress(self, user_id: str, job_progress: JobProgressEvent):
        """Emit job progress update to user."""
        event = RealtimeEvent(
            event_type=EventType.JOB_PROGRESS,
            user_id=user_id,
            data=job_progress.to_dict(),
            timestamp=datetime.now()
        )
        
        await self.connection_manager.send_to_user(user_id, event)
        await self.store_event(user_id, event)
    
    async def emit_job_completed(self, user_id: str, job_id: str, result: Dict[str, Any]):
        """Emit job completion notification."""
        event = RealtimeEvent(
            event_type=EventType.JOB_COMPLETED,
            user_id=user_id,
            data={"job_id": job_id, "result": result},
            timestamp=datetime.now()
        )
        
        await self.connection_manager.send_to_user(user_id, event)
        await self.store_event(user_id, event)
    
    async def emit_job_failed(self, user_id: str, job_id: str, error: str):
        """Emit job failure notification."""
        event = RealtimeEvent(
            event_type=EventType.JOB_FAILED,
            user_id=user_id,
            data={"job_id": job_id, "error": error},
            timestamp=datetime.now()
        )
        
        await self.connection_manager.send_to_user(user_id, event)
        await self.store_event(user_id, event)
    
    async def emit_credit_score_update(self, user_id: str, score_update: CreditScoreUpdate):
        """Emit credit score update notification."""
        event = RealtimeEvent(
            event_type=EventType.CREDIT_SCORE_UPDATED,
            user_id=user_id,
            data=score_update.to_dict(),
            timestamp=datetime.now()
        )
        
        await self.connection_manager.send_to_user(user_id, event)
        await self.store_event(user_id, event)
    
    async def emit_tradelines_updated(self, user_id: str, tradelines_data: Dict[str, Any]):
        """Emit tradelines update notification."""
        event = RealtimeEvent(
            event_type=EventType.TRADELINES_UPDATED,
            user_id=user_id,
            data=tradelines_data,
            timestamp=datetime.now()
        )
        
        await self.connection_manager.send_to_user(user_id, event)
        await self.store_event(user_id, event)
    
    async def emit_notification(self, user_id: str, notification: Dict[str, Any]):
        """Emit general notification to user."""
        event = RealtimeEvent(
            event_type=EventType.NOTIFICATION,
            user_id=user_id,
            data=notification,
            timestamp=datetime.now()
        )
        
        await self.connection_manager.send_to_user(user_id, event)
        await self.store_event(user_id, event)
    
    async def store_event(self, user_id: str, event: RealtimeEvent):
        """Store event in user's history."""
        if user_id not in self.event_history:
            self.event_history[user_id] = []
        
        self.event_history[user_id].append(event)
        
        # Limit history size
        if len(self.event_history[user_id]) > self.max_history_per_user:
            self.event_history[user_id] = self.event_history[user_id][-self.max_history_per_user:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get real-time service statistics."""
        return {
            "total_connections": self.connection_manager.get_connection_count(),
            "connected_users": len(self.connection_manager.get_connected_users()),
            "users_with_history": len(self.event_history),
            "total_stored_events": sum(len(events) for events in self.event_history.values())
        }


# Global real-time service instance
realtime_service = RealtimeService()


# Convenience functions for easy integration
async def notify_job_progress(user_id: str, job_id: str, progress: int, message: str, **kwargs):
    """Convenience function to notify job progress."""
    job_progress = JobProgressEvent(
        job_id=job_id,
        progress=progress,
        message=message,
        estimated_time_remaining=kwargs.get('eta'),
        stage=kwargs.get('stage'),
        tradelines_found=kwargs.get('tradelines_found')
    )
    await realtime_service.emit_job_progress(user_id, job_progress)


async def notify_job_completion(user_id: str, job_id: str, result: Dict[str, Any]):
    """Convenience function to notify job completion."""
    await realtime_service.emit_job_completed(user_id, job_id, result)


async def notify_job_failure(user_id: str, job_id: str, error: str):
    """Convenience function to notify job failure."""
    await realtime_service.emit_job_failed(user_id, job_id, error)


async def notify_credit_score_change(user_id: str, old_score: int, new_score: int, bureau: str, factors: List[str]):
    """Convenience function to notify credit score changes."""
    score_update = CreditScoreUpdate(
        old_score=old_score,
        new_score=new_score,
        change=new_score - old_score,
        bureau=bureau,
        factors=factors
    )
    await realtime_service.emit_credit_score_update(user_id, score_update)