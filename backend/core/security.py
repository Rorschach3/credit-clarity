"""
Enhanced security utilities with proper admin access control
JWT authentication, rate limiting, and role-based access control
"""
import logging
import time
import os
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.jwt_auth import SupabaseJWTValidator, JWTValidationError, jwt_validator
from core.exceptions import AuthenticationError, AuthorizationError
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize the security scheme
security = HTTPBearer()

# Error helper functions
def auth_error(detail: str) -> AuthenticationError:
    """Create authentication error with consistent logging"""
    logger.warning(f"🔒 Authentication error: {detail}")
    return AuthenticationError(detail)

def permission_error(detail: str) -> AuthorizationError:
    """Create permission error with consistent logging"""
    logger.warning(f"🚫 Permission error: {detail}")
    return AuthorizationError(detail)

async def get_supabase_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Enhanced dependency to get the current user from Supabase JWT token.
    Provides detailed validation and error handling with development bypass.
    """
    # Development bypass if enabled
    if settings.environment == "development" and os.getenv("BYPASS_AUTH", "false").lower() == "true":
        logger.warning("🚨 BYPASSING AUTHENTICATION - DEVELOPMENT MODE ONLY")
        return {
            "user_id": "dev-user-123",
            "email": "dev@creditclarity.com",
            "role": "user",
            "is_admin": True,  # For development access
            "bypass": True
        }
    
    if not credentials:
        logger.warning("🔒 No authorization credentials provided")
        raise auth_error("Authorization credentials required")
    
    token = credentials.credentials
    if not token:
        logger.warning("🔒 No token in authorization credentials")
        raise auth_error("Authorization token required")
    
    try:
        logger.debug("🔍 Validating JWT token...")
        user_info = await jwt_validator.extract_user_info(token)
        
        if not user_info.get('user_id'):
            logger.error("❌ No user_id in token payload")
            raise auth_error("Invalid token: missing user ID")
        
        # Enhanced validation
        if not user_info.get('email'):
            logger.warning("⚠️ No email in token payload")
        
        logger.info(f"✅ User authenticated: {user_info.get('user_id')} ({user_info.get('email', 'no-email')})")
        return user_info
        
    except JWTValidationError as e:
        logger.warning(f"🔒 JWT validation failed: {e}")
        # In development, provide more detailed error info
        if settings.environment == "development":
            raise auth_error(f"JWT validation failed: {str(e)}")
        raise auth_error("Invalid authentication token")
    except Exception as e:
        logger.error(f"❌ Unexpected authentication error: {e}")
        if settings.environment == "development":
            raise auth_error(f"Authentication failed: {str(e)}")
        raise auth_error("Authentication failed")

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[Dict[str, Any]]:
    """
    Get current user if authenticated, None otherwise.
    Enhanced with better error handling and logging.
    """
    if not credentials or not credentials.credentials:
        logger.debug("🔍 No credentials provided for optional auth")
        return None
    
    try:
        user_info = await jwt_validator.extract_user_info(credentials.credentials)
        logger.debug(f"✅ Optional auth successful: {user_info.get('user_id')}")
        return user_info
    except JWTValidationError as e:
        logger.debug(f"🔒 Optional auth failed (JWT): {e}")
        return None
    except Exception as e:
        logger.warning(f"⚠️ Optional auth failed (unexpected): {e}")
        return None

async def require_admin_access(
    current_user: Dict[str, Any] = Depends(get_supabase_user)
) -> Dict[str, Any]:
    """
    Require admin access for protected endpoints.
    Enhanced role checking with JWT-based permissions.
    """
    user_email = current_user.get('email', '')
    user_role = current_user.get('role', '')
    is_admin = current_user.get('is_admin', False)
    permissions = current_user.get('permissions', [])
    
    # Check various admin indicators
    # Enhanced admin access validation
    admin_email_domains = getattr(settings, 'admin_email_domains', ['@creditclarity.com'])
    admin_emails = getattr(settings, 'admin_emails', [])
    
    admin_check = (
        is_admin or
        user_role in ['admin', 'superuser'] or
        any(user_email.endswith(domain) for domain in admin_email_domains) or
        user_email in admin_emails or
        'admin:users' in permissions or
        'admin:all' in permissions
    )
    
    if not admin_check:
        logger.warning(f"🚫 Unauthorized admin access attempt by user: {current_user.get('id')} ({user_email})")
        raise permission_error("Admin access required")
    
    logger.debug(f"✅ Admin access granted to: {user_email}")
    return current_user

async def check_rate_limit(request: Request) -> None:
    """
    Enhanced rate limiting check.
    """
    # In production, implement proper rate limiting
    # For now, just pass through
    pass


async def validate_token_only(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Validate JWT token without fallback options.
    Used for strict authentication scenarios with enhanced error reporting.
    """
    if not credentials or not credentials.credentials:
        raise auth_error("Authentication token required")
    
    try:
        token = credentials.credentials
        
        # Additional token format validation
        if len(token) < 10:
            raise auth_error("Invalid token format")
        
        user_info = await jwt_validator.extract_user_info(token)
        
        # Enhanced user info validation
        required_fields = ['user_id', 'email']
        missing_fields = [field for field in required_fields if not user_info.get(field)]
        if missing_fields:
            logger.warning(f"⚠️ Token missing required fields: {missing_fields}")
        
        logger.debug(f"✅ Strict token validation successful: {user_info.get('email')}")
        return user_info
        
    except JWTValidationError as e:
        logger.warning(f"🔒 Strict token validation failed: {e}")
        raise auth_error(f"Token validation failed: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Unexpected token validation error: {e}")
        raise auth_error(f"Token validation failed: {str(e)}")


