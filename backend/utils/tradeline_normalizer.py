"""
Tradeline Data Normalizer
Standardizes and normalizes extracted tradeline data to match expected format
"""

import re
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TradelineNormalizer:
    """Normalizes tradeline data to standardized format"""
    
    def __init__(self):
        # Account type mapping from verbose to standard
        self.account_type_mapping = {
            # Revolving accounts
            "credit card": "Revolving",
            "store card": "Revolving", 
            "revolving": "Revolving",
            "line of credit": "Revolving",
            "credit line": "Revolving",
            
            # Installment accounts
            "auto loan": "Installment",
            "student loan": "Installment",
            "personal loan": "Installment",
            "mortgage": "Installment",
            "installment loan": "Installment",
            "installment": "Installment",
            "loan": "Installment",
        }
        
        # Account status mapping from verbose to standard
        self.account_status_mapping = {
            # Current/Open accounts
            "current": "Current",
            "current account": "Current", 
            "open": "Current",
            "good standing": "Current",
            "paid as agreed": "Current",
            "up to date": "Current",
            
            # Closed accounts
            "closed": "Closed",
            "paid": "Closed",
            "paid, closed": "Closed",
            "paid, closed; was paid as agreed": "Closed",
            "account closed": "Closed",
            "satisfied": "Closed",
            
            # Late accounts
            "late": "Late",
            "past due": "Late",
            "delinquent": "Late",
            "30 days late": "Late",
            "60 days late": "Late",
            "90 days late": "Late",
            
            # Collection accounts
            "collection": "Collection",
            "in collection": "Collection",
            "charged off": "Collection",
            "charge off": "Collection",
            "write off": "Collection",
        }
        
        # Enhanced account number patterns
        self.account_number_patterns = [
            # Masked patterns (preferred)
            re.compile(r'\*{4,}\d{4,}'),  # ****1234
            re.compile(r'x{4,}\d{4,}', re.IGNORECASE),  # xxxx1234
            re.compile(r'\d{4,}[-\s]?\*{4,}'),  # 1234****
            re.compile(r'\d{4,}[-\s]?x{4,}', re.IGNORECASE),  # 1234xxxx
            
            # Account with text
            re.compile(r'(?:account|acct|card)\s*#?\s*:?\s*(\*{4,}\d{4,}|\d{4,}\*{4,})', re.IGNORECASE),
            re.compile(r'(?:account|acct|card)\s*#?\s*:?\s*(x{4,}\d{4,}|\d{4,}x{4,})', re.IGNORECASE),
            
            # Full numbers (less preferred but valid)
            re.compile(r'\b\d{13,19}\b'),  # 13-19 digit card numbers
            re.compile(r'\b\d{10,12}\b'),  # 10-12 digit account numbers
            
            # Special formats
            re.compile(r'[A-Z]{2,3}\d{10,}'),  # CBA0000000001022****
            re.compile(r'\d{8,}[A-Z]\d{4,}'),  # 25068505471E0012024052124****
        ]
        
        # Date patterns for parsing
        self.date_patterns = [
            (re.compile(r'(\d{1,2})/(\d{1,2})/(\d{4})'), 'MM/DD/YYYY'),
            (re.compile(r'(\d{1,2})-(\d{1,2})-(\d{4})'), 'MM-DD-YYYY'),
            (re.compile(r'(\d{4})-(\d{1,2})-(\d{1,2})'), 'YYYY-MM-DD'),
            (re.compile(r'(\d{1,2})/(\d{4})'), 'MM/YYYY'),
        ]
    
    def normalize_tradeline(self, tradeline: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a single tradeline to standard format"""
        normalized = {
            "creditor_name": self._normalize_creditor_name(tradeline.get("creditor_name", "")),
            "account_number": self._normalize_account_number(tradeline.get("account_number", "")),
            "account_balance": self._normalize_currency(tradeline.get("account_balance", "")),
            "credit_limit": self._normalize_currency(tradeline.get("credit_limit", "")),
            "monthly_payment": self._normalize_currency(tradeline.get("monthly_payment", "")),
            "date_opened": self._normalize_date(tradeline.get("date_opened", "")),
            "account_type": self._normalize_account_type(tradeline.get("account_type", "")),
            "account_status": self._normalize_account_status(tradeline.get("account_status", "")),
            "credit_bureau": self._normalize_credit_bureau(tradeline.get("credit_bureau", "")),
            "is_negative": self._determine_negative_status(tradeline),
        }
        
        # Use None instead of empty strings for missing data
        for key, value in normalized.items():
            if value == "" or value == "N/A":
                normalized[key] = None
                
        return normalized
    
    def _normalize_creditor_name(self, value: str) -> Optional[str]:
        """Normalize creditor name"""
        if not value or not value.strip():
            return None
            
        # Clean up common OCR errors and whitespace
        cleaned = value.strip()
        
        # Skip purely numeric values (likely reference codes, not creditor names)
        if cleaned.isdigit():
            logger.warning(f"Skipping numeric creditor name: {cleaned} (likely a reference code)")
            return None
        
        # Convert to uppercase for standardization
        cleaned = cleaned.upper()
        
        # Common creditor name mappings (numeric codes to actual names)
        creditor_mappings = {
            # Major credit card companies
            "28368": "ALLY FINANCIAL",
            "3552": "DISCOVER BANK", 
            "28629": "SYNCHRONY BANK",
            "8874": "CAPITAL ONE",
            "23928": "CHASE BANK",
            
            # Banks and financial institutions
            "JPMCB CARD SERVICES": "CHASE BANK",
            "SYNCB/CARE CREDIT": "SYNCHRONY BANK/CARE CREDIT",
            "SELF FINANCIAL INC/ LEAD BANK": "SELF FINANCIAL INC/LEAD BANK",
            "MOHELA/DEPT OF ED": "MOHELA/DEPT OF ED",
            "SYNCHRONY/CARE CREDIT": "SYNCHRONY BANK/CARE CREDIT",
            
            # Common variations
            "SYNCHRONY": "SYNCHRONY BANK",
            "DISCOVER": "DISCOVER BANK",
            "CAPITAL ONE N.A.": "CAPITAL ONE",
            "CHASE": "CHASE BANK",
            "CITIBANK": "CITIBANK N.A.",
        }
        
        # Apply mappings
        for pattern, replacement in creditor_mappings.items():
            if pattern in cleaned:
                cleaned = replacement
                break
        
        # If still numeric after mapping, return None
        if cleaned.isdigit():
            return None
        
        return cleaned.title()  # Return in title case
    
    def _normalize_account_number(self, value: str, creditor_context: str = "") -> Optional[str]:
        """Extract and normalize account number"""
        if not value or not value.strip():
            # Try to extract from raw text if available
            return None
        
        value = value.strip()
        
        # Try each pattern
        for pattern in self.account_number_patterns:
            match = pattern.search(value)
            if match:
                account_num = match.group(1) if match.groups() else match.group(0)
                
                # Standardize format
                if len(account_num) >= 12 and account_num.isdigit():
                    # Mask full card numbers: 1234567890123456 -> 123456****3456
                    return f"{account_num[:6]}****{account_num[-4:]}" if len(account_num) >= 16 else f"{account_num[:-4]}****"
                elif '*' in account_num or 'x' in account_num.lower():
                    # Already masked
                    return account_num
                elif len(account_num) >= 8:
                    # Mask partial numbers
                    return f"{account_num[:-4]}****"
                
                return account_num
        
        return None
    
    def _normalize_currency(self, value: str) -> Optional[str]:
        """Normalize currency values"""
        if not value or not value.strip():
            return None
        
        # Handle malformed values
        if value in ["$,", "$", ","]:
            return None
        
        # Extract numeric value
        numeric_match = re.search(r'[\d,]+\.?\d*', value)
        if not numeric_match:
            return None
        
        try:
            # Clean and parse
            numeric_str = numeric_match.group(0).replace(',', '')
            amount = float(numeric_str)
            
            # Format consistently
            if amount == 0:
                return "$0"
            elif amount == int(amount):
                return f"${int(amount):,}"
            else:
                return f"${amount:,.2f}"
                
        except ValueError:
            return None
    
    def _normalize_date(self, value: str) -> Optional[str]:
        """Normalize date to MM/DD/YYYY format"""
        if not value or not value.strip():
            return None
        
        # Handle malformed dates like "'\"xxxx/xx/xx\"'::text"
        if "xxxx" in value or "xx/xx" in value or "'\"" in value:
            return None
        
        value = value.strip().strip("'\"")
        
        for pattern, format_type in self.date_patterns:
            match = pattern.match(value)
            if match:
                try:
                    if format_type == 'MM/DD/YYYY':
                        month, day, year = map(int, match.groups())
                    elif format_type == 'MM-DD-YYYY':
                        month, day, year = map(int, match.groups())
                    elif format_type == 'YYYY-MM-DD':
                        year, month, day = map(int, match.groups())
                    elif format_type == 'MM/YYYY':
                        month, year = map(int, match.groups())
                        day = 1  # Default to first of month
                    
                    # Validate ranges
                    if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= datetime.now().year:
                        return f"{month:02d}/{day:02d}/{year}"
                        
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _normalize_account_type(self, value: str) -> Optional[str]:
        """Normalize account type to standard values"""
        if not value or not value.strip():
            return None
        
        value_lower = value.strip().lower()
        
        # Direct mapping
        for verbose, standard in self.account_type_mapping.items():
            if verbose in value_lower:
                return standard
        
        # Default based on common patterns
        if any(term in value_lower for term in ["card", "revolving", "line"]):
            return "Revolving"
        elif any(term in value_lower for term in ["loan", "mortgage", "installment"]):
            return "Installment"
        
        return "Revolving"  # Default assumption
    
    def _normalize_account_status(self, value: str) -> Optional[str]:
        """Normalize account status to standard values"""
        if not value or not value.strip():
            return "Current"  # Default assumption
        
        value_lower = value.strip().lower()
        
        # Direct mapping
        for verbose, standard in self.account_status_mapping.items():
            if verbose in value_lower:
                return standard
        
        # Default based on common patterns
        if any(term in value_lower for term in ["open", "current", "good", "paid as agreed"]):
            return "Current"
        elif any(term in value_lower for term in ["closed", "paid", "satisfied"]):
            return "Closed"
        elif any(term in value_lower for term in ["late", "past due", "delinquent"]):
            return "Late"
        elif any(term in value_lower for term in ["collection", "charge", "write"]):
            return "Collection"
        
        return "Current"  # Default assumption
    
    def _normalize_credit_bureau(self, value: str) -> Optional[str]:
        """Normalize credit bureau name"""
        if not value or not value.strip():
            return None
        
        value_lower = value.strip().lower()
        
        if "experian" in value_lower:
            return "Experian"
        elif "equifax" in value_lower:
            return "Equifax"
        elif "transunion" in value_lower or "trans union" in value_lower:
            return "TransUnion"
        
        return None
    
    def _determine_negative_status(self, tradeline: Dict[str, Any]) -> bool:
        """Determine if tradeline has negative impact"""
        account_status = tradeline.get("account_status", "").lower()
        
        # Negative indicators
        negative_statuses = [
            "late", "past due", "delinquent", "collection", 
            "charged off", "charge off", "write off"
        ]
        
        return any(status in account_status for status in negative_statuses)


# Global instance
tradeline_normalizer = TradelineNormalizer()