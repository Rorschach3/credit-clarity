"""
Credit Report Field Mapping Dictionary
Comprehensive field variations for accurate OCR extraction across all major credit bureaus
"""

import re
from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher

# Credit Limit field variations across credit bureaus
CREDIT_LIMIT_VARIATIONS = [
    # Standard terms
    "credit limit", "credit_limit", "creditlimit",
    "limit", "lmt", "cl",
    
    # High Credit (common in Experian)
    "high credit", "high_credit", "highcredit",
    "high balance", "high_balance", "highbalance",
    "highest balance", "highest_balance",
    
    # Maximum terms
    "maximum", "max", "maximum credit", "max credit",
    "maximum limit", "max limit", "max lmt",
    
    # Credit line terms
    "credit line", "credit_line", "creditline",
    "line of credit", "line_of_credit",
    
    # Bureau-specific variations
    "original amount", "original_amount",  # TransUnion
    "original balance", "original_balance",
    "credit available", "available credit",
    
    # Abbreviations
    "cr limit", "cr_limit", "crlimit",
    "cr line", "cr_line", "crline",
]

# Monthly Payment field variations
MONTHLY_PAYMENT_VARIATIONS = [
    # Standard payment terms
    "monthly payment", "monthly_payment", "monthlypayment",
    "payment", "pmt", "pay", "payment amount",
    
    # Minimum payment terms
    "minimum payment", "minimum_payment", "minimumpayment",
    "min payment", "min_payment", "minpayment",
    "min pmt", "min_pmt", "minpmt",
    
    # Scheduled payment terms
    "scheduled payment", "scheduled_payment",
    "regular payment", "regular_payment",
    "installment", "installment amount",
    
    # Due amount terms
    "amount due", "amount_due", "amountdue",
    "payment due", "payment_due", "paymentdue",
    "due", "monthly due", "monthly_due",
    
    # Bureau-specific terms
    "pay amt", "pay_amt", "payamt",
    "payment amt", "payment_amt", "paymentamt",
    "monthly amt", "monthly_amt", "monthlyamt",
    
    # Contract terms (auto/mortgage)
    "contract payment", "contract_payment",
    "note payment", "note_payment",
]

# Account Type field variations and mappings
ACCOUNT_TYPE_VARIATIONS = {
    # Credit Cards
    "credit_card": [
        "credit card", "credit_card", "creditcard", "cc",
        "revolving", "revolving credit", "revolving_credit",
        "open", "open end", "open_end", "openend",
        "bank card", "bank_card", "bankcard",
        "charge card", "charge_card", "chargecard",
        "r", "rev", "revolving account"
    ],
    
    # Installment loans
    "installment": [
        "installment", "installment loan", "installment_loan",
        "i", "inst", "closed end", "closed_end", "closedend",
        "term loan", "term_loan", "termloan",
        "fixed payment", "fixed_payment", "fixedpayment"
    ],
    
    # Auto loans
    "auto_loan": [
        "auto loan", "auto_loan", "autoloan", "auto",
        "automobile", "automobile loan", "automobile_loan",
        "car loan", "car_loan", "carloan", "car",
        "vehicle", "vehicle loan", "vehicle_loan",
        "motor vehicle", "motor_vehicle", "motorvehicle",
        "automotive", "automotive loan", "automotive_loan"
    ],
    
    # Mortgages
    "mortgage": [
        "mortgage", "mortgage loan", "mortgage_loan",
        "home loan", "home_loan", "homeloan",
        "real estate", "real_estate", "realestate",
        "property", "property loan", "property_loan",
        "residential", "residential loan", "residential_loan",
        "m", "mtg", "mort", "home", "house"
    ],
    
    # Student loans
    "student_loan": [
        "student loan", "student_loan", "studentloan",
        "education", "education loan", "education_loan",
        "educational", "educational loan", "educational_loan",
        "federal student", "federal_student",
        "private student", "private_student",
        "academic", "academic loan", "academic_loan"
    ],
    
    # Personal loans
    "personal_loan": [
        "personal loan", "personal_loan", "personalloan",
        "personal", "unsecured", "unsecured loan", "unsecured_loan",
        "signature", "signature loan", "signature_loan",
        "cash loan", "cash_loan", "cashloan",
        "consumer", "consumer loan", "consumer_loan"
    ],
    
    # Business accounts
    "business": [
        "business", "business loan", "business_loan",
        "commercial", "commercial loan", "commercial_loan",
        "corporate", "corporate loan", "corporate_loan",
        "business credit", "business_credit"
    ],
    
    # Secured cards/loans
    "secured": [
        "secured", "secured loan", "secured_loan",
        "secured card", "secured_card", "securedcard",
        "collateral", "collateral loan", "collateral_loan"
    ],
    
    # Store cards
    "store_card": [
        "store card", "store_card", "storecard",
        "retail", "retail card", "retail_card",
        "merchant", "merchant card", "merchant_card",
        "store credit", "store_credit", "storecredit"
    ],
    
    # Lines of credit
    "line_of_credit": [
        "line of credit", "line_of_credit", "lineofcredit",
        "loc", "credit line", "credit_line", "creditline",
        "heloc", "home equity", "home_equity", "homeequity",
        "equity line", "equity_line", "equityline"
    ]
}

