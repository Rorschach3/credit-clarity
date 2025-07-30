### `backend/models/llm_models.py`
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