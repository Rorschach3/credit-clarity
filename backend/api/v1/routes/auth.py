"""
Authentication endpoints for JWT token management and testing
"""
import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from core.security import (
    get_supabase_user, 
    validate_token_only, 
    require_admin_access,
    create_test_token_endpoint,
    extract_user_id_from_token,
    is_token_expired
)
from core.config import get_settings
from core.jwt_auth import create_development_token, JWTValidationError
from schemas.responses import APIResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)
settings = get_settings()


@router.get("/me", response_model=APIResponse[Dict[str, Any]])
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """
    Get current authenticated user information.
    """
    # Remove sensitive fields before returning
    safe_user_info = {
        "id": current_user.get("id"),
        "email": current_user.get("email"),
        "role": current_user.get("role"),
        "is_admin": current_user.get("is_admin", False),
        "permissions": current_user.get("permissions", []),
        "aud": current_user.get("aud"),
        "exp": current_user.get("exp"),
    }
    
    return APIResponse[Dict[str, Any]](
        success=True,
        data=safe_user_info,
        message="User information retrieved successfully"
    )


@router.get("/validate", response_model=APIResponse[Dict[str, str]])
async def validate_current_token(
    current_user: Dict[str, Any] = Depends(validate_token_only)
):
    """
    Validate the current JWT token (strict validation, no fallback).
    """
    return APIResponse[Dict[str, str]](
        success=True,
        data={
            "status": "valid",
            "user_id": current_user.get("id"),
            "email": current_user.get("email")
        },
        message="Token is valid"
    )


@router.get("/dev-token", response_model=APIResponse[Dict[str, str]])
async def create_development_tokens():
    """
    Create development JWT tokens for testing.
    Only available in development mode.
    """
    if not settings.is_development():
        raise HTTPException(
            status_code=403,
            detail="Development tokens only available in development mode"
        )
    
    try:
        tokens = await create_test_token_endpoint()
        
        return APIResponse[Dict[str, str]](
            success=True,
            data=tokens,
            message="Development tokens created successfully"
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to create development tokens: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create development tokens"
        )


@router.post("/custom-token", response_model=APIResponse[Dict[str, str]])
async def create_custom_development_token(
    user_id: str,
    email: str,
    role: str = "authenticated",
    admin_user: Dict[str, Any] = Depends(require_admin_access)
):
    """
    Create a custom development token with specified parameters.
    Requires admin access.
    """
    if not settings.is_development():
        raise HTTPException(
            status_code=403,
            detail="Custom token creation only available in development mode"
        )
    
    try:
        token = create_development_token(user_id, email, role)
        
        logger.info(
            f"🔧 Custom token created by admin {admin_user.get('email')} "
            f"for user {email} (role: {role})"
        )
        
        return APIResponse[Dict[str, str]](
            success=True,
            data={
                "token": token,
                "user_id": user_id,
                "email": email,
                "role": role
            },
            message="Custom development token created"
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to create custom token: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create custom token"
        )


@router.get("/admin/users", response_model=APIResponse[Dict[str, Any]])
async def get_admin_user_stats(
    admin_user: Dict[str, Any] = Depends(require_admin_access)
):
    """
    Get user statistics (admin only).
    Demonstrates admin-only endpoint.
    """
    try:
        # In a real application, you would query the database
        # For now, return mock statistics
        stats = {
            "total_users": 150,
            "active_users_last_30_days": 45,
            "admin_users": 3,
            "new_users_this_month": 12,
            "user_roles": {
                "authenticated": 140,
                "premium": 7,
                "admin": 3
            }
        }
        
        return APIResponse[Dict[str, Any]](
            success=True,
            data=stats,
            message="User statistics retrieved"
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get user stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user statistics"
        )


@router.post("/token/check", response_model=APIResponse[Dict[str, Any]])
async def check_token_status(
    token: str,
    admin_user: Dict[str, Any] = Depends(require_admin_access)
):
    """
    Check the status of any JWT token (admin only).
    Useful for debugging and token management.
    """
    try:
        # Check if token is expired
        expired = await is_token_expired(token)
        
        # Try to extract user ID
        user_id = await extract_user_id_from_token(token)
        
        # Try full validation
        validation_result = "unknown"
        validation_error = None
        
        try:
            from core.jwt_auth import jwt_validator
            await jwt_validator.validate_token(token)
            validation_result = "valid"
        except JWTValidationError as e:
            validation_result = "invalid"
            validation_error = str(e)
        except Exception as e:
            validation_result = "error"
            validation_error = str(e)
        
        result = {
            "is_expired": expired,
            "user_id": user_id,
            "validation_status": validation_result,
            "validation_error": validation_error,
            "token_length": len(token),
            "token_prefix": token[:20] + "..." if len(token) > 20 else token
        }
        
        return APIResponse[Dict[str, Any]](
            success=True,
            data=result,
            message="Token status checked"
        )
        
    except Exception as e:
        logger.error(f"❌ Token check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to check token status"
        )


@router.get("/health")
async def auth_health_check():
    """
    Health check endpoint for authentication service.
    """
    try:
        # Test JWKS connectivity in production
        health_status = {
            "status": "healthy",
            "environment": settings.environment,
            "jwt_validation": "available",
            "supabase_configured": bool(settings.supabase_url and settings.supabase_anon_key)
        }
        
        # Test JWKS fetch in production
        if settings.is_production() and settings.supabase_url:
            try:
                from core.jwt_auth import jwt_validator
                await jwt_validator.get_jwks()
                health_status["jwks_connectivity"] = "ok"
            except Exception as e:
                health_status["jwks_connectivity"] = "failed"
                health_status["jwks_error"] = str(e)
                health_status["status"] = "degraded"
        
        return JSONResponse(content=health_status)
        
    except Exception as e:
        logger.error(f"❌ Auth health check failed: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e)
            },
            status_code=503
        )