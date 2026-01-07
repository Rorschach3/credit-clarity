"""
Validation pipeline for tradeline data.
Runs schema, business, and consistency checks to expose validation scores.
"""

import logging
from typing import Dict, Any, List, Tuple

from backend.services.tradeline_extraction.field_validators import FieldValidators
from backend.services.tradeline_extraction.confidence_scorer import ConfidenceScorer

logger = logging.getLogger(__name__)


class TradelineValidationPipeline:
    """Runs validation checks on normalized tradelines and computes confidence."""

    SEVERITY_CRITICAL = 'CRITICAL'
    SEVERITY_ERROR = 'ERROR'
    SEVERITY_WARNING = 'WARNING'
    SEVERITY_INFO = 'INFO'

    def __init__(self):
        self.validators = FieldValidators()
        self.scorer = ConfidenceScorer()

    def _severity_for_issues(self, errors: List[str], warnings: List[str]) -> str:
        if errors:
            return self.SEVERITY_CRITICAL
        if warnings:
            return self.SEVERITY_WARNING
        return self.SEVERITY_INFO

    def validate_tradeline(self, tradeline: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []
        infos: List[str] = []

        field_results = {}

        # Field-level validators
        bureau_ok, bureau_msg = self.validators.validate_bureau(tradeline.get('credit_bureau'))
        field_results['credit_bureau'] = {'ok': bureau_ok, 'msg': bureau_msg}
        if not bureau_ok:
            errors.append(bureau_msg)

        creditor_ok, creditor_msg = self.validators.validate_creditor(tradeline.get('creditor_name'))
        field_results['creditor_name'] = {'ok': creditor_ok, 'msg': creditor_msg}
        if not creditor_ok:
            errors.append(creditor_msg)

        account_ok, account_msg = self.validators.validate_account_number(
            tradeline.get('account_number'), tradeline.get('creditor_name')
        )
        field_results['account_number'] = {'ok': account_ok, 'msg': account_msg}
        if not account_ok:
            errors.append(account_msg)

        balance_ok, balance_msg = self.validators.validate_balance(tradeline.get('account_balance'), tradeline.get('account_status'))
        field_results['account_balance'] = {'ok': balance_ok, 'msg': balance_msg}
        if not balance_ok:
            warnings.append(balance_msg)

        # Date validation (opened / last activity / closed)
        date_checks, date_msgs = self.validators.validate_dates(
            tradeline.get('date_opened'), tradeline.get('date_of_last_activity'), tradeline.get('date_closed')
        )
        field_results['dates'] = date_checks
        for ok, msg, level in date_msgs:
            if not ok and level == self.SEVERITY_CRITICAL:
                errors.append(msg)
            elif not ok:
                warnings.append(msg)
            else:
                infos.append(msg)

        # Cross-field rules: closed -> zero balance
        try:
            status = (tradeline.get('account_status') or '').lower()
            balance_val = self.validators._parse_numeric(tradeline.get('account_balance'))
            if status == 'closed' and balance_val and abs(balance_val) > 0.01:
                warnings.append('Closed account with non-zero balance')
        except Exception:
            warnings.append('Unable to evaluate closed-account balance consistency')

        # Encoding/special character checks
        if any(isinstance(tradeline.get(k), str) and '\ufffd' in tradeline.get(k) for k in ['creditor_name', 'account_number']):
            warnings.append('Replacement character found in text fields (possible encoding/OCR issue)')

        # Compute confidence using field results and OCR quality if available
        confidence, contributions = self.scorer.compute_confidence(tradeline, field_results)

        severity = self._severity_for_issues(errors, warnings)

        validation_result = {
            'valid': len(errors) == 0 and confidence >= 0.5,
            'severity': severity,
            'confidence': confidence,
            'contributions': contributions,
            'errors': errors,
            'warnings': warnings,
            'infos': infos,
            'tradeline_id': tradeline.get('id'),
            'field_results': field_results,
        }

        logger.debug(
            f"Validation result for {tradeline.get('creditor_name', 'unknown')} | "
            f"confidence={confidence:.2f}, severity={severity}, errors={errors}, warnings={warnings}"
        )

        return validation_result

    def validate_batch(self, tradelines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        seen_accounts = set()
        for tr in tradelines:
            # check duplicates within batch
            acct = tr.get('account_number')
            if acct and acct in seen_accounts:
                tr.setdefault('duplicate_in_batch', True)
            else:
                if acct:
                    seen_accounts.add(acct)
            results.append(self.validate_tradeline(tr))
        return results
