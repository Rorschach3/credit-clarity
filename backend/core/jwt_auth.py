"""
JWT Authentication utilities for Supabase integration
Handles JWT token validation, user extraction, and role-based access control
"""
import logging
import httpx
import json
from typing import Dict, Any, Optional, List
from jose import jwt, jwk, JWTError
try:
    import jwcrypto
    JWCRYPTO_AVAILABLE = True
except ImportError:
    JWCRYPTO_AVAILABLE = False
from fastapi import HTTPException
import asyncio
from datetime import datetime, timedelta
from functools import lru_cache
import os
import time

from fastapi import HTTPException, status
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class JWTValidationError(Exception):
    """Custom exception for JWT validation errors."""
    pass


class SupabaseJWTValidator:
    """
    Supabase JWT token validator with caching and performance optimizations.
    Validates tokens against Supabase's public keys and extracts user information.
    """
    
    def __init__(self, supabase_url: Optional[str] = None, jwt_secret: Optional[str] = None):
        self.jwks_cache: Optional[Dict] = None
        self.jwks_cache_expiry: Optional[datetime] = None
        self.cache_duration = timedelta(hours=24)  # Cache JWKS for 24 hours
        
        # Supabase JWT configuration
        self.supabase_url = supabase_url or settings.supabase_url
        self.jwt_secret = jwt_secret or settings.jwt_secret  # For local development
        
        if not self.supabase_url:
            logger.warning("⚠️ SUPABASE_URL not configured - JWT validation may fail")
    
    @property
    def jwks_url(self) -> str:
        """Get the JWKS URL for Supabase."""
        if not self.supabase_url:
            raise JWTValidationError("Supabase URL not configured")
        return f"{self.supabase_url.rstrip('/')}/auth/v1/jwks"
    
    async def get_jwks(self) -> Dict[str, Any]:
        """Get JWKS with caching and better error handling"""
        # Check cache first
        if (self.jwks_cache and self.jwks_cache_expiry and 
            datetime.now() < self.jwks_cache_expiry):
            logger.info("🔄 Using cached JWKS")
            return self.jwks_cache
            
        logger.info(f"🔑 Fetching JWKS from: {self.jwks_url}")
        
        # Try multiple times with exponential backoff
        max_retries = 3
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                timeout = httpx.Timeout(10.0)  # 10 second timeout
                async with httpx.AsyncClient(timeout=timeout) as client:
                    # Add headers that Supabase might expect
                    headers = {
                        "User-Agent": "FastAPI-Backend/1.0",
                        "Accept": "application/json",
                    }
                    
                    response = await client.get(self.jwks_url, headers=headers)
                    
                    if response.status_code == 200:
                        jwks_data = response.json()
                        # Cache the successful response
                        self.jwks_cache = jwks_data
                        self.jwks_cache_expiry = datetime.now() + self.cache_duration
                        logger.info("✅ JWKS fetched and cached successfully")
                        return jwks_data
                    else:
                        logger.error(f"❌ JWKS fetch failed with status {response.status_code}: {response.text}")
                        if response.status_code == 401:
                            raise JWTValidationError(f"Unauthorized access to JWKS endpoint. Check Supabase URL: {self.jwks_url}")
                        elif response.status_code == 404:
                            raise JWTValidationError(f"JWKS endpoint not found. Verify Supabase URL: {self.jwks_url}")
                        
            except httpx.TimeoutException:
                logger.error(f"⏰ Timeout fetching JWKS (attempt {attempt + 1}/{max_retries})")
            except httpx.ConnectError:
                logger.error(f"🌐 Connection error fetching JWKS (attempt {attempt + 1}/{max_retries})")
            except Exception as e:
                logger.error(f"❌ Unexpected error fetching JWKS (attempt {attempt + 1}/{max_retries}): {e}")
            
            # Wait before retry (exponential backoff)
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.info(f"⏳ Waiting {delay}s before retry...")
                await asyncio.sleep(delay)
        
        # If we have cached JWKS and all retries failed, use cache
        if self.jwks_cache:
            logger.warning("⚠️ Using expired JWKS cache due to fetch failure")
            return self.jwks_cache
            
        raise JWTValidationError(f"Failed to fetch JWKS after {max_retries} attempts")
    
    def get_key_from_jwks(self, jwks: Dict[str, Any], kid: str) -> str:
        """
        Extract the public key from JWKS for the given key ID.
        """
        for key_data in jwks.get('keys', []):
            if key_data.get('kid') == kid:
                try:
                    if JWCRYPTO_AVAILABLE:
                        # Convert JWK to PEM format using jwcrypto
                        key = jwk.JWK(**key_data)
                        public_key = key.export_to_pem()
                        return public_key.decode('utf-8')
                    else:
                        # Fallback: use key data directly (limited support)
                        # This is a simplified approach for development
                        if key_data.get('kty') == 'RSA':
                            # For development, we'll skip JWKS validation
                            # In production, jwcrypto should be installed
                            raise JWTValidationError("JWKS RSA key processing requires jwcrypto library")
                        else:
                            raise JWTValidationError(f"Unsupported key type without jwcrypto: {key_data.get('kty')}")
                            
                except Exception as e:
                    logger.error(f"❌ Failed to convert JWK to PEM: {e}")
                    raise JWTValidationError(f"Key conversion failed: {e}")
        
        raise JWTValidationError(f"Key ID '{kid}' not found in JWKS")
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token with improved error handling"""
        try:
            # If we have a JWT secret, try that first (faster)
            if self.jwt_secret:
                try:
                    payload = jwt.decode(
                        token,
                        self.jwt_secret,
                        algorithms=["HS256"],
                        options={"verify_aud": False}
                    )
                    logger.info("✅ Token validated with JWT secret")
                    return payload
                except JWTError as e:
                    logger.warning(f"⚠️ JWT secret validation failed, trying JWKS: {e}")
            
            # Get the header to find the key ID
            header = jwt.get_unverified_header(token)
            kid = header.get('kid')
            
            if not kid:
                raise JWTValidationError("Token missing 'kid' in header")
            
            # Get JWKS
            jwks = await self.get_jwks()
            
            # Find the matching key
            public_key = None
            for key_data in jwks.get('keys', []):
                if key_data.get('kid') == kid:
                    public_key = jwk.construct(key_data)
                    break
            
            if not public_key:
                raise JWTValidationError(f"Public key not found for kid: {kid}")
            
            # Verify the token
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                options={"verify_aud": False}
            )
            
            logger.info("✅ Token validated with JWKS")
            return payload
            
        except JWTError as e:
            logger.error(f"❌ JWT validation error: {e}")
            raise JWTValidationError(f"Token validation failed: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error validating token: {e}")
            raise JWTValidationError(f"Token validation failed: {e}")
    
    def _validate_with_secret(self, token: str) -> Dict[str, Any]:
        """
        Validate token using JWT secret (for local development).
        """
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=['HS256', 'RS256'],
                options={
                    'verify_signature': True, 
                    'verify_exp': True,
                    'verify_aud': False  # Skip audience verification for development tokens
                }
            )
            self._validate_payload(payload)
            logger.debug("✅ Token validated with JWT secret (development)")
            return payload
        except Exception as e:
            raise JWTValidationError(f"Secret validation failed: {e}")
    
    def _validate_payload(self, payload: Dict[str, Any]) -> None:
        """
        Validate JWT payload structure and required fields.
        """
        required_fields = ['sub', 'exp']
        for field in required_fields:
            if field not in payload:
                raise JWTValidationError(f"Token missing required field: {field}")
        
        # Check expiration
        exp = payload.get('exp')
        if exp and exp < time.time():
            raise JWTValidationError("Token has expired")
        
        # Validate user ID format
        user_id = payload.get('sub')
        if not user_id or len(user_id) < 10:
            raise JWTValidationError("Invalid user ID in token")
    
    async def extract_user_info(self, token: str) -> Dict[str, Any]:
        """Extract user information from validated token"""
        try:
            payload = await self.validate_token(token)
            
            # Extract user info from the payload
            user_info = {
                'user_id': payload.get('sub'),
                'email': payload.get('email'),
                'role': payload.get('role'),
                'aud': payload.get('aud'),
                'exp': payload.get('exp'),
                'iat': payload.get('iat'),
                'iss': payload.get('iss'),
                'user_metadata': payload.get('user_metadata', {}),
                'app_metadata': payload.get('app_metadata', {}),
            }
            
            # Remove None values
            user_info = {k: v for k, v in user_info.items() if v is not None}
            
            # Determine user role and permissions
            user_info['is_admin'] = self._is_admin_user(user_info)
            user_info['permissions'] = self._get_user_permissions(user_info)
            
            logger.info(f"✅ User info extracted for user: {user_info.get('user_id')}")
            return user_info
            
        except Exception as e:
            logger.error(f"❌ Error extracting user info: {e}")
            raise
    
    def _is_admin_user(self, user_info: Dict[str, Any]) -> bool:
        """
        Determine if user has admin privileges.
        """
        email = user_info.get('email', '')
        role = user_info.get('role', '')
        app_metadata = user_info.get('app_metadata', {})
        
        # Check various admin indicators
        return (
            role == 'admin' or
            email.endswith('@creditclarity.com') or
            email in settings.admin_emails or
            app_metadata.get('role') == 'admin' or
            app_metadata.get('is_admin', False)
        )
    
    def _get_user_permissions(self, user_info: Dict[str, Any]) -> List[str]:
        """
        Get user permissions based on role and metadata.
        """
        permissions = ['read:own_data', 'write:own_data']
        
        if user_info.get('is_admin'):
            permissions.extend([
                'read:all_data',
                'write:all_data',
                'admin:users',
                'admin:settings',
                'admin:analytics'
            ])
        
        # Add role-based permissions
        role = user_info.get('role', '')
        if role == 'premium':
            permissions.extend(['premium:features', 'premium:reports'])
        
        return permissions


# Global JWT validator instance
jwt_validator = SupabaseJWTValidator()


# Convenience functions for FastAPI integration
async def validate_jwt_token(token: str) -> Dict[str, Any]:
    """
    Validate JWT token - convenience function for FastAPI dependencies.
    """
    return await jwt_validator.validate_token(token)


async def get_user_from_token(token: str) -> Dict[str, Any]:
    """
    Extract user information from JWT token - convenience function.
    """
    return await jwt_validator.extract_user_info(token)


def create_development_token(user_id: str, email: str, role: str = "authenticated") -> str:
    """
    Create a development JWT token for testing (only in development mode).
    """
    if not settings.is_development():
        raise ValueError("Development tokens can only be created in development mode")
    
    if not settings.jwt_secret:
        raise ValueError("JWT_SECRET required for development token creation")
    
    # Create payload
    now = int(time.time())
    payload = {
        'sub': user_id,
        'email': email,
        'role': role,
        'aud': 'authenticated',
        'exp': now + 3600 * 24,  # 24 hours
        'iat': now,
        'iss': 'supabase-local',
        'user_metadata': {'email': email},
        'app_metadata': {'provider': 'email', 'providers': ['email']}
    }
    
    # Create token
    token = jwt.encode(payload, settings.jwt_secret, algorithm='HS256')
    logger.info(f"🔧 Created development token for user: {email}")
    
    return token


# Cache for frequently used functions
@lru_cache(maxsize=100)
def get_cached_user_permissions(user_role: str, is_admin: bool) -> tuple:
    """Cache user permissions to avoid repeated calculations."""
    validator = SupabaseJWTValidator()
    user_info = {'role': user_role, 'is_admin': is_admin}
    return tuple(validator._get_user_permissions(user_info))