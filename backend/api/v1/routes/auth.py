"""
Authentication API Routes
Supabase-backed authentication endpoints for user management
"""
import re
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field, EmailStr, validator

from core.config import get_settings
from core.exceptions import (
    AuthenticationError,
    RateLimitExceededError,
    CreditClarityException,
    auth_error,
    rate_limit_error,
    validation_error,
)
from core.security import supabase_client, verify_supabase_jwt

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

# Rate limiting storage (in-memory for development, use Redis in production)
rate_limit_store: Dict[str, list] = {}


# ============== Request Models ==============

class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)

    @validator('password')
    def validate_password(cls, v):
        """Validate password complexity."""
        errors = []
        if len(v) < 8:
            errors.append("Password must be at least 8 characters")
        if not re.search(r'[A-Z]', v):
            errors.append("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', v):
            errors.append("Password must contain at least one lowercase letter")
        if not re.search(r'\d', v):
            errors.append("Password must contain at least one number")
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\'\\:"|<,./>?]', v):
            errors.append("Password must contain at least one special character")
        
        if errors:
            raise ValueError('; '.join(errors))
        return v


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class RefreshTokenRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Password reset request."""
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    """Password reset confirmation request."""
    new_password: str = Field(..., min_length=8, max_length=128)
    access_token: str

    @validator('new_password')
    def validate_password(cls, v):
        """Validate password complexity."""
        errors = []
        if len(v) < 8:
            errors.append("Password must be at least 8 characters")
        if not re.search(r'[A-Z]', v):
            errors.append("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', v):
            errors.append("Password must contain at least one lowercase letter")
        if not re.search(r'\d', v):
            errors.append("Password must contain at least one number")
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\'\\:"|<,./>?]', v):
            errors.append("Password must contain at least one special character")
        
        if errors:
            raise ValueError('; '.join(errors))
        return v


class LogoutRequest(BaseModel):
    """Logout request."""
    access_token: str = Field(..., description="Access token to invalidate")


# ============== Response Models ==============

class UserResponse(BaseModel):
    """User information response."""
    id: str
    email: str
    first_name: str
    last_name: str
    created_at: Optional[str] = None


class AuthTokensResponse(BaseModel):
    """Authentication tokens response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RegisterResponse(BaseModel):
    """Registration response."""
    user_id: str
    message: str


class LoginResponse(BaseModel):
    """Login response."""
    user: UserResponse
    tokens: AuthTokensResponse


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


# ============== Helper Functions ==============

def generate_request_id() -> str:
    """Generate unique request ID for tracing."""
    return str(uuid.uuid4())[:8]


def check_rate_limit(identifier: str, max_attempts: int = 10, window_seconds: int = 60) -> bool:
    """
    Check if request is rate limited.
    
    Args:
        identifier: Unique identifier (IP, user ID, etc.)
        max_attempts: Maximum allowed attempts in window
        window_seconds: Time window in seconds
    
    Returns:
        True if allowed, False if rate limited
    """
    now = datetime.now()
    
    if identifier not in rate_limit_store:
        rate_limit_store[identifier] = []
    
    # Clean old entries
    rate_limit_store[identifier] = [
        ts for ts in rate_limit_store[identifier]
        if (now - ts).total_seconds() < window_seconds
    ]
    
    # Check limit
    if len(rate_limit_store[identifier]) >= max_attempts:
        return False
    
    # Add current attempt
    rate_limit_store[identifier].append(now)
    return True


def get_rate_limit_retry_after(identifier: str, window_seconds: int = 60) -> int:
    """Get seconds until rate limit resets."""
    if identifier not in rate_limit_store:
        return 0
    
    now = datetime.now()
    oldest = min(rate_limit_store[identifier]) if rate_limit_store[identifier] else now
    remaining = window_seconds - (now - oldest).total_seconds()
    return max(0, int(remaining))


def create_success_response(data: Any, message: str = "", request_id: str = None) -> Dict[str, Any]:
    """Create standardized success response."""
    return {
        "success": True,
        "data": data if isinstance(data, dict) else data.dict() if hasattr(data, 'dict') else data,
        "error": None,
        "request_id": request_id or generate_request_id()
    }


def create_error_response(exc: CreditClarityException, request_id: str = None) -> Dict[str, Any]:
    """Create standardized error response."""
    return {
        "success": False,
        "data": None,
        "error": {
            "code": exc.error_code,
            "message": exc.message,
            "details": exc.details
        },
        "request_id": request_id or generate_request_id()
    }


# ============== Authentication Endpoints ==============

