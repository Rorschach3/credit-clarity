"""
Shared Date Parser Utility for Credit Reports
Handles various date formats and normalizes to MM/DD/YYYY
Uses fallback chain: exact strptime → dateutil → regex month names → partial inference
"""
import re
import logging
from typing import Optional, Tuple
from datetime import datetime, date
from dataclasses import dataclass

# Try to import dateutil for fuzzy parsing
try:
    from dateutil import parser as dateutil_parser
    from dateutil.parser import ParserError
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False
    ParserError = ValueError

logger = logging.getLogger(__name__)


@dataclass
class DateParseResult:
    """Result of date parsing with metadata."""
    value: Optional[str]  # Normalized MM/DD/YYYY or None on failure
    confidence: float  # 1.0 for exact parse, 0.8 for fuzzy/partial
    parse_method: str  # Description of how the date was parsed
    is_partial: bool  # True if day was defaulted to 01


# Month name mappings
MONTH_NAMES = {
    'jan': 1, 'january': 1,
    'feb': 2, 'february': 2,
    'mar': 3, 'march': 3,
    'apr': 4, 'april': 4,
    'may': 5,
    'jun': 6, 'june': 6,
    'jul': 7, 'july': 7,
    'aug': 8, 'august': 8,
    'sep': 9, 'sept': 9, 'september': 9,
    'oct': 10, 'october': 10,
    'nov': 11, 'november': 11,
    'dec': 12, 'december': 12,
}


