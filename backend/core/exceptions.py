"""
Custom exception classes and error handling
Standardized error responses and logging
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, status
from pydantic import BaseModel

class CreditClarityException(Exception):
    """Base exception for Credit Clarity application."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "GENERIC_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)

class ValidationError(CreditClarityException):
    """Validation error for input data."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={**(details or {}), "field": field} if field else details,
            status_code=400
        )

class AuthenticationError(CreditClarityException):
    """Authentication related errors."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            details=details,
            status_code=401
        )

class AuthorizationError(CreditClarityException):
    """Authorization/permission related errors."""
    
    def __init__(
        self,
        message: str = "Access denied",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details=details,
            status_code=403
        )

class ResourceNotFoundError(CreditClarityException):
    """Resource not found errors."""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"{resource_type} with ID '{resource_id}' not found"
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            details={**(details or {}), "resource_type": resource_type, "resource_id": resource_id},
            status_code=404
        )

class ProcessingError(CreditClarityException):
    """PDF processing related errors."""
    
    def __init__(
        self,
        message: str,
        processing_stage: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="PROCESSING_ERROR",
            details={**(details or {}), "stage": processing_stage} if processing_stage else details,
            status_code=500
        )

class DatabaseError(CreditClarityException):
    """Database operation errors."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details={**(details or {}), "operation": operation} if operation else details,
            status_code=500
        )

class CacheError(CreditClarityException):
    """Cache operation errors."""
    
    def __init__(
        self,
        message: str,
        cache_layer: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            details={**(details or {}), "cache_layer": cache_layer} if cache_layer else details,
            status_code=500
        )

class RateLimitExceededError(CreditClarityException):
    """Rate limiting errors."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            details={**(details or {}), "retry_after": retry_after} if retry_after else details,
            status_code=429
        )

class ConfigurationError(CreditClarityException):
    """Configuration related errors."""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details={**(details or {}), "config_key": config_key} if config_key else details,
            status_code=500
        )

class ExternalServiceError(CreditClarityException):
    """External service integration errors."""
    
    def __init__(
        self,
        message: str,
        service_name: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={**(details or {}), "service": service_name},
            status_code=502
        )

class BusinessLogicError(CreditClarityException):
    """Business rule violation errors."""
    
    def __init__(
        self,
        message: str,
        rule_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="BUSINESS_LOGIC_ERROR",
            details={**(details or {}), "rule": rule_name} if rule_name else details,
            status_code=422
        )

# Error response models
class ErrorDetail(BaseModel):
    """Structured error detail."""
    code: str
    message: str
    field: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    """Standardized error response format."""
    success: bool = False
    error: ErrorDetail
    timestamp: str
    request_id: Optional[str] = None
    version: str = "1.0"

# HTTP Exception mappings
def to_http_exception(exc: CreditClarityException, request_id: Optional[str] = None) -> HTTPException:
    """Convert custom exception to FastAPI HTTPException."""
    from datetime import datetime
    
    error_detail = ErrorDetail(
        code=exc.error_code,
        message=exc.message,
        field=exc.details.get("field"),
        details=exc.details
    )
    
    error_response = ErrorResponse(
        error=error_detail,
        timestamp=datetime.now().isoformat(),
        request_id=request_id
    )
    
    return HTTPException(
        status_code=exc.status_code,
        detail=error_response.dict()
    )

# Common error factories
def validation_error(message: str, field: Optional[str] = None) -> ValidationError:
    """Create validation error."""
    return ValidationError(message, field)

def not_found_error(resource_type: str, resource_id: str) -> ResourceNotFoundError:
    """Create resource not found error."""
    return ResourceNotFoundError(resource_type, resource_id)

def processing_error(message: str, stage: Optional[str] = None) -> ProcessingError:
    """Create processing error."""
    return ProcessingError(message, stage)

def auth_error(message: str = "Authentication required") -> AuthenticationError:
    """Create authentication error."""
    return AuthenticationError(message)

def permission_error(message: str = "Insufficient permissions") -> AuthorizationError:
    """Create authorization error."""
    return AuthorizationError(message)

def rate_limit_error(retry_after: Optional[int] = None) -> RateLimitExceededError:
    """Create rate limit error."""
    return RateLimitExceededError(retry_after=retry_after)

def config_error(message: str, config_key: Optional[str] = None) -> ConfigurationError:
    """Create configuration error."""
    return ConfigurationError(message, config_key)

