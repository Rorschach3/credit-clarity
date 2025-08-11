"""
Standardized API response schemas
Ensures consistent response format across all endpoints
"""
from typing import Any, Dict, List, Optional, Generic, TypeVar
from datetime import datetime
from pydantic import BaseModel, Field

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """Base API response model."""
    success: bool
    data: Optional[T] = None
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None
    version: str = "1.0"

class ErrorDetail(BaseModel):
    """Detailed error information."""
    code: str
    message: str
    field: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    """Standardized error response."""
    success: bool = False
    error: ErrorDetail
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None
    version: str = "1.0"

class PaginationMeta(BaseModel):
    """Pagination metadata."""
    page: int = 1
    limit: int = 50
    total: int
    pages: int
    has_next: bool
    has_prev: bool

class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated API response."""
    success: bool = True
    data: List[T]
    meta: PaginationMeta
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None
    version: str = "1.0"

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str
    environment: str
    services: Dict[str, Any]
    system_health: Optional[Dict[str, Any]] = None

class ProcessingResponse(BaseModel):
    """Credit report processing response."""
    job_id: Optional[str] = None
    status: str
    progress: int = 0
    tradelines_found: int = 0
    processing_method: str
    cost_estimate: float = 0.0
    processing_time: Dict[str, Any] = {}
    performance_metrics: Dict[str, Any] = {}
    cache_hit: bool = False

class JobStatusResponse(BaseModel):
    """Background job status."""
    job_id: str
    status: str
    progress: int
    message: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    processing_time: Optional[float] = None

class MetricsResponse(BaseModel):
    """System metrics response."""
    system: Dict[str, Any]
    api: Dict[str, Any]
    business: Dict[str, Any]
    background_jobs: Dict[str, Any]
    cache: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)