#!/usr/bin/env python3
"""
Test script for enhanced tradeline extraction
"""

import sys
import os
import logging

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from services.enhanced_extraction_service import EnhancedExtractionService
from enhanced_bureau_detection import EnhancedBureauDetector

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_enhanced_extraction():
    """Test enhanced extraction with sample credit report text"""
    
    # Sample credit report text (simplified)
    sample_text = """
    TransUnion Credit Report
    
    CHASE BANK USA, N.A.
    Account Number: ****1234
    Credit Card
    Current Balance: $1,250.00
    Credit Limit: $5,000.00
    Payment Status: Current
    Date Opened: 01/15/2020
    Monthly Payment: $35.00
    
    CAPITAL ONE BANK USA, N.A.
    Account Number: ****5678
    Credit Card
    Balance: $500.00
    High Credit: $2,500.00
    Payment Status: Current
    Opened: 03/22/2019
    
    WELLS FARGO AUTO
    Account Number: ****9012
    Auto Loan
    Current Balance: $15,000.00
    Credit Limit: $25,000.00
    Payment Status: Current
    Date Opened: 06/10/2021
    Monthly Payment: $320.00
    """
    
    logger.info("Testing Enhanced Extraction Service")
    
    # Initialize services
    extraction_service = EnhancedExtractionService()
    bureau_detector = EnhancedBureauDetector()
    
    # Test bureau detection
    logger.info("=" * 50)
    logger.info("Testing Bureau Detection")
    bureau, confidence, evidence = bureau_detector.detect_credit_bureau(sample_text)
    logger.info(f"Detected Bureau: {bureau}")
    logger.info(f"Confidence: {confidence:.2f}")
    logger.info(f"Evidence: {evidence}")
    
    # Test enhanced extraction
    logger.info("=" * 50)
    logger.info("Testing Enhanced Extraction")
    tradelines = extraction_service.extract_enhanced_tradelines(sample_text, bureau)
    
    logger.info(f"Extracted {len(tradelines)} tradelines:")
    for i, tradeline in enumerate(tradelines, 1):
        logger.info(f"\nTradeline {i}:")
        logger.info(f"  Creditor: {tradeline.get('creditor_name', 'N/A')}")
        logger.info(f"  Account Number: {tradeline.get('account_number', 'N/A')}")
        logger.info(f"  Account Type: {tradeline.get('account_type', 'N/A')}")
        logger.info(f"  Balance: {tradeline.get('current_balance', 'N/A')}")
        logger.info(f"  Credit Limit: {tradeline.get('credit_limit', 'N/A')}")
        logger.info(f"  Monthly Payment: {tradeline.get('monthly_payment', 'N/A')}")
        logger.info(f"  Status: {tradeline.get('payment_status', 'N/A')}")
        logger.info(f"  Date Opened: {tradeline.get('date_opened', 'N/A')}")
        logger.info(f"  Confidence: {tradeline.get('confidence_score', 0):.2f}")
    
    # Test OCR correction
    logger.info("=" * 50)
    logger.info("Testing OCR Correction")
    
    corrupted_text = "Credltor: CHASE BANK, Baiance: $1,250.00, Lirnit: $5,000.00"
    corrected_text = extraction_service.fix_ocr_errors(corrupted_text)
    logger.info(f"Original: {corrupted_text}")
    logger.info(f"Corrected: {corrected_text}")
    
    # Test field extraction patterns
    logger.info("=" * 50)
    logger.info("Testing Field Pattern Matching")
    
    test_fields = [
        ("account_number", "Account Number: ****1234"),
        ("current_balance", "Current Balance: $1,250.00"),
        ("credit_limit", "Credit Limit: $5,000.00"),
        ("monthly_payment", "Monthly Payment: $35.00"),
        ("date_opened", "Date Opened: 01/15/2020"),
        ("payment_status", "Payment Status: Current")
    ]
    
    for field_name, test_text in test_fields:
        patterns = extraction_service.field_patterns.get(field_name, [])
        extracted_value = extraction_service._extract_field_value(test_text, patterns, field_name)
        logger.info(f"{field_name}: '{test_text}' → '{extracted_value}'")
    
    logger.info("=" * 50)
    logger.info("Enhanced Extraction Test Complete")

if __name__ == "__main__":
    test_enhanced_extraction()