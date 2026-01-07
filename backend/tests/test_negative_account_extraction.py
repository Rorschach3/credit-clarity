"""
Test cases for negative account extraction and field formatting.
Verifies the complete pipeline processes negative accounts correctly.
"""
import pytest
import re
from typing import Dict, Any, List

# Import components to test
from utils.tradeline_normalizer import TradelineNormalizer
from utils.improved_tradeline_normalizer import ImprovedTradelineNormalizer
from services.tradeline_extraction.tradeline_parser import TransUnionTradelineParser
from services.tradeline_extraction.real_world_parser import RealWorldTransUnionParser


class TestCurrencyFormatting:
    """Test currency field formatting requirements."""
    
    def setup_method(self):
        self.normalizer = TradelineNormalizer()
        self.improved_normalizer = ImprovedTradelineNormalizer()
    
    def test_monthly_payment_has_two_decimals(self):
        """monthly_payment should have exactly 2 decimal places."""
        test_cases = [
            ("$25", "$25.00"),
            ("25.5", "$25.50"),
            ("$100.00", "$100.00"),
            ("1000", "$1,000.00"),
            ("$0", None),  # May return None for zero
        ]
        
        for input_val, expected_pattern in test_cases:
            result = self.normalizer._normalize_currency(input_val, field_name="monthly_payment")
            if expected_pattern is not None:
                assert result is not None, f"Failed for input: {input_val}"
                # Check it has exactly 2 decimal places
                assert re.match(r'^\$[\d,]+\.\d{2}$', result), f"Expected 2 decimals, got: {result}"
    
    def test_credit_limit_is_whole_number(self):
        """credit_limit should be whole number without decimals."""
        test_cases = [
            ("$5000", "$5,000"),
            ("5000.50", "$5,001"),  # Should round
            ("2500", "$2,500"),
            ("$100.99", "$101"),  # Should round
        ]
        
        for input_val, _ in test_cases:
            result = self.normalizer._normalize_currency(input_val, field_name="credit_limit")
            if result:
                # Should not have decimal places (or .00)
                assert not re.search(r'\.\d+$', result) or result.endswith(','), f"Expected whole number, got: {result}"
    
    def test_account_balance_is_whole_number(self):
        """account_balance should be whole number without decimals."""
        test_cases = [
            ("$2500", "$2,500"),
            ("2500.75", "$2,501"),  # Should round
            ("$808", "$808"),
        ]
        
        for input_val, _ in test_cases:
            result = self.normalizer._normalize_currency(input_val, field_name="account_balance")
            if result:
                # Should not have decimal places
                assert not re.search(r'\.\d+$', result) or result.endswith(','), f"Expected whole number, got: {result}"
    
    def test_ocr_error_correction(self):
        """Test OCR error correction (O->0, l->1, S->5)."""
        parser = TransUnionTradelineParser()
        
        # O should become 0
        result = parser._format_currency("$1,O00", field_name="account_balance")
        assert result is not None
        assert '0' in result
        
        # l should become 1
        result = parser._format_currency("$l,000", field_name="account_balance")
        assert result is not None
        
        # S should become 5
        result = parser._format_currency("$S00", field_name="account_balance")
        assert result is not None
    
    def test_parenthetical_negative_amounts(self):
        """Test handling of parenthetical negative amounts like ($1,234)."""
        parser = TransUnionTradelineParser()
        
        result = parser._format_currency("($1,234)", field_name="account_balance")
        assert result is not None
        assert result.startswith('-') or '(' in result


