"""
API v1 Router
Consolidates all v1 endpoints into a single router
"""
from fastapi import APIRouter

from .routes import health, processing, processing_v2, tradelines, admin, auth

# Create v1 router
v1_router = APIRouter(prefix="/v1")

# Include all route modules
v1_router.include_router(health.router)
v1_router.include_router(processing.router)
v1_router.include_router(processing_v2.router)  # A/B testing enabled V2 processing
v1_router.include_router(tradelines.router)
v1_router.include_router(admin.router)
v1_router.include_router(auth.router)

# Add any v1-specific middleware or configuration here
@v1_router.middleware("http")
async def add_version_header(request, call_next):
    """Add API version header to all v1 responses."""
    response = await call_next(request)
    response.headers["X-API-Version"] = "1.0"
    response.headers["X-API-Revision"] = "2025.01"
    return response