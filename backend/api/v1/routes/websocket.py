"""
WebSocket endpoints for real-time communication
Handles WebSocket connections, authentication, and real-time events
"""
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from fastapi.responses import JSONResponse

from services.realtime_service import realtime_service, RealtimeEvent, EventType
from core.security import get_supabase_user
from datetime import datetime

router = APIRouter(prefix="/ws", tags=["WebSocket"])
logger = logging.getLogger(__name__)


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token"),
    client_type: str = Query(default="web", description="Client type (web, mobile, etc.)"),
    app_version: str = Query(default="unknown", description="Application version")
):
    """
    WebSocket endpoint for real-time communication.
    
    Query Parameters:
    - token: JWT authentication token
    - client_type: Type of client connecting (web, mobile, etc.)
    - app_version: Version of the client application
    
    Events sent to client:
    - job:progress: Job processing progress updates
    - job:completed: Job completion notifications
    - job:failed: Job failure notifications
    - credit:score_updated: Credit score change notifications
    - tradelines:updated: Tradeline updates
    - notification: General notifications
    - system:status: System status messages
    """
    
    metadata = {
        "client_type": client_type,
        "app_version": app_version,
        "connected_at": datetime.now().isoformat(),
        "ip_address": websocket.client.host if websocket.client else "unknown"
    }
    
    logger.info(f"🔌 WebSocket connection attempt from {metadata['ip_address']}")
    
    try:
        await realtime_service.handle_connection(websocket, token, metadata)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")


@router.get("/stats")
async def get_realtime_stats(
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """
    Get real-time service statistics.
    Requires authentication.
    """
    try:
        stats = realtime_service.get_stats()
        
        # Add user-specific information if admin
        if current_user.get('is_admin', False):
            stats['connected_users_list'] = realtime_service.connection_manager.get_connected_users()
            stats['user_connection_details'] = {
                user_id: realtime_service.connection_manager.get_connection_count(user_id)
                for user_id in stats['connected_users_list']
            }
        
        return JSONResponse(content={
            "success": True,
            "data": stats,
            "message": "Real-time service statistics retrieved"
        })
        
    except Exception as e:
        logger.error(f"Failed to get real-time stats: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Failed to retrieve statistics",
                "detail": str(e)
            }
        )


@router.post("/test-event")
async def send_test_event(
    event_type: str,
    message: str,
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """
    Send a test event to the current user's WebSocket connections.
    Useful for testing real-time functionality.
    """
    try:
        user_id = current_user.get('id')
        
        # Create test event
        test_event = RealtimeEvent(
            event_type=EventType.NOTIFICATION,
            user_id=user_id,
            data={
                "type": "test",
                "event_type": event_type,
                "message": message,
                "sent_by": "test_endpoint"
            },
            timestamp=datetime.now()
        )
        
        # Send to user
        await realtime_service.connection_manager.send_to_user(user_id, test_event)
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "event_id": test_event.event_id,
                "user_id": user_id,
                "message": "Test event sent successfully"
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to send test event: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Failed to send test event",
                "detail": str(e)
            }
        )


@router.post("/broadcast")
async def broadcast_message(
    message: str,
    event_type: str = "notification",
    admin_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """
    Broadcast a message to all connected users.
    Requires admin access.
    """
    # Check admin access
    if not admin_user.get('is_admin', False):
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "error": "Admin access required"
            }
        )
    
    try:
        # Create broadcast event
        broadcast_event = RealtimeEvent(
            event_type=EventType.NOTIFICATION,
            user_id="system",  # System-generated event
            data={
                "type": "broadcast",
                "event_type": event_type,
                "message": message,
                "sent_by": admin_user.get('email', 'admin'),
                "is_system_message": True
            },
            timestamp=datetime.now()
        )
        
        # Broadcast to all users
        await realtime_service.connection_manager.broadcast(broadcast_event)
        
        stats = realtime_service.get_stats()
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "event_id": broadcast_event.event_id,
                "message": "Broadcast sent successfully",
                "recipients": stats['connected_users'],
                "total_connections": stats['total_connections']
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to broadcast message: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Failed to broadcast message",
                "detail": str(e)
            }
        )


@router.get("/health")
async def websocket_health_check():
    """
    Health check endpoint for WebSocket service.
    """
    try:
        stats = realtime_service.get_stats()
        
        health_status = {
            "status": "healthy",
            "service": "websocket",
            "connections": stats['total_connections'],
            "connected_users": stats['connected_users'],
            "timestamp": datetime.now().isoformat()
        }
        
        return JSONResponse(content=health_status)
        
    except Exception as e:
        logger.error(f"WebSocket health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "websocket",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )