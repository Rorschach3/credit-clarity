from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional
import logging
from datetime import datetime

from ..services.llm_parser_service import LLMParserService, ProcessingContext
from ..services.storage_service import StorageService
from ..models.llm_models import (
    LLMRequest, 
    LLMResponse, 
    NormalizationResult,
    ValidationRequest,
    ValidationResponse
)
from ..config.llm_config import get_llm_config
from ..utils.auth import get_current_user
from ..utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/llm", tags=["llm-parsing"])

# Rate limiter for LLM operations
rate_limiter = RateLimiter(max_requests=10, window_minutes=1)

@router.post("/normalize", response_model=NormalizationResult)
async def normalize_document_data(
    request: LLMRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    llm_service: LLMParserService = Depends(get_llm_service),
    storage_service: StorageService = Depends(get_storage_service)
):
    """
    Normalize document data using LLM
    
    This endpoint takes raw document data and normalizes it into
    structured tradeline and consumer information.
    """
    
    # Check rate limit
    if not rate_limiter.allow_request(current_user.get("user_id")):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )
    
    try:
        # Get processing context
        context = ProcessingContext(
            job_id=request.job_id,
            document_type=request.document_type,
            confidence_threshold=request.confidence_threshold or 0.7
        )
        
        # Get document data from storage
        document_data = await storage_service.get_document_ai_results(request.job_id)
        
        if not document_data:
            raise HTTPException(
                status_code=404,
                detail=f"Document AI results not found for job {request.job_id}"
            )
        
        # Start normalization process
        start_time = datetime.utcnow()
        
        logger.info(f"Starting LLM normalization for job {request.job_id}")
        
        # Perform normalization
        result = await llm_service.normalize_tradeline_data(
            raw_text=document_data.get("text_content", ""),
            table_data=document_data.get("tables", []),
            context=context
        )
        
        # Calculate processing duration
        processing_duration = (datetime.utcnow() - start_time).total_seconds()
        result.processing_metadata["processing_duration"] = processing_duration
        
        # Store results
        background_tasks.add_task(
            storage_service.store_llm_results,
            request.job_id,
            result
        )
        
        # Update job status
        background_tasks.add_task(
            storage_service.update_job_status,
            request.job_id,
            "llm_completed",
            {"llm_processing_duration": processing_duration}
        )
        
        logger.info(f"LLM normalization completed for job {request.job_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in LLM normalization: {str(e)}")
        
        # Update job status with error
        background_tasks.add_task(
            storage_service.update_job_status,
            request.job_id,
            "llm_failed",
            {"error": str(e)}
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"LLM normalization failed: {str(e)}"
        )

@router.post("/validate", response_model=ValidationResponse)
async def validate_normalized_data(
    request: ValidationRequest,
    current_user: dict = Depends(get_current_user),
    llm_service: LLMParserService = Depends(get_llm_service)
):
    """
    Validate normalized data using LLM
    
    This endpoint validates the consistency and accuracy of
    normalized tradeline data.
    """
    
    try:
        context = ProcessingContext(
            job_id=request.job_id,
            document_type=request.document_type,
            confidence_threshold=request.confidence_threshold or 0.7
        )
        
        # Perform validation
        validation_result = await llm_service._validate_and_score(
            tradelines=request.tradelines,
            consumer_info=request.consumer_info,
            context=context
        )
        
        return ValidationResponse(
            job_id=request.job_id,
            validation_result=validation_result,
            validated_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in data validation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Data validation failed: {str(e)}"
        )

@router.get("/jobs/{job_id}/results")
async def get_llm_results(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    storage_service: StorageService = Depends(get_storage_service)
):
    """
    Get LLM processing results for a specific job
    """
    
    try:
        results = await storage_service.get_llm_results(job_id)
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"LLM results not found for job {job_id}"
            )
        
        return results
        
    except Exception as e:
        logger.error(f"Error retrieving LLM results: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve LLM results: {str(e)}"
        )

@router.post("/jobs/{job_id}/reprocess")
async def reprocess_with_llm(
    job_id: str,
    background_tasks: BackgroundTasks,
    confidence_threshold: Optional[float] = 0.7,
    current_user: dict = Depends(get_current_user),
    llm_service: LLMParserService = Depends(get_llm_service),
    storage_service: StorageService = Depends(get_storage_service)
):
    """
    Reprocess document data with LLM using different parameters
    """
    
    try:
        # Get original document data
        document_data = await storage_service.get_document_ai_results(job_id)
        
        if not document_data:
            raise HTTPException(
                status_code=404,
                detail=f"Document AI results not found for job {job_id}"
            )
        
        # Create new processing context
        context = ProcessingContext(
            job_id=job_id,
            document_type=document_data.get("document_type", "credit_report"),
            confidence_threshold=confidence_threshold
        )
        
        # Start reprocessing in background
        background_tasks.add_task(
            _reprocess_job_background,
            job_id,
            document_data,
            context,
            llm_service,
            storage_service
        )
        
        return JSONResponse(
            content={
                "message": f"Reprocessing started for job {job_id}",
                "job_id": job_id,
                "status": "reprocessing"
            }
        )
        
    except Exception as e:
        logger.error(f"Error starting reprocessing: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start reprocessing: {str(e)}"
        )

