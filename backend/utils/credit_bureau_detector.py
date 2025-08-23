"""
Credit Bureau Detection Utilities
Identifies credit bureaus from PDF text content
"""
import re
import logging
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)


def detect_credit_bureau(text_content: str) -> str:
    """
    Detect credit bureau from PDF text content.
    Searches for: Equifax, Experian, TransUnion
    Returns the first bureau found, or "Unknown" if none detected.
    """
    if not text_content:
        return "Unknown"
    
    # Convert to lowercase for case-insensitive matching
    text_lower = text_content.lower()
    
    # Credit bureau names to search for (in order of priority)
    bureaus = [
        ("equifax", "Equifax"),
        ("experian", "Experian"), 
        ("transunion", "TransUnion"),
        ("trans union", "TransUnion")  # Handle space variation
    ]
    
    # Search for each bureau name
    for search_term, bureau_name in bureaus:
        if search_term in text_lower:
            logger.info(f"🔍 Credit bureau detected: {bureau_name}")
            return bureau_name
    
    logger.info("🔍 No credit bureau detected, using 'Unknown'")
    return "Unknown"


def detect_all_bureaus(text_content: str) -> List[str]:
    """
    Detect all credit bureaus mentioned in text content.
    Returns list of all bureaus found.
    """
    if not text_content:
        return []
    
    text_lower = text_content.lower()
    found_bureaus = []
    
    # Credit bureau names to search for
    bureaus = [
        ("equifax", "Equifax"),
        ("experian", "Experian"), 
        ("transunion", "TransUnion"),
        ("trans union", "TransUnion")
    ]
    
    for search_term, bureau_name in bureaus:
        if search_term in text_lower and bureau_name not in found_bureaus:
            found_bureaus.append(bureau_name)
            logger.debug(f"🔍 Found bureau: {bureau_name}")
    
    return found_bureaus


def extract_bureau_with_confidence(text_content: str) -> Tuple[str, float]:
    """
    Detect credit bureau with confidence score.
    
    Returns:
        Tuple of (bureau_name, confidence_score)
        Confidence is 0.0-1.0 based on how clearly the bureau is identified
    """
    if not text_content:
        return "Unknown", 0.0
    
    text_lower = text_content.lower()
    
    # Patterns with different confidence levels
    high_confidence_patterns = [
        (r'equifax\s+(credit\s+report|report)', "Equifax", 0.95),
        (r'experian\s+(credit\s+report|report)', "Experian", 0.95),
        (r'transunion\s+(credit\s+report|report)', "TransUnion", 0.95),
        (r'trans\s+union\s+(credit\s+report|report)', "TransUnion", 0.95),
    ]
    
    medium_confidence_patterns = [
        (r'equifax', "Equifax", 0.75),
        (r'experian', "Experian", 0.75),
        (r'transunion', "TransUnion", 0.75),
        (r'trans\s+union', "TransUnion", 0.75),
    ]
    
    # Check high confidence patterns first
    for pattern, bureau, confidence in high_confidence_patterns:
        if re.search(pattern, text_lower):
            logger.info(f"🔍 High confidence bureau detection: {bureau} ({confidence})")
            return bureau, confidence
    
    # Check medium confidence patterns
    for pattern, bureau, confidence in medium_confidence_patterns:
        if re.search(pattern, text_lower):
            logger.info(f"🔍 Medium confidence bureau detection: {bureau} ({confidence})")
            return bureau, confidence
    
    logger.info("🔍 No credit bureau detected with confidence")
    return "Unknown", 0.0


def is_multi_bureau_report(text_content: str) -> bool:
    """
    Determine if the text contains information from multiple credit bureaus.
    """
    found_bureaus = detect_all_bureaus(text_content)
    return len(found_bureaus) > 1


def get_bureau_sections(text_content: str) -> dict:
    """
    Split text content into sections by credit bureau.
    
    Returns:
        dict: {bureau_name: text_section}
    """
    if not text_content:
        return {}
    
    sections = {}
    lines = text_content.split('\n')
    current_bureau = "Unknown"
    current_section = []
    
    for line in lines:
        line_lower = line.lower()
        
        # Check if this line indicates a new bureau section
        if "equifax" in line_lower:
            if current_section:
                sections[current_bureau] = '\n'.join(current_section)
            current_bureau = "Equifax"
            current_section = [line]
        elif "experian" in line_lower:
            if current_section:
                sections[current_bureau] = '\n'.join(current_section)
            current_bureau = "Experian"
            current_section = [line]
        elif "transunion" in line_lower or "trans union" in line_lower:
            if current_section:
                sections[current_bureau] = '\n'.join(current_section)
            current_bureau = "TransUnion"
            current_section = [line]
        else:
            current_section.append(line)
    
    # Add the last section
    if current_section:
        sections[current_bureau] = '\n'.join(current_section)
    
    return sections