def external_service_error(service: str, message: str) -> ExternalServiceError:
    """Create external service error."""
    return ExternalServiceError(message, service)

def business_error(message: str, rule: Optional[str] = None) -> BusinessLogicError:
    """Create business logic error."""
    return BusinessLogicError(message, rule)

# Enhanced error handler middleware
async def log_and_format_error(
    exc: CreditClarityException, 
    request_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> HTTPException:
    """
    Enhanced error logging and formatting.
    Logs errors with context and formats for API response.
    """
    import logging
    from datetime import datetime
    
    logger = logging.getLogger("credit_clarity.errors")
    
    # Create error context
    error_context = {
        "error_code": exc.error_code,
        "status_code": exc.status_code,
        "message": exc.message,
        "request_id": request_id,
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        "details": exc.details
    }
    
    # Log based on severity
    if exc.status_code >= 500:
        logger.error(f"Server error: {exc.error_code}", extra=error_context)
    elif exc.status_code >= 400:
        logger.warning(f"Client error: {exc.error_code}", extra=error_context)
    else:
        logger.info(f"Error handled: {exc.error_code}", extra=error_context)
    
    return to_http_exception(exc, request_id)

# Rate limiting specific errors
class RateLimitError(CreditClarityException):
    """Enhanced rate limiting error with detailed information."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        rate_limit_type: str = "general",
        current_usage: Optional[int] = None,
        limit: Optional[int] = None,
        reset_time: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        enhanced_details = {
            **(details or {}),
            "rate_limit_type": rate_limit_type,
            "current_usage": current_usage,
            "limit": limit,
            "reset_time": reset_time
        }
        
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            details=enhanced_details,
            status_code=429
        )

# JWT specific errors
class JWTError(AuthenticationError):
    """JWT-specific authentication errors."""
    
    def __init__(
        self,
        message: str = "JWT authentication failed",
        token_error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        enhanced_details = {
            **(details or {}),
            "token_error": token_error,
            "auth_type": "jwt"
        }
        
        super().__init__(
            message=message,
            details=enhanced_details
        )
        self.error_code = "JWT_AUTHENTICATION_ERROR"

# File upload specific errors
class FileUploadError(CreditClarityException):
    """File upload and processing errors."""
    
    def __init__(
        self,
        message: str,
        file_name: Optional[str] = None,
        file_size: Optional[int] = None,
        file_type: Optional[str] = None,
        upload_stage: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        enhanced_details = {
            **(details or {}),
            "file_name": file_name,
            "file_size": file_size,
            "file_type": file_type,
            "upload_stage": upload_stage
        }
        
        super().__init__(
            message=message,
            error_code="FILE_UPLOAD_ERROR",
            details=enhanced_details,
            status_code=400
        )

# Background job specific errors
class JobError(CreditClarityException):
    """Background job processing errors."""
    
    def __init__(
        self,
        message: str,
        job_id: Optional[str] = None,
        job_type: Optional[str] = None,
        job_stage: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        enhanced_details = {
            **(details or {}),
            "job_id": job_id,
            "job_type": job_type,
            "job_stage": job_stage
        }
        
        super().__init__(
            message=message,
            error_code="BACKGROUND_JOB_ERROR",
            details=enhanced_details,
            status_code=500
        )

# Factory functions for new error types
def jwt_error(message: str = "JWT authentication failed", token_error: Optional[str] = None) -> JWTError:
    """Create JWT authentication error."""
    return JWTError(message, token_error)

def file_upload_error(message: str, file_name: Optional[str] = None, upload_stage: Optional[str] = None) -> FileUploadError:
    """Create file upload error."""
    return FileUploadError(message, file_name=file_name, upload_stage=upload_stage)

def job_error(message: str, job_id: Optional[str] = None, job_type: Optional[str] = None) -> JobError:
    """Create background job error."""
    return JobError(message, job_id=job_id, job_type=job_type)

def enhanced_rate_limit_error(
    rate_limit_type: str = "general",
    current_usage: Optional[int] = None,
    limit: Optional[int] = None,
    reset_time: Optional[int] = None
) -> RateLimitError:
    """Create enhanced rate limit error."""
    return RateLimitError(
        rate_limit_type=rate_limit_type,
        current_usage=current_usage,
        limit=limit,
        reset_time=reset_time
    )