#!/usr/bin/env python3
"""
Test the fixes made to tradeline processing
"""

import sys
import os
sys.path.append(os.getcwd())

from utils.field_validator import field_validator

def test_account_number_validation():
    """Test the improved account number validation"""
    print("🧪 Testing Account Number Validation Fixes...")
    
    test_cases = [
        "****1234",  # Should pass
        "636992104989****",  # Should pass now (was failing)
        "CBA0000000001497****",  # Should pass now
        "406095548379****",  # Should pass now
        "524306003974****",  # Should pass now
        "755678****",  # Should pass now
        "64161****",  # Should pass now
    ]
    
    for account_number in test_cases:
        is_valid, confidence, errors = field_validator.validate_account_number(account_number)
        print(f"  {account_number}: {'✅' if is_valid else '❌'} Valid={is_valid}, Confidence={confidence:.2f}, Errors={errors}")

def test_tradeline_validation():
    """Test full tradeline validation"""
    print("\n🧪 Testing Full Tradeline Validation...")
    
    # Test tradeline similar to what was extracted
    test_tradeline = {
        "creditor_name": "SYNCB/CARE CREDIT",
        "account_balance": "$640",
        "credit_limit": "$3,500",
        "monthly_payment": "$30",
        "account_number": "524306003974****",
        "date_opened": "08/27/2023",
        "account_type": "Credit Card",
        "account_status": "Current Account",
        "credit_bureau": "TransUnion",
        "is_negative": False
    }
    
    result = field_validator.validate_tradeline(test_tradeline)
    print(f"  Validation Result:")
    print(f"    - Is Valid: {result['is_valid']}")
    print(f"    - Confidence Score: {result['confidence_score']:.3f}")
    print(f"    - Errors: {result['errors']}")
    print(f"    - Warnings: {result['warnings']}")

if __name__ == "__main__":
    test_account_number_validation()
    test_tradeline_validation()
    print("\n✅ Test completed!")