async def _reprocess_job_background(
    job_id: str,
    document_data: dict,
    context: ProcessingContext,
    llm_service: LLMParserService,
    storage_service: StorageService
):
    """Background task for reprocessing job with LLM"""
    
    try:
        # Update status to reprocessing
        await storage_service.update_job_status(
            job_id, 
            "reprocessing", 
            {"reprocess_started_at": datetime.utcnow().isoformat()}
        )
        
        # Perform normalization
        result = await llm_service.normalize_tradeline_data(
            raw_text=document_data.get("text_content", ""),
            table_data=document_data.get("tables", []),
            context=context
        )
        
        # Store new results
        await storage_service.store_llm_results(job_id, result)
        
        # Update job status
        await storage_service.update_job_status(
            job_id,
            "reprocess_completed",
            {"reprocess_completed_at": datetime.utcnow().isoformat()}
        )
        
    except Exception as e:
        logger.error(f"Error in background reprocessing: {str(e)}")
        await storage_service.update_job_status(
            job_id,
            "reprocess_failed",
            {"error": str(e)}
        )

# Dependency functions
async def get_llm_service() -> LLMParserService:
    """Get LLM parser service instance"""
    config = get_llm_config()
    return LLMParserService(config)

---

## 4. Data Models for LLM Operations

### `backend/models/llm_models.py`

```python
"""
Data models for LLM request/response operations
"""
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from decimal import Decimal

from .tradeline_models import Tradeline, ConsumerInfo

class LLMRequest(BaseModel):
    """Request model for LLM processing"""
    job_id: str = Field(..., description="Unique job identifier")
    document_type: str = Field(default="credit_report", description="Type of document being processed")
    confidence_threshold: Optional[float] = Field(default=0.7, ge=0.0, le=1.0)
    processing_options: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('confidence_threshold')
    def validate_confidence_threshold(cls, v):
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError('Confidence threshold must be between 0.0 and 1.0')
        return v

class NormalizationResult(BaseModel):
    """Result of LLM normalization process"""
    job_id: str
    consumer_info: ConsumerInfo
    tradelines: List[Tradeline]
    validation_results: Optional[Any] = None  # ValidationResult type
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    processing_metadata: Dict[str, Any] = Field(default_factory=dict)
    normalized_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: str(v)
        }

class ValidationRequest(BaseModel):
    """Request model for data validation"""
    job_id: str
    document_type: str = "credit_report"
    tradelines: List[Tradeline]
    consumer_info: ConsumerInfo
    confidence_threshold: Optional[float] = 0.7
    validation_rules: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ValidationIssue(BaseModel):
    """Individual validation issue"""
    type: str = Field(..., description="Type of validation issue")
    description: str = Field(..., description="Detailed description of the issue")
    severity: str = Field(..., description="Severity level: low, medium, high, critical")
    tradeline_index: Optional[int] = Field(None, description="Index of affected tradeline")
    field_name: Optional[str] = Field(None, description="Name of affected field")
    suggested_fix: Optional[str] = Field(None, description="Suggested fix for the issue")

class ValidationSuggestion(BaseModel):
    """Validation improvement suggestion"""
    type: str = Field(..., description="Type of suggestion")
    description: str = Field(..., description="Detailed description")
    priority: str = Field(..., description="Priority level: low, medium, high")
    affected_items: Optional[List[str]] = Field(default_factory=list)

class QualityMetrics(BaseModel):
    """Data quality metrics"""
    completeness: float = Field(..., ge=0.0, le=1.0, description="Completeness score")
    accuracy: float = Field(..., ge=0.0, le=1.0, description="Accuracy score")
    consistency: float = Field(..., ge=0.0, le=1.0, description="Consistency score")
    reliability: float = Field(..., ge=0.0, le=1.0, description="Reliability score")

class ValidationSummary(BaseModel):
    """Summary of validation results"""
    total_tradelines: int = Field(..., ge=0)
    valid_tradelines: int = Field(..., ge=0)
    invalid_tradelines: int = Field(..., ge=0)
    warning_tradelines: int = Field(..., ge=0)
    data_quality_score: float = Field(..., ge=0.0, le=1.0)
    
    @validator('invalid_tradelines', 'valid_tradelines', 'warning_tradelines')
    def validate_tradeline_counts(cls, v, values):
        if 'total_tradelines' in values:
            total = values['total_tradelines']
            # These validations would run after all fields are processed
        return v

class ValidationResult(BaseModel):
    """Complete validation result"""
    overall_confidence: float = Field(..., ge=0.0, le=1.0)
    validation_summary: ValidationSummary
    issues_found: List[ValidationIssue] = Field(default_factory=list)
    suggestions: List[ValidationSuggestion] = Field(default_factory=list)
    quality_metrics: QualityMetrics
    validation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ValidationResponse(BaseModel):
    """Response model for validation operations"""
    job_id: str
    validation_result: ValidationResult
    validated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class LLMResponse(BaseModel):
    """Generic LLM response model"""
    job_id: str
    operation: str = Field(..., description="Type of LLM operation performed")
    result: Dict[str, Any] = Field(..., description="Operation result data")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None
    processing_time: Optional[float] = None
    tokens_used: Optional[int] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ReprocessingRequest(BaseModel):
    """Request model for reprocessing with different parameters"""
    job_id: str
    confidence_threshold: Optional[float] = Field(default=0.7, ge=0.0, le=1.0)
    processing_options: Optional[Dict[str, Any]] = Field(default_factory=dict)
    force_reprocess: bool = Field(default=False, description="Force reprocessing even if recent results exist")