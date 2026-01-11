"""
LLM-specific data models for Credit Clarity backend.
Contains models for LLM responses, validation, and consumer information.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from .tradeline_models import Tradeline


class IssueSeverity(Enum):
    """Severity levels for validation issues"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueType(Enum):
    """Types of validation issues"""
    DATA_QUALITY = "data_quality"
    MISSING_FIELD = "missing_field"
    INVALID_FORMAT = "invalid_format"
    INCONSISTENT_DATA = "inconsistent_data"
    LOW_CONFIDENCE = "low_confidence"
    PARSING_ERROR = "parsing_error"


@dataclass
class ValidationIssue:
    """Represents a validation issue found during processing"""
    type: str  # IssueType value
    description: str
    severity: str  # IssueSeverity value
    tradeline_index: Optional[int] = None
    field_name: Optional[str] = None
    suggested_fix: Optional[str] = None
    confidence_impact: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "type": self.type,
            "description": self.description,
            "severity": self.severity,
            "tradeline_index": self.tradeline_index,
            "field_name": self.field_name,
            "suggested_fix": self.suggested_fix,
            "confidence_impact": self.confidence_impact
        }


@dataclass
class ConsumerInfo:
    """Consumer personal information extracted from credit report"""
    name: str
    ssn: Optional[str] = None
    date_of_birth: Optional[str] = None
    addresses: List[str] = field(default_factory=list)
    phone_numbers: List[str] = field(default_factory=list)
    email: Optional[str] = None
    confidence_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "ssn": self.ssn,
            "date_of_birth": self.date_of_birth,
            "addresses": self.addresses,
            "phone_numbers": self.phone_numbers,
            "email": self.email,
            "confidence_score": self.confidence_score
        }


@dataclass
class ValidationResult:
    """Results from validation of extracted data"""
    overall_confidence: float
    issues: List[ValidationIssue] = field(default_factory=list)
    tradeline_scores: Dict[int, float] = field(default_factory=dict)
    consumer_info_score: float = 0.0
    passed_validation: bool = True
    validation_timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "overall_confidence": self.overall_confidence,
            "issues": [issue.to_dict() for issue in self.issues],
            "tradeline_scores": self.tradeline_scores,
            "consumer_info_score": self.consumer_info_score,
            "passed_validation": self.passed_validation,
            "validation_timestamp": self.validation_timestamp,
            "metadata": self.metadata
        }

    def add_issue(self, issue: ValidationIssue):
        """Add a validation issue"""
        self.issues.append(issue)
        if issue.severity in [IssueSeverity.HIGH.value, IssueSeverity.CRITICAL.value]:
            self.overall_confidence -= issue.confidence_impact
            self.overall_confidence = max(0.0, self.overall_confidence)

    def has_critical_issues(self) -> bool:
        """Check if there are any critical issues"""
        return any(issue.severity == IssueSeverity.CRITICAL.value for issue in self.issues)


@dataclass
class NormalizationResult:
    """Result from LLM normalization process"""
    job_id: str
    consumer_info: ConsumerInfo
    tradelines: List[Tradeline]
    validation_results: ValidationResult
    confidence_score: float
    processing_metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "job_id": self.job_id,
            "consumer_info": self.consumer_info.to_dict(),
            "tradelines": [
                {
                    "id": str(tl.id),
                    "user_id": str(tl.user_id),
                    "credit_bureau": tl.credit_bureau,
                    "account_number": tl.account_number,
                    "creditor_name": tl.creditor_name,
                    "account_type": tl.account_type,
                    "account_balance": tl.account_balance,
                    "credit_limit": tl.credit_limit,
                    "monthly_payment": tl.monthly_payment,
                    "account_status": tl.account_status,
                    "date_opened": tl.date_opened,
                    "dispute_count": tl.dispute_count,
                    "is_negative": tl.is_negative,
                    "created_at": tl.created_at.isoformat() if isinstance(tl.created_at, datetime) else tl.created_at
                }
                for tl in self.tradelines
            ],
            "validation_results": self.validation_results.to_dict(),
            "confidence_score": self.confidence_score,
            "processing_metadata": self.processing_metadata,
            "created_at": self.created_at
        }

    def get_high_confidence_tradelines(self, threshold: float = 0.7) -> List[Tradeline]:
        """Get tradelines with confidence above threshold"""
        return [
            tl for i, tl in enumerate(self.tradelines)
            if self.validation_results.tradeline_scores.get(i, 0.0) >= threshold
        ]

    def get_failed_tradelines(self) -> List[Tradeline]:
        """Get tradelines with critical validation issues"""
        failed_indices = {
            issue.tradeline_index for issue in self.validation_results.issues
            if issue.severity == IssueSeverity.CRITICAL.value and issue.tradeline_index is not None
        }
        return [tl for i, tl in enumerate(self.tradelines) if i in failed_indices]


@dataclass
class LLMExtractionResult:
    """Result from LLM extraction of tradeline fields"""
    tradeline_data: Dict[str, Any]
    confidence_score: float
    extracted_fields: List[str]
    missing_fields: List[str]
    extraction_notes: str = ""
    model_used: str = "unknown"
    tokens_used: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "tradeline_data": self.tradeline_data,
            "confidence_score": self.confidence_score,
            "extracted_fields": self.extracted_fields,
            "missing_fields": self.missing_fields,
            "extraction_notes": self.extraction_notes,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used
        }


@dataclass
class PromptResponse:
    """Wrapper for LLM prompt responses"""
    raw_response: str
    parsed_data: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: Optional[str] = None
    model: str = "unknown"
    tokens_used: int = 0
    response_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "raw_response": self.raw_response,
            "parsed_data": self.parsed_data,
            "success": self.success,
            "error_message": self.error_message,
            "model": self.model,
            "tokens_used": self.tokens_used,
            "response_time": self.response_time
        }
