"""
Real-world TransUnion PDF parser
Handles actual PDF structure with encoded characters and varied formats
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from services.tradeline_extraction.tradeline_parser import ParsedTradeline, TransUnionTradelineParser

logger = logging.getLogger(__name__)


class RealWorldTransUnionParser(TransUnionTradelineParser):
    """
    Enhanced parser for real-world TransUnion credit reports
    Handles PDF encoding issues and actual document structure
    """
    
    def __init__(self):
        super().__init__()
        
        # Real-world patterns for TransUnion PDFs
        self.account_line_pattern = re.compile(
            r'([A-Z][A-Z\s/&-]+?)\s+([A-Z0-9]+\*{4})',
            re.MULTILINE
        )
        
        # Account information extraction patterns
        self.info_patterns = {
            'account_type': re.compile(r'Account Type[:\s]+((?:Revolving|Installment)\s*Account?)', re.IGNORECASE),
            'balance': re.compile(r'Balance[:\s]+\$?([\d,]+(?:\.\d{2})?)', re.IGNORECASE),
            'credit_limit': re.compile(r'Credit Limit[:\s]+\$?([\d,]+(?:\.\d{2})?)', re.IGNORECASE),
            'date_opened': re.compile(r'Date Opened[:\s]+(\d{1,2}/\d{1,2}/\d{4})', re.IGNORECASE),
            'monthly_payment': re.compile(r'Monthly Payment[:\s]+\$?([\d,]+(?:\.\d{2})?)', re.IGNORECASE),
            'account_status': re.compile(r'Account Status[:\s]+(\w+)', re.IGNORECASE),
            # Negative account extraction patterns
            'charge_off_amount': re.compile(r'Charge[- ]?Off(?:\s+Amount)?[:\s]+\$?([\d,]+(?:\.\d{2})?)', re.IGNORECASE),
            'collection_amount': re.compile(r'Collection(?:\s+Amount)?[:\s]+\$?([\d,]+(?:\.\d{2})?)', re.IGNORECASE),
            'past_due_amount': re.compile(r'Past\s*Due(?:\s+Amount)?[:\s]+\$?([\d,]+(?:\.\d{2})?)', re.IGNORECASE),
            'settlement_amount': re.compile(r'Settlement(?:\s+Amount)?[:\s]+\$?([\d,]+(?:\.\d{2})?)', re.IGNORECASE),
            'negative_status': re.compile(r'(?:Account\s+)?Status[:\s]+((?:Charged[- ]?Off|Collection|Delinquent|Default(?:ed)?|Past\s*Due|Settled|Foreclosure|Repossession|Bankruptcy))', re.IGNORECASE),
            'late_payment_count': re.compile(r'(?:Late\s+Payments?|Times\s+(?:30|60|90|120)\+?\s*Days?\s*Late)[:\s]+(\d+)', re.IGNORECASE)
        }
        
        # Pattern to clean encoded characters
        self.cleanup_pattern = re.compile(r'\(cid:\d+\)')
    
    def parse_tradelines_from_text(self, text: str) -> List[ParsedTradeline]:
        """
        Parse tradelines from real TransUnion PDF text
        """
        # First, clean up the text
        cleaned_text = self._clean_pdf_text(text)
        
        # Extract account information sections
        account_sections = self._extract_account_sections(cleaned_text)
        
        tradelines = []
        for section in account_sections:
            try:
                tradeline = self._parse_account_section(section)
                if tradeline and self._is_valid_tradeline_data(tradeline):
                    tradelines.append(tradeline)
            except Exception as e:
                logger.warning(f"Failed to parse account section: {e}")
                continue
        
        # Generate metadata
        self._add_metadata_to_tradelines(tradelines)
        
        logger.info(f"Parsed {len(tradelines)} tradelines from real-world PDF")
        return tradelines
    
    def _clean_pdf_text(self, text: str) -> str:
        """
        Clean up PDF text by removing encoding artifacts
        """
        # Remove CID encoded characters
        text = self.cleanup_pattern.sub('', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page markers
        text = re.sub(r'--- Page \d+ ---', '\n', text)
        
        # Normalize line breaks
        text = text.replace('\n', ' ')
        
        return text.strip()
    
    def _extract_account_sections(self, text: str) -> List[str]:
        """
        Extract individual account sections from the cleaned text
        """
        # Find all creditor name + account number patterns
        matches = self.account_line_pattern.finditer(text)
        
        account_sections = []
        match_positions = []
        
        # Collect match positions
        for match in matches:
            creditor_name = match.group(1).strip()
            account_number = match.group(2)
            
            # Filter out false positives
            if self._is_likely_creditor_name(creditor_name):
                match_positions.append({
                    'start': match.start(),
                    'end': match.end(),
                    'creditor': creditor_name,
                    'account': account_number
                })
        
        # Extract sections between matches
        for i, match in enumerate(match_positions):
            # Find the end of this section (start of next match or end of text)
            if i + 1 < len(match_positions):
                section_end = match_positions[i + 1]['start']
            else:
                section_end = len(text)
            
            # Extract section text
            section_text = text[match['start']:section_end]
            
            # Add context info
            section_data = {
                'text': section_text,
                'creditor_name': match['creditor'],
                'account_number': match['account']
            }
            
            account_sections.append(section_data)
        
        logger.info(f"Found {len(account_sections)} account sections in real PDF")
        return account_sections
    
    def _is_likely_creditor_name(self, name: str) -> bool:
        """
        Check if a name is likely a creditor (not a person name, etc.)
        """
        name = name.strip()
        
        # Skip names that are clearly not creditors
        skip_patterns = [
            r'^[A-Z]{1,3}\s*$',  # Short abbreviations
            r'^\d+',  # Starts with numbers
            r'^(FERNANDO|HERNANDEZ|JOHN|JANE)',  # Common first names
        ]
        
        for pattern in skip_patterns:
            if re.match(pattern, name):
                return False
        
        # Look for business indicators
        business_indicators = [
            'BANK', 'CARD', 'CREDIT', 'LLC', 'INC', 'CORP', 'FCU', 
            'FINANCIAL', 'SERVICES', 'CAPITAL', 'DISCOVER', 'CHASE',
            'AMERICAN EXPRESS', 'WELLS FARGO', 'CITI', 'SYNCHRONY'
        ]
        
        name_upper = name.upper()
        has_business_indicator = any(indicator in name_upper for indicator in business_indicators)
        
        # Must be mostly uppercase and reasonable length
        is_mostly_upper = len([c for c in name if c.isupper()]) > len(name) * 0.7
        reasonable_length = 3 <= len(name) <= 50
        
        return has_business_indicator or (is_mostly_upper and reasonable_length)
    
    def _parse_account_section(self, section_data: Dict[str, Any]) -> Optional[ParsedTradeline]:
        """
        Parse a single account section into a tradeline
        """
        tradeline = ParsedTradeline()
        
        # Basic info from section metadata
        tradeline.creditor_name = section_data['creditor_name']
        
        # Clean account number - remove asterisks, X's, dots, dashes
        # Keep only alphanumeric characters per user requirement
        raw_account = section_data['account']
        tradeline.account_number = self._clean_account_number(raw_account)
        
        section_text = section_data['text']
        
        # Try to find unmasked account number in text if current is masked
        if tradeline.account_number and len(tradeline.account_number) < 8:
            unmasked_match = re.search(r'\b[A-Z0-9]{8,20}\b', section_text)
            if unmasked_match:
                potential_account = self._clean_account_number(unmasked_match.group(0))
                if potential_account and len(potential_account) > len(tradeline.account_number):
                    tradeline.account_number = potential_account
        
        # Extract additional information using patterns
        for field, pattern in self.info_patterns.items():
            match = pattern.search(section_text)
            if match:
                value = match.group(1).strip()
                
                if field == 'account_type':
                    tradeline.account_type = self._normalize_account_type(value)
                elif field == 'balance':
                    tradeline.account_balance = self._format_currency(value, field_name="account_balance")
                elif field == 'credit_limit':
                    tradeline.credit_limit = self._format_currency(value, field_name="credit_limit")
                elif field == 'date_opened':
                    tradeline.date_opened = self._format_date(value)
                elif field == 'monthly_payment':
                    tradeline.monthly_payment = self._format_currency(value, field_name="monthly_payment")
                elif field == 'account_status':
                    tradeline.account_status = self._normalize_account_status(value)
                # Negative account fields
                elif field == 'charge_off_amount':
                    tradeline.charge_off_amount = self._format_currency(value, field_name="charge_off_amount")
                elif field == 'collection_amount':
                    tradeline.collection_amount = self._format_currency(value, field_name="collection_amount")
                elif field == 'past_due_amount':
                    tradeline.past_due_amount = self._format_currency(value, field_name="past_due_amount")
                elif field == 'settlement_amount':
                    tradeline.settlement_amount = self._format_currency(value, field_name="settlement_amount")
                elif field == 'negative_status':
                    tradeline.negative_status = self._normalize_negative_status(value)
                elif field == 'late_payment_count':
                    tradeline.late_payment_count = int(value) if value.isdigit() else None
        
        # Mark tradeline as negative if negative indicators are present
        if any([
            tradeline.charge_off_amount,
            tradeline.collection_amount,
            tradeline.past_due_amount,
            getattr(tradeline, 'negative_status', None)
        ]):
            tradeline.is_negative = True
        
        return tradeline
    
    def _is_valid_tradeline_data(self, tradeline: ParsedTradeline) -> bool:
        """
        Check if tradeline has sufficient data for storage
        """
        # Must have creditor name and account number
        if not tradeline.creditor_name or not tradeline.account_number:
            return False
        
        # Account number should be alphanumeric only and at least 4 chars
        if not re.match(r'^[A-Za-z0-9]+$', tradeline.account_number):
            return False
        
        if len(tradeline.account_number) < 4:
            return False
        
        # Creditor name should be reasonable length
        if len(tradeline.creditor_name) < 3 or len(tradeline.creditor_name) > 50:
            return False
        
        return True
    
    def _clean_account_number(self, account_num: str) -> Optional[str]:
        """
        Clean account number - remove all special characters.
        Returns alphanumeric-only account number.
        """
        if not account_num:
            return None
        
        # Remove ALL special characters (asterisks, X's, dots, dashes, etc.)
        cleaned = re.sub(r'[^A-Za-z0-9]', '', account_num)
        
        # Validate: Must be at least 4 characters and contain at least one digit
        if not cleaned or len(cleaned) < 4:
            return None
        
        if not any(c.isdigit() for c in cleaned):
            return None
        
        # Validate reasonable length (4-20 characters)
        if len(cleaned) > 20:
            cleaned = cleaned[:20]
        
        return cleaned
    
    def _normalize_account_type(self, account_type: str) -> Optional[str]:
        """
        Normalize account type from real PDF format
        """
        if not account_type:
            return None
        
        account_type_clean = account_type.lower().strip()
        
        # Handle "Revolving Account" -> "Revolving"
        if 'revolving' in account_type_clean:
            return 'Revolving'
        elif 'installment' in account_type_clean:
            return 'Installment'
        
        return account_type
    
    def _normalize_account_status(self, status: str) -> Optional[str]:
        """
        Normalize account status from real PDF
        """
        if not status:
            return None
        
        status_clean = status.lower().strip()
        
        # Map various status formats
        status_mappings = {
            'current': 'Current',
            'open': 'Current',
            'active': 'Current',
            'closed': 'Closed',
            'paid': 'Closed',
            'paid closed': 'Closed'
        }
        
        return status_mappings.get(status_clean, status)
    
    def _normalize_negative_status(self, status: str) -> Optional[str]:
        """
        Normalize negative account status from real PDF
        """
        if not status:
            return None
        
        status_clean = status.lower().strip().replace('-', ' ').replace('  ', ' ')
        
        # Map various negative status formats to standardized values
        negative_status_mappings = {
            'charged off': 'Charged Off',
            'charge off': 'Charged Off',
            'chargedoff': 'Charged Off',
            'collection': 'Collection',
            'in collection': 'Collection',
            'collections': 'Collection',
            'delinquent': 'Delinquent',
            'default': 'Default',
            'defaulted': 'Default',
            'past due': 'Past Due',
            'pastdue': 'Past Due',
            'settled': 'Settled',
            'settlement': 'Settled',
            'foreclosure': 'Foreclosure',
            'repossession': 'Repossession',
            'repo': 'Repossession',
            'bankruptcy': 'Bankruptcy'
        }
        
        return negative_status_mappings.get(status_clean, status.title())
    
    def _format_currency(self, amount: str, field_name: str = "") -> Optional[str]:
        """
        Format currency from real PDF with field-specific rules: always $X,XXX.XX.
        """
        if not amount:
            return None

        # Handle explicit $0 or 0 - format based on field type
        amount_stripped = amount.strip().lower()
        if amount_stripped in ['$0', '0', '0.00', '$0.00']:
            return '$0.00'
        
        # Apply OCR error corrections
        amount = amount.replace('O', '0').replace('l', '1').replace('S', '5')
        
        # Handle parenthetical negatives
        is_negative = '(' in amount and ')' in amount or amount.startswith('-')
        
        # Remove non-numeric characters except decimal point
        cleaned = re.sub(r'[^\d.]', '', amount)
        
        if not cleaned:
            return None
        
        try:
            value = float(cleaned)
            abs_value = abs(value)
            formatted = f"${abs_value:,.2f}"
            return f"-{formatted}" if is_negative else formatted
        except ValueError:
            return None
    
    def get_parsing_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the parsing process for debugging
        """
        return {
            'parser_type': 'real_world_transunion',
            'patterns_used': list(self.info_patterns.keys()),
            'business_indicators': [
                'BANK', 'CARD', 'CREDIT', 'LLC', 'INC', 'CORP', 'FCU', 
                'FINANCIAL', 'SERVICES', 'CAPITAL'
            ],
            'supported_account_types': ['Revolving', 'Installment'],
            'supported_statuses': ['Current', 'Closed']
        }