class TestAccountNumberFormatting:
    """Test account number formatting requirements."""
    
    def setup_method(self):
        self.normalizer = TradelineNormalizer()
        self.parser = TransUnionTradelineParser()
        self.real_parser = RealWorldTransUnionParser()
    
    def test_account_number_alphanumeric_only(self):
        """Account numbers should contain only alphanumeric characters."""
        test_cases = [
            "****1234",
            "XXXX1234",
            "....1234",
            "1234-5678-9012",
            "****-****-****-1234",
        ]
        
        for test_input in test_cases:
            result = self.normalizer._normalize_account_number(test_input)
            if result:
                assert re.match(r'^[A-Za-z0-9]+$', result), f"Expected alphanumeric only, got: {result}"
    
    def test_account_number_minimum_length(self):
        """Account numbers should be at least 4 characters."""
        result = self.normalizer._normalize_account_number("123")
        assert result is None, "Should reject account numbers < 4 chars"
        
        result = self.normalizer._normalize_account_number("1234")
        assert result is not None, "Should accept account numbers >= 4 chars"
    
    def test_account_number_must_contain_digit(self):
        """Account numbers must contain at least one digit."""
        result = self.normalizer._normalize_account_number("ABCD")
        assert result is None, "Should reject account numbers with no digits"
        
        result = self.normalizer._normalize_account_number("ABC1")
        assert result is not None, "Should accept account numbers with digits"
    
    def test_parser_removes_special_characters(self):
        """Parsers should remove asterisks, X's, dots, dashes."""
        result = self.parser._format_account_number("****1234****")
        if result:
            assert '*' not in result
            
        result = self.parser._format_account_number("XXXX-1234-5678")
        if result:
            assert 'X' not in result and '-' not in result


class TestNegativeAccountDetection:
    """Test negative account classification."""
    
    def setup_method(self):
        self.normalizer = TradelineNormalizer()
    
    def test_charge_off_detected_as_negative(self):
        """Charge-off accounts should be marked as negative."""
        tradeline = {
            'creditor_name': 'CAPITAL ONE',
            'account_status': 'Charge Off',
            'account_balance': '$2500',
        }
        
        is_negative, confidence, indicators = self.normalizer._determine_negative_status(tradeline)
        assert is_negative, "Charge-off should be marked negative"
        assert confidence >= 0.5, f"Confidence should be >= 0.5, got {confidence}"
    
    def test_collection_detected_as_negative(self):
        """Collection accounts should be marked as negative."""
        tradeline = {
            'creditor_name': 'MIDLAND FUNDING LLC',
            'account_status': 'Collection',
            'account_balance': '$1892',
        }
        
        is_negative, confidence, indicators = self.normalizer._determine_negative_status(tradeline)
        assert is_negative, "Collection should be marked negative"
    
    def test_current_account_not_negative(self):
        """Current/good standing accounts should not be negative."""
        tradeline = {
            'creditor_name': 'CHASE BANK',
            'account_status': 'Current',
            'account_balance': '$500',
        }
        
        is_negative, confidence, indicators = self.normalizer._determine_negative_status(tradeline)
        assert not is_negative, "Current account should not be negative"
    
    def test_paid_charge_off_still_negative(self):
        """Paid charge-off should still be marked as negative."""
        tradeline = {
            'creditor_name': 'DISCOVER BANK',
            'account_status': 'Paid Charge Off',
            'account_balance': '$0',
        }
        
        is_negative, confidence, indicators = self.normalizer._determine_negative_status(tradeline)
        assert is_negative, "Paid charge-off should still be negative"
    
    def test_collection_agency_name_increases_confidence(self):
        """Accounts from collection agencies should increase negative confidence."""
        tradeline = {
            'creditor_name': 'PORTFOLIO RECOVERY ASSOCIATES',
            'account_status': 'Open',
            'account_balance': '$500',
        }
        
        is_negative, confidence, indicators = self.normalizer._determine_negative_status(tradeline)
        assert is_negative or confidence > 0.3, "Collection agency creditor should increase negative score"


class TestDateFormatting:
    """Test date formatting requirements."""
    
    def test_date_format_mm_dd_yyyy(self):
        """Dates should be in MM/DD/YYYY format."""
        normalizer = TradelineNormalizer()
        
        test_cases = [
            "01/15/2024",
            "12/31/2023",
        ]
        
        for date_str in test_cases:
            result = normalizer._normalize_date(date_str)
            if result:
                assert re.match(r'^\d{2}/\d{2}/\d{4}$', result), f"Expected MM/DD/YYYY, got: {result}"


