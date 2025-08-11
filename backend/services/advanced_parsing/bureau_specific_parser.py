"""
Bureau-Specific Credit Report Parsers
Specialized parsers for Experian, Equifax, and TransUnion formats
"""
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod
import json
from datetime import datetime, date

from core.logging.logger import get_logger

logger = get_logger(__name__)

@dataclass
class TradelineData:
    """Standardized tradeline data structure."""
    creditor_name: str = ""
    account_number: str = ""
    account_type: str = ""
    account_status: str = ""
    account_balance: str = ""
    credit_limit: str = ""
    monthly_payment: str = ""
    date_opened: str = ""
    date_closed: str = ""
    last_payment_date: str = ""
    payment_history: str = ""
    credit_bureau: str = ""
    is_negative: bool = False
    dispute_count: int = 0
    high_balance: str = ""
    terms: str = ""
    responsibility: str = ""
    comments: str = ""
    
    # Confidence and metadata
    extraction_confidence: float = 0.0
    parsing_method: str = ""
    raw_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.raw_data is None:
            self.raw_data = {}

@dataclass
class ParsingResult:
    """Result from bureau-specific parsing."""
    bureau: str
    success: bool
    tradelines: List[TradelineData]
    confidence: float
    parsing_method: str
    errors: List[str]
    metadata: Dict[str, Any]

class BureauParser(ABC):
    """Abstract base class for bureau-specific parsers."""
    
    def __init__(self, bureau_name: str):
        self.bureau_name = bureau_name
        self.patterns = self._load_patterns()
        self.field_mappings = self._load_field_mappings()
        
    @abstractmethod
    def _load_patterns(self) -> Dict[str, re.Pattern]:
        """Load regex patterns specific to this bureau."""
        pass
    
    @abstractmethod
    def _load_field_mappings(self) -> Dict[str, str]:
        """Load field name mappings for this bureau."""
        pass
    
    @abstractmethod
    def parse_tradelines(self, text: str) -> ParsingResult:
        """Parse tradelines from bureau-specific text."""
        pass
    
    def _clean_field_value(self, value: str) -> str:
        """Clean and standardize field values."""
        if not value:
            return ""
        
        # Remove extra whitespace
        value = re.sub(r'\s+', ' ', value.strip())
        
        # Remove common OCR artifacts
        value = value.replace('|', 'I').replace('O', '0')
        
        return value
    
    def _parse_date(self, date_str: str) -> str:
        """Parse various date formats to standard format."""
        if not date_str:
            return ""
        
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY
            r'(\d{1,2})/(\d{1,2})/(\d{2})',  # MM/DD/YY
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
            r'(\d{1,2})-(\d{1,2})-(\d{4})',  # MM-DD-YYYY
            r'(\d{2})/(\d{4})',              # MM/YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) == 2:  # MM/YYYY format
                        return f"{groups[0]}/01/{groups[1]}"
                    elif len(groups) == 3:
                        month, day, year = groups
                        if len(year) == 2:
                            year = f"20{year}" if int(year) < 50 else f"19{year}"
                        return f"{month.zfill(2)}/{day.zfill(2)}/{year}"
                except ValueError:
                    continue
        
        return date_str  # Return original if no pattern matches
    
    def _parse_currency(self, amount_str: str) -> str:
        """Parse currency amounts to standard format."""
        if not amount_str:
            return ""
        
        # Remove currency symbols and clean
        cleaned = re.sub(r'[$,\s]', '', amount_str)
        
        # Handle negative amounts
        if '(' in amount_str or amount_str.startswith('-'):
            cleaned = f"-{cleaned.replace('(', '').replace(')', '').replace('-', '')}"
        
        # Validate it's a number
        try:
            float(cleaned)
            return cleaned
        except ValueError:
            return amount_str  # Return original if not parseable

