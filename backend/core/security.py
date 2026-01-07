"""
Enhanced security utilities with proper admin access control
JWT authentication, rate limiting, and role-based access control
"""
import json
import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
try:
    import jwt
except ImportError:  # pragma: no cover - depends on runtime environment
    jwt = None

from .config import get_settings
from .exceptions import AuthenticationError, AuthorizationError, auth_error, permission_error

logger = logging.getLogger(__name__)
settings = get_settings()
security = HTTPBearer()
supabase_client: Optional[Client] = None

if settings.supabase_url and (settings.supabase_service_role_key or settings.supabase_anon_key):
    supabase_key = settings.supabase_service_role_key or settings.supabase_anon_key
    try:
        supabase_client = create_client(settings.supabase_url, supabase_key)
        logger.info("✅ Supabase auth client initialized")
    except Exception as e:
        logger.error(f"❌ Supabase auth client initialization failed: {e}")
        supabase_client = None

def _load_jwk_set() -> Dict[str, Any]:
    if not jwt:
        return {}
    if settings.supabase_jwt_jwk:
        return {"keys": [json.loads(settings.supabase_jwt_jwk)]}
    if settings.supabase_jwt_jwks:
        return json.loads(settings.supabase_jwt_jwks)
    return {}

def _get_public_key_for_token(token: str) -> Optional[Any]:
    if not jwt:
        return None
    jwk_set = _load_jwk_set()
    if not jwk_set:
        return None

    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    keys = jwk_set.get("keys", [])
    for key in keys:
        if kid and key.get("kid") != kid:
            continue
        return jwt.algorithms.ECAlgorithm.from_jwk(json.dumps(key))

    return None

def verify_supabase_jwt(token: str) -> Dict[str, Any]:
    if not jwt and not supabase_client:
        raise auth_error("JWT verification dependencies not available")
    public_key = _get_public_key_for_token(token)
    issuer = settings.supabase_jwt_issuer
    audience = settings.supabase_jwt_audience

    if public_key:
        options = {"verify_aud": bool(audience)}
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["ES256"],
            audience=audience if audience else None,
            issuer=issuer if issuer else None,
            options=options
        )
    elif supabase_client:
        user_response = supabase_client.auth.get_user(token)
        if not user_response or not user_response.user:
            raise auth_error("Invalid or expired authentication token")
        user = user_response.user
        return {
            "id": user.id,
            "email": user.email,
            "role": (user.user_metadata or {}).get("role", "user")
        }
    else:
        raise auth_error("Authentication service unavailable")

    return {
        "id": payload.get("sub"),
        "email": payload.get("email"),
        "role": (payload.get("user_metadata") or {}).get("role", "user")
    }

async def get_supabase_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Get authenticated user from Supabase token.
    Enhanced with better error handling.
    """
    try:
        return verify_supabase_jwt(credentials.credentials)
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
