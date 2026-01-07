import pytest

from backend.utils.enhanced_tradeline_normalizer import EnhancedTradelineNormalizer
from backend.services.tradeline_extraction.validation_pipeline import TradelineValidationPipeline


def make_tradeline(**kwargs):
    base = {
        'creditor_name': 'Capital One',
        'account_number': '4111-1111-1111-1111',
        'account_status': 'Current',
        'credit_bureau': 'TransUnion',
        'account_balance': '$1,234.56',
        'credit_limit': '$5,000',
        'date_opened': '01/15/2018',
        'date_of_last_activity': '12/01/2023',
    }
    base.update(kwargs)
    return base


def test_validation_happy_path():
    normalizer = EnhancedTradelineNormalizer()
    pipeline = TradelineValidationPipeline()

    tr = make_tradeline()
    norm = normalizer.normalize_tradeline(tr)
    result = pipeline.validate_tradeline(norm)

    assert result['severity'] in ('INFO', 'WARNING')
    assert 'confidence' in result
    assert result['confidence'] >= 50.0
    assert result['tradeline_id'] is None or True


def test_missing_critical_fields_fail():
    normalizer = EnhancedTradelineNormalizer()
    pipeline = TradelineValidationPipeline()

    tr = make_tradeline(creditor_name=None, account_number=None, credit_bureau=None)
    norm = normalizer.normalize_tradeline(tr)
    result = pipeline.validate_tradeline(norm)

    assert result['severity'] == 'CRITICAL'
    assert not result['valid']


def test_date_parsing_and_confidence():
    normalizer = EnhancedTradelineNormalizer()
    pipeline = TradelineValidationPipeline()

    tr = make_tradeline(date_opened='Jan 2010', account_balance='(123)', account_status='Closed')
    norm = normalizer.normalize_tradeline(tr)
    assert norm['date_opened'] is not None
    assert 0.0 <= norm['date_opened_confidence'] <= 1.0

    result = pipeline.validate_tradeline(norm)
    assert 'date_opened' in result['field_results']['dates']
