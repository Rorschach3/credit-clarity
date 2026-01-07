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

# Shared date parser utility
from utils.date_parser import CreditReportDateParser
from services.advanced_parsing.negative_tradeline_classifier import NegativeTradelineClassifier

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

        # Initialize shared date parser
        self.date_parser = CreditReportDateParser()

        # Negative classifier for extra signals
        self.negative_classifier = NegativeTradelineClassifier()

        # Section splitting helpers
        self.section_dividers = [
            r'(?i)account information',
            r'(?i)tradeline',
            r'(?i)creditor',
            r'(?i)company name',
            r'(?i)account #',
            r'(?i)loan type'
        ]

        # Table header mapping
        self.table_header_mapping = {
            'creditor': 'creditor_name',
            'company': 'creditor_name',
            'lender': 'creditor_name',
            'account': 'account_number',
            'account number': 'account_number',
            'acct': 'account_number',
            'balance': 'account_balance',
            'current balance': 'account_balance',
            'limit': 'credit_limit',
            'credit limit': 'credit_limit',
            'payment': 'monthly_payment',
            'monthly payment': 'monthly_payment',
            'status': 'account_status',
            'account status': 'account_status',
            'type': 'account_type',
            'account type': 'account_type',
            'opened': 'date_opened',
            'date opened': 'date_opened'
        }

        # Payment history detection
        self.payment_history_patterns = [
            re.compile(r'(?i)payment history[:\s]+(.+?)(?=\n\S|$)', re.MULTILINE),
            re.compile(r'(?i)(\d+\s+days?\s+late)', re.MULTILINE),
            re.compile(r'(?i)late\s+(\d+)', re.MULTILINE)
        ]
    
    def parse_tradelines_from_text(self, text: str) -> List[ParsedTradeline]:
        """
        Parse all tradelines from extracted text
        Returns list of ParsedTradeline objects
        """
        tradelines = []
        
        # Split text into sections for each creditor
        creditor_sections = self._split_into_creditor_sections(text)
        table_tradelines = self._extract_tradelines_from_tables(text)
        
        for section in creditor_sections:
            try:
                tradeline = self._parse_single_tradeline_section(section)
                if tradeline and tradeline.creditor_name:  # Only add if we found a creditor
                    tradelines.append(tradeline)
            except Exception as e:
                logger.warning(f"Failed to parse tradeline section: {e}")
                continue

        if table_tradelines:
            logger.info(f"Parsed {len(table_tradelines)} tradelines from detected tables")
            tradelines.extend(table_tradelines)
        
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

    def _extract_tradelines_from_tables(self, text: str) -> List[ParsedTradeline]:
        """Pull tradelines from rudimentary tables detected inside the report."""
        lines = [line.strip() for line in text.splitlines()]
        table_blocks: List[List[str]] = []
        current_block: List[str] = []

        for line in lines:
            if '|' in line and len(line.split('|')) > 1:
                current_block.append(line)
            else:
                if len(current_block) >= 2:
                    table_blocks.append(current_block.copy())
                current_block = []

        if len(current_block) >= 2:
            table_blocks.append(current_block)

        tradelines: List[ParsedTradeline] = []
        for block in table_blocks:
            headers = [header.strip().lower() for header in block[0].split('|')]

            for row in block[1:]:
                if '|' not in row:
                    continue
                values = [value.strip() for value in row.split('|')]
                if len(values) != len(headers):
                    continue
                mapping = dict(zip(headers, values))
                tradeline = self._build_tradeline_from_table_row(mapping)
                if tradeline:
                    tradelines.append(tradeline)

        return tradelines

    def _build_tradeline_from_table_row(self, mapping: Dict[str, str]) -> Optional[ParsedTradeline]:
        """Build a ParsedTradeline from a single table row mapping."""
        tradeline = ParsedTradeline()
        populated = False

        for header, value in mapping.items():
            if not value:
                continue
            field_key = self.table_header_mapping.get(header)
            if not field_key:
                continue

            populated = True
            if field_key == 'creditor_name':
                tradeline.creditor_name = self._clean_field_value(value)
            elif field_key == 'account_number':
                tradeline.account_number = self._format_account_number(value)
            elif field_key in ['account_balance', 'credit_limit', 'monthly_payment']:
                tradeline.__setattr__(field_key, self._format_currency(value, field_name=field_key))
            elif field_key == 'account_status':
                tradeline.account_status = self._normalize_account_status(value)
            elif field_key == 'account_type':
                tradeline.account_type = self._normalize_account_type(value)
            elif field_key == 'date_opened':
                tradeline.date_opened = self._format_date(value)

        payment_history_value = mapping.get('payment history') or mapping.get('history')
        if payment_history_value:
            tradeline.payment_history = payment_history_value

        if not populated:
            return None

        tradeline.credit_bureau = "TransUnion"
        self._classify_negative(tradeline)
        tradeline.extraction_confidence = self._calculate_tradeline_confidence(tradeline)
        tradeline.raw_data = {'table_row': mapping}

        if tradeline.creditor_name or tradeline.account_number:
            return tradeline
        return None
    
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

        # Capture payment history when present
        payment_history = self._parse_payment_history(section)
        if payment_history:
            tradeline.payment_history = payment_history

        # Default bureau and classification
        tradeline.credit_bureau = "TransUnion"
        self._classify_negative(tradeline)
        tradeline.extraction_confidence = self._calculate_tradeline_confidence(tradeline)
        tradeline.raw_data = {'raw_section': section}

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
            tradeline.monthly_payment = self._format_currency(payment, field_name="monthly_payment")
        
        # Credit Limit
        elif 'credit limit:' in line_lower:
            limit = line.split(':', 1)[1].strip()
            tradeline.credit_limit = self._format_currency(limit, field_name="credit_limit")
        
        # Balance
        elif 'balance:' in line_lower:
            balance = line.split(':', 1)[1].strip()
            tradeline.account_balance = self._format_currency(balance, field_name="account_balance")
    
    def _format_account_number(self, account_num: str) -> Optional[str]:
        """
        Format account number - remove all special characters and validate.
        Returns alphanumeric-only account number for clean output.
        """
        if not account_num or account_num.lower() in ['none', 'n/a', '']:
            return None
        
        # Clean up the account number
        account_num = account_num.strip()
        
        # Remove ALL special characters (asterisks, X's, dots, dashes, etc.)
        # Keep only alphanumeric characters per user requirement
        cleaned_account = re.sub(r'[^A-Za-z0-9]', '', account_num)
        
        # Validate: Must be at least 4 characters and contain at least one digit
        if not cleaned_account or len(cleaned_account) < 4:
            return None
        
        if not any(c.isdigit() for c in cleaned_account):
            return None
        
        # Validate reasonable length (4-20 characters)
        if len(cleaned_account) > 20:
            # Truncate if too long (likely OCR error)
            cleaned_account = cleaned_account[:20]
        
        return cleaned_account
    
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
        Format date to MM/DD/YYYY format using shared date parser.
        Handles month-name formats, ISO dates, MM/DD/YY, MM/DD/YYYY,
        MM-YY, MM-YYYY, and partial dates with sensible defaults.
        """
        return self.date_parser.parse_date(date_str)
    
    def _format_currency(self, amount: str, field_name: str = "") -> Optional[str]:
        """
        Format currency amount to match expected format: $X,XXX.XX for all fields.
        """
        if not amount or amount.lower() in ['none', 'n/a', '']:
            return None

        # Handle explicit $0 - format based on field type
        if amount.lower() == '$0' or amount == '0':
            return '$0.00'
        
        amount = amount.strip()
        
        # Apply OCR error corrections
        amount = amount.replace('O', '0').replace('l', '1').replace('S', '5')
        
        # Handle parenthetical negatives: ($1,234) or (1234)
        is_negative = '(' in amount and ')' in amount or amount.startswith('-')
        
        # Extract numeric value
        numeric_match = re.search(r'[\d,]+\.?\d*', amount)
        if not numeric_match:
            return None
        
        numeric_str = numeric_match.group()
        
        try:
            # Parse the numeric value
            numeric_value = float(numeric_str.replace(',', ''))
            abs_amount = abs(numeric_value)
            formatted = f"${abs_amount:,.2f}"
            return f"-{formatted}" if is_negative else formatted
                
        except ValueError:
            return None
    
    def _parse_payment_history(self, section: str) -> str:
        """Extract payment history summaries from a tradeline section."""
        for pattern in self.payment_history_patterns:
            match = pattern.search(section)
            if match:
                value = match.group(1).strip()
                return re.sub(r'\s+', ' ', value)
        late_matches = re.findall(r'(?i)\b(?:30|60|90|120)\s*days?\s*(?:late|past due)?\b', section)
        return ' '.join(late_matches) if late_matches else ""

    def _classify_negative(self, tradeline: ParsedTradeline) -> None:
        """Use the rule-based classifier to flag negative tradelines."""
        payload = {
            'account_status': tradeline.account_status or '',
            'payment_history': getattr(tradeline, 'payment_history', '') or '',
            'account_balance': tradeline.account_balance or '',
            'credit_limit': tradeline.credit_limit or '',
            'creditor_name': tradeline.creditor_name or '',
            'comments': getattr(tradeline, 'comments', '') or ''
        }
        classification = self.negative_classifier.classify(payload)
        tradeline.is_negative = classification.is_negative
        tradeline.negative_confidence = classification.confidence
        tradeline.negative_indicators = classification.indicators

    def _calculate_tradeline_confidence(self, tradeline: ParsedTradeline) -> float:
        """Score how confident we are in an individual tradeline."""
        confidence = 0.0
        if tradeline.creditor_name:
            confidence += 0.3
        if tradeline.account_type:
            confidence += 0.2
        if tradeline.account_status:
            confidence += 0.2
        if tradeline.account_balance:
            confidence += 0.1
        if tradeline.credit_limit:
            confidence += 0.1
        if tradeline.date_opened:
            confidence += 0.1
        return min(1.0, confidence)

    def _calculate_parsing_confidence(self, tradelines: List[ParsedTradeline], sections_count: int) -> float:
        """Compute an aggregate confidence score across all parsed tradelines."""
        if not tradelines or sections_count == 0:
            return 0.0
        extraction_rate = len(tradelines) / sections_count
        base_confidence = extraction_rate * 0.6
        avg_conf = sum(t.extraction_confidence for t in tradelines) / len(tradelines)
        base_confidence += avg_conf * 0.4
        return min(1.0, base_confidence)

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
