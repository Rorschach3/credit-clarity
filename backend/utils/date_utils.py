"""
Date utility functions for Credit Clarity
Handles date normalization and validation for PostgreSQL compatibility
"""
import re
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def normalize_date_for_postgres(date_str: str) -> Optional[str]:
    """
    Ensure date_opened is in ISO format (YYYY-MM-DD) for PostgreSQL.
    Input: '04/18/2022' or other formats
    Output: '2022-04-18' or None for invalid dates
    """
    if not date_str:
        return None
    
    # Convert to string and strip safely
    date_str = str(date_str).strip()
    if not date_str:
        return None
    
    # Pre-validation: Skip obviously invalid date strings
    # Skip strings with invalid patterns that look like reference numbers
    if re.match(r'^\d{2,}-\d+(-\d+)?$', date_str):
        parts = date_str.split('-')
        if len(parts) >= 2:
            try:
                first_part = int(parts[0])
                second_part = int(parts[1])
                # If first part > 12 (invalid month) or second part > 59 (likely reference), skip
                if first_part > 12 or second_part > 59:
                    return None
                # Additional check for 4+ digit numbers in first position (likely years in wrong position)
                if first_part > 31:
                    return None
            except ValueError:
                return None
    
    try:
        # If already in ISO format, validate and return
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            datetime.strptime(date_str, '%Y-%m-%d')
            return date_str
        
        # Try MM/DD/YYYY format (most common)
        if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_str):
            parsed_date = datetime.strptime(date_str, '%m/%d/%Y').date()
            return parsed_date.isoformat()  # Returns YYYY-MM-DD
        
        # Try MM/YYYY format (common in credit reports)
        if re.match(r'^\d{1,2}/\d{4}$', date_str):
            parsed_date = datetime.strptime(f"{date_str}/01", '%m/%Y/%d').date()  # Default to 1st of month
            return parsed_date.isoformat()  # Returns YYYY-MM-DD
        
        # Try other common formats
        formats = ['%m-%d-%Y', '%Y/%m/%d', '%d/%m/%Y']
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt).date()
                return parsed_date.isoformat()
            except ValueError:
                continue
                
        logger.warning(f"⚠️ Unable to parse date format: '{date_str}'")
        return None
        
    except (ValueError, TypeError) as e:
        logger.warning(f"⚠️ Invalid date: '{date_str}' - {e}")
        return None


def validate_date_range(date_str: str, min_year: int = 1950, max_year: int = None) -> bool:
    """
    Validate that a date string represents a reasonable date within acceptable range.
    
    Args:
        date_str: Date string to validate
        min_year: Minimum acceptable year (default: 1950)
        max_year: Maximum acceptable year (default: current year + 1)
    
    Returns:
        bool: True if date is valid and within range
    """
    if not max_year:
        max_year = datetime.now().year + 1
    
    normalized_date = normalize_date_for_postgres(date_str)
    if not normalized_date:
        return False
    
    try:
        date_obj = datetime.strptime(normalized_date, '%Y-%m-%d').date()
        return min_year <= date_obj.year <= max_year
    except ValueError:
        return False


def format_date_for_display(date_str: str, format_type: str = "short") -> str:
    """
    Format a date string for display purposes.
    
    Args:
        date_str: Date string in ISO format or other parseable format
        format_type: "short" (MM/DD/YYYY), "long" (Month DD, YYYY), or "iso" (YYYY-MM-DD)
    
    Returns:
        str: Formatted date string or original string if parsing fails
    """
    normalized_date = normalize_date_for_postgres(date_str)
    if not normalized_date:
        return date_str
    
    try:
        date_obj = datetime.strptime(normalized_date, '%Y-%m-%d').date()
        
        if format_type == "short":
            return date_obj.strftime('%m/%d/%Y')
        elif format_type == "long":
            return date_obj.strftime('%B %d, %Y')
        elif format_type == "iso":
            return normalized_date
        else:
            return date_obj.strftime('%m/%d/%Y')  # Default to short format
            
    except ValueError:
        return date_str