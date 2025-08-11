"""
Security middleware for request processing
"""
import time
import logging
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.security import rate_limiter
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Only add HTTPS headers in production
        if settings.is_production():
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"
        
        # Check for user authentication to create more specific rate limiting
        client_id = f"ip:{client_ip}"
        auth_header = request.headers.get("Authorization")
        
        if auth_header and auth_header.startswith("Bearer "):
            try:
                from core.security import extract_user_from_token
                token = auth_header.split(" ")[1]
                user_data = extract_user_from_token(token)
                client_id = f"user:{user_data['id']}"
            except Exception:
                # If token verification fails, fall back to IP-based limiting
                pass
        
        # Check rate limit
        if not rate_limiter.is_allowed(client_id):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "error_code": "RATE_LIMIT_EXCEEDED"
                },
                headers={
                    "Retry-After": str(settings.rate_limit_window),
                    "X-RateLimit-Limit": str(settings.rate_limit_requests),
                    "X-RateLimit-Window": str(settings.rate_limit_window)
                }
            )
        
        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests for monitoring and debugging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log request
        client_ip = request.client.host if request.client else "unknown"
        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"from {client_ip}"
        )
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"- Status: {response.status_code} - Time: {process_time:.3f}s"
            )
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"- Error: {str(e)} - Time: {process_time:.3f}s"
            )
            raise


class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """Enhanced CORS handling with security considerations."""
    
    def __init__(self, app, allowed_origins: list = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or settings.get_cors_origins()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        origin = request.headers.get("Origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
            if origin in self.allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
                if settings.cors_allow_credentials:
                    response.headers["Access-Control-Allow-Credentials"] = "true"
            return response
        
        response = await call_next(request)
        
        # Add CORS headers to actual requests
        if origin in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            if settings.cors_allow_credentials:
                response.headers["Access-Control-Allow-Credentials"] = "true"
        elif settings.is_development() and origin:
            # In development, be more lenient but log warnings
            logger.warning(f"CORS: Origin '{origin}' not in allowed list but allowing in development")
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response


class ContentValidationMiddleware(BaseHTTPMiddleware):
    """Validate request content and headers."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Validate content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 50 * 1024 * 1024:  # 50MB limit
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": "Request entity too large. Maximum file size is 50MB."}
            )
        
        # Validate content type for POST requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            
            # Allow multipart/form-data for file uploads
            allowed_content_types = [
                "application/json",
                "multipart/form-data",
                "application/x-www-form-urlencoded"
            ]
            
            # Check if content type is allowed (flexible matching for multipart)
            if not any(allowed in content_type for allowed in allowed_content_types):
                logger.warning(f"Suspicious content type: {content_type}")
                return JSONResponse(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    content={"detail": "Unsupported content type"}
                )
        
        return await call_next(request)