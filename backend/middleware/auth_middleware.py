"""
Authentication middleware for JWT token validation
Provides request-level authentication, logging, and security features
"""
import time
import logging
from typing import Dict, Any, Optional, Set
from fastapi import Request, Response, HTTPException
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware

from core.jwt_auth import jwt_validator, JWTValidationError
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware for JWT authentication with flexible configuration.
    Provides automatic token validation, user context, and security logging.
    """
    
    def __init__(self, app, exempt_paths: Optional[Set[str]] = None):
        super().__init__(app)
        
        # Paths that don't require authentication
        self.exempt_paths = exempt_paths or {
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/favicon.ico",
            "/api/auth/dev-token",  # Development token endpoint
        }
        
        # Add development paths if in dev mode
        if settings.is_development():
            self.exempt_paths.update({
                "/api/dev",
                "/api/test",
                "/api/health",
            })
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request with JWT authentication.
        """
        start_time = time.time()
        
        # Check if path is exempt from authentication
        if self._is_exempt_path(request.url.path):
            response = await call_next(request)
            self._log_request(request, response, start_time, "exempt")
            return response
        
        # Extract and validate token
        auth_result = await self._authenticate_request(request)
        
        if auth_result["success"]:
            # Add user context to request state
            request.state.user = auth_result["user"]
            request.state.authenticated = True
            
            # Process request
            response = await call_next(request)
            
            # Log successful authenticated request
            self._log_request(request, response, start_time, "authenticated", auth_result["user"])
            
        else:
            # Authentication failed
            if settings.is_development() and auth_result.get("allow_fallback", False):
                # Development fallback
                request.state.user = {
                    "id": "11111111-1111-1111-1111-111111111111",
                    "email": "test@creditclarity.com",
                    "role": "authenticated",
                    "is_admin": False,
                    "permissions": ["read:own_data", "write:own_data"]
                }
                request.state.authenticated = True
                
                response = await call_next(request)
                self._log_request(request, response, start_time, "dev_fallback")
                
            else:
                # Return authentication error
                response = Response(
                    content=f'{{"error": "Authentication required", "detail": "{auth_result["error"]}"}}',
                    status_code=401,
                    headers={"Content-Type": "application/json"}
                )
                self._log_request(request, response, start_time, "auth_failed", error=auth_result["error"])
        
        return response
    
    def _is_exempt_path(self, path: str) -> bool:
        """Check if the request path is exempt from authentication."""
        # Exact match
        if path in self.exempt_paths:
            return True
        
        # Pattern matching for API docs and static files
        exempt_patterns = [
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/static/",
            "/favicon.ico",
            "/health"
        ]
        
        return any(path.startswith(pattern) for pattern in exempt_patterns)
    
    async def _authenticate_request(self, request: Request) -> Dict[str, Any]:
        """
        Authenticate the request and return result.
        """
        try:
            # Extract authorization header
            authorization = request.headers.get("Authorization")
            if not authorization:
                return {
                    "success": False,
                    "error": "No authorization header",
                    "allow_fallback": True
                }
            
            # Parse authorization header
            scheme, token = get_authorization_scheme_param(authorization)
            if scheme.lower() != "bearer":
                return {
                    "success": False,
                    "error": f"Unsupported authorization scheme: {scheme}",
                    "allow_fallback": False
                }
            
            if not token:
                return {
                    "success": False,
                    "error": "No token provided",
                    "allow_fallback": True
                }
            
            # Validate JWT token
            user_info = await jwt_validator.extract_user_info(token)
            
            return {
                "success": True,
                "user": user_info,
                "token": token
            }
            
        except JWTValidationError as e:
            return {
                "success": False,
                "error": f"JWT validation failed: {e}",
                "allow_fallback": "expired" not in str(e).lower()
            }
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return {
                "success": False,
                "error": "Authentication failed",
                "allow_fallback": True
            }
    
    def _log_request(
        self, 
        request: Request, 
        response: Response, 
        start_time: float, 
        auth_status: str,
        user: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """
        Log request details with authentication context.
        """
        duration_ms = (time.time() - start_time) * 1000
        
        log_data = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "auth_status": auth_status,
            "user_id": user.get("id") if user else None,
            "user_email": user.get("email") if user else None,
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("User-Agent", "")[:100]  # Truncate UA
        }
        
        if error:
            log_data["error"] = error
        
        # Log level based on status
        if response.status_code >= 500:
            logger.error(f"🔴 Request failed: {log_data}")
        elif response.status_code >= 400:
            logger.warning(f"🟡 Client error: {log_data}")
        elif auth_status == "auth_failed":
            logger.warning(f"🔒 Auth failed: {log_data}")
        elif auth_status == "dev_fallback":
            logger.debug(f"🔧 Dev fallback: {log_data}")
        else:
            logger.info(f"✅ Request completed: {log_data}")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none';",
        }
        
        # Add HSTS in production
        if settings.is_production():
            security_headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Apply headers
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive request/response logging.
    """
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log incoming request
        logger.debug(
            f"📥 {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log response
        status_emoji = "✅" if response.status_code < 400 else "❌"
        logger.info(
            f"{status_emoji} {request.method} {request.url.path} "
            f"-> {response.status_code} ({duration_ms:.2f}ms)"
        )
        
        return response


# Middleware configuration for different environments
def get_middleware_config():
    """
    Get middleware configuration based on environment.
    """
    config = {
        "auth_middleware": True,
        "security_headers": True,
        "request_logging": settings.is_development() or settings.log_level == "DEBUG"
    }
    
    return config


# Helper functions for middleware integration
def add_auth_middleware(app, exempt_paths: Optional[Set[str]] = None):
    """
    Add JWT authentication middleware to FastAPI app.
    """
    app.add_middleware(JWTAuthMiddleware, exempt_paths=exempt_paths)
    logger.info("✅ JWT Authentication middleware added")


def add_security_middleware(app):
    """
    Add security middleware to FastAPI app.
    """
    app.add_middleware(SecurityHeadersMiddleware)
    if get_middleware_config()["request_logging"]:
        app.add_middleware(RequestLoggingMiddleware)
    
    logger.info("✅ Security middleware added")


def setup_all_middleware(app, exempt_paths: Optional[Set[str]] = None):
    """
    Setup all authentication and security middleware.
    """
    # Order matters - add in reverse order of execution
    add_security_middleware(app)
    add_auth_middleware(app, exempt_paths)
    
    logger.info("🛡️ All security middleware configured")