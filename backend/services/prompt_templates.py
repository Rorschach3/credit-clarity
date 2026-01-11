"""
Prompt templates for LLM-based credit report processing.
Contains prompts for tradeline normalization, validation, and consumer info extraction.
"""
from typing import Dict, List, Any, Optional
import json


class PromptTemplates:
    """
    Manages prompt templates for various LLM operations.
    Supports bureau-specific variations and context-aware prompts.
    """

    def __init__(self):
        self.supported_bureaus = ["Experian", "Equifax", "TransUnion"]

    def get_tradeline_normalization_prompt(
        self,
        raw_tradeline: Dict[str, Any],
        context: Any
    ) -> str:
        """
        Generate prompt for normalizing a single tradeline.

        Args:
            raw_tradeline: Raw tradeline data to normalize
            context: Processing context

        Returns:
            Formatted prompt string
        """
        bureau = raw_tradeline.get("credit_bureau", "Unknown")

        return f"""
You are an expert credit report data normalizer specializing in {bureau} credit bureau formats.

RAW TRADELINE DATA:
{json.dumps(raw_tradeline, indent=2)}

YOUR TASK:
Normalize and structure this tradeline data according to standard formats.

NORMALIZATION REQUIREMENTS:

1. CREDITOR NAME:
   - Standardize formatting (e.g., "chase bank" → "Chase Bank")
   - Remove extra whitespace and special characters
   - Keep recognizable brand names

2. ACCOUNT NUMBER:
   - Preserve masking format (e.g., ****1234)
   - Ensure consistent formatting
   - Extract from various formats

3. DATES:
   - Convert to ISO format: YYYY-MM-DD
   - Accept MM/DD/YYYY, MM/YYYY, or similar formats
   - Use first of month if day not specified

4. MONETARY VALUES:
   - Format as decimal numbers: "1250.50"
   - Remove currency symbols
   - Handle "N/A", "null", or missing values as null

5. ACCOUNT STATUS:
   - Standardize to: "Open", "Closed", "Charged Off", "Collection", "Current", "Late"
   - Map variations to standard terms

6. ACCOUNT TYPE:
   - Classify as: "Credit Card", "Auto Loan", "Mortgage", "Student Loan", "Personal Loan", "Line of Credit"
   - Use most appropriate category

RESPONSE FORMAT:
Return a JSON object with normalized data:

{{
  "creditor_name": "Chase Bank",
  "account_number": "****1234",
  "account_type": "Credit Card",
  "account_balance": "1250.50",
  "credit_limit": "5000.00",
  "monthly_payment": "35.00",
  "account_status": "Open",
  "date_opened": "2020-01-15",
  "date_closed": null,
  "confidence_score": 0.95,
  "normalization_notes": "Successfully normalized all fields"
}}

Return ONLY valid JSON, no additional text.
"""

    def get_consumer_info_prompt(
        self,
        raw_text: str,
        context: Any
    ) -> str:
        """
        Generate prompt for extracting consumer personal information.

        Args:
            raw_text: Raw document text
            context: Processing context

        Returns:
            Formatted prompt string
        """
        return f"""
You are an expert at extracting consumer personal information from credit reports.

DOCUMENT TEXT:
{raw_text[:5000]}  # Truncated for token limits

YOUR TASK:
Extract the consumer's personal information from this credit report.

EXTRACTION TARGETS:

1. FULL NAME:
   - First name, middle initial/name, last name
   - May appear in header or identification section

2. SOCIAL SECURITY NUMBER:
   - Format: XXX-XX-1234 or similar masked format
   - Look for "SSN", "Social Security", "SS#"

3. DATE OF BIRTH:
   - Format: MM/DD/YYYY
   - Look for "DOB", "Date of Birth", "Birth Date"

4. ADDRESSES:
   - Current address
   - Previous addresses (if listed)
   - Include: street, city, state, ZIP

5. PHONE NUMBERS:
   - Primary phone number
   - Additional phone numbers if listed
   - Format: (XXX) XXX-XXXX or similar

6. EMAIL ADDRESS:
   - If present in the report

EXTRACTION GUIDELINES:
- Extract information exactly as it appears
- Use null for missing information
- Include all available addresses in an array
- Provide confidence score based on clarity of extracted data

RESPONSE FORMAT:
Return valid JSON with this structure:

{{
  "name": "John A. Smith",
  "ssn": "***-**-1234",
  "date_of_birth": "1985-03-15",
  "addresses": [
    "123 Main St, Springfield, IL 62701",
    "456 Oak Ave, Chicago, IL 60601"
  ],
  "phone_numbers": [
    "(555) 123-4567"
  ],
  "email": null,
  "confidence_score": 0.92
}}

Return ONLY valid JSON, no additional text.
"""

    def get_validation_prompt(
        self,
        tradelines: List[Any],
        consumer_info: Any,
        context: Any
    ) -> str:
        """
        Generate prompt for validating extracted data quality.

        Args:
            tradelines: List of extracted tradelines
            consumer_info: Extracted consumer information
            context: Processing context

        Returns:
            Formatted prompt string
        """
        # Convert tradelines to simple dicts for JSON serialization
        tradeline_dicts = []
        for tl in tradelines:
            if hasattr(tl, '__dict__'):
                tl_dict = {k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
                          for k, v in tl.__dict__.items()}
            else:
                tl_dict = dict(tl)
            tradeline_dicts.append(tl_dict)

        consumer_dict = consumer_info.to_dict() if hasattr(consumer_info, 'to_dict') else dict(consumer_info)

        return f"""
You are an expert credit report data validator.

EXTRACTED DATA TO VALIDATE:

CONSUMER INFORMATION:
{json.dumps(consumer_dict, indent=2, default=str)}

TRADELINES ({len(tradeline_dicts)} total):
{json.dumps(tradeline_dicts[:10], indent=2, default=str)}  # Showing first 10

YOUR TASK:
Validate the quality and completeness of this extracted credit report data.

VALIDATION CHECKS:

1. CONSUMER INFO VALIDATION:
   - Is the name format valid?
   - Is SSN properly masked?
   - Is date of birth in valid format?
   - Are addresses complete?

2. TRADELINE VALIDATION:
   - Are all required fields present? (creditor, account number, dates)
   - Are monetary values in valid format?
   - Are dates in valid range?
   - Are account statuses using standard terms?
   - Are account types properly classified?

3. DATA CONSISTENCY:
   - Do dates make logical sense? (opened before closed)
   - Are balances reasonable relative to limits?
   - Are payment amounts reasonable?

4. COMPLETENESS:
   - How many tradelines have all critical fields?
   - How many are missing key information?
   - What is the overall data quality?

5. ISSUES IDENTIFICATION:
   - Identify specific validation issues
   - Categorize by severity: low, medium, high, critical
   - Suggest fixes where possible

RESPONSE FORMAT:
Return valid JSON with this structure:

{{
  "overall_confidence": 0.85,
  "consumer_info_score": 0.90,
  "tradeline_scores": {{
    "0": 0.95,
    "1": 0.85,
    "2": 0.70
  }},
  "passed_validation": true,
  "issues": [
    {{
      "type": "missing_field",
      "description": "Tradeline 2 missing credit limit",
      "severity": "medium",
      "tradeline_index": 2,
      "field_name": "credit_limit",
      "suggested_fix": "Verify if limit information is available in source document",
      "confidence_impact": 0.15
    }}
  ],
  "metadata": {{
    "total_tradelines": {len(tradeline_dicts)},
    "high_confidence_tradelines": 8,
    "medium_confidence_tradelines": 2,
    "low_confidence_tradelines": 0,
    "critical_issues_count": 0,
    "warnings_count": 3
  }}
}}

CONFIDENCE SCORING:
- 0.9-1.0: Excellent quality, all fields complete and valid
- 0.7-0.89: Good quality, minor issues or missing non-critical fields
- 0.5-0.69: Acceptable quality, some missing data or formatting issues
- 0.3-0.49: Poor quality, significant missing data or errors
- 0.0-0.29: Very poor quality, major data issues

Return ONLY valid JSON, no additional text.
"""

    def get_bureau_specific_prompt(
        self,
        bureau: str,
        text: str
    ) -> str:
        """
        Generate bureau-specific extraction prompt.

        Args:
            bureau: Credit bureau name (Experian, Equifax, TransUnion)
            text: Document text to process

        Returns:
            Bureau-specific prompt
        """
        bureau_specific_notes = {
            "Experian": """
EXPERIAN-SPECIFIC NOTES:
- Account numbers often start with reference numbers
- "High Credit" field indicates credit limit
- Payment history shows as grid of payment codes
- Look for "Account Summary" section
            """,
            "Equifax": """
EQUIFAX-SPECIFIC NOTES:
- Uses "Potentially Negative Items" section
- Date format typically MM/DD/YYYY
- "Terms" indicates account type
- Look for "Credit Items" section
            """,
            "TransUnion": """
TRANSUNION-SPECIFIC NOTES:
- Uses "Public Records and Derogatory Remarks" section
- Account numbers may be in "Reference Number" field
- "High Balance" indicates credit limit for revolving accounts
- Look for "Account History" section
            """
        }

        specific_notes = bureau_specific_notes.get(bureau, "")

        return f"""
You are an expert at parsing {bureau} credit reports.

{specific_notes}

DOCUMENT TEXT:
{text[:8000]}

Extract all tradeline information following the standard format.
Be aware of {bureau}-specific formatting and terminology.

Return valid JSON with the tradeline extraction format.
"""

    def get_enhanced_extraction_prompt(
        self,
        text: str,
        detected_bureau: str = "Unknown"
    ) -> str:
        """
        Generate enhanced extraction prompt (wrapper for compatibility).

        This method provides compatibility with enhanced_extraction_service.
        For actual implementation, use the method in EnhancedExtractionService.

        Args:
            text: Document text
            detected_bureau: Detected credit bureau

        Returns:
            Enhanced extraction prompt
        """
        return self.get_bureau_specific_prompt(detected_bureau, text)
