"""
API request schemas for validation
Standardized input validation across endpoints
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime

class PaginationParams(BaseModel):
    """Standard pagination parameters."""
    page: int = Field(1, ge=1, description="Page number (1-based)")
    limit: int = Field(50, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$", description="Sort order")

class FileUploadRequest(BaseModel):
    """File upload request validation."""
    filename: str = Field(..., min_length=1, max_length=255)
    file_size: int = Field(..., gt=0, description="File size in bytes")
    file_type: str = Field(..., pattern="^application/pdf$", description="Must be PDF")
    
    @validator('filename')
    def validate_filename(cls, v):
        if not v.lower().endswith('.pdf'):
            raise ValueError('Filename must end with .pdf')
        return v

class ProcessingOptions(BaseModel):
    """PDF processing options."""
    use_ocr: bool = Field(True, description="Enable OCR processing")
    use_ai_analysis: bool = Field(True, description="Enable AI analysis")
    priority: str = Field("normal", pattern="^(low|normal|high)$", description="Processing priority")
    save_to_database: bool = Field(True, description="Save results to database")
    
class TradelineCreateRequest(BaseModel):
    """Create new tradeline request."""
    creditor_name: str = Field(..., min_length=1, max_length=255)
    account_number: Optional[str] = Field(None, max_length=50)
    account_type: str = Field(..., max_length=50)
    account_status: str = Field(..., max_length=50)
    account_balance: Optional[str] = Field(None, max_length=20)
    credit_limit: Optional[str] = Field(None, max_length=20)
    monthly_payment: Optional[str] = Field(None, max_length=20)
    date_opened: Optional[str] = Field(None, description="Date account was opened")
    credit_bureau: str = Field(..., max_length=20)
    is_negative: bool = Field(False, description="Is this a negative tradeline")
    dispute_count: int = Field(0, ge=0, description="Number of disputes filed")

class TradelineUpdateRequest(BaseModel):
    """Update tradeline request."""
    creditor_name: Optional[str] = Field(None, min_length=1, max_length=255)
    account_number: Optional[str] = Field(None, max_length=50)
    account_type: Optional[str] = Field(None, max_length=50)
    account_status: Optional[str] = Field(None, max_length=50)
    account_balance: Optional[str] = Field(None, max_length=20)
    credit_limit: Optional[str] = Field(None, max_length=20)
    monthly_payment: Optional[str] = Field(None, max_length=20)
    date_opened: Optional[str] = Field(None)
    credit_bureau: Optional[str] = Field(None, max_length=20)
    is_negative: Optional[bool] = Field(None)
    dispute_count: Optional[int] = Field(None, ge=0)

class UserProfileUpdateRequest(BaseModel):
    """Update user profile request."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=50)
    state: Optional[str] = Field(None, max_length=2)
    zip_code: Optional[str] = Field(None, max_length=10)

class DisputeLetterRequest(BaseModel):
    """Generate dispute letter request."""
    tradeline_ids: List[int] = Field(..., min_items=1, description="Tradeline IDs to dispute")
    dispute_reasons: List[str] = Field(..., min_items=1, description="Reasons for dispute")
    personal_statement: Optional[str] = Field(None, max_length=500, description="Personal statement")
    letter_type: str = Field("standard", pattern="^(standard|advanced|custom)$")
    
class CacheManagementRequest(BaseModel):
    """Cache management operations."""
    action: str = Field(..., pattern="^(clear|warm|stats)$", description="Cache action")
    cache_type: Optional[str] = Field(None, pattern="^(redis|memory|all)$", description="Cache type")
    keys: Optional[List[str]] = Field(None, description="Specific cache keys")