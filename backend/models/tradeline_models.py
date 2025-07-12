from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

# ---------------------------
# Enums
# ---------------------------

class DocumentType(Enum):
    PDF = "pdf"
    IMAGE = "image"
    DOCX = "docx"
    TXT = "txt"
    UNKNOWN = "unknown"

class ProcessingStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TradelineStatus(Enum):
    CURRENT = "current"
    LATE = "late"
    CLOSED = "closed"
    CHARGED_OFF = "charged_off"
    COLLECTION = "collection"

# ---------------------------
# AI Result Data Structures
# ---------------------------

@dataclass
class ExtractedTable:
    table_id: str
    headers: List[str]
    rows: List[List[str]]
    confidence: float
    page_number: int
    bounding_box: Optional[Dict[str, float]] = None

@dataclass
class ExtractedText:
    content: str
    page_number: int
    confidence: float
    bounding_box: Optional[Dict[str, float]] = None

@dataclass
class DocumentAIResult:
    job_id: str
    document_type: DocumentType
    total_pages: int
    tables: List[ExtractedTable]
    text_blocks: List[ExtractedText]
    raw_text: str
    metadata: Dict[str, Any]
    processing_time: float
# Single tradeline model for LLM and parsing logic
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Tradeline:
    creditor_name: str
    account_number: str
    account_type: Optional[str] = None
    account_balance: Optional[str] = None
    credit_limit: Optional[str] = None
    account_status: Optional[str] = None
    date_opened: Optional[datetime] = None
    credit_bureau: Optional[str] = None
    created_on: Optional[datetime] = None
    is_negative: bool = False

# ---------------------------
# App Data Models
# ---------------------------

@dataclass
class Tradelines:
    id: str
    user_id: str
    account_number: str
    creditor_name: str
    account_type: str
    account_balance: str
    credit_limit: str
    account_status: str
    date_opened: datetime
    credit_bureau: str
    created_on: datetime
    is_negative: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'account_number': self.account_number,
            'creditor_name': self.creditor_name,
            'account_type': self.account_type,
            'account_balance': self.account_balance,
            'credit_limit': self.credit_limit,
            'account_status': self.account_status,
            'date_opened': self.date_opened.isoformat() if self.date_opened else None,
            'created_on': self.created_on.isoformat(),
            'is_negative': self.is_negative,
            'credit_bureau': self.credit_bureau
        }

@dataclass
class Profiles:
    id: uuid.UUID
    first_name: str
    last_name: str
    address1: str
    city: str
    state: str
    zip_code: str
    phone_number: str
    dob: str
    last_four_of_ssn: str
    updated_on: datetime
    address2: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'first_name': self.first_name,
            'last_name': self.last_name,
            'address1': self.address1,
            'address2': self.address2,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'phone_number': self.phone_number,
            'dob': self.dob,
            'last_four_of_ssn': self.last_four_of_ssn,
            'updated_on': self.updated_on.isoformat()
        }

@dataclass
class ProcessingJob:
    job_id: str
    user_id: Optional[str]
    status: str
    filename: str
    file_size: int
    created_at: str
    completed_at: Optional[str]
    error_message: Optional[str]
    document_ai_result: Optional[Dict[str, Any]]
    llm_result: Optional[Dict[str, Any]]
    final_tradelines: Optional[List[Dict[str, Any]]]

# ---------------------------
# Validation Utility
# ---------------------------

class TradelineValidationSchema:
    """Schema for validating tradeline data"""

    @staticmethod
    def validate_tradeline_data(data: Dict[str, Any]) -> Dict[str, Any]:
        required_fields = ['account_number', 'creditor_name', 'account_type', 'account_status']

        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        if data['account_status'] not in [status.value for status in TradelineStatus]:
            raise ValueError(f"Invalid account status: {data['account_status']}")

        if 'account_balance' in data and data['account_balance'] is not None:
            try:
                data['account_balance'] = float(data['account_balance'])
            except ValueError:
                raise ValueError("Account balance must be a valid number")

        return data
