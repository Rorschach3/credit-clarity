import pytest

from utils.enhanced_tradeline_normalizer import EnhancedTradelineNormalizer
from services.tradeline_extraction.validation_pipeline import TradelineValidationPipeline


@pytest.fixture
def normalizer():
    return EnhancedTradelineNormalizer()


@pytest.fixture
def validator():
    return TradelineValidationPipeline()


def test_normalizer_detects_collection_status_negative(normalizer):
    raw_tradeline = {
        "creditor_name": "CAPITAL ONE BANK",
        "account_status": "Collection",
        "account_balance": "$2,500",
        "credit_limit": "$5,000",
        "monthly_payment": "$0.00",
        "credit_bureau": "TransUnion",
        "comments": "Account has charge off history"
    }

    normalized = normalizer.normalize_tradeline(raw_tradeline)

    assert normalized["is_negative"] is True
    assert normalized["negative_confidence"] >= 0.35
    assert any("collection" in indicator.lower() or "charge off" in indicator.lower()
               for indicator in normalized["negative_indicators"])


def test_normalizer_detects_late_status_negative(normalizer):
    raw_tradeline = {
        "creditor_name": "SYNCHRONY BANK",
        "account_status": "Late 60 Days",
        "payment_history": "60 days late, past due",
        "account_balance": "$1,750",
        "credit_limit": "$3,000",
        "monthly_payment": "$80.00",
        "credit_bureau": "Equifax"
    }

    normalized = normalizer.normalize_tradeline(raw_tradeline)

    assert normalized["is_negative"] is True
    assert normalized["negative_confidence"] >= 0.35
    assert any("late" in indicator.lower() for indicator in normalized["negative_indicators"])


def test_validator_warns_when_negative_flag_missing(validator):
    tradeline = {
        "creditor_name": "MIDLAND FUNDING",
        "account_number": "5555444433332222",
        "account_status": "Charged Off",
        "credit_bureau": "Experian",
        "is_negative": False,
        "monthly_payment": "$0.00",
        "account_balance": "$1,892"
    }

    result = validator.validate_tradeline(tradeline)

    assert result["valid"] is True
    assert any("negative" in warning.lower() for warning in result["warnings"])
    assert result["score"] < 1.0


def test_validator_accepts_consistent_negative_flag(validator):
    tradeline = {
        "creditor_name": "DISCOVER",
        "account_number": "9999888877776666",
        "account_status": "Collection",
        "credit_bureau": "Equifax",
        "is_negative": True,
        "monthly_payment": "$0.00",
        "account_balance": "$1,000"
    }

    result = validator.validate_tradeline(tradeline)

    assert result["valid"] is True
    assert not result["errors"]
    assert not result["warnings"]
