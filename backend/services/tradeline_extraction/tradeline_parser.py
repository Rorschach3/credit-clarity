"""
Tradeline parser for TransUnion credit report text
Implements field-by-field parsing and validation with exact format matching
"""
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ParsedTradeline:
    """Parsed tradeline data structure"""
    credit_bureau: str = 'TransUnion'
    creditor_name: Optional[str] = None
    account_number: Optional[str] = None
    account_status: Optional[str] = None
    account_type: Optional[str] = None
    date_opened: Optional[str] = None
    monthly_payment: Optional[str] = None
    credit_limit: Optional[str] = None
    account_balance: Optional[str] = None
    user_id: Optional[str] = None
    id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format matching expected test data"""
        return {
            'credit_bureau': self.credit_bureau,
            'creditor_name': self.creditor_name,
            'account_number': self.account_number,
            'account_status': self.account_status,
            'account_type': self.account_type,
            'date_opened': self.date_opened,
            'monthly_payment': self.monthly_payment,
            'credit_limit': self.credit_limit,
            'account_balance': self.account_balance,
            'user_id': self.user_id,
            'id': self.id,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class TransUnionTradelineParser:
    """
    Parser for TransUnion credit report tradelines
    Implements exact field matching against expected test data
    """
    
    def __init__(self):
        # Account type mappings from TransUnion format to expected format
        self.account_type_mappings = {
            'revolving': 'Revolving',
            'revolving account': 'Revolving', 
            'installment': 'Installment',
            'installment account': 'Installment'
        }
        
        # Account status mappings
        self.account_status_mappings = {
            'current': 'Current',
            'closed': 'Closed',
            'open': 'Current',  # Map open to current
            'paid': 'Closed'    # Map paid to closed
        }
        
        # Currency pattern for formatting
        self.currency_pattern = re.compile(r'[\$,]')
        
        # Date pattern (MM/DD/YYYY)
        self.date_pattern = re.compile(r'(\d{1,2})/(\d{1,2})/(\d{4})')
    
    def parse_tradelines_from_text(self, text: str) -> List[ParsedTradeline]:
        """
        Parse all tradelines from extracted text
        Returns list of ParsedTradeline objects
        """
        tradelines = []
        
        # Split text into sections for each creditor
        creditor_sections = self._split_into_creditor_sections(text)
        
        for section in creditor_sections:
            try:
                tradeline = self._parse_single_tradeline_section(section)
                if tradeline and tradeline.creditor_name:  # Only add if we found a creditor
                    tradelines.append(tradeline)
            except Exception as e:
                logger.warning(f"Failed to parse tradeline section: {e}")
                continue
        
        # Generate IDs and timestamps for parsed tradelines
        self._add_metadata_to_tradelines(tradelines)
        
        return tradelines
    
    def _split_into_creditor_sections(self, text: str) -> List[str]:
        """
        Split text into individual creditor sections
        Each section contains information for one tradeline
        """
        lines = text.strip().split('\n')
        sections = []
        current_section = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line looks like a new creditor (starts with uppercase letters)
            if self._looks_like_creditor_name(line) and current_section:
                # Save previous section and start new one
                sections.append('\n'.join(current_section))
                current_section = [line]
            else:
                current_section.append(line)
        
        # Don't forget the last section
        if current_section:
            sections.append('\n'.join(current_section))
        
        return sections
    
    def _looks_like_creditor_name(self, line: str) -> bool:
        """
        Check if a line looks like a creditor name
        Creditor names are typically all caps and don't contain account info patterns
        """
        line = line.strip()
        
        # Skip header lines and common report sections
        skip_patterns = [
            'transunion', 'credit report', 'tradeline', 'account information',
            'account number:', 'account type:', 'balance:', 'date opened:',
            'monthly payment:', 'credit limit:', 'payment history:'
        ]
        
        if any(pattern in line.lower() for pattern in skip_patterns):
            return False
        
        # Skip lines that contain colons (likely field labels)
        if ':' in line:
            return False
        
        # Look for patterns that indicate this is likely a creditor name
        # Most creditor names are all caps or contain business indicators
        has_business_words = any(word in line.upper() for word in [
            'BANK', 'CARD', 'CREDIT', 'LLC', 'INC', 'CORP', 'FCU', 'FINANCIAL', 'SERVICES'
        ])
        
        # Check if mostly uppercase or has business indicators
        is_mostly_caps = len([c for c in line if c.isupper()]) > len(line) * 0.5
        
        # Must have at least some letters
        has_letters = any(c.isalpha() for c in line)
        
        return (is_mostly_caps or has_business_words) and len(line) > 3 and has_letters
    
    def _parse_single_tradeline_section(self, section: str) -> Optional[ParsedTradeline]:
        """
        Parse a single tradeline section into a ParsedTradeline object
        """
        tradeline = ParsedTradeline()
        lines = [line.strip() for line in section.split('\n') if line.strip()]
        
        if not lines:
            return None
        
        # First line should be the creditor name
        tradeline.creditor_name = lines[0].strip()
        
        # Parse remaining lines for account information
        for line in lines[1:]:
            self._parse_account_info_line(line, tradeline)
        
        return tradeline
    
    def _parse_account_info_line(self, line: str, tradeline: ParsedTradeline):
        """
        Parse a single line of account information
        """
        line_lower = line.lower().strip()
        
        # Account Number
        if 'account number:' in line_lower:
            account_num = line.split(':', 1)[1].strip()
            tradeline.account_number = self._format_account_number(account_num)
        
        # Account Type
        elif 'account type:' in line_lower:
            account_type = line.split(':', 1)[1].strip()
            tradeline.account_type = self._normalize_account_type(account_type)
        
        # Account Status
        elif 'account status:' in line_lower:
            status = line.split(':', 1)[1].strip()
            tradeline.account_status = self._normalize_account_status(status)
        
        # Date Opened
        elif 'date opened:' in line_lower:
            date_str = line.split(':', 1)[1].strip()
            tradeline.date_opened = self._format_date(date_str)
        
        # Monthly Payment
        elif 'monthly payment:' in line_lower:
            payment = line.split(':', 1)[1].strip()
            tradeline.monthly_payment = self._format_currency(payment)
        
        # Credit Limit
        elif 'credit limit:' in line_lower:
            limit = line.split(':', 1)[1].strip()
            tradeline.credit_limit = self._format_currency(limit)
        
        # Balance
        elif 'balance:' in line_lower:
            balance = line.split(':', 1)[1].strip()
            tradeline.account_balance = self._format_currency(balance)
    
    def _format_account_number(self, account_num: str) -> Optional[str]:
        """
        Format account number to match expected format
        Should end with ****
        """
        if not account_num or account_num.lower() in ['none', 'n/a', '']:
            return None
        
        # Clean up and ensure it ends with ****
        account_num = account_num.strip()
        if not account_num.endswith('****'):
            # If it looks like a partial account number, add ****
            if re.match(r'^[A-Z0-9]+$', account_num):
                account_num += '****'
        
        return account_num
    
    def _normalize_account_type(self, account_type: str) -> Optional[str]:
        """
        Normalize account type to match expected values (Revolving/Installment)
        """
        if not account_type:
            return None
        
        account_type_clean = account_type.lower().strip()
        return self.account_type_mappings.get(account_type_clean, account_type)
    
    def _normalize_account_status(self, status: str) -> Optional[str]:
        """
        Normalize account status to match expected values (Current/Closed)
        """
        if not status:
            return None
        
        status_clean = status.lower().strip()
        return self.account_status_mappings.get(status_clean, status)
    
    def _format_date(self, date_str: str) -> Optional[str]:
        """
        Format date to MM/DD/YYYY format
        """
        if not date_str or date_str.lower() in ['none', 'n/a', '']:
            return None
        
        date_str = date_str.strip()
        
        # Try to parse various date formats
        date_formats = [
            '%m/%d/%Y',    # MM/DD/YYYY
            '%m/%d/%y',    # MM/DD/YY
            '%Y-%m-%d',    # YYYY-MM-DD
            '%m-%d-%Y',    # MM-DD-YYYY
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime('%m/%d/%Y')  # Always return MM/DD/YYYY
            except ValueError:
                continue
        
        # If no format works, try to extract with regex
        match = self.date_pattern.search(date_str)
        if match:
            month, day, year = match.groups()
            return f"{month.zfill(2)}/{day.zfill(2)}/{year}"
        
        return None
    
    def _format_currency(self, amount: str) -> Optional[str]:
        """
        Format currency amount to match expected format ($X,XXX or $X)
        """
        if not amount or amount.lower() in ['none', 'n/a', '']:
            return None
        
        amount = amount.strip()
        
        # Extract numeric value
        numeric_match = re.search(r'[\d,]+\.?\d*', amount)
        if not numeric_match:
            return None
        
        numeric_str = numeric_match.group()
        
        try:
            # Parse the numeric value
            numeric_value = float(numeric_str.replace(',', ''))
            
            # Format as currency
            if numeric_value == 0:
                return '$0'
            elif numeric_value >= 1000:
                return f"${numeric_value:,.0f}"
            else:
                return f"${numeric_value:.0f}"
                
        except ValueError:
            return None
    
    def _add_metadata_to_tradelines(self, tradelines: List[ParsedTradeline]):
        """
        Add ID and timestamp metadata to tradelines
        """
        current_time = datetime.now().isoformat() + '+00'
        
        for tradeline in tradelines:
            tradeline.id = str(uuid.uuid4())
            tradeline.created_at = current_time
            tradeline.updated_at = current_time
    
    def validate_parsed_tradeline(self, tradeline: ParsedTradeline) -> Dict[str, Any]:
        """
        Validate parsed tradeline against expected format
        Returns validation results
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Required fields
        required_fields = ['creditor_name']
        for field in required_fields:
            if not getattr(tradeline, field):
                validation_result['valid'] = False
                validation_result['errors'].append(f"Missing required field: {field}")
        
        # Validate account type
        if tradeline.account_type and tradeline.account_type not in ['Revolving', 'Installment']:
            validation_result['warnings'].append(f"Unexpected account type: {tradeline.account_type}")
        
        # Validate account status  
        if tradeline.account_status and tradeline.account_status not in ['Current', 'Closed']:
            validation_result['warnings'].append(f"Unexpected account status: {tradeline.account_status}")
        
        # Validate date format
        if tradeline.date_opened:
            if not self.date_pattern.match(tradeline.date_opened):
                validation_result['errors'].append(f"Invalid date format: {tradeline.date_opened}")
        
        # Validate currency formats
        currency_fields = ['monthly_payment', 'credit_limit', 'account_balance']
        for field in currency_fields:
            value = getattr(tradeline, field)
            if value and not (value.startswith('$') or value == '$0'):
                validation_result['warnings'].append(f"Currency field {field} should start with $: {value}")
        
        return validation_result