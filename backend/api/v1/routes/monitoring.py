"""
Monitoring endpoints for application telemetry
"""
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from core.security import get_supabase_user

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])
logger = logging.getLogger(__name__)

class MonitoringEvent(BaseModel):
    event: str
    properties: Dict[str, Any]
    timestamp: str
    userId: str = None
    sessionId: str

@router.post("/events")
async def submit_monitoring_events(
    events: List[MonitoringEvent],
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """Submit monitoring events for telemetry"""
    try:
        user_id = current_user.get("id")
        logger.info(f"📊 Received {len(events)} monitoring events from user {user_id}")
        
        # For now, just log the events - could save to database later
        for event in events:
            logger.debug(f"📈 Event: {event.event} - {event.properties}")
        
        return {
            "success": True,
            "message": f"Processed {len(events)} monitoring events",
            "events_processed": len(events)
        }
    
    except Exception as e:
        logger.error(f"❌ Failed to process monitoring events: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process monitoring events")

@router.get("/health")
async def monitoring_health():
    """Monitoring service health check"""
    return {
        "status": "healthy",
        "service": "monitoring",
        "timestamp": "2023-01-01T00:00:00Z"
    }