class CreditReportDateParser:
    """
    Comprehensive date parser for credit report data.
    
    Supports all common date formats found in credit reports:
    - Month-name formats: "Jan 10", "January 10, 2024", "Jan 2024"
    - ISO dates: "2024-01-15", "2024-1-5"
    - MM/DD/YY: "01/15/24", "1/5/24"
    - MM/DD/YYYY: "01/15/2024"
    - MM-YY: "01-24"
    - MM-YYYY: "01-2024"
    - MM/YY: "01/24", "1/24"
    - MM/YYYY: "01/2024"
    - Partial dates with sensible defaults (day=01)
    
    Uses fallback chain:
    1. Exact strptime patterns (highest confidence)
    2. dateutil.parser fuzzy parsing (if available)
    3. Regex for month names
    4. Partial inference for MM/YY, MM/YYYY formats
    
    Always outputs MM/DD/YYYY format or None on failure.
    """
    
    def __init__(self, context_year: Optional[int] = None):
        """
        Initialize the date parser.
        
        Args:
            context_year: Optional year to use for context-aware parsing.
                         If not provided, uses current year.
        """
        self.context_year = context_year or datetime.now().year
        self.current_year = datetime.now().year
        
    def _expand_two_digit_year(self, year_str: str) -> int:
        """
        Expand 2-digit year to 4-digit.
        Uses cutoff of 50: 00-49 -> 2000-2049, 50-99 -> 1950-1999
        """
        year_int = int(year_str)
        if year_int < 50:
            return 2000 + year_int
        else:
            return 1900 + year_int
    
    def _normalize_date_components(self, month: int, day: int, year: int) -> Optional[str]:
        """
        Validate and normalize date components to MM/DD/YYYY string.
        Returns None if date is invalid.
        """
        try:
            # Validate ranges
            if not (1 <= month <= 12):
                return None
            if not (1 <= day <= 31):
                return None
            if not (1900 <= year <= 2100):
                return None
            
            # Try to create actual date to validate
            date(year, month, day)
            
            return f"{month:02d}/{day:02d}/{year}"
        except (ValueError, TypeError):
            return None
    
    def _try_exact_strptime(self, date_str: str) -> Optional[DateParseResult]:
        """
        Try exact strptime patterns (highest confidence).
        """
        exact_formats = [
            ('%m/%d/%Y', False),   # MM/DD/YYYY
            ('%m/%d/%y', False),   # MM/DD/YY
            ('%Y-%m-%d', False),   # YYYY-MM-DD (ISO)
            ('%m-%d-%Y', False),   # MM-DD-YYYY
            ('%m-%d-%y', False),   # MM-DD-YY
            ('%B %d, %Y', False),  # January 10, 2024
            ('%b %d, %Y', False),  # Jan 10, 2024
            ('%B %d %Y', False),   # January 10 2024
            ('%b %d %Y', False),   # Jan 10 2024
            ('%d %B %Y', False),   # 10 January 2024
            ('%d %b %Y', False),   # 10 Jan 2024
        ]
        
        for fmt, is_partial in exact_formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                result = self._normalize_date_components(parsed.month, parsed.day, parsed.year)
                if result:
                    return DateParseResult(
                        value=result,
                        confidence=1.0,
                        parse_method=f'strptime_{fmt}',
                        is_partial=is_partial
                    )
            except ValueError:
                continue
        
        return None
    
    def _try_dateutil_parser(self, date_str: str) -> Optional[DateParseResult]:
        """
        Try dateutil.parser for fuzzy parsing (medium confidence).
        """
        if not DATEUTIL_AVAILABLE:
            return None
        
        try:
            # Use dateutil with dayfirst=False for US format preference
            parsed = dateutil_parser.parse(date_str, dayfirst=False, fuzzy=True)
            result = self._normalize_date_components(parsed.month, parsed.day, parsed.year)
            if result:
                return DateParseResult(
                    value=result,
                    confidence=0.85,
                    parse_method='dateutil_fuzzy',
                    is_partial=False
                )
        except (ParserError, ValueError, OverflowError):
            pass
        
        return None
    
    def _try_regex_patterns(self, date_str: str) -> Optional[DateParseResult]:
        """
        Try regex patterns for various formats.
        """
        # Pattern 1: Full MM/DD/YYYY
        match = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', date_str)
        if match:
            month, day, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
            result = self._normalize_date_components(month, day, year)
            if result:
                return DateParseResult(value=result, confidence=1.0, parse_method='regex_mm_dd_yyyy', is_partial=False)
        
        # Pattern 2: MM/DD/YY
        match = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2})$', date_str)
        if match:
            month, day = int(match.group(1)), int(match.group(2))
            year = self._expand_two_digit_year(match.group(3))
            result = self._normalize_date_components(month, day, year)
            if result:
                return DateParseResult(value=result, confidence=0.95, parse_method='regex_mm_dd_yy', is_partial=False)
        
        # Pattern 3: ISO format YYYY-MM-DD
        match = re.match(r'^(\d{4})-(\d{1,2})-(\d{1,2})$', date_str)
        if match:
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            result = self._normalize_date_components(month, day, year)
            if result:
                return DateParseResult(value=result, confidence=1.0, parse_method='regex_iso', is_partial=False)
        
        # Pattern 4: MM-DD-YYYY
        match = re.match(r'^(\d{1,2})-(\d{1,2})-(\d{4})$', date_str)
        if match:
            month, day, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
            result = self._normalize_date_components(month, day, year)
            if result:
                return DateParseResult(value=result, confidence=1.0, parse_method='regex_mm_dd_yyyy_dash', is_partial=False)
        
        # Pattern 5: Month name with day and year - "January 10, 2024", "Jan 10, 2024"
        match = re.match(r'^([A-Za-z]+)\s+(\d{1,2}),?\s*(\d{4})$', date_str, re.IGNORECASE)
        if match:
            month_name, day, year = match.group(1).lower(), int(match.group(2)), int(match.group(3))
            if month_name in MONTH_NAMES:
                month = MONTH_NAMES[month_name]
                result = self._normalize_date_components(month, day, year)
                if result:
                    return DateParseResult(value=result, confidence=1.0, parse_method='regex_month_name_day_year', is_partial=False)
        
        # Pattern 6: Month name with day only (no year) - "Jan 10", "January 10"
        match = re.match(r'^([A-Za-z]+)\s+(\d{1,2})$', date_str, re.IGNORECASE)
        if match:
            month_name, day = match.group(1).lower(), int(match.group(2))
            if month_name in MONTH_NAMES:
                month = MONTH_NAMES[month_name]
                result = self._normalize_date_components(month, day, self.current_year)
                if result:
                    return DateParseResult(value=result, confidence=0.7, parse_method='regex_month_name_day_current_year', is_partial=True)
        
        # Pattern 7: Day Month Year - "10 Jan 2024", "10 January 2024"
        match = re.match(r'^(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})$', date_str, re.IGNORECASE)
        if match:
            day, month_name, year = int(match.group(1)), match.group(2).lower(), int(match.group(3))
            if month_name in MONTH_NAMES:
                month = MONTH_NAMES[month_name]
                result = self._normalize_date_components(month, day, year)
                if result:
                    return DateParseResult(value=result, confidence=1.0, parse_method='regex_day_month_name_year', is_partial=False)
        
        return None
    
    def _try_partial_patterns(self, date_str: str) -> Optional[DateParseResult]:
        """
        Try partial date patterns (MM/YYYY, MM-YY, etc.) with day defaulted to 01.
        """
        # Pattern: MM/YYYY
        match = re.match(r'^(\d{1,2})/(\d{4})$', date_str)
        if match:
            month, year = int(match.group(1)), int(match.group(2))
            result = self._normalize_date_components(month, 1, year)
            if result:
                return DateParseResult(value=result, confidence=0.8, parse_method='partial_mm_yyyy', is_partial=True)
        
        # Pattern: MM-YYYY
        match = re.match(r'^(\d{1,2})-(\d{4})$', date_str)
        if match:
            month, year = int(match.group(1)), int(match.group(2))
            result = self._normalize_date_components(month, 1, year)
            if result:
                return DateParseResult(value=result, confidence=0.8, parse_method='partial_mm_yyyy_dash', is_partial=True)
        
        # Pattern: MM/YY (2-digit year)
        match = re.match(r'^(\d{1,2})/(\d{2})$', date_str)
        if match:
            month = int(match.group(1))
            year = self._expand_two_digit_year(match.group(2))
            result = self._normalize_date_components(month, 1, year)
            if result:
                return DateParseResult(value=result, confidence=0.75, parse_method='partial_mm_yy', is_partial=True)
        
        # Pattern: MM-YY (2-digit year with dash)
        match = re.match(r'^(\d{1,2})-(\d{2})$', date_str)
        if match:
            month = int(match.group(1))
            year = self._expand_two_digit_year(match.group(2))
            result = self._normalize_date_components(month, 1, year)
            if result:
                return DateParseResult(value=result, confidence=0.75, parse_method='partial_mm_yy_dash', is_partial=True)
        
        # Pattern: Month name with year only - "Jan 2024", "January 2024"
        match = re.match(r'^([A-Za-z]+)\s+(\d{4})$', date_str, re.IGNORECASE)
        if match:
            month_name, year = match.group(1).lower(), int(match.group(2))
            if month_name in MONTH_NAMES:
                month = MONTH_NAMES[month_name]
                result = self._normalize_date_components(month, 1, year)
                if result:
                    return DateParseResult(value=result, confidence=0.8, parse_method='partial_month_name_year', is_partial=True)
        
        # Pattern: Month name with 2-digit year - "Jan 24", "January 24"
        match = re.match(r'^([A-Za-z]+)\s+(\d{2})$', date_str, re.IGNORECASE)
        if match:
            month_name, year_str = match.group(1).lower(), match.group(2)
            if month_name in MONTH_NAMES:
                month = MONTH_NAMES[month_name]
                year = self._expand_two_digit_year(year_str)
                result = self._normalize_date_components(month, 1, year)
                if result:
                    return DateParseResult(value=result, confidence=0.75, parse_method='partial_month_name_yy', is_partial=True)
        
        return None
    
    def _try_fuzzy_extraction(self, date_str: str) -> Optional[DateParseResult]:
        """
        Try to extract any date pattern from string (fuzzy match).
        """
        patterns_fuzzy = [
            # MM/DD/YYYY anywhere in string
            (r'(\d{1,2})/(\d{1,2})/(\d{4})', lambda m: (int(m.group(1)), int(m.group(2)), int(m.group(3))), False),
            # MM/DD/YY anywhere
            (r'(\d{1,2})/(\d{1,2})/(\d{2})', lambda m: (int(m.group(1)), int(m.group(2)), self._expand_two_digit_year(m.group(3))), False),
            # YYYY-MM-DD anywhere
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', lambda m: (int(m.group(2)), int(m.group(3)), int(m.group(1))), False),
            # MM/YYYY anywhere
            (r'(\d{1,2})/(\d{4})', lambda m: (int(m.group(1)), 1, int(m.group(2))), True),
            # MM-YYYY anywhere
            (r'(\d{1,2})-(\d{4})', lambda m: (int(m.group(1)), 1, int(m.group(2))), True),
        ]
        
        for pattern, extractor, is_partial in patterns_fuzzy:
            match = re.search(pattern, date_str)
            if match:
                try:
                    month, day, year = extractor(match)
                    result = self._normalize_date_components(month, day, year)
                    if result:
                        return DateParseResult(
                            value=result,
                            confidence=0.7,
                            parse_method='fuzzy_extraction',
                            is_partial=is_partial
                        )
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def parse_date(self, date_str: str) -> Optional[str]:
        """
        Parse a date string and return normalized MM/DD/YYYY format.
        
        Args:
            date_str: Input date string in various formats
            
        Returns:
            Normalized MM/DD/YYYY string or None on failure
        """
        result = self.parse_date_with_details(date_str)
        return result.value
    
    def parse_date_with_details(self, date_str: str) -> DateParseResult:
        """
        Parse a date string with full details about the parsing.
        
        Args:
            date_str: Input date string in various formats
            
        Returns:
            DateParseResult with normalized value, confidence, and metadata
        """
        if not date_str:
            return DateParseResult(value=None, confidence=0.0, parse_method='empty_input', is_partial=False)
        
        # Clean input
        date_str = str(date_str).strip()
        if date_str.lower() in ['none', 'n/a', 'na', 'null', '', '-', '--']:
            return DateParseResult(value=None, confidence=0.0, parse_method='null_value', is_partial=False)
        
        # Fallback chain: try each method in order of confidence
        try:
            # 1. Try exact strptime patterns (highest confidence)
            result = self._try_exact_strptime(date_str)
            if result:
                return result
            
            # 2. Try regex patterns
            result = self._try_regex_patterns(date_str)
            if result:
                return result
            
            # 3. Try partial patterns (MM/YYYY, etc.)
            result = self._try_partial_patterns(date_str)
            if result:
                return result
            
            # 4. Try dateutil fuzzy parsing
            result = self._try_dateutil_parser(date_str)
            if result:
                return result
            
            # 5. Try fuzzy extraction from embedded dates
            result = self._try_fuzzy_extraction(date_str)
            if result:
                return result
            
        except Exception as e:
            logger.warning(f"Date parsing exception for '{date_str}': {e}")
        
        # No pattern matched
        return DateParseResult(value=None, confidence=0.0, parse_method='no_match', is_partial=False)