class ExperianParser(BureauParser):
    """Experian-specific credit report parser."""
    
    def __init__(self):
        super().__init__("Experian")
    
    def _load_patterns(self) -> Dict[str, re.Pattern]:
        """Load Experian-specific regex patterns."""
        return {
            'tradeline_start': re.compile(r'(?i)(account\s+information|tradeline|credit\s+account)', re.MULTILINE),
            'creditor': re.compile(r'(?i)(company\s*name|creditor|lender)[:\s]+(.*?)(?=\n|$)', re.MULTILINE),
            'account_number': re.compile(r'(?i)(account\s*(?:number|#)|acct\s*(?:number|#|num))[:\s]+(.*?)(?=\n|\s{3,})', re.MULTILINE),
            'account_type': re.compile(r'(?i)(account\s+type|type\s+of\s+account)[:\s]+(.*?)(?=\n|$)', re.MULTILINE),
            'balance': re.compile(r'(?i)(current\s+balance|balance|amount\s+owed)[:\s]+\$?([\d,.-]+)', re.MULTILINE),
            'credit_limit': re.compile(r'(?i)(credit\s+limit|high\s+credit|limit)[:\s]+\$?([\d,.-]+)', re.MULTILINE),
            'payment': re.compile(r'(?i)(monthly\s+payment|payment\s+amount)[:\s]+\$?([\d,.-]+)', re.MULTILINE),
            'status': re.compile(r'(?i)(account\s+status|status|condition)[:\s]+(.*?)(?=\n|$)', re.MULTILINE),
            'opened': re.compile(r'(?i)(date\s+opened|opened|open\s+date)[:\s]+([\d/\-]+)', re.MULTILINE),
            'payment_history': re.compile(r'(?i)(payment\s+history|history)[:\s]+(.*?)(?=\n\n|\Z)', re.MULTILINE | re.DOTALL),
        }
    
    def _load_field_mappings(self) -> Dict[str, str]:
        """Load Experian field name mappings."""
        return {
            'company name': 'creditor_name',
            'creditor': 'creditor_name',
            'lender': 'creditor_name',
            'account number': 'account_number',
            'acct number': 'account_number',
            'account type': 'account_type',
            'current balance': 'account_balance',
            'balance': 'account_balance',
            'credit limit': 'credit_limit',
            'high credit': 'credit_limit',
            'monthly payment': 'monthly_payment',
            'payment amount': 'monthly_payment',
            'account status': 'account_status',
            'status': 'account_status',
            'date opened': 'date_opened',
            'opened': 'date_opened',
        }
    
    def parse_tradelines(self, text: str) -> ParsingResult:
        """Parse Experian credit report for tradelines."""
        logger.info("Starting Experian tradeline parsing")
        
        tradelines = []
        errors = []
        
        try:
            # Split text into potential tradeline sections
            sections = self._split_into_tradeline_sections(text)
            
            for i, section in enumerate(sections):
                try:
                    tradeline = self._parse_single_tradeline(section)
                    if tradeline.creditor_name:  # Only add if we found a creditor
                        tradeline.credit_bureau = "Experian"
                        tradeline.parsing_method = "experian_regex"
                        tradelines.append(tradeline)
                except Exception as e:
                    errors.append(f"Section {i}: {str(e)}")
                    logger.warning(f"Failed to parse Experian tradeline section {i}: {e}")
            
            # Calculate overall confidence
            confidence = self._calculate_parsing_confidence(tradelines, len(sections))
            
            return ParsingResult(
                bureau="Experian",
                success=len(tradelines) > 0,
                tradelines=tradelines,
                confidence=confidence,
                parsing_method="experian_specific",
                errors=errors,
                metadata={
                    'sections_found': len(sections),
                    'tradelines_extracted': len(tradelines),
                    'parsing_method': 'regex_patterns'
                }
            )
            
        except Exception as e:
            logger.error(f"Experian parsing failed: {e}")
            return ParsingResult(
                bureau="Experian",
                success=False,
                tradelines=[],
                confidence=0.0,
                parsing_method="experian_specific",
                errors=[str(e)],
                metadata={}
            )
    
    def _split_into_tradeline_sections(self, text: str) -> List[str]:
        """Split text into individual tradeline sections."""
        # Look for section dividers specific to Experian
        dividers = [
            r'(?i)company\s+name[:\s]',
            r'(?i)creditor[:\s]',
            r'(?i)account\s+information',
            r'(?i)tradeline\s+\d+',
            r'(?i)credit\s+account\s+\d+',
        ]
        
        sections = []
        current_section = ""
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line starts a new tradeline
            is_new_section = any(re.search(pattern, line) for pattern in dividers)
            
            if is_new_section and current_section.strip():
                sections.append(current_section)
                current_section = line + '\n'
            else:
                current_section += line + '\n'
        
        # Add the last section
        if current_section.strip():
            sections.append(current_section)
        
        return sections
    
    def _parse_single_tradeline(self, section: str) -> TradelineData:
        """Parse a single tradeline from a text section."""
        tradeline = TradelineData()
        
        # Extract each field using patterns
        for pattern_name, pattern in self.patterns.items():
            matches = pattern.findall(section)
            if matches:
                if pattern_name == 'creditor':
                    tradeline.creditor_name = self._clean_field_value(matches[0][1] if isinstance(matches[0], tuple) else matches[0])
                elif pattern_name == 'account_number':
                    tradeline.account_number = self._clean_field_value(matches[0][1] if isinstance(matches[0], tuple) else matches[0])
                elif pattern_name == 'account_type':
                    tradeline.account_type = self._clean_field_value(matches[0][1] if isinstance(matches[0], tuple) else matches[0])
                elif pattern_name == 'balance':
                    tradeline.account_balance = self._parse_currency(matches[0][1] if isinstance(matches[0], tuple) else matches[0])
                elif pattern_name == 'credit_limit':
                    tradeline.credit_limit = self._parse_currency(matches[0][1] if isinstance(matches[0], tuple) else matches[0])
                elif pattern_name == 'payment':
                    tradeline.monthly_payment = self._parse_currency(matches[0][1] if isinstance(matches[0], tuple) else matches[0])
                elif pattern_name == 'status':
                    tradeline.account_status = self._clean_field_value(matches[0][1] if isinstance(matches[0], tuple) else matches[0])
                elif pattern_name == 'opened':
                    tradeline.date_opened = self._parse_date(matches[0][1] if isinstance(matches[0], tuple) else matches[0])
                elif pattern_name == 'payment_history':
                    tradeline.payment_history = self._clean_field_value(matches[0][1] if isinstance(matches[0], tuple) else matches[0])
        
        # Determine if it's negative
        tradeline.is_negative = self._is_negative_tradeline(tradeline, section)
        
        # Calculate confidence for this tradeline
        tradeline.extraction_confidence = self._calculate_tradeline_confidence(tradeline)
        
        # Store raw section for reference
        tradeline.raw_data = {'raw_section': section}
        
        return tradeline
    
    def _is_negative_tradeline(self, tradeline: TradelineData, section: str) -> bool:
        """Determine if a tradeline is negative/derogatory."""
        negative_indicators = [
            'charge off', 'collection', 'foreclosure', 'repossession',
            'bankruptcy', 'late payment', 'delinquent', 'default',
            'closed', 'settled', 'paid charge off'
        ]
        
        section_lower = section.lower()
        status_lower = tradeline.account_status.lower()
        
        return any(indicator in section_lower or indicator in status_lower 
                  for indicator in negative_indicators)
    
    def _calculate_tradeline_confidence(self, tradeline: TradelineData) -> float:
        """Calculate confidence score for individual tradeline."""
        confidence = 0.0
        
        # Essential fields
        if tradeline.creditor_name: confidence += 0.3
        if tradeline.account_type: confidence += 0.2
        if tradeline.account_status: confidence += 0.2
        
        # Important fields
        if tradeline.account_balance: confidence += 0.1
        if tradeline.credit_limit: confidence += 0.1
        if tradeline.date_opened: confidence += 0.1
        
        return min(1.0, confidence)
    
    def _calculate_parsing_confidence(self, tradelines: List[TradelineData], sections_count: int) -> float:
        """Calculate overall parsing confidence."""
        if not tradelines or sections_count == 0:
            return 0.0
        
        # Base confidence from extraction rate
        extraction_rate = len(tradelines) / sections_count
        base_confidence = extraction_rate * 0.6
        
        # Average individual tradeline confidence
        if tradelines:
            avg_tradeline_confidence = sum(t.extraction_confidence for t in tradelines) / len(tradelines)
            base_confidence += avg_tradeline_confidence * 0.4
        
        return min(1.0, base_confidence)

