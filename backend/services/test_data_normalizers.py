import pytest # type: ignore
from decimal import Decimal
from datetime import date

from backend.utils.data_normalizers import (
    CurrencyNormalizer,
    DateNormalizer, 
    TextNormalizer,
    AccountNumberNormalizer,
    SSNNormalizer,
    PhoneNumberNormalizer,
    ComprehensiveNormalizer
)

class TestCurrencyNormalizer:
    
    def test_normalize_valid_currencies(self):
        """Test normalization of valid currency values"""
        
        # Test various formats
        assert CurrencyNormalizer.normalize("$1,234.56") == Decimal("1234.56")
        assert CurrencyNormalizer.normalize("1234.56") == Decimal("1234.56")
        assert CurrencyNormalizer.normalize("USD 1,234.56") == Decimal("1234.56")
        assert CurrencyNormalizer.normalize("1,234") == Decimal("1234")
        
        # Test negative values
        assert CurrencyNormalizer.normalize("($1,234.56)") == Decimal("-1234.56")
        assert CurrencyNormalizer.normalize("-$1,234.56") == Decimal("-1234.56")
        assert CurrencyNormalizer.normalize("1234.56CR") == Decimal("-1234.56")
    
    def test_normalize_invalid_currencies(self):
        """Test handling of invalid currency values"""
        
        assert CurrencyNormalizer.normalize("invalid") is None
        assert CurrencyNormalizer.normalize("") is None
        assert CurrencyNormalizer.normalize(None) is None
        assert CurrencyNormalizer.normalize("N/A") is None
        assert CurrencyNormalizer.normalize("--") is None
    
    def test_normalize_numeric_types(self):
        """Test normalization of numeric types"""
        
        assert CurrencyNormalizer.normalize(1234.56) == Decimal("1234.56")
        assert CurrencyNormalizer.normalize(1234) == Decimal("1234")
        assert CurrencyNormalizer.normalize(Decimal("1234.56")) == Decimal("1234.56")

class TestDateNormalizer:
    
    def test_normalize_valid_dates(self):
        """Test normalization of valid date formats"""
        
        # Test various formats
        assert DateNormalizer.normalize("2023-12-25") == date(2023, 12, 25)
        assert DateNormalizer.normalize("12/25/2023") == date(2023, 12, 25)
        assert DateNormalizer.normalize("25/12/2023") == date(2023, 12, 25)
        assert DateNormalizer.normalize("December 25, 2023") == date(2023, 12, 25)
        assert DateNormalizer.normalize("Dec 25, 2023") == date(2023, 12, 25)
        
        # Test partial dates
        assert DateNormalizer.normalize("12/2023") == date(2023, 12, 1)
        assert DateNormalizer.normalize("2023") == date(2023, 1, 1)
    
    def test_normalize_invalid_dates(self):
        """Test handling of invalid dates"""
        
        assert DateNormalizer.normalize("invalid") is None
        assert DateNormalizer.normalize("") is None
        assert DateNormalizer.normalize(None) is None
        assert DateNormalizer.normalize("N/A") is None
    
    def test_normalize_date_objects(self):
        """Test handling of existing date objects"""
        
        test_date = date(2023, 12, 25)
        assert DateNormalizer.normalize(test_date) == test_date
        
        from datetime import datetime
        test_datetime = datetime(2023, 12, 25, 10, 30)
        assert DateNormalizer.normalize(test_datetime) == date(2023, 12, 25)

class TestTextNormalizer:
    
    def test_normalize_creditor_names(self):
        """Test creditor name normalization"""
        
        assert TextNormalizer.normalize_creditor_name("CHASE") == "Chase Bank"
        assert TextNormalizer.normalize_creditor_name("CITI") == "Citibank"
        assert TextNormalizer.normalize_creditor_name("BOA") == "Bank of America"
        assert TextNormalizer.normalize_creditor_name("AMEX") == "American Express"
        
        # Test title casing for unknown creditors
        assert TextNormalizer.normalize_creditor_name("test bank") == "Test Bank"
    
    def test_normalize_account_types(self):
        """Test account type normalization"""
        
        assert TextNormalizer.normalize_account_type("credit card") == "Credit Card"
        assert TextNormalizer.normalize_account_type("CC") == "Credit Card"
        assert TextNormalizer.normalize_account_type("mortgage") == "Mortgage"
        assert TextNormalizer.normalize_account_type("auto loan") == "Auto Loan"
        assert TextNormalizer.normalize_account_type("student") == "Student Loan"
        
        # Test unknown types
        assert TextNormalizer.normalize_account_type("unknown type") == "Unknown Type"
    
    def test_normalize_payment_status(self):
        """Test payment status normalization"""
        
        assert TextNormalizer.normalize_payment_status("current") == "Current"
        assert TextNormalizer.normalize_payment_status("OK") == "Current"
        assert TextNormalizer.normalize_payment_status("30") == "30 days late"
        assert TextNormalizer.normalize_payment_status("60 days") == "60 days late"
        assert TextNormalizer.normalize_payment_status("charged off") == "Charged off"
        assert TextNormalizer.normalize_payment_status("collection") == "Collection"
    
    def test_normalize_person_names(self):
        """Test person name normalization"""
        
        assert TextNormalizer.normalize_name("john doe") == "John Doe"
        assert TextNormalizer.normalize_name("MARY JANE SMITH") == "Mary Jane Smith"
        assert TextNormalizer.normalize_name("mc donald") == "McDonald"  # Special case
        assert TextNormalizer.normalize_name("o'connor") == "O'Connor"  # Special case

