"""
API v1 Router
Consolidates all v1 endpoints into a single router
"""
from fastapi import APIRouter

from .routes import health, processing, processing_v2, tradelines, admin, auth, websocket, monitoring

# Create v1 router
v1_router = APIRouter(prefix="/v1")

# Include all route modules
v1_router.include_router(health.router)
v1_router.include_router(processing.router)
v1_router.include_router(processing_v2.router)  # A/B testing enabled V2 processing
v1_router.include_router(tradelines.router)
v1_router.include_router(admin.router)
v1_router.include_router(auth.router)  # JWT authentication endpoints
v1_router.include_router(websocket.router)  # WebSocket real-time endpoints
v1_router.include_router(monitoring.router)  # Monitoring and telemetry endpoints

# Export the router for use by the app factory
api_router = v1_router