@router.post("/register", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, req: Request):
    """
    Register a new user.
    
    Creates a user in Supabase Auth and sends verification email.
    Password must meet complexity requirements.
    """
    request_id = generate_request_id()
    client_ip = req.client.host if req.client else "unknown"
    
    logger.info(f"[{request_id}] Registration attempt for email: {request.email} from IP: {client_ip}")
    
    if not supabase_client:
        logger.error(f"[{request_id}] Supabase client not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=create_error_response(
                auth_error("Authentication service temporarily unavailable"),
                request_id
            )
        )
    
    try:
        # Create user in Supabase Auth
        auth_response = supabase_client.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {
                    "first_name": request.first_name,
                    "last_name": request.last_name,
                    "full_name": f"{request.first_name} {request.last_name}"
                }
            }
        })
        
        if auth_response.user:
            user_id = auth_response.user.id
            logger.info(f"[{request_id}] User registered successfully: {user_id}")
            
            # Log security event
            logger.info(
                f"[{request_id}] SECURITY_EVENT: user_registered "
                f"user_id={user_id} email={request.email} ip={client_ip}"
            )
            
            return create_success_response(
                data={"user_id": user_id, "message": "Registration successful. Please check your email to verify your account."},
                request_id=request_id
            )
        else:
            raise auth_error("Registration failed")
            
    except Exception as e:
        logger.error(f"[{request_id}] Registration failed: {str(e)}")
        
        # Handle specific Supabase errors
        error_str = str(e).lower()
        if "email" in error_str and "already" in error_str:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=create_error_response(
                    validation_error("Email already registered"),
                    request_id
                )
            )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                auth_error(f"Registration failed: {str(e)}"),
                request_id
            )
        )


@router.post("/login", response_model=Dict[str, Any])
async def login(request: LoginRequest, req: Request):
    """
    Authenticate user and return JWT tokens.
    
    Rate limited to 10 attempts per minute per IP.
    """
    request_id = generate_request_id()
    client_ip = req.client.host if req.client else "unknown"
    rate_limit_key = f"login:{client_ip}"
    
    # Check rate limit
    if not check_rate_limit(rate_limit_key, max_attempts=10, window_seconds=60):
        retry_after = get_rate_limit_retry_after(rate_limit_key)
        logger.warning(f"[{request_id}] Rate limit exceeded for login from IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=create_error_response(
                rate_limit_error(retry_after=retry_after),
                request_id
            )
        )
    
    logger.info(f"[{request_id}] Login attempt for email: {request.email} from IP: {client_ip}")
    
    if not supabase_client:
        logger.error(f"[{request_id}] Supabase client not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=create_error_response(
                auth_error("Authentication service temporarily unavailable"),
                request_id
            )
        )
    
    try:
        # Authenticate with Supabase
        auth_response = supabase_client.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        if auth_response.session:
            session = auth_response.session
            user = auth_response.user
            
            logger.info(f"[{request_id}] Login successful for user: {user.id}")
            
            # Log security event
            logger.info(
                f"[{request_id}] SECURITY_EVENT: user_login "
                f"user_id={user.id} email={request.email} ip={client_ip}"
            )
            
            return create_success_response(
                data={
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "first_name": user.user_metadata.get("first_name", ""),
                        "last_name": user.user_metadata.get("last_name", "")
                    },
                    "tokens": {
                        "access_token": session.access_token,
                        "refresh_token": session.refresh_token,
                        "token_type": "bearer",
                        "expires_in": session.expires_in
                    }
                },
                request_id=request_id
            )
        else:
            raise auth_error("Invalid credentials")
            
    except Exception as e:
        logger.warning(f"[{request_id}] Login failed for email {request.email}: {str(e)}")
        
        # Log failed login attempt
        logger.warning(
            f"[{request_id}] SECURITY_EVENT: failed_login_attempt "
            f"email={request.email} ip={client_ip} reason={str(e)}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=create_error_response(
                auth_error("Invalid email or password"),
                request_id
            )
        )


@router.post("/logout", response_model=Dict[str, Any])
async def logout(request: LogoutRequest, req: Request):
    """
    Terminate user session.
    
    Invalidates the Supabase session.
    """
    request_id = generate_request_id()
    
    logger.info(f"[{request_id}] Logout request received")
    
    if not supabase_client:
        logger.warning(f"[{request_id}] Supabase client not initialized, skipping logout")
        return create_success_response(
            data={"message": "Logged out successfully"},
            request_id=request_id
        )
    
    try:
        # Invalidate the session
        supabase_client.auth.sign_out()
        
        logger.info(f"[{request_id}] Logout successful")
        
        # Log security event
        logger.info(f"[{request_id}] SECURITY_EVENT: user_logout success=true")
        
        return create_success_response(
            data={"message": "Logged out successfully"},
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"[{request_id}] Logout failed: {str(e)}")
        
        return create_success_response(
            data={"message": "Logged out successfully"},
            request_id=request_id
        )


