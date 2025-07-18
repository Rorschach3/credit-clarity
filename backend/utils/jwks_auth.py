"""
JWKS-based JWT authentication for Supabase tokens
Implements secure JWT verification using JSON Web Key Set (JWKS)
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from jose.backends import RSAKey
import aiohttp
import asyncio
from functools import lru_cache

# Configure logging
logger = logging.getLogger(__name__)

# HTTP Bearer token extractor
security = HTTPBearer()

# Cache for JWKS data (10 minutes as recommended by Supabase)
JWKS_CACHE_DURATION = 600  # 10 minutes in seconds
jwks_cache = {"data": None, "timestamp": None}

class JWKSAuthenticator:
    """
    Handles JWT authentication using JWKS (JSON Web Key Set)
    """
    
    def __init__(self, supabase_url: str):
        self.supabase_url = supabase_url.rstrip('/')
        self.jwks_url = f"{self.supabase_url}/auth/v1/.well-known/jwks.json"
        self.session = None
        
    async def _get_http_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10),
                headers={"User-Agent": "CreditClarity-Backend/1.0"}
            )
        return self.session
    
    async def _fetch_jwks(self) -> Dict[str, Any]:
        """
        Fetch JWKS from Supabase endpoint with caching
        """
        global jwks_cache
        
        # Check cache first
        if (jwks_cache["data"] and jwks_cache["timestamp"] and 
            (datetime.now() - jwks_cache["timestamp"]).total_seconds() < JWKS_CACHE_DURATION):
            logger.debug("Using cached JWKS data")
            return jwks_cache["data"]
        
        try:
            session = await self._get_http_session()
            async with session.get(self.jwks_url) as response:
                if response.status == 200:
                    jwks_data = await response.json()
                    
                    # Update cache
                    jwks_cache["data"] = jwks_data
                    jwks_cache["timestamp"] = datetime.now()
                    
                    logger.info(f"Successfully fetched JWKS with {len(jwks_data.get('keys', []))} keys")
                    return jwks_data
                else:
                    logger.error(f"Failed to fetch JWKS: HTTP {response.status}")
                    raise HTTPException(
                        status_code=503,
                        detail="Authentication service unavailable"
                    )
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching JWKS: {e}")
            raise HTTPException(
                status_code=503,
                detail="Authentication service unavailable"
            )
        except Exception as e:
            logger.error(f"Unexpected error fetching JWKS: {e}")
            raise HTTPException(
                status_code=500,
                detail="Internal authentication error"
            )
    
    def _find_key(self, jwks_data: Dict[str, Any], kid: str) -> Optional[Dict[str, Any]]:
        """
        Find the correct key from JWKS data using key ID (kid)
        """
        keys = jwks_data.get("keys", [])
        for key in keys:
            if key.get("kid") == kid:
                return key
        return None
    
    async def verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """
        Verify JWT token using JWKS
        Returns the decoded payload if valid
        """
        try:
            # Decode header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            if not kid:
                logger.warning("JWT token missing key ID (kid)")
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token: missing key ID"
                )
            
            # Fetch JWKS
            jwks_data = await self._fetch_jwks()
            
            # Find the correct key
            key_data = self._find_key(jwks_data, kid)
            if not key_data:
                logger.warning(f"Key ID {kid} not found in JWKS")
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token: key not found"
                )
            
            # Verify token
            payload = jwt.decode(
                token,
                key_data,
                algorithms=["RS256", "ES256", "HS256"],  # Support common algorithms
                audience=None,  # Supabase doesn't use audience validation
                issuer=f"{self.supabase_url}/auth/v1"
            )
            
            # Validate required claims
            if not payload.get("sub"):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token: missing subject"
                )
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
                raise HTTPException(
                    status_code=401,
                    detail="Token expired"
                )
            
            logger.debug(f"Successfully verified JWT for user {payload.get('sub')}")
            return payload
            
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )
        except Exception as e:
            logger.error(f"Unexpected error verifying JWT: {e}")
            raise HTTPException(
                status_code=500,
                detail="Internal authentication error"
            )
    
    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()

# Global authenticator instance
authenticator = None

def get_authenticator() -> JWKSAuthenticator:
    """Get or create global authenticator instance"""
    global authenticator
    if authenticator is None:
        supabase_url = os.getenv("SUPABASE_URL", "https://gywohmbqohytziwsjrps.supabase.co")
        authenticator = JWKSAuthenticator(supabase_url)
    return authenticator

# FastAPI dependencies
async def get_current_user_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency to get current user from JWT token
    """
    auth = get_authenticator()
    return await auth.verify_jwt_token(credentials.credentials)

async def get_current_user_id_jwt(
    user_data: Dict[str, Any] = Depends(get_current_user_jwt)
) -> str:
    """
    FastAPI dependency to get current user ID from JWT token
    """
    return user_data.get("sub")

async def get_current_user_role_jwt(
    user_data: Dict[str, Any] = Depends(get_current_user_jwt)
) -> str:
    """
    FastAPI dependency to get current user role from JWT token
    """
    return user_data.get("role", "authenticated")

# Admin role checker
async def require_admin_role(
    user_data: Dict[str, Any] = Depends(get_current_user_jwt)
) -> Dict[str, Any]:
    """
    FastAPI dependency to require admin role
    """
    role = user_data.get("role", "authenticated")
    if role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return user_data

# Authenticated user checker
async def require_authenticated_user(
    user_data: Dict[str, Any] = Depends(get_current_user_jwt)
) -> Dict[str, Any]:
    """
    FastAPI dependency to require authenticated user
    """
    return user_data

# Cleanup function for FastAPI shutdown
async def cleanup_auth():
    """Cleanup function to close HTTP sessions"""
    global authenticator
    if authenticator:
        await authenticator.close()
        authenticator = None

# Backward compatibility wrapper
async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[str]:
    """
    Backward compatibility wrapper for existing code
    """
    try:
        user_data = await get_current_user_jwt(credentials)
        return user_data.get("sub")
    except HTTPException:
        # For development, allow fallback to None
        logger.warning("JWT authentication failed, falling back to None")
        return None

# Rate limiting (from original auth.py)
from typing import List

class RateLimiter:
    def __init__(self, max_requests: int, window_minutes: int):
        self.max_requests = max_requests
        self.window_minutes = window_minutes
        self.client_requests: Dict[str, List[datetime]] = {}

    def allow_request(self, client_id: str) -> bool:
        now = datetime.now()
        if client_id not in self.client_requests:
            self.client_requests[client_id] = []

        # Remove old requests outside the window
        self.client_requests[client_id] = [
            req_time for req_time in self.client_requests[client_id]
            if now - req_time < timedelta(minutes=self.window_minutes)
        ]

        if len(self.client_requests[client_id]) < self.max_requests:
            self.client_requests[client_id].append(now)
            return True
        return False