"""
Field Validation and Confidence Scoring for Credit Report Extraction
Validates extracted field values and provides confidence scores for accuracy assessment
"""

import re
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

class FieldValidator:
    """Validates extracted credit report fields and provides confidence scores"""
    
    def __init__(self):
        self.currency_pattern = re.compile(r'^\$\d{1,3}(,\d{3})*(\.\d{2})?$')
        self.date_patterns = [
            re.compile(r'^\d{1,2}/\d{1,2}/\d{4}$'),  # MM/DD/YYYY
            re.compile(r'^\d{1,2}-\d{1,2}-\d{4}$'),  # MM-DD-YYYY
            re.compile(r'^\d{4}-\d{1,2}-\d{1,2}$'),  # YYYY-MM-DD
        ]
        self.account_number_patterns = [
            re.compile(r'^\*{4,}\d{4}$'),  # ****1234
            re.compile(r'^x{4,}\d{4}$', re.IGNORECASE),  # xxxx1234
            re.compile(r'^\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}$'),  # Full numbers
            re.compile(r'^\d+$'),  # Plain numbers
        ]
    
    def validate_tradeline(self, tradeline: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a complete tradeline and return validation results with confidence scores
        """
        validation_results = {
            "is_valid": True,
            "confidence_score": 0.0,
            "field_scores": {},
            "errors": [],
            "warnings": []
        }
        
        # Validate each field
        fields_to_validate = [
            ("creditor_name", self.validate_creditor_name),
            ("account_balance", self.validate_currency),
            ("credit_limit", self.validate_currency),
            ("monthly_payment", self.validate_currency),
            ("account_number", self.validate_account_number),
            ("date_opened", self.validate_date),
            ("account_type", self.validate_account_type),
            ("account_status", self.validate_account_status),
            ("credit_bureau", self.validate_credit_bureau),
        ]
        
        total_score = 0
        valid_fields = 0
        
        for field_name, validator_func in fields_to_validate:
            field_value = tradeline.get(field_name, "")
            is_valid, confidence, errors = validator_func(field_value)
            
            validation_results["field_scores"][field_name] = {
                "is_valid": is_valid,
                "confidence": confidence,
                "errors": errors
            }
            
            if is_valid:
                total_score += confidence
                valid_fields += 1
            else:
                validation_results["errors"].extend([f"{field_name}: {error}" for error in errors])
        
        # Calculate overall confidence score
        if valid_fields > 0:
            validation_results["confidence_score"] = total_score / len(fields_to_validate)
        
        # Mark as invalid if too many fields are missing or invalid
        if valid_fields < 3:  # Require at least 3 valid fields
            validation_results["is_valid"] = False
            validation_results["errors"].append("Too few valid fields extracted")
        
        # Add business logic warnings
        self._add_business_logic_warnings(tradeline, validation_results)
        
        return validation_results
    
    def validate_creditor_name(self, value: str) -> Tuple[bool, float, list]:
        """Validate creditor name field"""
        if not value or value.strip() == "":
            return False, 0.0, ["Creditor name is required"]
        
        value = value.strip()
        
        # High confidence for known patterns
        if len(value) >= 3 and any(char.isalpha() for char in value):
            confidence = 0.9
            if any(keyword in value.upper() for keyword in ["BANK", "CREDIT", "CAPITAL", "CHASE", "AMEX"]):
                confidence = 0.95
            return True, confidence, []
        
        return False, 0.3, ["Creditor name appears invalid"]
    
    def validate_currency(self, value: str) -> Tuple[bool, float, list]:
        """Validate currency field (balance, credit limit, payment)"""
        if not value or value.strip() == "":
            return True, 0.5, []  # Empty is acceptable
        
        value = value.strip()
        
        # Check format
        if self.currency_pattern.match(value):
            # Extract numeric value for range validation
            numeric_value = float(value.replace('$', '').replace(',', ''))
            
            # Reasonable range validation
            if 0 <= numeric_value <= 1000000:  # $0 to $1M
                return True, 0.9, []
            else:
                return False, 0.3, [f"Amount {value} seems unrealistic"]
        
        # Try to extract and validate numeric part
        numeric_match = re.search(r'\d+\.?\d*', value)
        if numeric_match:
            return True, 0.6, [f"Currency format needs standardization: {value}"]
        
        return False, 0.1, [f"Invalid currency format: {value}"]
    
    def validate_account_number(self, value: str) -> Tuple[bool, float, list]:
        """Validate account number field"""
        if not value or value.strip() == "":
            return True, 0.4, []  # Empty is acceptable but not ideal
        
        value = value.strip()
        
        # Check against known patterns
        for pattern in self.account_number_patterns:
            if pattern.match(value):
                if value.startswith('*') or value.lower().startswith('x'):
                    return True, 0.9, []  # Masked numbers are good
                else:
                    return True, 0.8, []  # Full numbers are valid but less secure
        
        return False, 0.2, [f"Invalid account number format: {value}"]
    
    def validate_date(self, value: str) -> Tuple[bool, float, list]:
        """Validate date field"""
        if not value or value.strip() == "":
            return True, 0.3, []  # Empty is acceptable but not ideal
        
        value = value.strip()
        
        # Check format
        for pattern in self.date_patterns:
            if pattern.match(value):
                # Try to parse the date
                try:
                    if '/' in value:
                        parts = value.split('/')
                        if len(parts) == 3:
                            month, day, year = map(int, parts)
                    elif '-' in value:
                        parts = value.split('-')
                        if len(parts) == 3:
                            if len(parts[0]) == 4:  # YYYY-MM-DD
                                year, month, day = map(int, parts)
                            else:  # MM-DD-YYYY
                                month, day, year = map(int, parts)
                    
                    # Validate ranges
                    if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= datetime.now().year:
                        return True, 0.9, []
                    else:
                        return False, 0.3, [f"Date values out of range: {value}"]
                
                except (ValueError, IndexError):
                    return False, 0.2, [f"Invalid date format: {value}"]
        
        return False, 0.1, [f"Unrecognized date format: {value}"]
    
    def validate_account_type(self, value: str) -> Tuple[bool, float, list]:
        """Validate account type field"""
        if not value or value.strip() == "":
            return False, 0.0, ["Account type is required"]
        
        value = value.strip()
        
        # Valid types in both formats (space-separated and underscore)
        valid_types = [
            "Credit Card", "credit_card", "Auto Loan", "auto_loan", "Mortgage", "mortgage", 
            "Student Loan", "student_loan", "Personal Loan", "personal_loan", 
            "Store Card", "store_card", "Line of Credit", "line_of_credit", 
            "Installment Loan", "installment", "Business", "business", "Secured", "secured"
        ]
        
        if value in valid_types:
            return True, 0.95, []
        
        # Check for partial matches (case insensitive)
        value_lower = value.lower()
        for valid_type in valid_types:
            valid_type_lower = valid_type.lower()
            if value_lower in valid_type_lower or valid_type_lower in value_lower:
                return True, 0.8, [f"Account type needs standardization: {value}"]
        
        return False, 0.3, [f"Unknown account type: {value}"]
    
    def validate_account_status(self, value: str) -> Tuple[bool, float, list]:
        """Validate account status field"""
        if not value or value.strip() == "":
            return True, 0.4, []  # Empty is acceptable
        
        value = value.strip()
        
        valid_statuses = [
            "Open", "Closed", "Current", "Late", "Charged Off", 
            "Collection", "Paid", "Settled", "Dispute"
        ]
        
        if value in valid_statuses:
            return True, 0.9, []
        
        # Check for partial matches
        for valid_status in valid_statuses:
            if value.lower() in valid_status.lower() or valid_status.lower() in value.lower():
                return True, 0.7, [f"Status needs standardization: {value}"]
        
        return True, 0.5, [f"Unusual account status: {value}"]
    
    def validate_credit_bureau(self, value: str) -> Tuple[bool, float, list]:
        """Validate credit bureau field"""
        if not value or value.strip() == "":
            return True, 0.3, []  # Empty is acceptable
        
        value = value.strip()
        
        valid_bureaus = ["Experian", "Equifax", "TransUnion"]
        
        if value in valid_bureaus:
            return True, 0.95, []
        
        # Check for partial matches
        for bureau in valid_bureaus:
            if value.lower() in bureau.lower() or bureau.lower() in value.lower():
                return True, 0.8, [f"Bureau name needs standardization: {value}"]
        
        return True, 0.4, [f"Unknown bureau: {value}"]
    
    def _add_business_logic_warnings(self, tradeline: Dict[str, Any], validation_results: Dict[str, Any]):
        """Add business logic warnings based on field relationships"""
        warnings = validation_results["warnings"]
        
        # Credit limit should be >= balance
        balance = self._extract_numeric_value(tradeline.get("account_balance", ""))
        credit_limit = self._extract_numeric_value(tradeline.get("credit_limit", ""))
        
        if balance and credit_limit and balance > credit_limit:
            warnings.append(f"Balance (${balance:,.2f}) exceeds credit limit (${credit_limit:,.2f})")
        
        # Monthly payment validation
        monthly_payment = self._extract_numeric_value(tradeline.get("monthly_payment", ""))
        if monthly_payment and balance:
            if monthly_payment > balance:
                warnings.append(f"Monthly payment (${monthly_payment:,.2f}) exceeds balance (${balance:,.2f})")
        
        # Account type vs creditor name consistency
        account_type = tradeline.get("account_type", "").lower()
        creditor_name = tradeline.get("creditor_name", "").lower()
        
        if "auto" in account_type and not any(auto_kw in creditor_name for auto_kw in ["ford", "honda", "toyota", "auto", "motor"]):
            warnings.append("Account type 'Auto Loan' but creditor doesn't appear to be auto-related")
        
        if "student" in account_type and not any(edu_kw in creditor_name for edu_kw in ["navient", "nelnet", "education", "student"]):
            warnings.append("Account type 'Student Loan' but creditor doesn't appear to be education-related")
    
    def _extract_numeric_value(self, currency_str: str) -> Optional[float]:
        """Extract numeric value from currency string"""
        if not currency_str:
            return None
        
        try:
            # Remove currency symbols and commas
            numeric_str = re.sub(r'[^0-9.]', '', currency_str)
            return float(numeric_str) if numeric_str else None
        except ValueError:
            return None

# Create global instance for easy import
field_validator = FieldValidator()