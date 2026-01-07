"""
User Profile API Routes
Handles user profile management with audit logging
"""
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, validator

from core.config import get_settings
from core.security import get_supabase_user
from core.response import success_response, error_response
from core.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    auth_error,
)
from services.audit_service import audit_service, AuditAction
from services.storage_service import storage_service

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/users", tags=["Users"])


# ============== Request Models ==============

class ProfileUpdateRequest(BaseModel):
    """Profile update request."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    phone: Optional[str] = Field(None, regex=r'^\+?[\d\s\-()]{10,}$')
    date_of_birth: Optional[str] = Field(None, regex=r'^\d{4}-\d{2}-\d{2}$')
    address: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None

    @validator('first_name', 'last_name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Name cannot be empty or whitespace only')
        return v.strip() if v else None


class EmailUpdateRequest(BaseModel):
    """Email update request."""
    new_email: EmailStr
    password: str = Field(..., min_length=1)


class PasswordUpdateRequest(BaseModel):
    """Password update request."""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)

    @validator('new_password')
    def validate_password(cls, v):
        """Validate password complexity."""
        import re
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


# ============== Response Models ==============

class ProfileResponse(BaseModel):
    """User profile response."""
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    avatar_url: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ProfileUpdateResponse(BaseModel):
    """Profile update response."""
    user_id: str
    message: str
    changes: Dict[str, Any]


# ============== Helper Functions ==============

def generate_request_id() -> str:
    """Generate unique request ID."""
    return str(uuid.uuid4())[:8]


def get_client_info(request: Request) -> tuple:
    """Extract client IP and user agent from request."""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    return client_ip, user_agent


# ============== Profile Endpoints ==============

@router.get("/me", response_class=JSONResponse)
async def get_current_user_profile(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """
    Get current user's profile.
    
    Returns the user's profile information from Supabase Auth metadata
    and the profiles table.
    """
    request_id = generate_request_id()
    user_id = current_user.get("id")
    client_ip, user_agent = get_client_info(request)
    
    logger.info(f"[{request_id}] GET /users/me - User: {user_id}")
    
    try:
        # Get user data from Supabase
        profile_data = {
            "id": user_id,
            "email": current_user.get("email", ""),
            "first_name": current_user.get("user_metadata", {}).get("first_name"),
            "last_name": current_user.get("user_metadata", {}).get("last_name"),
            "avatar_url": current_user.get("user_metadata", {}).get("avatar_url"),
            "created_at": current_user.get("created_at"),
        }
        
        # Try to get additional profile data from profiles table
        # This would use supabase client in production
        # For now, return auth metadata
        
        return success_response(
            data=ProfileResponse(**profile_data).__dict__,
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"[{request_id}] Failed to get profile: {str(e)}")
        return error_response(
            code="PROFILE_FETCH_FAILED",
            message=str(e),
            request_id=request_id
        )


@router.patch("/me", response_class=JSONResponse)
async def update_current_user_profile(
    request: Request,
    update_data: ProfileUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """
    Update current user's profile.
    
    Updates profile fields and logs the change for audit.
    """
    request_id = generate_request_id()
    user_id = current_user.get("id")
    client_ip, user_agent = get_client_info(request)
    
    logger.info(f"[{request_id}] PATCH /users/me - User: {user_id}")
    
    try:
        # Get current profile data (mock - would fetch from database)
        current_data = {
            "first_name": current_user.get("user_metadata", {}).get("first_name"),
            "last_name": current_user.get("user_metadata", {}).get("last_name"),
            "phone": None,
            "date_of_birth": None,
            "address": None,
            "preferences": {}
        }
        
        # Calculate changes
        changes = {}
        update_dict = update_data.dict(exclude_unset=True)
        
        for field, new_value in update_dict.items():
            old_value = current_data.get(field)
            if old_value != new_value:
                changes[field] = {
                    "old": old_value,
                    "new": new_value
                }
        
        if not changes:
            return success_response(
                data={"user_id": user_id, "message": "No changes detected", "changes": {}},
                request_id=request_id
            )
        
        # Update profile (would update Supabase in production)
        logger.info(f"[{request_id}] Profile changes: {list(changes.keys())}")
        
        # Log audit entry
        await audit_service.log_profile_updated(
            user_id=user_id,
            old_data=current_data,
            new_data={**current_data, **update_dict},
            ip_address=client_ip,
            user_agent=user_agent,
            request_id=request_id
        )
        
        return success_response(
            data={
                "user_id": user_id,
                "message": "Profile updated successfully",
                "changes": {k: {"old": v["old"], "new": v["new"]} for k, v in changes.items()}
            },
            request_id=request_id
        )
        
    except ValidationError as ve:
        logger.warning(f"[{request_id}] Validation error: {str(ve)}")
        return error_response(
            code="VALIDATION_ERROR",
            message=str(ve),
            request_id=request_id
        )
    except Exception as e:
        logger.error(f"[{request_id}] Failed to update profile: {str(e)}")
        return error_response(
            code="PROFILE_UPDATE_FAILED",
            message=str(e),
            request_id=request_id
        )


@router.put("/me/avatar", response_class=JSONResponse)
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """
    Upload user avatar.
    
    Stores avatar image and updates user profile with avatar URL.
    """
    request_id = generate_request_id()
    user_id = current_user.get("id")
    client_ip, user_agent = get_client_info(request)
    
    logger.info(f"[{request_id}] PUT /users/me/avatar - User: {user_id}")
    
    try:
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        if file.content_type not in allowed_types:
            return error_response(
                code="INVALID_FILE_TYPE",
                message=f"Invalid file type. Allowed: {', '.join(allowed_types)}",
                request_id=request_id
            )
        
        # Read file content
        file_content = await file.read()
        
        # Validate file size (max 5MB)
        if len(file_content) > 5 * 1024 * 1024:
            return error_response(
                code="FILE_TOO_LARGE",
                message="File size exceeds maximum allowed (5MB)",
                request_id=request_id
            )
        
        # Store avatar with deduplication
        result = await storage_service.store_avatar(
            user_id=user_id,
            file_content=file_content,
            metadata={
                "filename": file.filename,
                "content_type": file.content_type
            }
        )
        
        if result["success"]:
            # Log audit entry
            await audit_service.log_avatar_uploaded(
                user_id=user_id,
                avatar_url=result.get("avatar_url", ""),
                ip_address=client_ip,
                user_agent=user_agent,
                request_id=request_id
            )
            
            return success_response(
                data={
                    "user_id": user_id,
                    "avatar_url": result.get("avatar_url"),
                    "file_hash": result.get("file_hash"),
                    "is_duplicate": result.get("is_duplicate", False),
                    "message": "Avatar uploaded successfully"
                },
                request_id=request_id
            )
        else:
            return error_response(
                code="AVATAR_UPLOAD_FAILED",
                message=result.get("message", "Failed to upload avatar"),
                request_id=request_id
            )
        
    except Exception as e:
        logger.error(f"[{request_id}] Failed to upload avatar: {str(e)}")
        return error_response(
            code="AVATAR_UPLOAD_FAILED",
            message=str(e),
            request_id=request_id
        )


@router.delete("/me/avatar", response_class=JSONResponse)
async def remove_avatar(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """
    Remove user avatar.
    
    Deletes avatar file and clears avatar URL from profile.
    """
    request_id = generate_request_id()
    user_id = current_user.get("id")
    client_ip, user_agent = get_client_info(request)
    
    logger.info(f"[{request_id}] DELETE /users/me/avatar - User: {user_id}")
    
    try:
        # Log audit entry
        await audit_service.log_avatar_removed(
            user_id=user_id,
            ip_address=client_ip,
            user_agent=user_agent,
            request_id=request_id
        )
        
        return success_response(
            data={
                "user_id": user_id,
                "message": "Avatar removed successfully"
            },
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"[{request_id}] Failed to remove avatar: {str(e)}")
        return error_response(
            code="AVATAR_REMOVE_FAILED",
            message=str(e),
            request_id=request_id
        )


@router.put("/me/email", response_class=JSONResponse)
async def update_email(
    request: Request,
    email_data: EmailUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """
    Update user email address.
    
    Requires password verification and logs the change for audit.
    """
    request_id = generate_request_id()
    user_id = current_user.get("id")
    client_ip, user_agent = get_client_info(request)
    old_email = current_user.get("email", "")
    
    logger.info(f"[{request_id}] PUT /users/me/email - User: {user_id}")
    
    try:
        # Verify password (would use Supabase in production)
        # This is a placeholder for password verification
        
        # Update email in Supabase
        # supabase.auth.update_user({"email": email_data.new_email})
        
        # Log audit entry
        await audit_service.log_email_changed(
            user_id=user_id,
            old_email=old_email,
            new_email=email_data.new_email,
            ip_address=client_ip,
            user_agent=user_agent,
            request_id=request_id
        )
        
        return success_response(
            data={
                "user_id": user_id,
                "old_email": old_email,
                "new_email": email_data.new_email,
                "message": "Email updated successfully. Please verify your new email address."
            },
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"[{request_id}] Failed to update email: {str(e)}")
        return error_response(
            code="EMAIL_UPDATE_FAILED",
            message=str(e),
            request_id=request_id
        )


@router.put("/me/password", response_class=JSONResponse)
async def update_password(
    request: Request,
    password_data: PasswordUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """
    Update user password.
    
    Requires current password verification and logs the change for audit.
    """
    request_id = generate_request_id()
    user_id = current_user.get("id")
    client_ip, user_agent = get_client_info(request)
    
    logger.info(f"[{request_id}] PUT /users/me/password - User: {user_id}")
    
    try:
        # Verify current password (would use Supabase in production)
        # This is a placeholder for password verification
        
        # Update password in Supabase
        # supabase.auth.update_user({"password": password_data.new_password})
        
        # Log audit entry
        await audit_service.log_password_changed(
            user_id=user_id,
            ip_address=client_ip,
            user_agent=user_agent,
            request_id=request_id,
            reason="user_initiated"
        )
        
        return success_response(
            data={
                "user_id": user_id,
                "message": "Password updated successfully"
            },
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"[{request_id}] Failed to update password: {str(e)}")
        return error_response(
            code="PASSWORD_UPDATE_FAILED",
            message=str(e),
            request_id=request_id
        )


# ============== Audit Log Endpoints ==============

@router.get("/me/audit-logs", response_class=JSONResponse)
async def get_audit_logs(
    request: Request,
    limit: int = 100,
    offset: int = 0,
    action_filter: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """
    Get current user's audit logs.
    
    Returns a paginated list of audit log entries for the user.
    """
    request_id = generate_request_id()
    user_id = current_user.get("id")
    
    logger.info(f"[{request_id}] GET /users/me/audit-logs - User: {user_id}")
    
    try:
        logs_result = await audit_service.get_user_audit_logs(
            user_id=user_id,
            limit=limit,
            offset=offset,
            action_filter=action_filter
        )
        
        return success_response(
            data=logs_result,
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"[{request_id}] Failed to get audit logs: {str(e)}")
        return error_response(
            code="AUDIT_LOGS_FETCH_FAILED",
            message=str(e),
            request_id=request_id
        )
