import pytest
from datetime import date, datetime
from decimal import Decimal

from backend.services.validation_service import ValidationService, ValidationConfig
from backend.models.tradeline_models import Tradeline, ConsumerInfo
from backend.models.llm_models import ValidationIssue

class TestValidationService:
    
    @pytest.fixture
    def validation_service(self):
        config = ValidationConfig(
            min_confidence_score=0.7,
            max_reasonable_balance=Decimal('100000')
        )
        return ValidationService(config)
    
    @pytest.fixture
    def sample_tradeline(self):
        return Tradeline(
            creditor_name="Chase Bank",
            account_number="****5678",
            account_type="Credit Card",
            balance=Decimal("1234.56"),
            credit_limit=Decimal("5000.00"),
            payment_status="Current",
            date_opened=date(2020, 1, 15),
            date_closed=None,
            payment_history=["Current", "Current", "Current"],
            confidence_score=0.85
        )
    
    @pytest.fixture
    def sample_consumer_info(self):
        return ConsumerInfo(
            name="John Doe",
            ssn="XXX-XX-1234",
            date_of_birth=date(1980, 1, 15),
            addresses=[{
                "street": "123 Main St",
                "city": "Anytown", 
                "state": "CA",
                "zip": "12345"
            }],
            confidence_score=0.9
        )
    
    def test_validate_normalized_data_success(
        self, 
        validation_service, 
        sample_tradeline, 
        sample_consumer_info
    ):
        """Test successful validation of good data"""
        
        result = validation_service.validate_normalized_data(
            tradelines=[sample_tradeline],
            consumer_info=sample_consumer_info,
            job_id="test-job"
        )
        
        assert result.overall_confidence > 0.7
        assert result.validation_summary.total_tradelines == 1
        assert result.validation_summary.valid_tradelines >= 0
        assert len(result.issues_found) >= 0  # May have minor issues
    
    def test_validate_tradeline_with_issues(self, validation_service):
        """Test tradeline validation with various issues"""
        
        # Create problematic tradeline
        problematic_tradeline = Tradeline(
            creditor_name="",  # Missing creditor name
            account_number="****5678",
            account_type="Unknown",  # Unknown account type
            balance=Decimal("150000"),  # Excessive balance
            credit_limit=Decimal("5000"),  # Balance > limit
            payment_status="Current",
            date_opened=date(2025, 1, 1),  # Future date
            date_closed=date(2020, 1, 1),  # Closed before opened
            payment_history=[],
            confidence_score=0.3  # Low confidence
        )
        
        issues, suggestions = validation_service._validate_tradeline(problematic_tradeline, 0)
        
        # Should find multiple issues
        assert len(issues) > 0
        
        # Check for specific issue types
        issue_types = [issue.type for issue in issues]
        assert "missing_data" in issue_types  # Missing creditor name
        assert "data_range" in issue_types  # Excessive balance
        assert "date_error" in issue_types  # Future date
        assert "date_inconsistency" in issue_types  # Date logic error
    
    def test_validate_consumer_info_with_issues(self, validation_service):
        """Test consumer info validation with issues"""
        
        problematic_consumer = ConsumerInfo(
            name="",  # Missing name
            ssn="123-45-6789-INVALID",  # Invalid SSN format
            date_of_birth=date(2030, 1, 1),  # Future birth date
            addresses=[],  # No addresses
            confidence_score=0.5
        )
        
        issues, suggestions = validation_service._validate_consumer_info(problematic_consumer)
        
        assert len(issues) > 0
        
        issue_types = [issue.type for issue in issues]
        assert "missing_data" in issue_types
        assert "format_error" in issue_types
        assert "date_error" in issue_types
    
    def test_cross_validate_duplicates(self, validation_service):
        """Test cross-validation for duplicate detection"""
        
        # Create similar tradelines
        tradeline1 = Tradeline(
            creditor_name="Chase Bank",
            account_number="****5678",
            account_type="Credit Card",
            confidence_score=0.8
        )
        
        tradeline2 = Tradeline(
            creditor_name="Chase Bank", 
            account_number="****5678",
            account_type="Credit Card",
            confidence_score=0.8
        )
        
        issues, suggestions = validation_service._cross_validate_tradelines([tradeline1, tradeline2])
        
        # Should detect potential duplicate
        duplicate_issues = [issue for issue in issues if issue.type == "potential_duplicate"]
        assert len(duplicate_issues) > 0
    
    def test_calculate_quality_metrics(self, validation_service, sample_tradeline, sample_consumer_info):
        """Test quality metrics calculation"""
        
        # Create some validation issues
        issues = [
            ValidationIssue(
                type="data_quality",
                description="Test issue",
                severity="medium",
                tradeline_index=0
            )
        ]
        
        metrics = validation_service._calculate_quality_metrics(
            tradelines=[sample_tradeline],
            consumer_info=sample_consumer_info,
            issues=issues
        )
        
        assert 0.0 <= metrics.completeness <= 1.0
        assert 0.0 <= metrics.accuracy <= 1.0
        assert 0.0 <= metrics.consistency <= 1.0
        assert 0.0 <= metrics.reliability <= 1.0
    
    def test_monetary_value_validation(self, validation_service):
        """Test monetary value range validation"""
        
        # Test valid value
        issues = validation_service._validate_monetary_value(
            Decimal("5000"), "balance", 0, Decimal("0"), Decimal("100000")
        )
        assert len(issues) == 0
        
        # Test value too high
        issues = validation_service._validate_monetary_value(
            Decimal("200000"), "balance", 0, Decimal("0"), Decimal("100000")
        )
        assert len(issues) > 0
        assert any(issue.type == "data_range" for issue in issues)
        
        # Test negative value
        issues = validation_service._validate_monetary_value(
            Decimal("-100"), "balance", 0, Decimal("0"), Decimal("100000")
        )
        assert len(issues) > 0
    
    def test_date_validation(self, validation_service):
        """Test date logic validation"""
        
        from datetime import date, timedelta
        
        # Valid tradeline
        valid_tradeline = Tradeline(
            creditor_name="Test",
            account_type="Credit Card",
            date_opened=date(2020, 1, 1),
            date_closed=date(2023, 1, 1),
            confidence_score=0.8
        )
        
        issues = validation_service._validate_tradeline_dates(valid_tradeline, 0)
        assert len(issues) == 0
        
        # Invalid tradeline (closed before opened)
        invalid_tradeline = Tradeline(
            creditor_name="Test",
            account_type="Credit Card", 
            date_opened=date(2023, 1, 1),
            date_closed=date(2020, 1, 1),  # Before opened
            confidence_score=0.8
        )
        
        issues = validation_service._validate_tradeline_dates(invalid_tradeline, 0)
        assert len(issues) > 0
        assert any(issue.type == "date_inconsistency" for issue in issues)