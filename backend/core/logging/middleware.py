"""
Logging middleware for FastAPI
Request/response logging with performance tracking
"""
import time
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .logger import get_logger, LogContext

logger = get_logger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive request/response logging.
    Tracks performance, errors, and request details.
    """
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with comprehensive logging."""
        
        # Skip logging for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        start_time = time.time()
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        # Extract request details
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": dict(request.headers),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "content_length": request.headers.get("content-length")
        }
        
        # Remove sensitive headers
        sensitive_headers = ["authorization", "cookie", "x-api-key"]
        for header in sensitive_headers:
            if header in request_info["headers"]:
                request_info["headers"][header] = "[REDACTED]"
        
        # Log request start
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "request_info": request_info,
                "event_type": "request_start"
            }
        )
        
        # Extract user ID if available from auth
        user_id = None
        try:
            # Try to extract user from authorization header
            auth_header = request.headers.get("authorization")
            if auth_header:
                # In a real app, you'd decode the JWT token here
                user_id = "extracted_from_token"
        except Exception:
            pass
        
        # Set up logging context
        with LogContext(request_id, user_id, request.url.path):
            try:
                # Process request
                response = await call_next(request)
                
                # Calculate timing
                process_time = time.time() - start_time
                
                # Extract response details
                response_info = {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "content_length": response.headers.get("content-length")
                }
                
                # Log successful request
                log_level = "INFO"
                if response.status_code >= 500:
                    log_level = "ERROR"
                elif response.status_code >= 400:
                    log_level = "WARNING"
                
                getattr(logger, log_level.lower())(
                    f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                    extra={
                        "request_id": request_id,
                        "user_id": user_id,
                        "request_info": request_info,
                        "response_info": response_info,
                        "duration_ms": process_time * 1000,
                        "status_code": response.status_code,
                        "event_type": "request_complete"
                    }
                )
                
                return response
                
            except Exception as e:
                # Log request error
                process_time = time.time() - start_time
                
                logger.error(
                    f"Request failed: {request.method} {request.url.path}",
                    exc_info=True,
                    extra={
                        "request_id": request_id,
                        "user_id": user_id,
                        "request_info": request_info,
                        "duration_ms": process_time * 1000,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "event_type": "request_error"
                    }
                )
                
                raise

class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for security event logging.
    Tracks authentication, authorization, and suspicious activity.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Monitor security events."""
        
        request_id = getattr(request.state, 'request_id', 'unknown')
        client_ip = request.client.host if request.client else None
        
        # Check for suspicious patterns
        suspicious_indicators = []
        
        # Check for common attack patterns in URL
        suspicious_paths = [
            "wp-admin", "phpMyAdmin", "admin.php", ".env", 
            "../", "etc/passwd", "cmd=", "eval(", "<script"
        ]
        
        for pattern in suspicious_paths:
            if pattern in str(request.url):
                suspicious_indicators.append(f"suspicious_path:{pattern}")
        
        # Check for suspicious headers
        suspicious_headers = ["x-forwarded-host", "x-real-ip"]
        for header in suspicious_headers:
            if header in request.headers:
                value = request.headers[header]
                if any(bad in value.lower() for bad in ["localhost", "127.0.0.1", "internal"]):
                    suspicious_indicators.append(f"suspicious_header:{header}")
        
        # Check for rapid requests (basic rate limiting detection)
        user_agent = request.headers.get("user-agent", "")
        if not user_agent or len(user_agent) < 10:
            suspicious_indicators.append("missing_or_short_user_agent")
        
        # Log security events
        if suspicious_indicators:
            logger.warning(
                f"Suspicious request detected from {client_ip}",
                extra={
                    "request_id": request_id,
                    "client_ip": client_ip,
                    "url": str(request.url),
                    "user_agent": user_agent,
                    "indicators": suspicious_indicators,
                    "event_type": "security_warning"
                }
            )
        
        # Monitor authentication attempts
        if "authorization" in request.headers:
            auth_header = request.headers["authorization"]
            
            try:
                response = await call_next(request)
                
                # Log authentication result
                if response.status_code == 401:
                    logger.warning(
                        f"Authentication failed from {client_ip}",
                        extra={
                            "request_id": request_id,
                            "client_ip": client_ip,
                            "endpoint": request.url.path,
                            "event_type": "auth_failure"
                        }
                    )
                elif response.status_code == 403:
                    logger.warning(
                        f"Authorization denied from {client_ip}",
                        extra={
                            "request_id": request_id,
                            "client_ip": client_ip,
                            "endpoint": request.url.path,
                            "event_type": "auth_denied"
                        }
                    )
                
                return response
                
            except Exception as e:
                logger.error(
                    f"Security middleware error for {client_ip}",
                    exc_info=True,
                    extra={
                        "request_id": request_id,
                        "client_ip": client_ip,
                        "error_type": type(e).__name__,
                        "event_type": "security_error"
                    }
                )
                raise
        else:
            return await call_next(request)

class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for performance monitoring and logging.
    Tracks slow requests and resource usage.
    """
    
    def __init__(self, app, slow_request_threshold: float = 1.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold  # seconds
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Monitor request performance."""
        
        start_time = time.time()
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        try:
            response = await call_next(request)
            
            # Calculate performance metrics
            duration = time.time() - start_time
            duration_ms = duration * 1000
            
            # Log slow requests
            if duration > self.slow_request_threshold:
                logger.warning(
                    f"Slow request detected: {request.method} {request.url.path} took {duration:.2f}s",
                    extra={
                        "request_id": request_id,
                        "endpoint": request.url.path,
                        "method": request.method,
                        "duration_ms": duration_ms,
                        "threshold_ms": self.slow_request_threshold * 1000,
                        "status_code": response.status_code,
                        "event_type": "slow_request"
                    }
                )
            
            # Log performance metrics for all requests
            logger.info(
                f"Performance: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "endpoint": request.url.path,
                    "method": request.method,
                    "duration_ms": duration_ms,
                    "status_code": response.status_code,
                    "event_type": "performance_metric"
                }
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            logger.error(
                f"Performance monitoring error: {request.method} {request.url.path}",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "endpoint": request.url.path,
                    "method": request.method,
                    "duration_ms": duration * 1000,
                    "error_type": type(e).__name__,
                    "event_type": "performance_error"
                }
            )
            
            raise