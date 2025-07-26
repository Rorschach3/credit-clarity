import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)

class EnhancedExtractionService:
    """Enhanced service for extracting tradelines with improved accuracy and completeness"""
    
    def __init__(self):
        self.field_patterns = self._initialize_field_patterns()
        self.creditor_patterns = self._initialize_creditor_patterns()
        self.common_ocr_fixes = self._initialize_ocr_fixes()
        
    def _initialize_field_patterns(self) -> Dict[str, List[str]]:
        """Initialize comprehensive field detection patterns"""
        return {
            'account_number': [
                r'account\s*(?:number|#|num)[\s:]*([*\dX-]{4,})',
                r'acct\s*(?:number|#|num)[\s:]*([*\dX-]{4,})',
                r'ref\s*(?:number|#|num)[\s:]*([*\dX-]{4,})',
                r'(\*{4,}\d{4}|\d{4}\*{4,}|[*X]{4,}\d{4}|\d{4}[*X]{4,})',
                r'([*X-]{4,}\d{4,}|\d{4,}[*X-]{4,})',
            ],
            'current_balance': [
                r'current\s*balance[\s:]*\$?([\d,]+\.?\d*)',
                r'balance[\s:]*\$?([\d,]+\.?\d*)',
                r'curr\s*bal[\s:]*\$?([\d,]+\.?\d*)',
                r'outstanding[\s:]*\$?([\d,]+\.?\d*)',
                r'amount\s*owed[\s:]*\$?([\d,]+\.?\d*)',
                r'balance\s*due[\s:]*\$?([\d,]+\.?\d*)',
            ],
            'credit_limit': [
                r'credit\s*limit[\s:]*\$?([\d,]+\.?\d*)',
                r'limit[\s:]*\$?([\d,]+\.?\d*)',
                r'credit\s*line[\s:]*\$?([\d,]+\.?\d*)',
                r'high\s*credit[\s:]*\$?([\d,]+\.?\d*)',
                r'high\s*balance[\s:]*\$?([\d,]+\.?\d*)',
                r'max\s*credit[\s:]*\$?([\d,]+\.?\d*)',
                r'available\s*credit[\s:]*\$?([\d,]+\.?\d*)',
            ],
            'monthly_payment': [
                r'monthly\s*payment[\s:]*\$?([\d,]+\.?\d*)',
                r'payment\s*amount[\s:]*\$?([\d,]+\.?\d*)',
                r'min\s*payment[\s:]*\$?([\d,]+\.?\d*)',
                r'minimum\s*payment[\s:]*\$?([\d,]+\.?\d*)',
                r'scheduled\s*payment[\s:]*\$?([\d,]+\.?\d*)',
                r'contract\s*payment[\s:]*\$?([\d,]+\.?\d*)',
            ],
            'date_opened': [
                r'opened[\s:]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
                r'date\s*opened[\s:]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
                r'account\s*opened[\s:]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
                r'open\s*date[\s:]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
                r'start\s*date[\s:]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
            ],
            'date_closed': [
                r'closed[\s:]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
                r'date\s*closed[\s:]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
                r'account\s*closed[\s:]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
                r'close\s*date[\s:]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
                r'end\s*date[\s:]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
            ],
            'payment_status': [
                r'(current|pays as agreed|ok|good)',
                r'(\d+)\s*days?\s*late',
                r'(past due|delinquent|late)',
                r'(charged off|charge[- ]?off)',
                r'(collection|collections)',
                r'(settled|settlement)',
                r'(bankruptcy|bk)',
            ],
            'account_status': [
                r'status[\s:]*([a-zA-Z\s]+)',
                r'account\s*status[\s:]*([a-zA-Z\s]+)',
                r'(open|closed|transferred|sold)',
                r'(active|inactive)',
            ]
        }
    
    def _initialize_creditor_patterns(self) -> List[str]:
        """Initialize comprehensive creditor name patterns"""
        return [
            # Major Credit Cards - with variations
            r'(CHASE|Chase|chase)(?:\s+(?:BANK|Bank|bank|CARD|Card|card))?',
            r'(CAPITAL\s*ONE|Capital\s*One|capital\s*one)',
            r'(AMERICAN\s*EXPRESS|American\s*Express|Amex|AMEX|amex)',
            r'(BANK\s*OF\s*AMERICA|Bank\s*of\s*America|BOA|boa)',
            r'(WELLS\s*FARGO|Wells\s*Fargo|wells\s*fargo)',
            r'(CITI|Citi|citi|CITIBANK|Citibank|citibank)',
            r'(DISCOVER|Discover|discover)',
            r'(SYNCHRONY|Synchrony|synchrony)',
            r'(BARCLAY|Barclays?|barclay)',
            r'(US\s*BANK|US\s*Bank|us\s*bank)',
            
            # Store Cards - enhanced patterns
            r'(AMAZON|Amazon|amazon)(?:\s+(?:STORE|store|CARD|card))?',
            r'(TARGET|Target|target)(?:\s+(?:CARD|card))?',
            r'(HOME\s*DEPOT|Home\s*Depot|HOMEDEPOT)',
            r'(LOWES?|Lowe\'s|LOWE\'S|lowes?)',
            r'(WALMART|Walmart|walmart)',
            r'(COSTCO|Costco|costco)',
            r'(NORDSTROM|Nordstrom|nordstrom)',
            r'(MACY\'S|Macy\'s|macys)',
            r'(KOHL\'S|Kohl\'s|kohls)',
            r'(BEST\s*BUY|Best\s*Buy|bestbuy)',
            
            # Auto Loans - with financing variations
            r'(FORD\s*(?:CREDIT|MOTOR\s*CREDIT)?|Ford\s*(?:Credit|Motor\s*Credit)?)',
            r'(HONDA\s*(?:FINANCIAL|FINANCE)?|Honda\s*(?:Financial|Finance)?)',
            r'(TOYOTA\s*(?:FINANCIAL|FINANCE)?|Toyota\s*(?:Financial|Finance)?)',
            r'(NISSAN\s*(?:MOTOR|FINANCIAL)?|Nissan\s*(?:Motor|Financial)?)',
            r'(GM\s*FINANCIAL|GM\s*Financial|gm\s*financial)',
            r'(CHRYSLER\s*CAPITAL|Chrysler\s*Capital)',
            r'(ALLY\s*(?:AUTO|FINANCIAL)?|Ally\s*(?:Auto|Financial)?)',
            r'(SANTANDER|Santander|santander)',
            
            # Student Loans - with variations
            r'(NAVIENT|Navient|navient)',
            r'(GREAT\s*LAKES|Great\s*Lakes|great\s*lakes)',
            r'(NELNET|Nelnet|nelnet)',
            r'(FEDLOAN|FedLoan|fedloan)',
            r'(MOHELA|MOHELA|mohela)',
            r'(DEPT\.?\s*OF\s*EDUCATION|Department\s*of\s*Education)',
            r'(STUDENT\s*LOAN|Student\s*Loan)',
            
            # Mortgage - with variations
            r'(QUICKEN\s*LOANS|Quicken\s*Loans|ROCKET\s*MORTGAGE|Rocket\s*Mortgage)',
            r'(FREEDOM\s*MORTGAGE|Freedom\s*Mortgage)',
            r'(PENNYMAC|PennyMac|pennymac)',
            r'(CALIBER|Caliber|caliber)',
            r'(MORTGAGE|Mortgage|mortgage)',
            
            # Credit Unions
            r'(NAVY\s*FEDERAL|Navy\s*Federal)',
            r'(USAA|usaa)',
            r'(PENTAGON\s*FCU|Pentagon\s*FCU)',
            r'(CREDIT\s*UNION|Credit\s*Union)',
            
            # Fintech and Others
            r'(PAYPAL|PayPal|paypal)',
            r'(AFFIRM|Affirm|affirm)',
            r'(KLARNA|Klarna|klarna)',
            r'(SOFI|SoFi|sofi)',
            r'(UPSTART|Upstart|upstart)',
            r'(LENDING\s*CLUB|Lending\s*Club)',
            r'(PROSPER|Prosper|prosper)',
            r'(AVANT|Avant|avant)',
            r'(ONEMAIN|OneMain|onemain)',
        ]
    
    def _initialize_ocr_fixes(self) -> Dict[str, str]:
        """Initialize common OCR error corrections"""
        return {
            # Word-level corrections (more specific)
            'Credltor': 'Creditor',
            'Credlf': 'Credit',
            'Baiance': 'Balance',
            'Lirnit': 'Limit',
            'Payrnent': 'Payment',
            'Accounf': 'Account',
            'Nurnber': 'Number',
            'Arnount': 'Amount',
            'Lirnited': 'Limited',
            'Narne': 'Name',
            'Addi-ess': 'Address',
            # Less aggressive character replacements
            '\brn\b': 'm',  # Only replace 'rn' as whole word
            '\brnent\b': 'ment',  # Only specific endings
        }
    
    def fix_ocr_errors(self, text: str) -> str:
        """Apply OCR error corrections to text"""
        corrected_text = text
        for error, correction in self.common_ocr_fixes.items():
            # Use word boundaries for single letters to avoid over-correction
            if len(error) == 1 and error not in ['O', 'l', 'I']:
                continue  # Skip single character replacements that are too aggressive
            corrected_text = re.sub(error, correction, corrected_text, flags=re.IGNORECASE)
        return corrected_text
    
    def extract_enhanced_tradelines(self, text: str, detected_bureau: str = "Unknown") -> List[Dict[str, Any]]:
        """
        Enhanced tradeline extraction with improved field detection and completeness
        """
        logger.info(f"Starting enhanced tradeline extraction for {detected_bureau} bureau")
        
        # Step 1: Fix OCR errors
        corrected_text = self.fix_ocr_errors(text)
        
        # Step 2: Split text into tradeline sections
        tradeline_sections = self._split_into_tradeline_sections(corrected_text, detected_bureau)
        
        # Step 3: Extract tradelines from each section
        tradelines = []
        for i, section in enumerate(tradeline_sections):
            logger.debug(f"Processing tradeline section {i+1}/{len(tradeline_sections)}")
            tradeline = self._extract_tradeline_from_section(section)
            if tradeline and tradeline.get('creditor_name'):
                tradelines.append(tradeline)
        
        # Step 4: Post-process and validate
        validated_tradelines = self._validate_and_enhance_tradelines(tradelines)
        
        logger.info(f"Enhanced extraction completed: {len(validated_tradelines)} tradelines found")
        return validated_tradelines
    
    def _split_into_tradeline_sections(self, text: str, bureau: str) -> List[str]:
        """Split text into individual tradeline sections based on bureau format"""
        sections = []
        
        # First try bureau-specific splitting
        if bureau.lower() == "transunion":
            # TransUnion typically has clear separators
            sections = re.split(r'\n\n+|\n\s*(?=[A-Z][A-Z\s,&.]+(?:BANK|CARD|FINANCIAL|CREDIT|AUTO|LOAN))', text)
        
        elif bureau.lower() == "experian":
            # Experian often has tabular format
            sections = re.split(r'\n\s*(?=[A-Z][A-Z\s]+\s+\*+\d+)', text)
        
        elif bureau.lower() == "equifax":
            # Equifax has block format
            sections = re.split(r'\n\s*(?=[A-Z][A-Z\s&]+\s+Account)', text)
        
        # If bureau-specific didn't work well, try generic approach
        if not sections or len(sections) < 2:
            # Generic approach - split on creditor patterns or empty lines
            creditor_pattern = '|'.join([f'(?:{pattern})' for pattern in self.creditor_patterns])
            sections = re.split(f'\n\s*(?=(?:{creditor_pattern}))', text, flags=re.IGNORECASE)
            
            # Also try splitting on double newlines
            if len(sections) < 2:
                sections = re.split(r'\n\s*\n+', text)
        
        # Filter sections and ensure we have reasonable content
        filtered_sections = []
        for section in sections:
            section = section.strip()
            if len(section) > 30 and any(pattern in section.upper() for pattern in 
                ['ACCOUNT', 'BANK', 'CARD', 'CREDIT', 'BALANCE', 'LIMIT', 'PAYMENT']):
                filtered_sections.append(section)
        
        return filtered_sections if filtered_sections else [text]  # Return original if splitting failed
    
    def _extract_tradeline_from_section(self, section: str) -> Optional[Dict[str, Any]]:
        """Extract a complete tradeline from a text section"""
        tradeline = {}
        
        # Extract creditor name (highest priority)
        creditor_name = self._extract_creditor_name(section)
        if not creditor_name:
            return None  # Skip sections without identifiable creditor
        
        tradeline['creditor_name'] = creditor_name
        
        # Extract account type based on creditor
        tradeline['account_type'] = self._determine_account_type(creditor_name)
        
        # Extract all other fields
        for field_name, patterns in self.field_patterns.items():
            if field_name not in ['creditor_name']:  # Skip already extracted
                value = self._extract_field_value(section, patterns, field_name)
                if value:
                    tradeline[field_name] = value
        
        # Set defaults for missing fields
        tradeline = self._set_field_defaults(tradeline)
        
        # Calculate confidence score
        tradeline['confidence_score'] = self._calculate_confidence_score(tradeline, section)
        
        return tradeline
    
    def _extract_creditor_name(self, section: str) -> Optional[str]:
        """Extract creditor name from section using enhanced patterns"""
        # Try each creditor pattern
        for pattern in self.creditor_patterns:
            match = re.search(pattern, section, re.IGNORECASE)
            if match:
                creditor_name = match.group(0).strip()
                # Clean up the name
                creditor_name = re.sub(r'\s+', ' ', creditor_name)  # Normalize whitespace
                return creditor_name.title()  # Proper case
        
        # Fallback: Look for capitalized words at beginning of section
        lines = section.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if len(line) > 3 and line.isupper():
                # Likely a creditor name in all caps
                return line.title()
        
        return None
    
    def _extract_field_value(self, section: str, patterns: List[str], field_name: str) -> Optional[str]:
        """Extract field value using multiple patterns"""
        for pattern in patterns:
            match = re.search(pattern, section, re.IGNORECASE | re.MULTILINE)
            if match:
                if match.groups():
                    value = match.group(1).strip()
                else:
                    value = match.group(0).strip()
                
                # Post-process based on field type
                value = self._post_process_field_value(value, field_name)
                if value:
                    return value
        
        return None
    
    def _post_process_field_value(self, value: str, field_name: str) -> Optional[str]:
        """Post-process extracted field values"""
        if not value or value.lower() in ['none', 'n/a', 'null', '']:
            return None
        
        if field_name in ['current_balance', 'credit_limit', 'monthly_payment']:
            # Clean monetary values
            value = re.sub(r'[^\d.,]', '', value)  # Keep only digits, dots, commas
            if not value or value in ['0', '0.00', '.00']:
                return None
            return value
        
        elif field_name in ['date_opened', 'date_closed']:
            # Normalize date format
            value = re.sub(r'[^\d/\-]', '', value)
            if len(value) < 6:  # Too short to be a valid date
                return None
            return value
        
        elif field_name == 'account_number':
            # Clean account numbers
            value = re.sub(r'[^\d*X\-]', '', value)
            if len(value) < 4:  # Too short to be an account number
                return None
            return value
        
        elif field_name in ['payment_status', 'account_status']:
            # Normalize status values
            value = value.lower().strip()
            if value in ['current', 'ok', 'good', 'pays as agreed']:
                return 'Current'
            elif 'late' in value or 'past due' in value:
                return 'Late'
            elif 'charged off' in value or 'charge off' in value:
                return 'Charged Off'
            elif 'collection' in value:
                return 'Collection'
            return value.title()
        
        return value.strip()
    
    def _determine_account_type(self, creditor_name: str) -> str:
        """Determine account type based on creditor name"""
        creditor_upper = creditor_name.upper()
        
        # Auto loans
        auto_keywords = ['FORD', 'HONDA', 'TOYOTA', 'NISSAN', 'GM', 'CHRYSLER', 'ALLY AUTO', 'SANTANDER']
        if any(keyword in creditor_upper for keyword in auto_keywords):
            return 'Auto Loan'
        
        # Student loans
        student_keywords = ['NAVIENT', 'GREAT LAKES', 'NELNET', 'FEDLOAN', 'MOHELA', 'DEPT OF EDUCATION', 'STUDENT']
        if any(keyword in creditor_upper for keyword in student_keywords):
            return 'Student Loan'
        
        # Mortgages
        mortgage_keywords = ['QUICKEN', 'ROCKET', 'FREEDOM', 'PENNYMAC', 'CALIBER', 'MORTGAGE']
        if any(keyword in creditor_upper for keyword in mortgage_keywords):
            return 'Mortgage'
        
        # Personal loans
        personal_keywords = ['LENDING CLUB', 'PROSPER', 'SOFI', 'AVANT', 'ONEMAIN', 'SPRINGLEAF', 'PERSONAL']
        if any(keyword in creditor_upper for keyword in personal_keywords):
            return 'Personal Loan'
        
        # Default to credit card
        return 'Credit Card'
    
    def _set_field_defaults(self, tradeline: Dict[str, Any]) -> Dict[str, Any]:
        """Set default values for missing fields"""
        defaults = {
            'account_balance': None,
            'credit_limit': None,
            'monthly_payment': None,
            'account_number': '',
            'date_opened': None,
            'date_closed': None,
            'payment_status': 'Unknown',
            'account_status': 'Open',
            'is_negative': False,
            'dispute_count': 0,
            'credit_bureau': 'Unknown'
        }
        
        for field, default_value in defaults.items():
            if field not in tradeline:
                tradeline[field] = default_value
        
        return tradeline
    
    def _calculate_confidence_score(self, tradeline: Dict[str, Any], section: str) -> float:
        """Calculate confidence score for extracted tradeline"""
        score = 0.0
        max_score = 10.0
        
        # Creditor name found (required)
        if tradeline.get('creditor_name'):
            score += 3.0
        
        # Account number found
        if tradeline.get('account_number'):
            score += 2.0
        
        # Financial fields found
        financial_fields = ['current_balance', 'credit_limit', 'monthly_payment']
        for field in financial_fields:
            if tradeline.get(field):
                score += 1.0
        
        # Date fields found
        date_fields = ['date_opened', 'date_closed']
        for field in date_fields:
            if tradeline.get(field):
                score += 0.5
        
        # Status fields found
        status_fields = ['payment_status', 'account_status']
        for field in status_fields:
            if tradeline.get(field) and tradeline[field] != 'Unknown':
                score += 0.5
        
        # Section quality (length and structure)
        if len(section) > 200:
            score += 1.0
        
        return min(score / max_score, 1.0)
    
    def _validate_and_enhance_tradelines(self, tradelines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and enhance extracted tradelines"""
        validated = []
        
        for tradeline in tradelines:
            # Skip low-confidence tradelines
            if tradeline.get('confidence_score', 0) < 0.3:
                logger.debug(f"Skipping low-confidence tradeline: {tradeline.get('creditor_name')}")
                continue
            
            # Validate monetary values
            tradeline = self._validate_monetary_fields(tradeline)
            
            # Validate dates
            tradeline = self._validate_date_fields(tradeline)
            
            # Add metadata
            tradeline['extracted_at'] = datetime.utcnow().isoformat()
            tradeline['extraction_method'] = 'enhanced_extraction'
            
            validated.append(tradeline)
        
        return validated
    
    def _validate_monetary_fields(self, tradeline: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize monetary fields"""
        monetary_fields = ['current_balance', 'credit_limit', 'monthly_payment']
        
        for field in monetary_fields:
            value = tradeline.get(field)
            if value:
                try:
                    # Remove currency symbols and commas
                    cleaned = re.sub(r'[^\d.]', '', str(value))
                    if cleaned:
                        # Convert to float to validate, but keep as string for storage
                        float_val = float(cleaned)
                        if float_val >= 0:  # Must be non-negative
                            tradeline[field] = cleaned
                        else:
                            tradeline[field] = None
                    else:
                        tradeline[field] = None
                except (ValueError, TypeError):
                    tradeline[field] = None
        
        # Validate logical relationships
        balance = tradeline.get('current_balance')
        limit = tradeline.get('credit_limit')
        
        if balance and limit:
            try:
                balance_val = float(balance)
                limit_val = float(limit)
                
                # Balance shouldn't exceed limit by too much for credit cards
                if tradeline.get('account_type') == 'Credit Card' and balance_val > limit_val * 1.2:
                    logger.warning(f"Balance ({balance}) significantly exceeds limit ({limit}) for {tradeline.get('creditor_name')}")
            except (ValueError, TypeError):
                pass
        
        return tradeline
    
    def _validate_date_fields(self, tradeline: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize date fields"""
        date_fields = ['date_opened', 'date_closed']
        
        for field in date_fields:
            value = tradeline.get(field)
            if value:
                try:
                    # Try to parse and normalize date
                    from dateutil import parser
                    parsed_date = parser.parse(value, fuzzy=True)
                    
                    # Check if date is reasonable (not too far in future/past)
                    current_year = datetime.now().year
                    if 1970 <= parsed_date.year <= current_year + 1:
                        tradeline[field] = parsed_date.strftime('%Y-%m-%d')
                    else:
                        tradeline[field] = None
                        
                except (ValueError, TypeError):
                    tradeline[field] = None
        
        # Validate date relationships
        opened = tradeline.get('date_opened')
        closed = tradeline.get('date_closed')
        
        if opened and closed:
            try:
                from dateutil import parser
                opened_date = parser.parse(opened)
                closed_date = parser.parse(closed)
                
                if closed_date < opened_date:
                    logger.warning(f"Close date before open date for {tradeline.get('creditor_name')}")
                    tradeline['date_closed'] = None  # Remove invalid close date
                    
            except (ValueError, TypeError):
                pass
        
        return tradeline

    def get_enhanced_extraction_prompt(self, text: str, detected_bureau: str = "Unknown") -> str:
        """Generate enhanced extraction prompt for LLM processing"""
        
        return f"""
You are an expert credit report parser with deep knowledge of {detected_bureau} bureau formats.

DOCUMENT TEXT TO ANALYZE:
{text[:8000]}  # Truncated for token limits

YOUR TASK:
Extract ALL tradeline accounts from this credit report with maximum completeness and accuracy.

EXTRACTION REQUIREMENTS:

1. CREDITOR IDENTIFICATION:
   - Look for company names, banks, credit card issuers
   - Include variations: "CHASE BANK", "Chase", "CHASE CARD"
   - Don't miss store cards, auto loans, mortgages, student loans
   - Extract EXACT name as it appears

2. ACCOUNT NUMBERS:
   - Find masked numbers: ****1234, XXXX5678, etc.
   - Include partial numbers: 1234****, ****-****-1234
   - Look for "Account", "Acct", "Ref Number", etc.

3. FINANCIAL DATA (CRITICAL):
   - Current Balance: Look for "Balance", "Current Balance", "Amount Owed", "Outstanding"
   - Credit Limit: Look for "Limit", "Credit Limit", "High Credit", "High Balance", "Available Credit"
   - Monthly Payment: Look for "Payment", "Monthly Payment", "Min Payment", "Scheduled Payment"
   - Extract EXACT amounts, including cents

4. DATES:
   - Date Opened: "Opened", "Date Opened", "Account Opened", "Start Date"
   - Date Closed: "Closed", "Date Closed", "Account Closed" (if applicable)
   - Format: MM/DD/YYYY or similar

5. STATUS INFORMATION:
   - Payment Status: "Current", "30 days late", "60 days late", "Charged Off", "Collection"
   - Account Status: "Open", "Closed", "Transferred", "Active", "Inactive"

6. ACCOUNT TYPE CLASSIFICATION:
   - Credit Card, Auto Loan, Mortgage, Student Loan, Personal Loan, Line of Credit

SEARCH STRATEGIES:
- Scan ENTIRE document section by section
- Look for tabular data and structured sections
- Check both narrative text and table formats
- Use context clues to associate data with accounts
- Follow account information across multiple lines

IMPORTANT GUIDELINES:
- Extract information even if partially complete
- Use "null" only if truly not present
- Be thorough - missing tradelines is the biggest issue
- Double-check for financial amounts (balances, limits, payments)
- Look for account numbers in various formats

RESPONSE FORMAT:
Return valid JSON with this structure:

{{
  "tradelines": [
    {{
      "creditor_name": "CHASE BANK",
      "account_number": "****1234",
      "account_type": "Credit Card",
      "current_balance": "1250.00",
      "credit_limit": "5000.00",
      "monthly_payment": "35.00",
      "payment_status": "Current",
      "account_status": "Open",
      "date_opened": "2020-01-15",
      "date_closed": null,
      "confidence_score": 0.95,
      "extraction_notes": "All fields clearly identified"
    }}
  ],
  "extraction_summary": {{
    "total_found": 8,
    "high_confidence": 6,
    "medium_confidence": 2,
    "missing_critical_data": ["Account 3 missing balance", "Account 7 missing limit"]
  }}
}}

CRITICAL SUCCESS FACTORS:
1. Find ALL tradelines (don't miss any)
2. Extract financial amounts completely
3. Identify account numbers accurately
4. Assign appropriate confidence scores
5. Note any extraction challenges

Be extremely thorough - the current system is missing many tradelines and field values.
"""