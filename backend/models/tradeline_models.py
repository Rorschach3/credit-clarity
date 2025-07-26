import re
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
    OPEN = "open"
    CURRENT = "current"
    LATE = "late"
    CLOSED = "closed"
    CHARGED_OFF = "charged_off"
    COLLECTION = "collection"
    LATE_DETAILED = ["30_days_late", "60_days_late", "90_days_late", "120_days_late", "150_days_late"]

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
    id: uuid.UUID
    user_id: uuid.UUID
    credit_bureau: str = "Unknown"
    account_number: Optional[str] = None
    creditor_name: Optional[str] = None
    account_type: Optional[str] = None
    account_balance: Optional[str] = "$0"
    credit_limit:  Optional[str] = "$0"
    monthly_payment: Optional[str] = "$0"
    account_status: Optional[str] = None
    date_opened: Optional[str] = None
    dispute_count: int = 0
    created_at: datetime = datetime.utcnow()
    is_negative: bool = False

# ---------------------------
# App Data Models
# ---------------------------

@dataclass
class Tradelines:
    id: uuid.UUID
    user_id: uuid.UUID
    credit_bureau: str = "Unknown"
    account_number: Optional[str] = None
    creditor_name: Optional[str] = None
    account_type: Optional[str] = None
    account_balance: Optional[str] = "$0"
    credit_limit:  Optional[str] = "$0"
    monthly_payment: Optional[str] = "$0"
    account_status: Optional[str] = None
    date_opened: Optional[str] = None
    dispute_count: int = 0
    created_at: datetime = datetime.utcnow()
    is_negative: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'account_number': self.account_number,
            'creditor_name': self.creditor_name,
            'monthly_payment': self.monthly_payment,
            'account_type': self.account_type,
            'account_balance': self.account_balance,
            'credit_limit': self.credit_limit,
            'account_status': self.account_status,
            'date_opened': self.date_opened.isoformat() if self.date_opened else None,
            'created_at': self.created_at.isoformat(),
            'is_negative': self.is_negative,
            'credit_bureau': self.credit_bureau,
            'dispute_count': self.dispute_count
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
    updated_at: datetime
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
            'updated_at': self.updated_at.isoformat()
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
    """Schema for validating and normalizing tradeline data"""

    currency_pattern = re.compile(r"^\$\d+$")
    mm_dd_yyyy_pattern = re.compile(r"^\d{2}/\d{2}/\d{4}$")
    mm_yyyy_pattern = re.compile(r"^\d{2}/\d{4}$")

    @staticmethod
    def normalize_date(value: str) -> str:
        """Normalize MM/YYYY to MM/01/YYYY, or return MM/DD/YYYY unchanged"""
        if TradelineValidationSchema.mm_dd_yyyy_pattern.match(value):
            return value
        if TradelineValidationSchema.mm_yyyy_pattern.match(value):
            mm, yyyy = value.split('/')
            return f"{mm}/01/{yyyy}"
        raise ValueError(f"Date must be in MM/YYYY or MM/DD/YYYY format: got '{value}'")

    @staticmethod
    def coerce_currency(value: Any, field_name: str) -> str:
        """Convert a value to a string in '$1234' format if possible"""
        if isinstance(value, str):
            value = value.strip()
            if TradelineValidationSchema.currency_pattern.match(value):
                return value
            if value.isdigit():
                return f"${int(value)}"
        elif isinstance(value, (int, float)):
            return f"${int(value)}"
        raise ValueError(f"{field_name} must be a number or a string formatted like '$1234'")

    @staticmethod
    def validate_tradeline_data(data: Dict[str, Any]) -> Dict[str, Any]:
        required_fields = ['account_bureau', 'creditor_name', 'account_number', 'date_opened']

        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        if data['account_status'] not in [status.value for status in TradelineStatus]:
            raise ValueError(f"Invalid account status: {data['account_status']}")

        # Normalize/validate currency fields
        for field in ['account_balance', 'monthly_payment', 'credit_limit']:
            if field in data and data[field] is not None:
                data[field] = TradelineValidationSchema.coerce_currency(data[field], field)

        # Normalize date format
        if 'date_opened' in data and data['date_opened']:
            data['date_opened'] = TradelineValidationSchema.normalize_date(data['date_opened'])

        return data