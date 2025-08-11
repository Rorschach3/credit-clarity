"""
Test tradeline parsing functionality
"""
import sys
sys.path.append('/mnt/c/projects/credit-clarity/backend')

from services.tradeline_extraction.tradeline_parser import (
    TransUnionTradelineParser,
    ParsedTradeline
)
from tests.test_fixtures.tradeline_test_data import (
    EXPECTED_TRADELINE_RECORDS,
    get_expected_tradeline_by_account_number,
    compare_tradeline_to_expected
)


class TestTransUnionTradelineParser:
    """Test tradeline parsing logic"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.parser = TransUnionTradelineParser()
        self.sample_text = """
        LENTEGRITY LLC
        Account Number: 2212311376****
        Account Type: Installment
        Account Status: Closed
        Date Opened: 12/29/2022
        Monthly Payment: $0
        Balance: $0
        
        CAPITAL ONE
        Account Number: 414709844770****
        Account Type: Revolving
        Account Status: Current
        Date Opened: 01/23/2013
        Credit Limit: $25,000
        Balance: $0
        """
    
    def test_parser_initialization(self):
        """Test parser initialization"""
        parser = TransUnionTradelineParser()
        
        assert 'revolving' in parser.account_type_mappings
        assert 'installment' in parser.account_type_mappings
        assert parser.account_type_mappings['revolving'] == 'Revolving'
        assert parser.account_type_mappings['installment'] == 'Installment'
        
        assert 'current' in parser.account_status_mappings
        assert 'closed' in parser.account_status_mappings
        assert parser.account_status_mappings['current'] == 'Current'
        assert parser.account_status_mappings['closed'] == 'Closed'
    
    def test_looks_like_creditor_name(self):
        """Test creditor name detection"""
        parser = TransUnionTradelineParser()
        
        # Should recognize as creditor names
        assert parser._looks_like_creditor_name("LENTEGRITY LLC") == True
        assert parser._looks_like_creditor_name("CAPITAL ONE") == True
        assert parser._looks_like_creditor_name("JPMCB CARD SERVICES") == True
        assert parser._looks_like_creditor_name("BANK OF AMERICA") == True
        
        # Should not recognize as creditor names
        assert parser._looks_like_creditor_name("Account Number: 123****") == False
        assert parser._looks_like_creditor_name("Account Type: Revolving") == False
        assert parser._looks_like_creditor_name("Balance: $0") == False
        assert parser._looks_like_creditor_name("TransUnion Credit Report") == False
    
    def test_split_into_creditor_sections(self):
        """Test splitting text into creditor sections"""
        parser = TransUnionTradelineParser()
        sections = parser._split_into_creditor_sections(self.sample_text)
        
        assert len(sections) == 2  # Should find LENTEGRITY LLC and CAPITAL ONE
        
        # Check first section contains LENTEGRITY LLC info
        assert "LENTEGRITY LLC" in sections[0]
        assert "2212311376****" in sections[0]
        
        # Check second section contains CAPITAL ONE info  
        assert "CAPITAL ONE" in sections[1]
        assert "414709844770****" in sections[1]
    
    def test_parse_single_tradeline_section(self):
        """Test parsing a single tradeline section"""
        parser = TransUnionTradelineParser()
        
        section = """
        LENTEGRITY LLC
        Account Number: 2212311376****
        Account Type: Installment
        Account Status: Closed
        Date Opened: 12/29/2022
        Monthly Payment: $0
        Balance: $0
        """
        
        tradeline = parser._parse_single_tradeline_section(section)
        
        assert tradeline is not None
        assert tradeline.creditor_name == "LENTEGRITY LLC"
        assert tradeline.account_number == "2212311376****"
        assert tradeline.account_type == "Installment"
        assert tradeline.account_status == "Closed"
        assert tradeline.date_opened == "12/29/2022"
        assert tradeline.monthly_payment == "$0"
        assert tradeline.account_balance == "$0"
    
    def test_format_account_number(self):
        """Test account number formatting"""
        parser = TransUnionTradelineParser()
        
        # Should preserve existing **** format
        assert parser._format_account_number("2212311376****") == "2212311376****"
        assert parser._format_account_number("414709844770****") == "414709844770****"
        
        # Should handle None/empty values
        assert parser._format_account_number("") is None
        assert parser._format_account_number("none") is None
        assert parser._format_account_number("N/A") is None
    
    def test_normalize_account_type(self):
        """Test account type normalization"""
        parser = TransUnionTradelineParser()
        
        assert parser._normalize_account_type("Revolving") == "Revolving"
        assert parser._normalize_account_type("revolving") == "Revolving"
        assert parser._normalize_account_type("Revolving Account") == "Revolving"
        assert parser._normalize_account_type("Installment") == "Installment"
        assert parser._normalize_account_type("installment") == "Installment"
        
        # Unknown types should pass through
        assert parser._normalize_account_type("Unknown") == "Unknown"
    
    def test_normalize_account_status(self):
        """Test account status normalization"""
        parser = TransUnionTradelineParser()
        
        assert parser._normalize_account_status("Current") == "Current"
        assert parser._normalize_account_status("current") == "Current"
        assert parser._normalize_account_status("Closed") == "Closed"
        assert parser._normalize_account_status("closed") == "Closed"
        assert parser._normalize_account_status("Open") == "Current"  # Maps to Current
        assert parser._normalize_account_status("Paid") == "Closed"   # Maps to Closed
    
    def test_format_date(self):
        """Test date formatting"""
        parser = TransUnionTradelineParser()
        
        # Test various input formats
        assert parser._format_date("12/29/2022") == "12/29/2022"
        assert parser._format_date("1/23/2013") == "01/23/2013"   # Should pad with zeros
        assert parser._format_date("2022-12-29") == "12/29/2022"  # Convert from YYYY-MM-DD
        
        # Test invalid dates
        assert parser._format_date("") is None
        assert parser._format_date("none") is None
        assert parser._format_date("invalid") is None
    
    def test_format_currency(self):
        """Test currency formatting"""
        parser = TransUnionTradelineParser()
        
        # Test various currency formats
        assert parser._format_currency("$0") == "$0"
        assert parser._format_currency("$25") == "$25"
        assert parser._format_currency("$25,000") == "$25,000"
        assert parser._format_currency("$142,000") == "$142,000"
        assert parser._format_currency("25000") == "$25,000"  # Add $ and comma
        
        # Test invalid amounts
        assert parser._format_currency("") is None
        assert parser._format_currency("none") is None
        assert parser._format_currency("N/A") is None
    
    def test_parse_tradelines_from_text(self):
        """Test parsing multiple tradelines from text"""
        parser = TransUnionTradelineParser()
        tradelines = parser.parse_tradelines_from_text(self.sample_text)
        
        assert len(tradelines) == 2
        
        # Check first tradeline (LENTEGRITY LLC)
        lentegrity = tradelines[0]
        assert lentegrity.creditor_name == "LENTEGRITY LLC"
        assert lentegrity.account_number == "2212311376****"
        assert lentegrity.account_type == "Installment"
        assert lentegrity.account_status == "Closed"
        
        # Check second tradeline (CAPITAL ONE)
        capital_one = tradelines[1]
        assert capital_one.creditor_name == "CAPITAL ONE"
        assert capital_one.account_number == "414709844770****"
        assert capital_one.account_type == "Revolving"
        assert capital_one.account_status == "Current"
        
        # Check that metadata was added
        for tradeline in tradelines:
            assert tradeline.id is not None
            assert tradeline.created_at is not None
            assert tradeline.updated_at is not None
            assert tradeline.credit_bureau == "TransUnion"
    
    def test_validate_parsed_tradeline(self):
        """Test tradeline validation"""
        parser = TransUnionTradelineParser()
        
        # Valid tradeline
        valid_tradeline = ParsedTradeline(
            creditor_name="CAPITAL ONE",
            account_number="414709844770****",
            account_type="Revolving",
            account_status="Current",
            date_opened="01/23/2013",
            monthly_payment="$0",
            credit_limit="$25,000",
            account_balance="$0"
        )
        
        result = parser.validate_parsed_tradeline(valid_tradeline)
        assert result['valid'] is True
        assert len(result['errors']) == 0
        
        # Invalid tradeline (missing creditor name)
        invalid_tradeline = ParsedTradeline(
            account_number="414709844770****",
            account_type="Revolving",
            account_status="Current"
        )
        
        result = parser.validate_parsed_tradeline(invalid_tradeline)
        assert result['valid'] is False
        assert "Missing required field: creditor_name" in result['errors']
    
    def test_parsed_tradeline_to_dict(self):
        """Test converting ParsedTradeline to dictionary"""
        tradeline = ParsedTradeline(
            creditor_name="CAPITAL ONE",
            account_number="414709844770****",
            account_type="Revolving",
            account_status="Current",
            date_opened="01/23/2013",
            monthly_payment="$0",
            credit_limit="$25,000",
            account_balance="$0"
        )
        
        tradeline_dict = tradeline.to_dict()
        
        assert isinstance(tradeline_dict, dict)
        assert tradeline_dict['creditor_name'] == "CAPITAL ONE"
        assert tradeline_dict['account_number'] == "414709844770****"
        assert tradeline_dict['credit_bureau'] == "TransUnion"
        assert 'id' in tradeline_dict
        assert 'created_at' in tradeline_dict
        assert 'updated_at' in tradeline_dict


def run_tests():
    """Run all tests"""
    test_class = TestTransUnionTradelineParser()
    test_class.setUp()
    
    print("Testing TransUnion Tradeline Parser...")
    
    print("1. Testing parser initialization...")
    test_class.test_parser_initialization()
    print("✓ Parser initialization test passed")
    
    print("2. Testing creditor name detection...")
    test_class.test_looks_like_creditor_name()
    print("✓ Creditor name detection test passed")
    
    print("3. Testing text splitting into sections...")
    test_class.test_split_into_creditor_sections()
    print("✓ Text splitting test passed")
    
    print("4. Testing single tradeline parsing...")
    test_class.test_parse_single_tradeline_section()
    print("✓ Single tradeline parsing test passed")
    
    print("5. Testing account number formatting...")
    test_class.test_format_account_number()
    print("✓ Account number formatting test passed")
    
    print("6. Testing account type normalization...")
    test_class.test_normalize_account_type()
    print("✓ Account type normalization test passed")
    
    print("7. Testing account status normalization...")
    test_class.test_normalize_account_status()
    print("✓ Account status normalization test passed")
    
    print("8. Testing date formatting...")
    test_class.test_format_date()
    print("✓ Date formatting test passed")
    
    print("9. Testing currency formatting...")
    test_class.test_format_currency()
    print("✓ Currency formatting test passed")
    
    print("10. Testing multiple tradeline parsing...")
    test_class.test_parse_tradelines_from_text()
    print("✓ Multiple tradeline parsing test passed")
    
    print("11. Testing tradeline validation...")
    test_class.test_validate_parsed_tradeline()
    print("✓ Tradeline validation test passed")
    
    print("12. Testing tradeline to dict conversion...")
    test_class.test_parsed_tradeline_to_dict()
    print("✓ Tradeline to dict conversion test passed")
    
    print("\n✓ All tradeline parser tests completed successfully!")


if __name__ == "__main__":
    run_tests()