"""
API v1 Routes
Modular route definitions for different API endpoints
"""
from fastapi import APIRouter

from . import health, processing, processing_v2, tradelines, admin, auth, users

# Create v1 router
v1_router = APIRouter(prefix="/v1")

# Include all route modules
v1_router.include_router(health.router)
v1_router.include_router(processing.router)
v1_router.include_router(processing_v2.router)  # A/B testing enabled V2 processing
v1_router.include_router(tradelines.router)
v1_router.include_router(admin.router)
v1_router.include_router(auth.router, prefix="/auth")
v1_router.include_router(users.router, prefix="/users")