class EquifaxParser(BureauParser):
    """Equifax-specific credit report parser."""
    
    def __init__(self):
        super().__init__("Equifax")
    
    def _load_patterns(self) -> Dict[str, re.Pattern]:
        """Load Equifax-specific regex patterns."""
        return {
            'tradeline_start': re.compile(r'(?i)(company|business\s+name|creditor\s+name)', re.MULTILINE),
            'creditor': re.compile(r'(?i)(company|business\s+name|creditor\s+name)[:\s]+(.*?)(?=\n|$)', re.MULTILINE),
            'account_number': re.compile(r'(?i)(account\s*number|account\s*#)[:\s]+(.*?)(?=\n|\s{3,})', re.MULTILINE),
            'account_type': re.compile(r'(?i)(type\s+of\s+account|account\s+type)[:\s]+(.*?)(?=\n|$)', re.MULTILINE),
            'balance': re.compile(r'(?i)(balance|current\s+balance)[:\s]+\$?([\d,.-]+)', re.MULTILINE),
            'credit_limit': re.compile(r'(?i)(credit\s+limit|high\s+credit)[:\s]+\$?([\d,.-]+)', re.MULTILINE),
            'payment': re.compile(r'(?i)(payment\s+amount|monthly\s+payment)[:\s]+\$?([\d,.-]+)', re.MULTILINE),
            'status': re.compile(r'(?i)(status|account\s+condition)[:\s]+(.*?)(?=\n|$)', re.MULTILINE),
            'opened': re.compile(r'(?i)(date\s+opened|open\s+date)[:\s]+([\d/\-]+)', re.MULTILINE),
            'responsibility': re.compile(r'(?i)(responsibility|liable\s+party)[:\s]+(.*?)(?=\n|$)', re.MULTILINE),
        }
    
    def _load_field_mappings(self) -> Dict[str, str]:
        """Load Equifax field name mappings."""
        return {
            'company': 'creditor_name',
            'business name': 'creditor_name',
            'creditor name': 'creditor_name',
            'account number': 'account_number',
            'type of account': 'account_type',
            'balance': 'account_balance',
            'current balance': 'account_balance',
            'credit limit': 'credit_limit',
            'high credit': 'credit_limit',
            'payment amount': 'monthly_payment',
            'monthly payment': 'monthly_payment',
            'status': 'account_status',
            'account condition': 'account_status',
            'date opened': 'date_opened',
            'open date': 'date_opened',
            'responsibility': 'responsibility',
        }
    
    def parse_tradelines(self, text: str) -> ParsingResult:
        """Parse Equifax credit report for tradelines."""
        logger.info("Starting Equifax tradeline parsing")
        
        tradelines = []
        errors = []
        
        try:
            # Equifax has different section structure
            sections = self._split_equifax_sections(text)
            
            for i, section in enumerate(sections):
                try:
                    tradeline = self._parse_equifax_tradeline(section)
                    if tradeline.creditor_name:
                        tradeline.credit_bureau = "Equifax"
                        tradeline.parsing_method = "equifax_regex"
                        tradelines.append(tradeline)
                except Exception as e:
                    errors.append(f"Section {i}: {str(e)}")
                    logger.warning(f"Failed to parse Equifax tradeline section {i}: {e}")
            
            confidence = self._calculate_parsing_confidence(tradelines, len(sections))
            
            return ParsingResult(
                bureau="Equifax",
                success=len(tradelines) > 0,
                tradelines=tradelines,
                confidence=confidence,
                parsing_method="equifax_specific",
                errors=errors,
                metadata={
                    'sections_found': len(sections),
                    'tradelines_extracted': len(tradelines),
                    'parsing_method': 'equifax_regex'
                }
            )
            
        except Exception as e:
            logger.error(f"Equifax parsing failed: {e}")
            return ParsingResult(
                bureau="Equifax",
                success=False,
                tradelines=[],
                confidence=0.0,
                parsing_method="equifax_specific",
                errors=[str(e)],
                metadata={}
            )
    
    def _split_equifax_sections(self, text: str) -> List[str]:
        """Split Equifax text into tradeline sections."""
        # Equifax uses different section markers
        dividers = [
            r'(?i)company[:\s]',
            r'(?i)business\s+name[:\s]',
            r'(?i)creditor\s+name[:\s]',
            r'(?i)account\s+\d+',
        ]
        
        sections = []
        current_section = ""
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            is_new_section = any(re.search(pattern, line) for pattern in dividers)
            
            if is_new_section and current_section.strip():
                sections.append(current_section)
                current_section = line + '\n'
            else:
                current_section += line + '\n'
        
        if current_section.strip():
            sections.append(current_section)
        
        return sections
    
    def _parse_equifax_tradeline(self, section: str) -> TradelineData:
        """Parse single Equifax tradeline."""
        tradeline = TradelineData()
        
        # Use patterns to extract fields
        for pattern_name, pattern in self.patterns.items():
            matches = pattern.findall(section)
            if matches:
                value = matches[0][1] if isinstance(matches[0], tuple) else matches[0]
                
                if pattern_name == 'creditor':
                    tradeline.creditor_name = self._clean_field_value(value)
                elif pattern_name == 'account_number':
                    tradeline.account_number = self._clean_field_value(value)
                elif pattern_name == 'account_type':
                    tradeline.account_type = self._clean_field_value(value)
                elif pattern_name == 'balance':
                    tradeline.account_balance = self._parse_currency(value)
                elif pattern_name == 'credit_limit':
                    tradeline.credit_limit = self._parse_currency(value)
                elif pattern_name == 'payment':
                    tradeline.monthly_payment = self._parse_currency(value)
                elif pattern_name == 'status':
                    tradeline.account_status = self._clean_field_value(value)
                elif pattern_name == 'opened':
                    tradeline.date_opened = self._parse_date(value)
                elif pattern_name == 'responsibility':
                    tradeline.responsibility = self._clean_field_value(value)
        
        tradeline.is_negative = self._is_negative_tradeline(tradeline, section)
        tradeline.extraction_confidence = self._calculate_tradeline_confidence(tradeline)
        tradeline.raw_data = {'raw_section': section}
        
        return tradeline

