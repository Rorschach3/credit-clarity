"""
Tradeline data schemas
Data models for credit report tradeline information
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator

class TradelineBase(BaseModel):
    """Base tradeline model."""
    creditor_name: str = Field(..., description="Name of the creditor")
    account_number: Optional[str] = Field(None, description="Account number (masked)")
    account_type: str = Field(..., description="Type of account (credit card, loan, etc.)")
    account_status: str = Field(..., description="Current status of account")
    account_balance: Optional[str] = Field(None, description="Current balance")
    credit_limit: Optional[str] = Field(None, description="Credit limit")
    monthly_payment: Optional[str] = Field(None, description="Monthly payment amount")
    date_opened: Optional[str] = Field(None, description="Date account was opened")
    credit_bureau: str = Field(..., description="Credit bureau (Experian, Equifax, TransUnion)")
    is_negative: bool = Field(False, description="Whether this is a negative tradeline")
    dispute_count: int = Field(0, description="Number of times this has been disputed")

class TradelineCreate(TradelineBase):
    """Tradeline creation model."""
    user_id: Optional[str] = Field(None, description="User ID (set by server)")

class TradelineResponse(TradelineBase):
    """Tradeline response model."""
    id: int = Field(..., description="Unique tradeline ID")
    user_id: str = Field(..., description="User who owns this tradeline")
    created_at: datetime = Field(..., description="When tradeline was created")
    updated_at: Optional[datetime] = Field(None, description="When tradeline was last updated")
    
    class Config:
        from_attributes = True

class TradelineUpdate(BaseModel):
    """Tradeline update model."""
    creditor_name: Optional[str] = None
    account_number: Optional[str] = None
    account_type: Optional[str] = None
    account_status: Optional[str] = None
    account_balance: Optional[str] = None
    credit_limit: Optional[str] = None
    monthly_payment: Optional[str] = None
    date_opened: Optional[str] = None
    credit_bureau: Optional[str] = None
    is_negative: Optional[bool] = None
    dispute_count: Optional[int] = None

class TradeLinesStats(BaseModel):
    """Tradeline statistics."""
    total_tradelines: int
    positive_tradelines: int
    negative_tradelines: int
    disputed_tradelines: int
    by_credit_bureau: Dict[str, int]
    by_account_type: Dict[str, int]
    by_account_status: Dict[str, int]
    average_account_age_months: Optional[float] = None
    total_credit_limit: Optional[float] = None
    total_balance: Optional[float] = None
    credit_utilization_ratio: Optional[float] = None

class TradelineAnalysis(BaseModel):
    """AI analysis of tradeline."""
    accuracy_score: float = Field(..., ge=0, le=1, description="Confidence in extraction accuracy")
    potential_issues: List[str] = Field(default_factory=list, description="Potential data issues")
    improvement_suggestions: List[str] = Field(default_factory=list, description="Suggestions for data quality")
    risk_factors: List[str] = Field(default_factory=list, description="Credit risk factors identified")
    positive_factors: List[str] = Field(default_factory=list, description="Positive credit factors")

class BulkTradelineOperation(BaseModel):
    """Bulk operations on tradelines."""
    operation: str = Field(..., pattern="^(update|delete|dispute)$", description="Operation to perform")
    tradeline_ids: List[int] = Field(..., min_items=1, description="Tradeline IDs to operate on")
    update_data: Optional[Dict[str, Any]] = Field(None, description="Data for update operations")
    batch_size: int = Field(50, ge=1, le=100, description="Batch size for processing")