@router.post("/password-reset/request", response_model=Dict[str, Any])
async def request_password_reset(request: PasswordResetRequest, req: Request):
    """
    Request a password reset email.
    
    Returns success regardless of whether email exists (security best practice).
    """
    request_id = generate_request_id()
    client_ip = req.client.host if req.client else "unknown"
    
    logger.info(f"[{request_id}] Password reset request for email: {request.email} from IP: {client_ip}")
    
    if not supabase_client:
        logger.error(f"[{request_id}] Supabase client not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=create_error_response(
                auth_error("Authentication service temporarily unavailable"),
                request_id
            )
        )
    
    try:
        # Send password reset email
        supabase_client.auth.reset_password_email(request.email)
        
        logger.info(f"[{request_id}] Password reset email sent")
        
        # Log security event (without revealing if email exists)
        logger.info(
            f"[{request_id}] SECURITY_EVENT: password_reset_requested "
            f"email={'*' * (len(request.email) - 4) + request.email[-4:] if '@' in request.email else '***'} "
            f"ip={client_ip}"
        )
        
        return create_success_response(
            data={"message": "If an account exists with this email, a password reset link has been sent."},
            request_id=request_id
        )
        
    except Exception as e:
        logger.warning(f"[{request_id}] Password reset request failed: {str(e)}")
        
        # Still return success to prevent email enumeration
        return create_success_response(
            data={"message": "If an account exists with this email, a password reset link has been sent."},
            request_id=request_id
        )


@router.post("/password-reset/confirm", response_model=Dict[str, Any])
async def confirm_password_reset(request: PasswordResetConfirmRequest, req: Request):
    """
    Confirm password reset with new password.
    
    Updates password in Supabase and logs security event.
    """
    request_id = generate_request_id()
    client_ip = req.client.host if req.client else "unknown"
    
    logger.info(f"[{request_id}] Password reset confirmation request from IP: {client_ip}")
    
    if not supabase_client:
        logger.error(f"[{request_id}] Supabase client not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=create_error_response(
                auth_error("Authentication service temporarily unavailable"),
                request_id
            )
        )
    
    try:
        # Verify the token first
        user_data = verify_supabase_jwt(request.access_token)
        user_id = user_data.get("id")
        
        # Update password (requires authenticated session)
        # For password reset flow, we use the recovery flow
        supabase_client.auth.update_user({"password": request.new_password})
        
        logger.info(f"[{request_id}] Password reset successful for user: {user_id}")
        
        # Log security event
        logger.info(
            f"[{request_id}] SECURITY_EVENT: password_reset_completed "
            f"user_id={user_id} ip={client_ip}"
        )
        
        return create_success_response(
            data={"message": "Password has been reset successfully."},
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"[{request_id}] Password reset confirmation failed: {str(e)}")
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                auth_error("Password reset failed. The link may have expired."),
                request_id
            )
        )


@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_token(request: RefreshTokenRequest, req: Request):
    """
    Refresh access token using refresh token.
    
    Returns new access and refresh tokens.
    """
    request_id = generate_request_id()
    client_ip = req.client.host if req.client else "unknown"
    
    logger.info(f"[{request_id}] Token refresh request from IP: {client_ip}")
    
    if not supabase_client:
        logger.error(f"[{request_id}] Supabase client not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=create_error_response(
                auth_error("Authentication service temporarily unavailable"),
                request_id
            )
        )
    
    try:
        # Refresh the session
        auth_response = supabase_client.auth.refresh_session(request.refresh_token)
        
        if auth_response.session:
            session = auth_response.session
            
            logger.info(f"[{request_id}] Token refresh successful")
            
            return create_success_response(
                data={
                    "access_token": session.access_token,
                    "refresh_token": session.refresh_token,
                    "token_type": "bearer",
                    "expires_in": session.expires_in
                },
                request_id=request_id
            )
        else:
            raise auth_error("Invalid refresh token")
            
    except Exception as e:
        logger.warning(f"[{request_id}] Token refresh failed: {str(e)}")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=create_error_response(
                auth_error("Invalid or expired refresh token"),
                request_id
            )
        )