class TransUnionParser(BureauParser):
    """TransUnion-specific credit report parser."""
    
    def __init__(self):
        super().__init__("TransUnion")
    
    def _load_patterns(self) -> Dict[str, re.Pattern]:
        """Load TransUnion-specific regex patterns."""
        return {
            'creditor': re.compile(r'(?i)(creditor|company\s+name|subscriber)[:\s]+(.*?)(?=\n|$)', re.MULTILINE),
            'account_number': re.compile(r'(?i)(account|acct)[:\s#]+(.*?)(?=\n|\s{3,})', re.MULTILINE),
            'account_type': re.compile(r'(?i)(loan\s+type|account\s+type)[:\s]+(.*?)(?=\n|$)', re.MULTILINE),
            'balance': re.compile(r'(?i)(current\s+balance|balance)[:\s]+\$?([\d,.-]+)', re.MULTILINE),
            'credit_limit': re.compile(r'(?i)(credit\s+limit|high\s+balance)[:\s]+\$?([\d,.-]+)', re.MULTILINE),
            'payment': re.compile(r'(?i)(scheduled\s+payment|payment)[:\s]+\$?([\d,.-]+)', re.MULTILINE),
            'status': re.compile(r'(?i)(account\s+status|status)[:\s]+(.*?)(?=\n|$)', re.MULTILINE),
            'opened': re.compile(r'(?i)(date\s+opened|opened)[:\s]+([\d/\-]+)', re.MULTILINE),
            'terms': re.compile(r'(?i)(terms|payment\s+terms)[:\s]+(.*?)(?=\n|$)', re.MULTILINE),
        }
    
    def _load_field_mappings(self) -> Dict[str, str]:
        """Load TransUnion field mappings."""
        return {
            'creditor': 'creditor_name',
            'company name': 'creditor_name',
            'subscriber': 'creditor_name',
            'account': 'account_number',
            'loan type': 'account_type',
            'current balance': 'account_balance',
            'balance': 'account_balance',
            'credit limit': 'credit_limit',
            'high balance': 'credit_limit',
            'scheduled payment': 'monthly_payment',
            'payment': 'monthly_payment',
            'account status': 'account_status',
            'status': 'account_status',
            'date opened': 'date_opened',
            'opened': 'date_opened',
            'terms': 'terms',
        }
    
    def parse_tradelines(self, text: str) -> ParsingResult:
        """Parse TransUnion credit report for tradelines."""
        logger.info("Starting TransUnion tradeline parsing")
        
        tradelines = []
        errors = []
        
        try:
            sections = self._split_transunion_sections(text)
            
            for i, section in enumerate(sections):
                try:
                    tradeline = self._parse_transunion_tradeline(section)
                    if tradeline.creditor_name:
                        tradeline.credit_bureau = "TransUnion"
                        tradeline.parsing_method = "transunion_regex"
                        tradelines.append(tradeline)
                except Exception as e:
                    errors.append(f"Section {i}: {str(e)}")
                    logger.warning(f"Failed to parse TransUnion tradeline section {i}: {e}")
            
            confidence = self._calculate_parsing_confidence(tradelines, len(sections))
            
            return ParsingResult(
                bureau="TransUnion",
                success=len(tradelines) > 0,
                tradelines=tradelines,
                confidence=confidence,
                parsing_method="transunion_specific",
                errors=errors,
                metadata={
                    'sections_found': len(sections),
                    'tradelines_extracted': len(tradelines),
                    'parsing_method': 'transunion_regex'
                }
            )
            
        except Exception as e:
            logger.error(f"TransUnion parsing failed: {e}")
            return ParsingResult(
                bureau="TransUnion",
                success=False,
                tradelines=[],
                confidence=0.0,
                parsing_method="transunion_specific",
                errors=[str(e)],
                metadata={}
            )
    
    def _split_transunion_sections(self, text: str) -> List[str]:
        """Split TransUnion text into sections."""
        dividers = [
            r'(?i)creditor[:\s]',
            r'(?i)company\s+name[:\s]',
            r'(?i)subscriber[:\s]',
            r'(?i)tradeline\s+\d+',
        ]
        
        sections = []
        current_section = ""
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            is_new_section = any(re.search(pattern, line) for pattern in dividers)
            
            if is_new_section and current_section.strip():
                sections.append(current_section)
                current_section = line + '\n'
            else:
                current_section += line + '\n'
        
        if current_section.strip():
            sections.append(current_section)
        
        return sections
    
    def _parse_transunion_tradeline(self, section: str) -> TradelineData:
        """Parse single TransUnion tradeline."""
        tradeline = TradelineData()
        
        for pattern_name, pattern in self.patterns.items():
            matches = pattern.findall(section)
            if matches:
                value = matches[0][1] if isinstance(matches[0], tuple) else matches[0]
                
                if pattern_name == 'creditor':
                    tradeline.creditor_name = self._clean_field_value(value)
                elif pattern_name == 'account_number':
                    tradeline.account_number = self._clean_field_value(value)
                elif pattern_name == 'account_type':
                    tradeline.account_type = self._clean_field_value(value)
                elif pattern_name == 'balance':
                    tradeline.account_balance = self._parse_currency(value)
                elif pattern_name == 'credit_limit':
                    tradeline.credit_limit = self._parse_currency(value)
                elif pattern_name == 'payment':
                    tradeline.monthly_payment = self._parse_currency(value)
                elif pattern_name == 'status':
                    tradeline.account_status = self._clean_field_value(value)
                elif pattern_name == 'opened':
                    tradeline.date_opened = self._parse_date(value)
                elif pattern_name == 'terms':
                    tradeline.terms = self._clean_field_value(value)
        
        tradeline.is_negative = self._is_negative_tradeline(tradeline, section)
        tradeline.extraction_confidence = self._calculate_tradeline_confidence(tradeline)
        tradeline.raw_data = {'raw_section': section}
        
        return tradeline

