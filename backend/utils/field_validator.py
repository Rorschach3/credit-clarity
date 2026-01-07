"""
Field Validation and Data Cleaning for Credit Report Extraction
Validates, cleans, and transforms extracted field values to produce clean output
"""

import re
from typing import Dict, Any, Tuple, Optional, Union
from datetime import datetime

class FieldValidator:
    """Validates and cleans extracted credit report fields"""
    
    def __init__(self):
        self.currency_pattern = re.compile(r'^\$\d{1,3}(,\d{3})*\.\d{2}$')
        self.date_patterns = [
            re.compile(r'^\d{1,2}/\d{1,2}/\d{4}$'),  # MM/DD/YYYY
            re.compile(r'^\d{1,2}-\d{1,2}-\d{4}$'),  # MM-DD-YYYY
            re.compile(r'^\d{4}-\d{1,2}-\d{1,2}$'),  # YYYY-MM-DD
        ]
        self.account_number_patterns = [
            re.compile(r'^\*{4,}\d{4}$'),  # ****1234
            re.compile(r'^x{4,}\d{4}$', re.IGNORECASE),  # xxxx1234
            re.compile(r'^\d+\*{4,}$'),  # 1234****
            re.compile(r'^\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}$'),  # Full numbers
            re.compile(r'^\d+$'),  # Plain numbers
            re.compile(r'^[A-Za-z0-9]+\*{4,}$'),  # Alpha-numeric with trailing asterisks
        ]
        
        # Field mappings for cleaning and standardization
        self.field_mappings = {
            'account_type_standardization': {
                # Transform to match expected output format
                'Credit Card': 'Revolving',
                'credit_card': 'Revolving', 
                'Store Card': 'Revolving',
                'store_card': 'Revolving',
                'Line of Credit': 'Revolving',
                'line_of_credit': 'Revolving',
                'Installment Loan': 'Installment',
                'installment_loan': 'Installment',
                'Auto Loan': 'Installment',
                'auto_loan': 'Installment',
                'Personal Loan': 'Installment', 
                'personal_loan': 'Installment',
                'Student Loan': 'Installment',
                'student_loan': 'Installment',
                'Mortgage': 'Installment',
                'mortgage': 'Installment',
                # Already correct formats
                'Revolving': 'Revolving',
                'revolving': 'Revolving',
                'Installment': 'Installment',
                'installment': 'Installment',
            },
            'account_status_standardization': {
                # Standardize status formats
                'Current Account': 'Current',
                'current_account': 'Current',
                'Paid, Closed; was Paid as agreed': 'Closed',
                'Account Closed': 'Closed',
                'Paid as agreed': 'Current',
                # Keep existing good formats
                'Current': 'Current',
                'Closed': 'Closed', 
                'Open': 'Open',
                'Late': 'Late',
                'Collection': 'Collection',
            }
        }
    
    def validate_tradeline(self, tradeline: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main validation method: Clean, transform, and validate tradeline data
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug(f"🔍 FIELD VALIDATOR - Processing: {tradeline.get('creditor_name', 'N/A')}")
        
        # Step 1: Clean and transform the data
        cleaned_tradeline = self._clean_tradeline_data(tradeline)
        
        # Step 2: Validate the cleaned data
        validation_results = {
            "is_valid": True,
            "confidence_score": 0.0,
            "field_scores": {},
            "errors": [],
            "warnings": [],
            "normalized_data": cleaned_tradeline
        }
        
        # Step 3: Validate each field
        fields_to_validate = [
            ("creditor_name", self.validate_creditor_name, True),      # REQUIRED
            ("account_type", self.validate_account_type, True),        # REQUIRED  
            ("account_balance", self.validate_currency, False),        # OPTIONAL
            ("credit_limit", self.validate_currency, False),           # OPTIONAL
            ("monthly_payment", self.validate_currency, False),        # OPTIONAL
            ("account_number", self.validate_account_number, False),   # OPTIONAL
            ("date_opened", self.validate_date, False),               # OPTIONAL
            ("account_status", self.validate_account_status, False),   # OPTIONAL
            ("credit_bureau", self.validate_credit_bureau, False),     # OPTIONAL
        ]
        
        total_score = 0
        valid_fields = 0
        required_fields = 0
        required_fields_valid = 0
        
        logger.debug("    📊 FIELD VALIDATION:")
        for field_name, validator_func, is_required in fields_to_validate:
            field_value = cleaned_tradeline.get(field_name, "")
            is_valid, confidence, errors = validator_func(field_value)
            
            logger.debug(f"      {field_name}: '{field_value}' → Valid: {is_valid}, Confidence: {confidence:.2f} {'(REQUIRED)' if is_required else '(OPTIONAL)'}")
            if errors:
                logger.debug(f"        Errors: {errors}")
            
            validation_results["field_scores"][field_name] = {
                "is_valid": is_valid,
                "confidence": confidence,
                "errors": errors,
                "is_required": is_required
            }
            
            if is_required:
                required_fields += 1
                if is_valid:
                    required_fields_valid += 1
                else:
                    validation_results["errors"].extend([f"{field_name}: {error}" for error in errors])
            
            if is_valid:
                total_score += confidence
                valid_fields += 1
        
        # Calculate confidence score
        if len(fields_to_validate) > 0:
            validation_results["confidence_score"] = total_score / len(fields_to_validate)
        
        logger.debug(f"    📈 VALIDATION SUMMARY:")
        logger.debug(f"      Required fields valid: {required_fields_valid}/{required_fields}")
        logger.debug(f"      Total valid fields: {valid_fields}/{len(fields_to_validate)}")
        logger.debug(f"      Confidence: {validation_results['confidence_score']:.2f}")
        
        # Validation logic - only require essential fields
        if required_fields_valid < required_fields:
            validation_results["is_valid"] = False
            validation_results["errors"].append(f"Required fields missing: {required_fields_valid}/{required_fields}")
            logger.debug(f"      ❌ MARKED INVALID: Required fields missing ({required_fields_valid}/{required_fields})")
        else:
            logger.debug(f"      ✅ MARKED VALID: All required fields present ({required_fields_valid}/{required_fields})")
        
        # Add business logic warnings
        self._add_business_logic_warnings(cleaned_tradeline, validation_results)
        
        if validation_results["warnings"]:
            logger.debug(f"      ⚠️ WARNINGS: {validation_results['warnings']}")
        
        return validation_results
    
    def _clean_tradeline_data(self, tradeline: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and transform tradeline data to match expected output format"""
        cleaned = {}
        
        # Copy basic fields
        for key in ['id', 'user_id', 'created_at', 'updated_at', 'idx', 'is_negative', 'dispute_count']:
            if key in tradeline:
                cleaned[key] = tradeline[key]
        
        # Clean each field
        cleaned['creditor_name'] = self._clean_creditor_name(tradeline.get('creditor_name', ''))
        cleaned['account_type'] = self._clean_account_type(tradeline.get('account_type', ''))
        cleaned['account_status'] = self._clean_account_status(tradeline.get('account_status', ''))
        cleaned['account_number'] = self._clean_account_number(tradeline.get('account_number', ''))
        cleaned['date_opened'] = self._clean_date_opened(tradeline.get('date_opened', ''))
        cleaned['account_balance'] = self._clean_currency_field(tradeline.get('account_balance', ''))
        cleaned['credit_limit'] = self._clean_currency_field(tradeline.get('credit_limit', ''))
        cleaned['monthly_payment'] = self._clean_currency_field(tradeline.get('monthly_payment', ''))
        cleaned['credit_bureau'] = self._clean_credit_bureau(tradeline.get('credit_bureau', ''))
        
        return cleaned
    
    def _clean_creditor_name(self, value: Any) -> str:
        """Clean creditor name"""
        if not value:
            return ""
        
        value = str(value).strip()
        # Remove extra whitespace
        value = re.sub(r'\s+', ' ', value)
        
        # Standardize common creditor names
        standardizations = {
            'CAPITAL ONE BANK': 'CAPITAL ONE',
            'BANK OF AMERICA, N.A.': 'BANK OF AMERICA',
            'JPMORGAN CHASE BANK': 'JPMCB CARD SERVICES',
            'SYNCHRONY BANK': 'SYNCB',
        }
        
        value_upper = value.upper()
        for old, new in standardizations.items():
            if old in value_upper:
                value = value.replace(old, new).replace(old.lower(), new)
        
        return value
    
    def _clean_account_type(self, value: Any) -> str:
        """Clean and standardize account type"""
        if not value:
            return ""
        
        value = str(value).strip()
        
        # Apply standardization mapping
        if value in self.field_mappings['account_type_standardization']:
            return self.field_mappings['account_type_standardization'][value]
        
        # Case-insensitive matching
        value_lower = value.lower()
        for key, standardized in self.field_mappings['account_type_standardization'].items():
            if value_lower == key.lower():
                return standardized
        
        # Fallback logic
        if any(term in value_lower for term in ['credit', 'card', 'revolving']):
            return 'Revolving'
        elif any(term in value_lower for term in ['loan', 'installment', 'mortgage', 'auto']):
            return 'Installment'
        
        return value
    
    def _clean_account_status(self, value: Any) -> str:
        """Clean and standardize account status"""
        if not value:
            return ""
        
        value = str(value).strip()
        
        # Apply standardization mapping
        if value in self.field_mappings['account_status_standardization']:
            return self.field_mappings['account_status_standardization'][value]
        
        # Case-insensitive matching
        value_lower = value.lower()
        for key, standardized in self.field_mappings['account_status_standardization'].items():
            if value_lower == key.lower():
                return standardized
        
        return value
    
    def _clean_account_number(self, value: Any) -> str:
        """Extract and clean account number"""
        if not value:
            return ""
        
        value = str(value).strip()
        
        # Handle PostgreSQL quoted text format
        if value.startswith("'\"") and value.endswith("\"'::text"):
            inner_value = value[2:-7]
            if inner_value != "xxxx/xx/xx":
                value = inner_value
            else:
                return ""
        
        # Remove extra whitespace
        value = re.sub(r'\s+', '', value)
        
        # If already in good masked format, keep it
        if re.match(r'^\d+\*{4,}$', value) or re.match(r'^\*{4,}\d{4}$', value):
            return value
        
        # Extract from "Account 120" format
        account_match = re.search(r'Account\s+(\d+)', value, re.IGNORECASE)
        if account_match:
            return account_match.group(1) + "****"
        
        # Look for long numeric sequences and mask them
        long_number = re.search(r'\d{8,}', value)
        if long_number:
            num = long_number.group()
            if len(num) >= 12:
                return num[:-4] + "****" 
            else:
                return num + "****"
        
        # Look for any numeric sequence
        numbers = re.findall(r'\d+', value)
        if numbers:
            longest = max(numbers, key=len)
            if len(longest) >= 4:
                return longest + "****"
        
        return ""
    
    def _clean_date_opened(self, value: Any) -> Optional[str]:
        """Extract and clean date"""
        if not value:
            return None
        
        value = str(value).strip()
        
        # Handle PostgreSQL quoted text format
        if value.startswith("'\"") and value.endswith("\"'::text"):
            inner_value = value[2:-7]
            if inner_value == "xxxx/xx/xx":
                return None
            value = inner_value
        
        # Check if already in good format
        for pattern in self.date_patterns:
            if pattern.match(value):
                try:
                    if '/' in value:
                        parts = value.split('/')
                        if len(parts) == 3:
                            month, day, year = map(int, parts)
                            if 1 <= month <= 12 and 1 <= day <= 31 and 1950 <= year <= datetime.now().year + 1:
                                return value
                except (ValueError, IndexError):
                    continue
        
        # Try to extract date from various formats
        iso_match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', value)
        if iso_match:
            year, month, day = iso_match.groups()
            try:
                return f"{int(month):02d}/{int(day):02d}/{year}"
            except ValueError:
                pass
        
        # Look for MM/DD/YYYY or MM-DD-YYYY
        date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', value)
        if date_match:
            month, day, year = date_match.groups()
            try:
                if 1 <= int(month) <= 12 and 1 <= int(day) <= 31:
                    return f"{int(month):02d}/{int(day):02d}/{year}"
            except ValueError:
                pass
        
        return None
    
    def _clean_currency_field(self, value: Any) -> Union[str, None]:
        """Clean currency fields"""
        if value is None:
            return None
        
        if isinstance(value, (int, float)):
            return f"${value:,.2f}"
        
        value = str(value).strip()
        if not value or value.lower() in ['null', 'none', 'n/a']:
            return None
        
        # Handle special cases
        if value in ["$,", "$", ","]:
            return None
        
        # Extract numeric value
        numeric_match = re.search(r'[\d,]+\.?\d*', value)
        if numeric_match:
            try:
                numeric_str = numeric_match.group().replace(',', '')
                numeric_value = float(numeric_str)
                return f"${numeric_value:,.2f}"
            except ValueError:
                pass
        
        return None
    
    def _clean_credit_bureau(self, value: Any) -> str:
        """Clean and standardize credit bureau names"""
        if not value:
            return ""
        
        value = str(value).strip()
        
        standardizations = {
            'experian': 'Experian',
            'equifax': 'Equifax', 
            'transunion': 'TransUnion',
            'trans union': 'TransUnion',
            'exp': 'Experian',
            'eqf': 'Equifax',
            'tu': 'TransUnion',
        }
        
        value_lower = value.lower()
        if value_lower in standardizations:
            return standardizations[value_lower]
        
        # Partial matching
        for key, standard in standardizations.items():
            if key in value_lower:
                return standard
        
        return value
    
    def validate_creditor_name(self, value: Union[str, None]) -> Tuple[bool, float, list]:
        """Validate creditor name - required field"""
        if not value or (isinstance(value, str) and value.strip() == ""):
            return False, 0.0, ["Creditor name is required"]
        
        value = str(value).strip()
        
        if len(value) >= 1:
            confidence = 0.7
            if len(value) >= 3:
                confidence = 0.85
            if any(char.isalpha() for char in value):
                confidence = 0.9
            if any(keyword in value.upper() for keyword in ["BANK", "CREDIT", "CAPITAL"]):
                confidence = 0.95
            return True, confidence, []
        
        return False, 0.3, ["Creditor name invalid"]
    
    def validate_account_type(self, value: Union[str, None]) -> Tuple[bool, float, list]:
        """Validate account type - required field"""
        if not value:
            return False, 0.0, ["Account type is required"]
        
        value = str(value).strip()
        
        # After cleaning, should be standardized
        if value in ['Revolving', 'Installment']:
            return True, 0.95, []
        
        # Accept other reasonable values
        if any(keyword in value.lower() for keyword in ['credit', 'card', 'loan', 'mortgage']):
            return True, 0.8, [f"Account type accepted: {value}"]
        
        if len(value) >= 2:
            return True, 0.6, [f"Unusual account type: {value}"]
        
        return False, 0.2, [f"Invalid account type: {value}"]
    
    def validate_currency(self, value: Union[str, None]) -> Tuple[bool, float, list]:
        """Validate currency - optional field"""
        if value is None:
            return True, 0.8, []

        if isinstance(value, (int, float)):
            return True, 0.95, []

        if isinstance(value, str):
            val = value.strip()
            if self.currency_pattern.match(val):
                return True, 0.95, []
            return False, 0.4, ["Currency must be in format $X.XX with 2 decimal places"]

        return True, 0.6, []
    
    def validate_account_number(self, value: Union[str, None]) -> Tuple[bool, float, list]:
        """Validate account number - optional field"""
        if not value:
            return True, 0.7, []
        
        # Check for proper masked format
        if re.match(r'^\d+\*{4,}$', value) or re.match(r'^\*{4,}\d{4}$', value):
            return True, 0.95, []
        
        return True, 0.7, []
    
    def validate_date(self, value: Union[str, None]) -> Tuple[bool, float, list]:
        """Validate date - optional field"""
        if value is None:
            return True, 0.6, []
        
        if re.match(r'^\d{2}/\d{2}/\d{4}$', value):
            return True, 0.95, []
        
        return True, 0.5, []
    
    def validate_account_status(self, value: Union[str, None]) -> Tuple[bool, float, list]:
        """Validate account status - optional field"""
        if not value:
            return True, 0.6, []
        
        if value in ['Current', 'Closed', 'Open', 'Late', 'Collection']:
            return True, 0.95, []
        
        return True, 0.7, []
    
    def validate_credit_bureau(self, value: Union[str, None]) -> Tuple[bool, float, list]:
        """Validate credit bureau - optional field"""
        if not value:
            return True, 0.5, []
        
        if value in ['Experian', 'Equifax', 'TransUnion']:
            return True, 0.95, []
        
        return True, 0.7, []
    
    def _add_business_logic_warnings(self, tradeline: Dict[str, Any], validation_results: Dict[str, Any]):
        """Add business logic warnings"""
        warnings = validation_results["warnings"]
        
        try:
            balance = self._extract_numeric_value(tradeline.get("account_balance", ""))
            credit_limit = self._extract_numeric_value(tradeline.get("credit_limit", ""))
            
            if balance is not None and credit_limit is not None and credit_limit > 0:
                utilization = balance / credit_limit
                if utilization > 1.0:
                    warnings.append(f"Balance exceeds credit limit - {utilization:.1%} utilization")
                elif utilization > 0.9:
                    warnings.append(f"High credit utilization: {utilization:.1%}")
            
            monthly_payment = self._extract_numeric_value(tradeline.get("monthly_payment", ""))
            if monthly_payment is not None and balance is not None:
                if monthly_payment > balance and balance > 0:
                    warnings.append("Monthly payment exceeds balance")
        except Exception:
            pass
    
    def _extract_numeric_value(self, currency_str: Union[str, None, int, float]) -> Optional[float]:
        """Extract numeric value from currency string"""
        if currency_str is None:
            return None
        
        if isinstance(currency_str, (int, float)):
            return float(currency_str)
        
        try:
            currency_str = str(currency_str).strip()
            if not currency_str or currency_str.lower() in ['null', 'none', 'n/a']:
                return None
            
            numeric_str = re.sub(r'[^\d.]', '', currency_str)
            return float(numeric_str) if numeric_str else None
        except (ValueError, TypeError):
            return None

# Create global instance for easy import
field_validator = FieldValidator()
