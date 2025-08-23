"""
Basic text parsing utilities for Credit Clarity
Provides fallback parsing when AI methods are not available
"""
import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def parse_tradelines_basic(text: str) -> List[Dict[str, Any]]:
    """
    Parse tradelines using basic text pattern matching.
    This is a fallback method when AI parsing is not available.
    """
    try:
        logger.info("🔧 BASIC PARSING - INPUT DATA:")
        logger.info(f"  Text length: {len(text)} characters")
        
        if not text or len(text.strip()) < 50:
            logger.warning("Text too short for basic parsing")
            return []
        
        tradelines = []
        lines = text.split('\n')
        
        # Look for lines that might contain tradeline information
        credit_keywords = ['account', 'balance', 'limit', 'payment', 'creditor', 'card', 'loan']
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) < 20:
                continue
            
            line_lower = line.lower()
            
            # Skip header/footer lines
            if any(skip_word in line_lower for skip_word in ['page', 'report', 'bureau', 'summary']):
                continue
            
            # Check if line contains credit-related keywords
            keyword_count = sum(1 for keyword in credit_keywords if keyword in line_lower)
            if keyword_count < 2:  # Need at least 2 credit keywords
                continue
            
            # Try to extract structured data from the line
            tradeline = extract_tradeline_from_line(line, lines[max(0, i-1):i+2])
            if tradeline:
                tradelines.append(tradeline)
        
        logger.info(f"🔧 Basic parsing extracted {len(tradelines)} potential tradelines")
        return tradelines
        
    except Exception as e:
        logger.error(f"❌ Basic parsing failed: {str(e)}")
        return []


def extract_tradeline_from_line(line: str, context_lines: List[str]) -> Optional[Dict[str, Any]]:
    """
    Extract tradeline information from a single line with context.
    """
    try:
        # Look for account numbers (sequences of digits, possibly with dashes)
        account_matches = re.findall(r'\b\d{4,16}\b|\b\d{4}-\d{4}-\d{4}-\d{4}\b', line)
        
        # Look for dollar amounts
        amount_matches = re.findall(r'\$[\d,]+\.?\d*', line)
        
        # Look for creditor names (words before account numbers or amounts)
        creditor_match = re.search(r'^([A-Za-z\s&.]+?)(?:\s+\d|\s+\$)', line)
        
        # If we found key components, create a tradeline
        if account_matches and (amount_matches or creditor_match):
            tradeline = {
                "creditor_name": creditor_match.group(1).strip() if creditor_match else "Unknown Creditor",
                "account_number": account_matches[0],
                "account_balance": amount_matches[0] if amount_matches else "",
                "credit_limit": amount_matches[1] if len(amount_matches) > 1 else "",
                "monthly_payment": "",
                "date_opened": "",
                "account_type": "Credit Card",  # Default
                "account_status": "Open",      # Default
                "credit_bureau": "",           # Will be set later
                "is_negative": False,
                "dispute_count": 0
            }
            
            # Try to extract dates from context
            date_match = extract_date_from_context(context_lines)
            if date_match:
                tradeline["date_opened"] = date_match
            
            # Determine if account is negative based on keywords
            negative_keywords = ['late', 'delinquent', 'charged off', 'collection', 'closed']
            if any(keyword in line.lower() for keyword in negative_keywords):
                tradeline["is_negative"] = True
            
            return tradeline
            
    except Exception as e:
        logger.debug(f"Failed to extract tradeline from line: {e}")
    
    return None


def extract_date_from_context(context_lines: List[str]) -> Optional[str]:
    """
    Try to extract a date from context lines.
    """
    date_patterns = [
        r'\b\d{1,2}/\d{1,2}/\d{4}\b',    # MM/DD/YYYY
        r'\b\d{1,2}/\d{4}\b',            # MM/YYYY
        r'\b\d{4}-\d{2}-\d{2}\b'         # YYYY-MM-DD
    ]
    
    for line in context_lines:
        for pattern in date_patterns:
            match = re.search(pattern, line)
            if match:
                return match.group()
    
    return None


def extract_account_numbers(text: str) -> List[str]:
    """
    Extract all potential account numbers from text.
    """
    account_patterns = [
        r'\b\d{4,16}\b',                    # Simple digit sequences
        r'\b\d{4}-\d{4}-\d{4}-\d{4}\b',    # Credit card format
        r'\b\d{4}\s\d{4}\s\d{4}\s\d{4}\b', # Spaced format
    ]
    
    account_numbers = []
    for pattern in account_patterns:
        matches = re.findall(pattern, text)
        account_numbers.extend(matches)
    
    # Filter out obviously invalid account numbers
    valid_accounts = []
    for account in account_numbers:
        # Remove spaces and dashes for validation
        clean_account = re.sub(r'[\s-]', '', account)
        
        # Skip if too short or too long
        if len(clean_account) < 4 or len(clean_account) > 20:
            continue
        
        # Skip if all same digit (likely not real account)
        if len(set(clean_account)) == 1:
            continue
        
        valid_accounts.append(account)
    
    return list(set(valid_accounts))  # Remove duplicates


def extract_dollar_amounts(text: str) -> List[str]:
    """
    Extract all dollar amounts from text.
    """
    amount_patterns = [
        r'\$[\d,]+\.?\d*',          # $1,234.56
        r'\$\s*[\d,]+\.?\d*',       # $ 1,234.56
        r'[\d,]+\.?\d*\s*dollars?', # 1,234.56 dollars
    ]
    
    amounts = []
    for pattern in amount_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        amounts.extend(matches)
    
    return amounts


def identify_table_structure(text: str) -> List[Dict[str, Any]]:
    """
    Try to identify table-like structures in text.
    """
    tables = []
    lines = text.split('\n')
    
    current_table = []
    potential_headers = []
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_table:
                # End of potential table
                if len(current_table) > 1:  # Need at least header + 1 data row
                    tables.append({
                        'headers': potential_headers,
                        'rows': current_table,
                        'confidence': calculate_table_confidence(current_table)
                    })
                current_table = []
                potential_headers = []
            continue
        
        # Check if line looks like tabular data (multiple columns)
        if '\t' in line or len(re.findall(r'\s{3,}', line)) >= 2:
            columns = re.split(r'\s{2,}|\t', line)
            if len(columns) >= 3:  # Need at least 3 columns
                if not current_table:
                    potential_headers = columns
                current_table.append(columns)
    
    # Handle last table if exists
    if current_table and len(current_table) > 1:
        tables.append({
            'headers': potential_headers,
            'rows': current_table,
            'confidence': calculate_table_confidence(current_table)
        })
    
    return tables


def calculate_table_confidence(table_rows: List[List[str]]) -> float:
    """
    Calculate confidence score for detected table structure.
    """
    if not table_rows or len(table_rows) < 2:
        return 0.0
    
    # Check column consistency
    column_counts = [len(row) for row in table_rows]
    if not column_counts:
        return 0.0
    
    most_common_count = max(set(column_counts), key=column_counts.count)
    consistency = column_counts.count(most_common_count) / len(column_counts)
    
    # Check for credit-related headers
    if table_rows:
        first_row = [col.lower() for col in table_rows[0]]
        credit_headers = ['account', 'balance', 'limit', 'payment', 'creditor', 'status']
        header_matches = sum(1 for header in credit_headers if any(h in col for col in first_row for h in [header]))
        header_score = min(header_matches / len(credit_headers), 1.0)
    else:
        header_score = 0.0
    
    # Combined confidence score
    confidence = (consistency * 0.6) + (header_score * 0.4)
    return round(confidence, 2)