class UniversalBureauParser:
    """Universal parser that handles all three bureaus."""
    
    def __init__(self):
        self.parsers = {
            'experian': ExperianParser(),
            'equifax': EquifaxParser(),
            'transunion': TransUnionParser()
        }
        self.bureau_detection_patterns = {
            'experian': [
                r'(?i)experian',
                r'(?i)company\s+name[:\s]',
                r'(?i)account\s+information'
            ],
            'equifax': [
                r'(?i)equifax',
                r'(?i)business\s+name[:\s]',
                r'(?i)account\s+condition'
            ],
            'transunion': [
                r'(?i)trans\s*union',
                r'(?i)subscriber[:\s]',
                r'(?i)loan\s+type'
            ]
        }
    
    def detect_bureau(self, text: str) -> str:
        """Detect which credit bureau format the text follows."""
        text_sample = text[:5000].lower()  # Check first 5k characters
        
        bureau_scores = {bureau: 0 for bureau in self.parsers.keys()}
        
        for bureau, patterns in self.bureau_detection_patterns.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, text_sample))
                bureau_scores[bureau] += matches
        
        # Return bureau with highest score
        best_bureau = max(bureau_scores, key=bureau_scores.get)
        
        logger.info(f"Detected bureau: {best_bureau} (scores: {bureau_scores})")
        
        return best_bureau if bureau_scores[best_bureau] > 0 else 'experian'  # Default to Experian
    
    def parse_with_all_bureaus(self, text: str) -> List[ParsingResult]:
        """Parse text with all bureau parsers and return results."""
        results = []
        
        for bureau_name, parser in self.parsers.items():
            try:
                result = parser.parse_tradelines(text)
                results.append(result)
                logger.info(f"{bureau_name} parser found {len(result.tradelines)} tradelines with confidence {result.confidence:.2f}")
            except Exception as e:
                logger.error(f"Failed to parse with {bureau_name} parser: {e}")
        
        return results
    
    def get_best_result(self, text: str) -> ParsingResult:
        """Get the best parsing result from all bureau parsers."""
        # First try detected bureau
        detected_bureau = self.detect_bureau(text)
        
        try:
            best_result = self.parsers[detected_bureau].parse_tradelines(text)
            
            # If confidence is low, try other parsers
            if best_result.confidence < 0.7:
                all_results = self.parse_with_all_bureaus(text)
                # Return the result with highest confidence
                best_result = max(all_results, key=lambda r: r.confidence)
            
            return best_result
            
        except Exception as e:
            logger.error(f"Best result parsing failed: {e}")
            # Fallback: try all parsers and return best
            all_results = self.parse_with_all_bureaus(text)
            return max(all_results, key=lambda r: r.confidence) if all_results else ParsingResult(
                bureau="unknown",
                success=False,
                tradelines=[],
                confidence=0.0,
                parsing_method="fallback",
                errors=[str(e)],
                metadata={}
            )