from typing import Dict, List, Any
from dataclasses import dataclass
import json

@dataclass
class ProcessingContext:
    job_id: str
    document_type: str
    confidence_threshold: float = 0.7

class PromptTemplates:
    """Collection of prompt templates for different LLM operations"""
    
    def get_extraction_prompt(
        self, 
        raw_text: str, 
        table_data: List[Dict], 
        document_type: str
    ) -> str:
        """Generate prompt for extracting structured data from raw document"""
        
        return f"""
You are an expert document parser specializing in credit reports and financial documents.

DOCUMENT TYPE: {document_type}

RAW TEXT FROM DOCUMENT:
{raw_text[:5000]}  # Truncate for token limits

TABLE DATA:
{json.dumps(table_data, indent=2)[:3000]}  # Truncate for token limits

TASK: Extract and structure the following information from the document:

1. CONSUMER INFORMATION:
   - Full name
   - Social Security Number (if present)
   - Date of birth
   - Current and previous addresses
   - Phone numbers

2. TRADELINE INFORMATION:
   - Creditor/Company name
   - Account number (masked if necessary)
   - Account type (Credit Card, Mortgage, Auto Loan, etc.)
   - Current balance
   - Credit limit or high credit
   - Payment status (Current, 30 days late, etc.)
   - Date account opened
   - Date account closed (if applicable)
   - Payment history (last 24 months if available)
   - Account status (Open, Closed, etc.)

3. INQUIRIES:
   - Date of inquiry
   - Company that made inquiry
   - Type of inquiry (Hard/Soft)

4. PUBLIC RECORDS:
   - Type of record (Bankruptcy, Lien, etc.)
   - Date filed
   - Amount (if applicable)
   - Status

RESPONSE FORMAT:
Provide your response as a valid JSON object with the following structure:

{{
  "consumer_info": {{
    "name": "Full Name",
    "ssn": "XXX-XX-XXXX or null",
    "date_of_birth": "YYYY-MM-DD or null",
    "addresses": [
      {{
        "street": "123 Main St",
        "city": "City",
        "state": "ST",
        "zip": "12345",
        "type": "current/previous"
      }}
    ],
    "phones": ["(555) 123-4567"]
  }},
  "tradelines": [
    {{
      "creditor_name": "Creditor Name",
      "account_number": "****1234",
      "account_type": "Credit Card",
      "balance": "1000.00",
      "credit_limit": "5000.00",
      "payment_status": "Current",
      "date_opened": "YYYY-MM-DD",
      "date_closed": "YYYY-MM-DD or null",
      "payment_history": ["Current", "Current", "30 days"],
      "account_status": "Open"
    }}
  ],
  "inquiries": [
    {{
      "date": "YYYY-MM-DD",
      "company": "Company Name",
      "type": "Hard"
    }}
  ],
  "public_records": [
    {{
      "type": "Bankruptcy",
      "date_filed": "YYYY-MM-DD",
      "amount": "0.00",
      "status": "Discharged"
    }}
  ]
}}

IMPORTANT GUIDELINES:
- Extract only information that is clearly present in the document
- Use "null" for missing information
- Standardize date formats to YYYY-MM-DD
- Normalize payment statuses to standard terms (Current, 30 days late, 60 days late, etc.)
- Mask sensitive information like full account numbers
- If information is ambiguous, indicate uncertainty in a confidence field
"""

    def get_tradeline_normalization_prompt(
        self, 
        raw_tradeline: Dict[str, Any], 
        context: ProcessingContext
    ) -> str:
        """Generate prompt for normalizing individual tradeline data"""
        
        return f"""
You are an expert at normalizing credit report tradeline data.

RAW TRADELINE DATA:
{json.dumps(raw_tradeline, indent=2)}

TASK: Normalize this tradeline data into a standard format with the following requirements:

1. CREDITOR NAME: Standardize creditor names (e.g., "CHASE BANK" → "Chase Bank")
2. ACCOUNT TYPE: Normalize to standard categories:
   - Credit Card
   - Mortgage
   - Auto Loan
   - Student Loan
   - Personal Loan
   - Line of Credit
   - Installment Loan
   - Other

3. PAYMENT STATUS: Normalize to standard terms:
   - Current
   - 30 days late
   - 60 days late
   - 90 days late
   - 120+ days late
   - Charged off
   - Collection
   - Settled

4. MONETARY VALUES: Convert to decimal format (e.g., "$1,234.56" → "1234.56")

5. DATES: Convert to YYYY-MM-DD format

6. CONFIDENCE SCORING: Assign a confidence score (0.0-1.0) based on:
   - Clarity of source data
   - Completeness of information
   - Consistency of formatting

RESPONSE FORMAT:
Provide a JSON object with the normalized tradeline:

{{
  "creditor_name": "Normalized Creditor Name",
  "account_number": "****1234",
  "account_type": "Credit Card",
  "balance": "1234.56",
  "credit_limit": "5000.00",
  "payment_status": "Current",
  "date_opened": "2020-01-15",
  "date_closed": null,
  "payment_history": ["Current", "Current", "30 days late"],
  "account_status": "Open",
  "confidence_score": 0.85,
  "normalization_notes": "Any issues or assumptions made during normalization"
}}

GUIDELINES:
- Maintain accuracy while standardizing format
- If unsure about a value, use your best judgment and lower the confidence score
- Include normalization notes for any assumptions or issues
- Preserve original account number masking for security
"""

    def get_consumer_info_prompt(
        self, 
        raw_text: str, 
        context: ProcessingContext
    ) -> str:
        """Generate prompt for extracting consumer information"""
        
        return f"""
You are an expert at extracting consumer information from credit reports.

DOCUMENT TEXT:
{raw_text[:4000]}  # Truncate for token limits

TASK: Extract consumer personal information from this credit report text.

INFORMATION TO EXTRACT:
1. Full name (as it appears on the report)
2. Social Security Number (if present, keep masked)
3. Date of birth
4. Current address
5. Previous addresses (if any)
6. Phone numbers
7. Employment information (if present)

RESPONSE FORMAT:
Provide a JSON object with the consumer information:

{{
  "name": "John Doe",
  "ssn": "XXX-XX-1234",
  "date_of_birth": "1980-01-15",
  "current_address": {{
    "street": "123 Main St",
    "city": "Anytown",
    "state": "CA",
    "zip": "12345"
  }},
  "previous_addresses": [
    {{
      "street": "456 Oak Ave",
      "city": "Oldtown",
      "state": "CA",
      "zip": "54321"
    }}
  ],
  "phone_numbers": ["(555) 123-4567"],
  "employment": {{
    "current_employer": "ABC Company",
    "position": "Manager",
    "income": "50000"
  }},
  "confidence_score": 0.9
}}

GUIDELINES:
- Extract only information that is clearly present
- Maintain privacy by keeping SSN masked
- Standardize address formats
- Use null for missing information
- Assign confidence score based on clarity and completeness
"""

    def get_validation_prompt(
        self, 
        tradelines: List[Any], 
        consumer_info: Any, 
        context: ProcessingContext
    ) -> str:
        """Generate prompt for validating normalized data"""
        
        return f"""
You are an expert at validating credit report data for accuracy and consistency.

NORMALIZED DATA TO VALIDATE:

CONSUMER INFO:
{json.dumps(consumer_info.dict() if hasattr(consumer_info, 'dict') else consumer_info, indent=2)}

TRADELINES:
{json.dumps([t.dict() if hasattr(t, 'dict') else t for t in tradelines[:10]], indent=2)}  # Limit for tokens

VALIDATION TASKS:
1. Check for data consistency across all tradelines
2. Validate date formats and logical date sequences
3. Verify monetary values are reasonable
4. Check for duplicate tradelines
5. Validate account types and payment statuses
6. Assess overall data quality

RESPONSE FORMAT:
Provide a JSON object with validation results:

{{
  "overall_confidence": 0.85,
  "validation_summary": {{
    "total_tradelines": 15,
    "valid_tradelines": 14,
    "invalid_tradelines": 1,
    "data_quality_score": 0.85
  }},
  "issues_found": [
    {{
      "type": "date_inconsistency",
      "description": "Date closed before date opened for account ****1234",
      "severity": "high",
      "tradeline_index": 3
    }}
  ],
  "suggestions": [
    {{
      "type": "data_correction",
      "description": "Consider manual review of account ****1234 dates",
      "priority": "high"
    }}
  ],
  "quality_metrics": {{
    "completeness": 0.90,
    "accuracy": 0.85,
    "consistency": 0.80
  }}
}}

VALIDATION CRITERIA:
- Dates: opened_date < closed_date, reasonable date ranges
- Balances: Non-negative, reasonable amounts
- Payment Status: Consistent with payment history
- Account Types: Valid categories
- Duplicates: Check for similar account numbers/creditors
"""