# Convenience functions for backward compatibility
def parse_date(date_str: str) -> DateParseResult:
    """Parse date using default parser instance."""
    parser = CreditReportDateParser()
    return parser.parse_date_with_details(date_str)


def parse_date_simple(date_str: str) -> Optional[str]:
    """
    Simple wrapper that returns just the normalized date string or None.
    
    Args:
        date_str: Input date string in various formats
        
    Returns:
        Normalized MM/DD/YYYY string or None on failure
    """
    parser = CreditReportDateParser()
    return parser.parse_date(date_str)


def validate_date_logic(
    date_opened: Optional[str],
    date_closed: Optional[str] = None,
    last_payment: Optional[str] = None
) -> Tuple[bool, list[str]]:
    """
    Validate logical relationships between dates.
    
    Args:
        date_opened: Date account was opened (MM/DD/YYYY)
        date_closed: Date account was closed (MM/DD/YYYY), optional
        last_payment: Date of last payment (MM/DD/YYYY), optional
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    today = datetime.now().date()
    
    def _parse_to_date(date_str: Optional[str]) -> Optional[date]:
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%m/%d/%Y').date()
        except ValueError:
            return None
    
    opened = _parse_to_date(date_opened)
    closed = _parse_to_date(date_closed)
    last_pay = _parse_to_date(last_payment)
    
    # Check for future dates
    if opened and opened > today:
        errors.append(f"date_opened ({date_opened}) is in the future")
    
    if closed and closed > today:
        errors.append(f"date_closed ({date_closed}) is in the future")
    
    if last_pay and last_pay > today:
        errors.append(f"last_payment ({last_payment}) is in the future")
    
    # Check year ranges (reasonable credit history range: 1950-current)
    min_year = 1950
    current_year = today.year
    
    if opened and (opened.year < min_year or opened.year > current_year):
        errors.append(f"date_opened ({date_opened}) year is outside valid range ({min_year}-{current_year})")
    
    if closed and (closed.year < min_year or closed.year > current_year):
        errors.append(f"date_closed ({date_closed}) year is outside valid range ({min_year}-{current_year})")
    
    if last_pay and (last_pay.year < min_year or last_pay.year > current_year):
        errors.append(f"last_payment ({last_payment}) year is outside valid range ({min_year}-{current_year})")
    
    # Check logical ordering: date_closed should not be before date_opened
    if opened and closed and closed < opened:
        errors.append(f"date_closed ({date_closed}) is before date_opened ({date_opened})")
    
    # Check logical ordering: last_payment should not be before date_opened
    if opened and last_pay and last_pay < opened:
        errors.append(f"last_payment ({last_payment}) is before date_opened ({date_opened})")
    
    return (len(errors) == 0, errors)
