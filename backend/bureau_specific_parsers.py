import re
import uuid
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

# Define TradelineSchema locally to avoid circular imports

from pydantic import BaseModel
from datetime import datetime

class TradelineSchema(BaseModel):
    id: uuid.UUID = uuid.uuid4()
    user_id: uuid.UUID = uuid.uuid4()
    creditor_name: str = "NULL"
    account_balance: str = "$0"
    credit_limit: str = "$0"
    monthly_payment: str = "$0"
    account_number: str = ""
    date_opened: str = ""
    account_type: str = ""
    account_status: str = ""
    credit_bureau: str = ""
    is_negative: bool = False
    dispute_count: int = 0
    created_at: datetime = datetime.utcnow()

class BureauParser(ABC):
    """Abstract base class for bureau-specific parsers"""
    
    def __init__(self, bureau_name: str):
        self.bureau_name = bureau_name
        self.common_creditors = {
            'AMEX': 'AMERICAN EXPRESS',
            'BOA': 'BANK OF AMERICA', 
            'CAP1': 'CAPITAL ONE',
            'CHASE': 'CHASE',
            'CITI': 'CITIBANK',
            'DISC': 'DISCOVER',
            'WF': 'WELLS FARGO',
            'SYNC': 'SYNCHRONY'
        }
    
    @abstractmethod
    def parse_tradelines(self, text: str) -> List[TradelineSchema]:
        """Parse tradelines from bureau-specific text format"""
        pass
    
    def normalize_creditor_name(self, name: str) -> str:
        """Normalize creditor names using common abbreviations"""
        if not name:
            return ""
        
        name = name.upper().strip()
        
        # Remove common prefixes/suffixes
        name = re.sub(r'\b(BANK|CREDIT|CARD|SERVICES|INC|LLC|CORP|NA|N\.A\.)\b', '', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Check for known abbreviations
        for abbrev, full_name in self.common_creditors.items():
            if abbrev in name:
                return full_name
        
        return name
    
    def extract_account_number(self, text: str) -> str:
        """Extract account number from text"""
        # Look for patterns like "Account: 1234567890" or "Acct#: 1234567890"
        patterns = [
            r'(?:Account|Acct)(?:\s*[#:]?\s*)(\d{4,16})',
            r'(?:Number|No|#)(?:\s*[:]?\s*)(\d{4,16})',
            r'\b(\d{4,16})\b'  # Fallback: any 4-16 digit number
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""
    
    def extract_date(self, text: str, date_type: str = "opened") -> str:
        """Extract date from text (opened, closed, last_payment, etc.)"""
        # Common date patterns
        date_patterns = [
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
            r'\b(\d{1,2}[/-]\d{2,4})\b',
            r'\b(\w{3}\s+\d{4})\b',  # Jan 2020
            r'\b(\w{3}\s+\d{1,2},?\s+\d{4})\b'  # Jan 15, 2020
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]  # Return first date found
        
        return ""
    
    def extract_currency_amount(self, text: str, amount_type: str = "balance") -> str:
        """Extract currency amounts from text"""
        # Look for patterns like $1,234.56 or 1234.56
        patterns = [
            r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'\b(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\b'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0].replace(',', '')
        
        return ""

class ExperianParser(BureauParser):
    """Parser for Experian credit report format"""
    
    def __init__(self):
        super().__init__("Experian")
        self.section_headers = [
            r'Potentially Negative Items',
            r'Accounts in Good Standing',
            r'Closed Accounts',
            r'Credit Accounts'
        ]
    
    def parse_tradelines(self, text: str) -> List[TradelineSchema]:
        tradelines = []
        
        # Experian often has tabular format - look for table sections
        sections = self._split_into_sections(text)
        
        for section_name, section_text in sections.items():
            section_tradelines = self._parse_section(section_text, section_name)
            tradelines.extend(section_tradelines)
        
        return tradelines
    
    def _split_into_sections(self, text: str) -> Dict[str, str]:
        """Split Experian report into sections"""
        sections = {}
        current_section = "unknown"
        current_text = []
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line is a section header
            is_header = False
            for header_pattern in self.section_headers:
                if re.search(header_pattern, line, re.IGNORECASE):
                    # Save previous section
                    if current_text:
                        sections[current_section] = '\n'.join(current_text)
                    
                    current_section = line
                    current_text = []
                    is_header = True
                    break
            
            if not is_header:
                current_text.append(line)
        
        # Save final section
        if current_text:
            sections[current_section] = '\n'.join(current_text)
        
        return sections
    
    def _parse_section(self, section_text: str, section_name: str) -> List[TradelineSchema]:
        """Parse a specific section of Experian report"""
        tradelines = []
        
        # Experian typically has entries like:
        # CAPITAL ONE    Account: 1234567890    Opened: 01/2020    Balance: $1,500
        
        lines = section_text.split('\n')
        current_tradeline_data = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line contains creditor name (usually starts the entry)
            creditor_match = re.match(r'^([A-Z\s&]+)(?:\s+Account|Acct)', line, re.IGNORECASE)
            if creditor_match:
                # Save previous tradeline if exists
                if current_tradeline_data and 'creditor_name' in current_tradeline_data:
                    tradeline = self._create_tradeline_from_data(current_tradeline_data, section_name)
                    if tradeline:
                        tradelines.append(tradeline)
                
                # Start new tradeline
                current_tradeline_data = {
                    'creditor_name': self.normalize_creditor_name(creditor_match.group(1))
                }
            
            # Extract account details from current line
            self._extract_line_data(line, current_tradeline_data)
        
        # Don't forget the last tradeline
        if current_tradeline_data and 'creditor_name' in current_tradeline_data:
            tradeline = self._create_tradeline_from_data(current_tradeline_data, section_name)
            if tradeline:
                tradelines.append(tradeline)
        
        return tradelines
    
    def _extract_line_data(self, line: str, data: Dict):
        """Extract data from a line and add to tradeline data"""
        
        # Account number
        if 'account_number' not in data:
            account_num = self.extract_account_number(line)
            if account_num:
                data['account_number'] = account_num
        
        # Dates
        if 'date_opened' not in data and re.search(r'opened', line, re.IGNORECASE):
            date = self.extract_date(line)
            if date:
                data['date_opened'] = date
        
        # Balance
        if re.search(r'balance|owed|owes', line, re.IGNORECASE):
            balance = self.extract_currency_amount(line)
            if balance:
                data['account_balance'] = balance
        
        # Credit limit
        if re.search(r'limit|credit', line, re.IGNORECASE):
            limit = self.extract_currency_amount(line)
            if limit:
                data['credit_limit'] = limit
        
        # Account status
        status_indicators = {
            'open': r'\b(open|current|ok)\b',
            'closed': r'\b(closed|terminated)\b',
            'charged_off': r'\b(charge[- ]?off|charged[- ]?off)\b',
            'in_collection': r'\b(collection|sold)\b'
        }
        
        for status, pattern in status_indicators.items():
            if re.search(pattern, line, re.IGNORECASE):
                data['account_status'] = status
                break
    
    def _create_tradeline_from_data(self, data: Dict, section_name: str) -> Optional[TradelineSchema]:
        """Create a TradelineSchema from extracted data"""
        
        # Minimum required fields
        if not data.get('creditor_name') or not data.get('account_number'):
            return None
        
        # Determine if negative based on section
        is_negative = 'negative' in section_name.lower() or 'collection' in section_name.lower()
        
        return TradelineSchema(
            creditor_name=data.get('creditor_name', ''),
            account_number=data.get('account_number', ''),
            account_balance=data.get('account_balance', ''),
            credit_limit=data.get('credit_limit', ''),
            monthly_payment=data.get('monthly_payment', ''),
            date_opened=data.get('date_opened', 'xx/xx/xxxxx'),
            account_type=data.get('account_type', ''),
            account_status=data.get('account_status', ''),
            credit_bureau='Experian',
            is_negative=is_negative,
            dispute_count=0
        )

class EquifaxParser(BureauParser):
    """Parser for Equifax credit report format"""
    
    def __init__(self):
        super().__init__("Equifax")
        self.section_patterns = [
            r'Accounts with adverse information',
            r'Accounts in good standing',
            r'Credit accounts',
            r'Account history as of'
        ]
    
    def parse_tradelines(self, text: str) -> List[TradelineSchema]:
        tradelines = []
        
        # Equifax often lists accounts in blocks with detailed info
        account_blocks = self._extract_account_blocks(text)
        
        for block in account_blocks:
            tradeline = self._parse_account_block(block)
            if tradeline:
                tradelines.append(tradeline)
        
        return tradelines
    
    def _extract_account_blocks(self, text: str) -> List[str]:
        """Extract individual account blocks from Equifax format"""
        blocks = []
        
        lines = text.split('\n')
        current_block = []
        in_account_section = False
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines unless we're building a block
            if not line:
                if current_block:
                    current_block.append('')
                continue
            
            # Check if this looks like a creditor name (all caps, at start of line)
            if re.match(r'^[A-Z\s&]{3,}(?:\s+\d+)?$', line) and len(line) > 3:
                # Start new block if we have a previous one
                if current_block:
                    blocks.append('\n'.join(current_block))
                    current_block = []
                
                current_block.append(line)
                in_account_section = True
            elif in_account_section:
                current_block.append(line)
                
                # Check if this might be the end of an account block
                if re.search(r'Date\s+reported|Last\s+activity|Payment\s+history', line, re.IGNORECASE):
                    # This might be the end, but continue for a few more lines
                    pass
        
        # Add the last block
        if current_block:
            blocks.append('\n'.join(current_block))
        
        return blocks
    
    def _parse_account_block(self, block_text: str) -> Optional[TradelineSchema]:
        """Parse a single account block from Equifax format"""
        
        lines = [line.strip() for line in block_text.split('\n') if line.strip()]
        
        if not lines:
            return None
        
        # First line is usually the creditor name
        creditor_name = self.normalize_creditor_name(lines[0])
        
        if not creditor_name:
            return None
        
        # Extract data from all lines
        data = {'creditor_name': creditor_name}
        full_text = ' '.join(lines)
        
        # Account number - Equifax often shows it as "Account number: XXXXXXXXX"
        account_patterns = [
            r'Account\s+number:?\s*(\d{4,16})',
            r'Account:?\s*(\d{4,16})',
            r'#\s*(\d{4,16})'
        ]
        
        for pattern in account_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                data['account_number'] = match.group(1)
                break
        
        # Date opened
        date_patterns = [
            r'Date\s+opened:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'Opened:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'Open\s+date:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                data['date_opened'] = match.group(1)
                break
        
        # Balance
        balance_patterns = [
            r'Balance:?\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'Current\s+balance:?\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'Amount\s+owed:?\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        ]
        
        for pattern in balance_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                data['account_balance'] = match.group(1).replace(',', '')
                break
        
        # Credit limit
        limit_patterns = [
            r'Credit\s+limit:?\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'High\s+credit:?\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'Limit:?\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        ]
        
        for pattern in limit_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                data['credit_limit'] = match.group(1).replace(',', '')
                break
        
        # Account status
        if re.search(r'\bopen\b|\bcurrent\b|\bgood\s+standing\b', full_text, re.IGNORECASE):
            data['account_status'] = 'open'
        elif re.search(r'\bclosed\b|\bterminated\b', full_text, re.IGNORECASE):
            data['account_status'] = 'closed'
        elif re.search(r'\bcharge\s?off\b|\bcharged\s?off\b', full_text, re.IGNORECASE):
            data['account_status'] = 'charged_off'
        elif re.search(r'\bcollection\b|\bsold\b', full_text, re.IGNORECASE):
            data['account_status'] = 'in_collection'
        
        # Account type
        if re.search(r'\bcredit\s+card\b|\brevolving\b', full_text, re.IGNORECASE):
            data['account_type'] = 'credit_card'
        elif re.search(r'\bmortgage\b|\bhome\s+loan\b', full_text, re.IGNORECASE):
            data['account_type'] = 'mortgage'
        elif re.search(r'\bauto\b|\bcar\b|\bvehicle\b', full_text, re.IGNORECASE):
            data['account_type'] = 'auto_loan'
        elif re.search(r'\binstallment\b', full_text, re.IGNORECASE):
            data['account_type'] = 'installment'
        
        # Determine if negative
        is_negative = any(term in full_text.lower() for term in 
                         ['collection', 'charge off', 'charged off', 'delinquent', 'late'])
        
        return TradelineSchema(
            creditor_name=data.get('creditor_name', ''),
            account_number=data.get('account_number', ''),
            account_balance=data.get('account_balance', ''),
            credit_limit=data.get('credit_limit', ''),
            monthly_payment=data.get('monthly_payment', ''),
            date_opened=data.get('date_opened', 'xx/xx/xxxxx'),
            account_type=data.get('account_type', ''),
            account_status=data.get('account_status', ''),
            credit_bureau='Equifax',
            is_negative=is_negative,
            dispute_count=0
        )

class TransUnionParser(BureauParser):
    """Parser for TransUnion credit report format"""
    
    def __init__(self):
        super().__init__("TransUnion")
        self.account_separators = [
            r'^\s*-{3,}\s*$',  # Lines with dashes
            r'^\s*={3,}\s*$',  # Lines with equals
            r'Account\s+Information\s+Summary',
            r'Satisfactory\s+Accounts',
            r'Potentially\s+Negative\s+Accounts'
        ]
    
    def parse_tradelines(self, text: str) -> List[TradelineSchema]:
        tradelines = []
        
        # TransUnion often uses a more structured format with clear separators
        account_sections = self._split_by_separators(text)
        
        for section in account_sections:
            section_tradelines = self._parse_transunion_section(section)
            tradelines.extend(section_tradelines)
        
        return tradelines
    
    def _split_by_separators(self, text: str) -> List[str]:
        """Split TransUnion report into account sections"""
        sections = []
        current_section = []
        
        lines = text.split('\n')
        
        for line in lines:
            # Check if this line is a separator
            is_separator = any(re.match(pattern, line) for pattern in self.account_separators)
            
            if is_separator:
                if current_section:
                    sections.append('\n'.join(current_section))
                    current_section = []
            else:
                current_section.append(line)
        
        # Add the last section
        if current_section:
            sections.append('\n'.join(current_section))
        
        return sections
    
    def _parse_transunion_section(self, section_text: str) -> List[TradelineSchema]:
        """Parse a TransUnion section for tradelines"""
        tradelines = []
        
        # Look for patterns that indicate account entries
        account_entries = self._extract_transunion_accounts(section_text)
        
        for entry in account_entries:
            tradeline = self._parse_transunion_account(entry)
            if tradeline:
                tradelines.append(tradeline)
        
        return tradelines
    
    def _extract_transunion_accounts(self, text: str) -> List[str]:
        """Extract individual account entries from TransUnion text"""
        accounts = []
        
        # TransUnion typically has creditor names on their own line
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        current_account = []
        
        for i, line in enumerate(lines):
            # Check if this looks like a creditor name (title case, multiple words)
            if (re.match(r'^[A-Z][a-z]*(?:\s+[A-Z][a-z]*)*$', line) or 
                re.match(r'^[A-Z\s&]+$', line)) and len(line) > 3:
                
                # Save previous account
                if current_account:
                    accounts.append('\n'.join(current_account))
                
                # Start new account
                current_account = [line]
            elif current_account:
                current_account.append(line)
                
                # Stop if we've gone too far (next creditor or end of relevant data)
                if i < len(lines) - 1:
                    next_line = lines[i + 1]
                    if re.match(r'^[A-Z][a-z]*(?:\s+[A-Z][a-z]*)*$', next_line):
                        # Next line looks like another creditor
                        continue
        
        # Add the last account
        if current_account:
            accounts.append('\n'.join(current_account))
        
        return accounts
    
    def _parse_transunion_account(self, account_text: str) -> Optional[TradelineSchema]:
        """Parse a single TransUnion account entry"""
        
        lines = [line.strip() for line in account_text.split('\n') if line.strip()]
        
        if not lines:
            return None
        
        # First line should be creditor name
        creditor_name = self.normalize_creditor_name(lines[0])
        
        if not creditor_name:
            return None
        
        full_text = ' '.join(lines)
        data = {'creditor_name': creditor_name}
        
        # Extract account details using TransUnion-specific patterns
        
        # Account number
        account_patterns = [
            r'Account\s+Number:?\s*(\d{4,16})',
            r'Acct\s*#:?\s*(\d{4,16})',
            r'Account:?\s*(\d{4,16})'
        ]
        
        for pattern in account_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                data['account_number'] = match.group(1)
                break
        
        # Date opened
        date_match = re.search(r'Date\s+Opened:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', full_text, re.IGNORECASE)
        if date_match:
            data['date_opened'] = date_match.group(1)
        
        # Balance
        balance_patterns = [
            r'Current\s+Balance:?\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'Balance:?\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        ]
        
        for pattern in balance_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                data['account_balance'] = match.group(1).replace(',', '')
                break
        
        # Credit limit
        limit_patterns = [
            r'Credit\s+Limit:?\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'High\s+Balance:?\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        ]
        
        for pattern in limit_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                data['credit_limit'] = match.group(1).replace(',', '')
                break
        
        # Payment amount
        payment_match = re.search(r'Monthly\s+Payment:?\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', full_text, re.IGNORECASE)
        if payment_match:
            data['monthly_payment'] = payment_match.group(1).replace(',', '')
        
        # Account status and type
        if re.search(r'\bOpen\b|\bCurrent\b', full_text, re.IGNORECASE):
            data['account_status'] = 'open'
        elif re.search(r'\bClosed\b', full_text, re.IGNORECASE):
            data['account_status'] = 'closed'
        elif re.search(r'\bCharge\s?Off\b', full_text, re.IGNORECASE):
            data['account_status'] = 'charged_off'
        elif re.search(r'\bCollection\b', full_text, re.IGNORECASE):
            data['account_status'] = 'in_collection'
        
        # Account type
        if re.search(r'\bCredit\s+Card\b|\bRevolving\b', full_text, re.IGNORECASE):
            data['account_type'] = 'credit_card'
        elif re.search(r'\bMortgage\b', full_text, re.IGNORECASE):
            data['account_type'] = 'mortgage'
        elif re.search(r'\bAuto\b|\bVehicle\b', full_text, re.IGNORECASE):
            data['account_type'] = 'auto_loan'
        elif re.search(r'\bInstallment\b', full_text, re.IGNORECASE):
            data['account_type'] = 'installment'
        
        # Determine if negative
        is_negative = any(term in full_text.lower() for term in 
                         ['potentially negative', 'collection', 'charge off', 'delinquent'])
        
        return TradelineSchema(
            creditor_name=data.get('creditor_name', ''),
            account_number=data.get('account_number', ''),
            account_balance=data.get('account_balance', ''),
            credit_limit=data.get('credit_limit', ''),
            monthly_payment=data.get('monthly_payment', ''),
            date_opened=data.get('date_opened', 'xx/xx/xxxxx'),
            account_type=data.get('account_type', ''),
            account_status=data.get('account_status', ''),
            credit_bureau='TransUnion',
            is_negative=is_negative,
            dispute_count=0
        )

# Factory class to get the right parser
class BureauParserFactory:
    """Factory to create appropriate parser based on detected bureau"""
    
    @staticmethod
    def get_parser(bureau_name: str) -> BureauParser:
        """Get the appropriate parser for the detected bureau"""
        parsers = {
            'Experian': ExperianParser(),
            'Equifax': EquifaxParser(),
            'TransUnion': TransUnionParser()
        }
        
        return parsers.get(bureau_name, ExperianParser())  # Default to Experian

# Usage in your main processing function
def enhanced_parse_tradelines(text: str, detected_bureau: str) -> List[TradelineSchema]:
    """
    Enhanced tradeline parsing using bureau-specific parsers
    """
    parser = BureauParserFactory.get_parser(detected_bureau)
    tradelines = parser.parse_tradelines(text)
    
    print(f"Bureau-specific parsing results for {detected_bureau}:")
    print(f"  - Extracted {len(tradelines)} tradelines")
    
    # Fallback to basic parsing if bureau parser found nothing
    if not tradelines:
        print("  - Bureau parser found no tradelines, trying basic parsing...")
        # You'll need to import or define parse_tradelines_basic
        # tradelines = parse_tradelines_basic(text)  # Your existing basic parser
        
        # Set the detected bureau for all tradelines
        for tradeline in tradelines:
            tradeline.credit_bureau = detected_bureau
    
    return tradelines