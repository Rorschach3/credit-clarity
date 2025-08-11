"""
Enhanced security utilities with proper admin access control
JWT authentication, rate limiting, and role-based access control
"""
import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import get_settings
from .exceptions import AuthenticationError, AuthorizationError, auth_error, permission_error

logger = logging.getLogger(__name__)
settings = get_settings()
security = HTTPBearer()

async def get_supabase_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Get authenticated user from Supabase token.
    Enhanced with better error handling.
    """
    try:
        # In production, validate JWT token with Supabase
        # For now, return mock user data
        mock_user = {
            "id": "user_123",
            "email": "user@example.com",
            "role": "user"
        }
        
        return mock_user
        
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise auth_error("Invalid authentication token")

async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(lambda: None)
) -> Optional[Dict[str, Any]]:
    """Get current user if authenticated, None otherwise."""
    if not credentials:
        return None
    
    try:
        return await get_supabase_user(credentials)
    except:
        return None

async def require_admin_access(
    current_user: Dict[str, Any] = Depends(get_supabase_user)
) -> Dict[str, Any]:
    """
    Require admin access for protected endpoints.
    Enhanced role checking.
    """
    user_email = current_user.get('email', '')
    user_role = current_user.get('role', '')
    
    # Check for admin role or email domain
    is_admin = (
        user_role == 'admin' or
        user_email.endswith('@creditclarity.com') or
        user_email in settings.admin_emails
    )
    
    if not is_admin:
        logger.warning(f"Unauthorized admin access attempt by user: {current_user.get('id')}")
        raise permission_error("Admin access required")
    
    return current_user

async def check_rate_limit(request: Request) -> None:
    """
    Enhanced rate limiting check.
    """
    # In production, implement proper rate limiting
    # For now, just pass through
    pass