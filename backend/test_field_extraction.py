#!/usr/bin/env python3
"""
Test script for enhanced credit report field extraction
Tests the new field mapping and validation improvements
"""

from utils.credit_report_field_mappings import field_mapper
from utils.field_validator import field_validator

def test_credit_limit_extraction():
    """Test credit limit extraction with various formats"""
    print("🧪 Testing Credit Limit Extraction:")
    
    test_cases = [
        "High Credit: $2,500.00",
        "Credit Limit $5,000",
        "Limit: $1,200.50", 
        "Maximum: $3,000",
        "Original Amount: $4,500.00",
        "Credit Line: $10,000"
    ]
    
    for test_case in test_cases:
        result = field_mapper.extract_credit_limit(test_case)
        print(f"  '{test_case}' → {result}")
    print()

def test_monthly_payment_extraction():
    """Test monthly payment extraction with various formats"""
    print("🧪 Testing Monthly Payment Extraction:")
    
    test_cases = [
        "Monthly Payment: $125.00",
        "Payment $89.50",
        "Min Payment: $45.00",
        "Payment Amount: $200.25",
        "Minimum: $35"
    ]
    
    for test_case in test_cases:
        result = field_mapper.extract_monthly_payment(test_case)
        print(f"  '{test_case}' → {result}")
    print()

def test_account_type_extraction():
    """Test account type extraction and mapping"""
    print("🧪 Testing Account Type Extraction:")
    
    test_cases = [
        ("Credit Card info", "CHASE BANK"),
        ("Auto Loan details", "FORD CREDIT"),
        ("R - Revolving account", "CAPITAL ONE"),
        ("I - Installment loan", "PERSONAL FINANCE"),
        ("Student loan info", "NAVIENT"),
        ("Mortgage details", "QUICKEN LOANS")
    ]
    
    for text, creditor in test_cases:
        result = field_mapper.extract_account_type(text, creditor)
        print(f"  '{text}' + '{creditor}' → {result}")
    print()

def test_field_validation():
    """Test field validation and confidence scoring"""
    print("🧪 Testing Field Validation:")
    
    sample_tradeline = {
        "creditor_name": "CHASE BANK",
        "account_balance": "$1,234.56",
        "credit_limit": "$5,000.00",
        "monthly_payment": "$125.00",
        "account_number": "****1234",
        "date_opened": "01/15/2020",
        "account_type": "Credit Card",
        "account_status": "Current",
        "credit_bureau": "Experian",
        "is_negative": False
    }
    
    validation_result = field_validator.validate_tradeline(sample_tradeline)
    
    print(f"  Overall Valid: {validation_result['is_valid']}")
    print(f"  Confidence Score: {validation_result['confidence_score']:.2f}")
    print(f"  Errors: {len(validation_result['errors'])}")
    print(f"  Warnings: {len(validation_result['warnings'])}")
    
    if validation_result['warnings']:
        print("  Warnings:")
        for warning in validation_result['warnings']:
            print(f"    - {warning}")
    print()

def test_invalid_tradeline():
    """Test validation with invalid/problematic data"""
    print("🧪 Testing Invalid Tradeline Validation:")
    
    invalid_tradeline = {
        "creditor_name": "",  # Missing
        "account_balance": "$50,000.00",  # High balance
        "credit_limit": "$1,000.00",  # Lower than balance
        "monthly_payment": "$100,000.00",  # Unrealistic payment
        "account_number": "invalid",  # Bad format
        "date_opened": "13/45/2025",  # Invalid date
        "account_type": "Unknown Type",  # Invalid type
        "account_status": "Weird Status",
        "credit_bureau": "Fake Bureau",
        "is_negative": False
    }
    
    validation_result = field_validator.validate_tradeline(invalid_tradeline)
    
    print(f"  Overall Valid: {validation_result['is_valid']}")
    print(f"  Confidence Score: {validation_result['confidence_score']:.2f}")
    print(f"  Errors ({len(validation_result['errors'])}):")
    for error in validation_result['errors']:
        print(f"    - {error}")
    print(f"  Warnings ({len(validation_result['warnings'])}):")
    for warning in validation_result['warnings']:
        print(f"    - {warning}")
    print()

def test_real_world_text():
    """Test with realistic credit report text"""
    print("🧪 Testing Real-World Credit Report Text:")
    
    sample_text = """
    CHASE BANK USA, N.A.
    Account Number: ****1234
    Account Type: R - Revolving
    Date Opened: 01/15/2018
    High Credit: $5,000
    Current Balance: $1,250.75
    Payment: $125.00
    Status: Current
    
    FORD MOTOR CREDIT COMPANY
    Account Number: ****5678
    Account Type: I - Installment
    Date Opened: 03/20/2019
    Original Amount: $25,000.00
    Current Balance: $18,500.00
    Payment Amount: $389.50
    Status: Current
    """
    
    # Test individual field extractions
    print("  Credit Limit Extractions:")
    credit_limits = []
    for line in sample_text.split('\n'):
        result = field_mapper.extract_credit_limit(line.strip())
        if result:
            credit_limits.append(result)
            print(f"    '{line.strip()}' → {result}")
    
    print("  Monthly Payment Extractions:")
    payments = []
    for line in sample_text.split('\n'):
        result = field_mapper.extract_monthly_payment(line.strip())
        if result:
            payments.append(result)
            print(f"    '{line.strip()}' → {result}")
    
    print("  Account Type Extractions:")
    for line in sample_text.split('\n'):
        if 'CHASE' in line or 'FORD' in line:
            creditor = line.strip()
            for text_line in sample_text.split('\n'):
                result = field_mapper.extract_account_type(text_line, creditor)
                if result and result != 'credit_card':  # Skip default
                    print(f"    '{text_line.strip()}' + '{creditor}' → {result}")
                    break
    print()

if __name__ == "__main__":
    print("🚀 Credit Report Field Extraction Test Suite")
    print("=" * 50)
    
    test_credit_limit_extraction()
    test_monthly_payment_extraction() 
    test_account_type_extraction()
    test_field_validation()
    test_invalid_tradeline()
    test_real_world_text()
    
    print("✅ All tests completed!")