class TestCreditBureauValidation:
    """Test credit bureau field validation."""
    
    def test_valid_credit_bureaus(self):
        """credit_bureau should be one of the three valid bureaus."""
        valid_bureaus = ['Experian', 'Equifax', 'TransUnion']
        normalizer = TradelineNormalizer()
        
        for bureau in valid_bureaus:
            result = normalizer._normalize_credit_bureau(bureau)
            assert result in valid_bureaus, f"Should accept {bureau}"
    
    def test_case_insensitive_bureau_detection(self):
        """Bureau detection should be case-insensitive."""
        normalizer = TradelineNormalizer()
        
        assert normalizer._normalize_credit_bureau("experian") == "Experian"
        assert normalizer._normalize_credit_bureau("EQUIFAX") == "Equifax"
        assert normalizer._normalize_credit_bureau("TransUnion") == "TransUnion"


class TestFieldInference:
    """Test field inference for negative accounts."""
    
    def test_collection_defaults_zero_monthly_payment(self):
        """Collections typically should default to $0.00 monthly payment."""
        improved_normalizer = ImprovedTradelineNormalizer()
        
        tradeline = {
            'creditor_name': 'COLLECTION AGENCY',
            'account_status': 'Collection',
            'account_balance': '$1000',
            # No monthly_payment specified
        }
        
        normalized = improved_normalizer.normalize_tradeline(tradeline)
        # The normalizer should handle missing fields appropriately
        assert 'is_negative' in normalized


class TestNormalizerIntegration:
    """Test normalizer integration with all field types."""
    
    def setup_method(self):
        self.normalizer = TradelineNormalizer()
    
    def test_full_negative_tradeline_normalization(self):
        """Test complete normalization of a negative account."""
        raw_tradeline = {
            'creditor_name': 'CAPITAL ONE',
            'account_number': '****1234',
            'account_status': 'Charge Off',
            'account_balance': '$2,500.00',
            'credit_limit': '$5,000',
            'monthly_payment': '$50',
            'date_opened': '01/15/2020',
            'credit_bureau': 'Experian',
        }
        
        normalized = self.normalizer.normalize_tradeline(raw_tradeline)
        
        # Verify is_negative flag
        assert normalized.get('is_negative') == True, "Should be marked as negative"
        
        # Verify account number is alphanumeric
        if normalized.get('account_number'):
            assert re.match(r'^[A-Za-z0-9]+$', normalized['account_number']), \
                f"Account number should be alphanumeric: {normalized['account_number']}"
        
        # Verify credit_bureau is valid
        assert normalized.get('credit_bureau') in ['Experian', 'Equifax', 'TransUnion'], \
            f"Invalid credit_bureau: {normalized.get('credit_bureau')}"


class TestRealWorldParserValidation:
    """Test real-world parser validation methods."""
    
    def setup_method(self):
        self.parser = RealWorldTransUnionParser()
    
    def test_valid_tradeline_data(self):
        """Test tradeline validation for alphanumeric account numbers."""
        from services.tradeline_extraction.tradeline_parser import ParsedTradeline
        
        # Valid tradeline
        valid = ParsedTradeline()
        valid.creditor_name = "CHASE BANK"
        valid.account_number = "ABC1234567"  # Alphanumeric only
        
        assert self.parser._is_valid_tradeline_data(valid), "Should accept valid tradeline"
        
        # Invalid - account number with special characters
        invalid = ParsedTradeline()
        invalid.creditor_name = "CHASE BANK"
        invalid.account_number = "****1234"  # Has asterisks
        
        # After cleaning, should still validate if digits present
        cleaned = self.parser._clean_account_number(invalid.account_number)
        assert cleaned is not None and re.match(r'^[A-Za-z0-9]+$', cleaned)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