class TestAccountNumberNormalizer:
    
    def test_normalize_account_numbers(self):
        """Test account number normalization"""
        
        # Test masking
        assert AccountNumberNormalizer.normalize("1234567890", mask_digits=True) == "******7890"
        assert AccountNumberNormalizer.normalize("1234", mask_digits=True) == "****"
        
        # Test no masking
        assert AccountNumberNormalizer.normalize("1234567890", mask_digits=False) == "1234567890"
        
        # Test already masked
        assert AccountNumberNormalizer.normalize("****7890", mask_digits=True) == "****7890"
    
    def test_normalize_invalid_account_numbers(self):
        """Test handling of invalid account numbers"""
        
        assert AccountNumberNormalizer.normalize("") is None
        assert AccountNumberNormalizer.normalize(None) is None

class TestSSNNormalizer:
    
    def test_normalize_ssn(self):
        """Test SSN normalization"""
        
        # Test masking
        assert SSNNormalizer.normalize("123456789", mask=True) == "XXX-XX-6789"
        assert SSNNormalizer.normalize("123-45-6789", mask=True) == "XXX-XX-6789"
        
        # Test no masking
        assert SSNNormalizer.normalize("123456789", mask=False) == "123-45-6789"
        
        # Test already masked
        assert SSNNormalizer.normalize("XXX-XX-6789", mask=True) == "XXX-XX-6789"
    
    def test_normalize_invalid_ssn(self):
        """Test handling of invalid SSNs"""
        
        assert SSNNormalizer.normalize("12345") is None  # Too short
        assert SSNNormalizer.normalize("") is None
        assert SSNNormalizer.normalize(None) is None

class TestPhoneNumberNormalizer:
    
    def test_normalize_phone_numbers(self):
        """Test phone number normalization"""
        
        # Test 10-digit US numbers
        assert PhoneNumberNormalizer.normalize("5551234567") == "(555) 123-4567"
        assert PhoneNumberNormalizer.normalize("(555) 123-4567") == "(555) 123-4567"
        assert PhoneNumberNormalizer.normalize("555-123-4567") == "(555) 123-4567"
        
        # Test 11-digit with country code
        assert PhoneNumberNormalizer.normalize("15551234567") == "(555) 123-4567"
        
        # Test 7-digit local
        assert PhoneNumberNormalizer.normalize("1234567") == "(000) 123-4567"
    
    def test_normalize_invalid_phone_numbers(self):
        """Test handling of invalid phone numbers"""
        
        assert PhoneNumberNormalizer.normalize("") is None
        assert PhoneNumberNormalizer.normalize(None) is None
        assert PhoneNumberNormalizer.normalize("abc") is None

class TestComprehensiveNormalizer:
    
    @pytest.fixture
    def normalizer(self):
        return ComprehensiveNormalizer()
    
    def test_normalize_tradeline_data(self, normalizer):
        """Test comprehensive tradeline normalization"""
        
        raw_data = {
            "creditor_name": "CHASE",
            "account_number": "1234567890",
            "account_type": "cc",
            "balance": "$1,234.56",
            "credit_limit": "5000.00",
            "payment_status": "current",
            "date_opened": "01/15/2020",
            "extra_field": "keep this"
        }
        
        normalized = normalizer.normalize_tradeline_data(raw_data)
        
        assert normalized["creditor_name"] == "Chase Bank"
        assert "****7890" in normalized["account_number"]
        assert normalized["account_type"] == "Credit Card"
        assert normalized["balance"] == Decimal("1234.56")
        assert normalized["payment_status"] == "Current"
        assert normalized["date_opened"] == date(2020, 1, 15)
        assert normalized["extra_field"] == "keep this"  # Pass-through
        
        # Check normalization stats
        assert "_normalization_stats" in normalized
        stats = normalized["_normalization_stats"]
        assert stats["fields_processed"] > 0
        assert stats["success_rate"] > 0
    
    def test_normalize_consumer_data(self, normalizer):
        """Test comprehensive consumer normalization"""
        
        raw_data = {
            "name": "john doe",
            "ssn": "123456789",
            "date_of_birth": "01/15/1980",
            "addresses": [{
                "street": "123 main st",
                "city": "anytown",
                "state": "ca",
                "zip": "12345"
            }],
            "phone_numbers": ["5551234567", "(555) 987-6543"]
        }
        
        normalized = normalizer.normalize_consumer_data(raw_data)
        
        assert normalized["name"] == "John Doe"
        assert normalized["ssn"] == "XXX-XX-6789"
        assert normalized["date_of_birth"] == date(1980, 1, 15)
        assert len(normalized["addresses"]) == 1
        assert normalized["addresses"][0]["city"] == "Anytown"
        assert len(normalized["phone_numbers"]) == 2
        assert "(555) 123-4567" in normalized["phone_numbers"]