from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class LLMRequest(BaseModel):
    job_id: str
    document_type: str
    confidence_threshold: Optional[float] = 0.7


class Tradeline(BaseModel):
    creditor_name: str
    account_number: str
    account_type: Optional[str]
    balance: Optional[float]
    credit_limit: Optional[float]
    payment_status: Optional[str]
    date_opened: Optional[str]
    date_closed: Optional[str]
    payment_history: List[str] = []
    account_status: Optional[str]
    confidence_score: float
    normalization_notes: Optional[str]


class ConsumerInfo(BaseModel):
    name: str
    ssn: Optional[str]
    date_of_birth: Optional[str]
    addresses: List[Dict[str, Any]] = []
    phones: List[str] = []
    confidence_score: float


class ValidationResult(BaseModel):
    overall_confidence: float
    validation_summary: Dict[str, Any]
    issues_found: List[Dict[str, Any]]
    suggestions: List[Dict[str, Any]]
    quality_metrics: Dict[str, float]


class NormalizationResult(BaseModel):
    job_id: str
    consumer_info: ConsumerInfo
    tradelines: List[Tradeline]
    validation_results: Optional[ValidationResult]
    confidence_score: float
    processing_metadata: Dict[str, Any]


class ValidationRequest(BaseModel):
    job_id: str
    document_type: str
    tradelines: List[Tradeline]
    consumer_info: ConsumerInfo
    confidence_threshold: Optional[float] = 0.7


class LLMResponse(BaseModel):
    job_id: str
    validation_result: ValidationResult
    validated_at: datetime