# Metro 2 format account type codes
METRO2_ACCOUNT_CODES = {
    "00": "auto_loan",
    "01": "auto_loan", 
    "02": "secured",
    "03": "home_improvement",
    "04": "home_improvement",
    "05": "credit_card",
    "06": "line_of_credit",
    "07": "student_loan",
    "08": "personal_loan",
    "09": "recreational_vehicle",
    "10": "home_equity",
    "11": "mortgage",
    "12": "business",
    "13": "commercial_line_of_credit",
    "14": "construction",
    "15": "debt_consolidation",
    "16": "home_equity",
    "17": "time_share",
    "18": "mobile_home",
    "19": "undetermined",
    "20": "family_support",
    "21": "business",
    "22": "business",
    "89": "medical_debt",
    "91": "personal_loan",
    "92": "personal_loan",
    "93": "personal_loan",
    "94": "personal_loan",
    "95": "personal_loan"
}

class CreditReportFieldMapper:
    """Maps credit report field variations to standardized field names"""
    
    def __init__(self):
        self.credit_limit_patterns = self._create_patterns(CREDIT_LIMIT_VARIATIONS)
        self.monthly_payment_patterns = self._create_patterns(MONTHLY_PAYMENT_VARIATIONS)
        self.account_type_mappings = self._create_account_type_mappings()
    
    def _create_patterns(self, variations: List[str]) -> List[re.Pattern]:
        """Create compiled regex patterns from field variations"""
        patterns = []
        for variation in variations:
            # Create pattern that matches the variation with common separators
            pattern = re.compile(
                rf'\b{re.escape(variation)}\b[:\s]*\$?(\d{{1,3}}(?:,\d{{3}})*(?:\.\d{{2}})?)',
                re.IGNORECASE
            )
            patterns.append(pattern)
        return patterns
    
    def _create_account_type_mappings(self) -> Dict[str, str]:
        """Create mapping from all variations to standardized account types"""
        mappings = {}
        for account_type, variations in ACCOUNT_TYPE_VARIATIONS.items():
            for variation in variations:
                mappings[variation.lower()] = account_type
        return mappings
    
    def extract_credit_limit(self, text: str) -> Optional[str]:
        """Extract credit limit from text using pattern matching with fuzzy matching"""
        # Apply OCR corrections first
        corrected_text = apply_ocr_corrections(text)
        
        # First try direct pattern matching on corrected text
        for pattern in self.credit_limit_patterns:
            match = pattern.search(corrected_text)
            if match:
                amount = correct_ocr_in_numbers(match.group(1))
                return f"${amount}"
        
        # Try fuzzy matching for OCR-corrupted field names
        fuzzy_result = self._extract_with_fuzzy_matching(corrected_text, CREDIT_LIMIT_VARIATIONS)
        if fuzzy_result:
            return fuzzy_result
        
        # Try contextual extraction with nearby dollar amounts
        return self._extract_field_with_context(corrected_text, CREDIT_LIMIT_VARIATIONS, ["credit", "limit", "high"])
    
    def extract_monthly_payment(self, text: str) -> Optional[str]:
        """Extract monthly payment from text using pattern matching with fuzzy matching"""
        # Apply OCR corrections first
        corrected_text = apply_ocr_corrections(text)
        
        # First try direct pattern matching on corrected text
        for pattern in self.monthly_payment_patterns:
            match = pattern.search(corrected_text)
            if match:
                amount = correct_ocr_in_numbers(match.group(1))
                return f"${amount}"
        
        # Try fuzzy matching for OCR-corrupted field names
        fuzzy_result = self._extract_with_fuzzy_matching(corrected_text, MONTHLY_PAYMENT_VARIATIONS)
        if fuzzy_result:
            return fuzzy_result
        
        # Try contextual extraction
        return self._extract_field_with_context(corrected_text, MONTHLY_PAYMENT_VARIATIONS, ["payment", "monthly", "minimum"])
    
    def extract_account_type(self, text: str, creditor_name: str = "") -> Optional[str]:
        """Extract account type from text and creditor context"""
        text_lower = text.lower()
        creditor_lower = creditor_name.lower()
        
        # Check for Metro 2 format codes first
        metro2_match = re.search(r'\b(\d{2})\b', text)
        if metro2_match and metro2_match.group(1) in METRO2_ACCOUNT_CODES:
            return METRO2_ACCOUNT_CODES[metro2_match.group(1)]
        
        # Check for single letter codes (R, I, M)
        if re.search(r'\bR\b.*revolv', text_lower):
            return "credit_card"
        elif re.search(r'\bI\b.*install', text_lower):
            return "installment"
        elif re.search(r'\bM\b.*mortg', text_lower):
            return "mortgage"
        
        # Score each account type based on text content
        type_scores = {}
        for account_type, variations in ACCOUNT_TYPE_VARIATIONS.items():
            score = 0
            for variation in variations:
                if variation in text_lower:
                    score += 2
                if variation in creditor_lower:
                    score += 1
            type_scores[account_type] = score
        
        # Return the highest scoring type (if score > 0)
        if type_scores:
            best_type = max(type_scores.items(), key=lambda x: x[1])
            if best_type[1] > 0:
                return best_type[0]
        
        # Fallback: infer from creditor name
        return self._infer_account_type_from_creditor(creditor_name)
    
    def _extract_field_with_context(self, text: str, field_variations: List[str], context_keywords: List[str]) -> Optional[str]:
        """Extract field value using contextual clues with enhanced multi-line support"""
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Check if line contains field variation or context keywords
            has_field_keyword = any(var in line_lower for var in field_variations)
            has_context = any(kw in line_lower for kw in context_keywords)
            
            if has_field_keyword or has_context:
                # Enhanced search: look in current line and up to 3 lines below/above
                search_range = 3
                search_lines = []
                
                # Add lines before (up to search_range)
                for j in range(max(0, i - search_range), i):
                    search_lines.append(lines[j])
                
                # Add current line
                search_lines.append(line)
                
                # Add lines after (up to search_range)  
                for j in range(i + 1, min(len(lines), i + search_range + 1)):
                    search_lines.append(lines[j])
                
                # Look for dollar amounts in all search lines
                for search_line in search_lines:
                    # Try multiple dollar amount patterns
                    dollar_patterns = [
                        r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $1,234.56
                        r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $ 1,234.56
                        r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*\$',  # 1,234.56$
                        r'USD\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # USD 1,234.56
                        r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*USD',  # 1,234.56 USD
                    ]
                    
                    for pattern in dollar_patterns:
                        dollar_match = re.search(pattern, search_line)
                        if dollar_match:
                            amount = dollar_match.group(1)
                            # Clean OCR errors
                            amount = self._clean_ocr_number(amount)
                            return f"${amount}"
                
                # If no dollar amount found, try looking for just numbers that might be currency
                for search_line in search_lines:
                    # Look for standalone numbers that could be currency amounts
                    number_pattern = r'\b(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\b'
                    number_matches = re.findall(number_pattern, search_line)
                    
                    for number in number_matches:
                        # Skip obviously non-currency numbers (like years, phone numbers)
                        if self._is_likely_currency_amount(number):
                            amount = self._clean_ocr_number(number)
                            return f"${amount}"
        
        return None
    
    def _is_likely_currency_amount(self, number_str: str) -> bool:
        """Determine if a number string is likely a currency amount"""
        try:
            # Remove commas and convert to float
            amount = float(number_str.replace(',', ''))
            
            # Reasonable currency range: $1 to $1,000,000
            if 1.0 <= amount <= 1000000.0:
                # Additional checks
                if '.' in number_str:
                    # If has decimal, should be .XX format
                    decimal_part = number_str.split('.')[1]
                    if len(decimal_part) == 2:
                        return True
                else:
                    # Whole dollar amounts are valid
                    return True
            
            return False
        except ValueError:
            return False
    
    def _extract_with_fuzzy_matching(self, text: str, field_variations: List[str], threshold: float = 0.7) -> Optional[str]:
        """Extract field value using fuzzy matching for OCR-corrupted field names"""
        lines = text.split('\n')
        
        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue
            
            # Look for potential field names with fuzzy matching
            words = line_clean.split()
            
            # Check different word combinations for field name matches
            for i in range(len(words)):
                for j in range(i + 1, min(i + 4, len(words) + 1)):  # Check up to 3-word combinations
                    phrase = " ".join(words[i:j]).lower()
                    
                    # Find best fuzzy match
                    for variation in field_variations:
                        similarity = SequenceMatcher(None, phrase, variation.lower()).ratio()
                        
                        if similarity >= threshold:
                            # Found fuzzy match, look for dollar amount in rest of line
                            remaining_text = " ".join(words[j:])
                            dollar_match = re.search(r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', remaining_text)
                            
                            if dollar_match:
                                amount = dollar_match.group(1)
                                # Clean up OCR errors in numbers
                                amount = self._clean_ocr_number(amount)
                                return f"${amount}"
                            
                            # Also check the words before the matched phrase
                            preceding_text = " ".join(words[:i])
                            dollar_match = re.search(r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', preceding_text)
                            
                            if dollar_match:
                                amount = dollar_match.group(1)
                                amount = self._clean_ocr_number(amount)
                                return f"${amount}"
        
        return None
    
    def _clean_ocr_number(self, number_str: str) -> str:
        """Clean OCR errors from number strings"""
        # Remove extra spaces
        cleaned = re.sub(r'\s+', '', number_str)
        
        # Fix common OCR errors
        cleaned = cleaned.replace('O', '0')  # Letter O to zero
        cleaned = cleaned.replace('l', '1')  # Letter l to one
        cleaned = cleaned.replace('I', '1')  # Letter I to one
        cleaned = cleaned.replace('S', '5')  # Letter S to five (sometimes)
        
        # Ensure proper comma placement
        if ',' in cleaned:
            parts = cleaned.split(',')
            if len(parts) == 2 and len(parts[1]) == 3:
                # Looks like proper thousands separator
                pass
            else:
                # Remove improper commas and reformat
                cleaned = cleaned.replace(',', '')
                if len(cleaned) >= 4:
                    # Add proper comma for thousands
                    cleaned = cleaned[:-3] + ',' + cleaned[-3:]
        
        return cleaned
    
    def _infer_account_type_from_creditor(self, creditor_name: str) -> str:
        """Infer account type from creditor name patterns"""
        creditor_lower = creditor_name.lower()
        
        # Auto loans
        auto_keywords = ["ford", "honda", "toyota", "nissan", "gm", "chrysler", "auto", "motor", "vehicle"]
        if any(kw in creditor_lower for kw in auto_keywords):
            return "auto_loan"
        
        # Student loans
        student_keywords = ["navient", "great lakes", "nelnet", "fedloan", "mohela", "education", "student"]
        if any(kw in creditor_lower for kw in student_keywords):
            return "student_loan"
        
        # Mortgages
        mortgage_keywords = ["quicken", "rocket", "freedom mortgage", "pennymac", "caliber", "mortgage"]
        if any(kw in creditor_lower for kw in mortgage_keywords):
            return "mortgage"
        
        # Store cards
        store_keywords = ["amazon", "target", "home depot", "lowes", "walmart", "costco", "nordstrom", "macys", "kohls"]
        if any(kw in creditor_lower for kw in store_keywords):
            return "store_card"
        
        # Personal loans
        personal_keywords = ["lending club", "prosper", "sofi", "avant", "onemain", "springleaf", "personal"]
        if any(kw in creditor_lower for kw in personal_keywords):
            return "personal_loan"
        
        # Default to credit card for banks and general creditors
        return "credit_card"
    
    def validate_currency_format(self, value: str) -> bool:
        """Check if a value looks like a valid currency amount"""
        if not value:
            return False
        
        # Check for dollar sign and numbers
        currency_pattern = re.compile(r'^\$?\d{1,3}(,\d{3})*(\.\d{2})?$')
        
        # Clean the value and check
        cleaned = value.strip().replace(' ', '')
        if currency_pattern.match(cleaned):
            return True
        
        # Also accept just numbers (will be formatted later)
        number_pattern = re.compile(r'^\d+(\.\d{2})?$')
        if number_pattern.match(cleaned):
            return True
        
        return False

# OCR Error Correction Patterns
OCR_CORRECTION_PATTERNS = {
    # Common OCR errors in credit report field names
    "field_name_corrections": {
        # Credit Limit variations with OCR errors
        "high cr edit": "high credit",
        "high cred it": "high credit", 
        "high cre dit": "high credit",
        "high credlt": "high credit",
        "hlgh credit": "high credit",
        "hìgh credit": "high credit",
        "crédit limit": "credit limit",
        "credit lim it": "credit limit",
        "credit lirnit": "credit limit",
        "credìt limit": "credit limit",
        "credit lìmit": "credit limit",
        "limìt": "limit",
        "lirnit": "limit",
        "maximum": "maximum",
        "maximurn": "maximum",
        "maxìmum": "maximum",
        
        # Monthly Payment variations with OCR errors
        "monthly pay ment": "monthly payment",
        "monthly payrnent": "monthly payment",
        "rnonthly payment": "monthly payment",
        "monthIy payment": "monthly payment",
        "payment arnount": "payment amount",
        "payment amt": "payment amount",
        "pay ment": "payment",
        "payrnent": "payment",
        "rninimum": "minimum",
        "mìnimum": "minimum",
        "min pay ment": "min payment",
        "min payrnent": "min payment",
        
        # Account balance variations
        "current bal": "current balance",
        "current baI": "current balance",
        "balance": "balance",
        "baIance": "balance",
        "balanee": "balance",
        "arnount owed": "amount owed",
        "amount owèd": "amount owed",
        
        # General OCR character corrections
        "rn": "m",  # Common OCR error: rn -> m
        "Ii": "li",  # Common OCR error: capital I -> lowercase l
    },
    
    # Common OCR errors in numbers
    "number_corrections": {
        "O": "0",  # Letter O to zero
        "l": "1",  # Letter l to one  
        "I": "1",  # Letter I to one
        "S": "5",  # Letter S to five (sometimes)
        "s": "5",  # Letter s to five (sometimes)
        "B": "8",  # Letter B to eight (sometimes)
        "G": "6",  # Letter G to six (sometimes)
        "Z": "2",  # Letter Z to two (sometimes)
    }
}

def apply_ocr_corrections(text: str) -> str:
    """Apply OCR error corrections to text"""
    corrected_text = text.lower()
    
    # Apply field name corrections
    for error, correction in OCR_CORRECTION_PATTERNS["field_name_corrections"].items():
        corrected_text = corrected_text.replace(error, correction)
    
    return corrected_text

def correct_ocr_in_numbers(number_str: str) -> str:
    """Apply OCR corrections specifically to number strings"""
    corrected = number_str
    
    for error, correction in OCR_CORRECTION_PATTERNS["number_corrections"].items():
        corrected = corrected.replace(error, correction)
    
    return corrected

# Create global instance for easy import
field_mapper = CreditReportFieldMapper()