def require_permission(permission: str):
    """
    Decorator to require specific permission for endpoint access.
    
    Usage:
    @app.get("/admin/data")
    async def get_admin_data(user: Dict = Depends(require_permission("admin:users"))):
        ...
    """
    async def permission_dependency(
        current_user: Dict[str, Any] = Depends(get_supabase_user)
    ) -> Dict[str, Any]:
        user_permissions = current_user.get('permissions', [])
        
        if permission not in user_permissions:
            logger.warning(
                f"🚫 Permission denied: {current_user.get('email')} lacks '{permission}'"
            )
            raise permission_error(f"Permission required: {permission}")
        
        return current_user
    
    return permission_dependency


async def create_test_token_endpoint() -> Dict[str, str]:
    """
    Development endpoint to create test JWT tokens.
    Only available in development mode.
    """
    if not getattr(settings, 'environment', 'production') == 'development':
        raise HTTPException(
            status_code=403,
            detail="Test token creation only available in development"
        )
    
    try:
        # Create test tokens for different user types
        user_token = create_development_token(
            user_id="11111111-1111-1111-1111-111111111111",
            email="test@creditclarity.com",
            role="authenticated"
        )
        
        admin_token = create_development_token(
            user_id="22222222-2222-2222-2222-222222222222", 
            email="admin@creditclarity.com",
            role="admin"
        )
        
        return {
            "user_token": user_token,
            "admin_token": admin_token,
            "note": "These tokens are for development testing only"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to create test tokens: {e}")
        raise HTTPException(status_code=500, detail="Failed to create test tokens")


# Token validation helpers for external use
async def extract_user_id_from_token(token: str) -> Optional[str]:
    """Extract user ID from token without full validation."""
    try:
        user_info = await jwt_validator.extract_user_info(token)
        return user_info.get('id')
    except Exception:
        return None


async def is_token_expired(token: str) -> bool:
    """Check if token is expired without full validation."""
    try:
        await jwt_validator.validate_token(token)
        return False
    except JWTValidationError as e:
        return "expired" in str(e).lower()
    except Exception:
        return True