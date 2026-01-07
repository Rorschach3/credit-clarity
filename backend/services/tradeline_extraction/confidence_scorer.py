"""Confidence scoring for tradeline validation.

Aggregates multiple component scores into a final score on 0-100 scale and
returns both score and contribution breakdown.
"""

from typing import Dict, Any, Tuple


class ConfidenceScorer:
    # weights as percentages
    FIELD_COMPLETENESS_W = 0.40
    FORMAT_VALIDITY_W = 0.30
    CROSS_VALIDATION_W = 0.20
    OCR_QUALITY_W = 0.10

    def compute_confidence(self, tradeline: Dict[str, Any], field_results: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        # Field completeness: required fields present
        required = ['creditor_name', 'account_number', 'account_status', 'credit_bureau']
        present = sum(1 for f in required if tradeline.get(f))
        field_completeness = present / len(required)

        # Format validity: proportion of field_results that are ok
        if not field_results:
            format_validity = 0.0
        else:
            ok_count = 0
            total = 0
            for k, v in field_results.items():
                total += 1
                if isinstance(v, dict):
                    if v.get('ok'):
                        ok_count += 1
                else:
                    # dates structure
                    total += 0
            format_validity = ok_count / max(1, total)

        # Cross validation: simple heuristics
        cross_score = 1.0
        status = (tradeline.get('account_status') or '').lower()
        balance = tradeline.get('account_balance')
        try:
            if status == 'closed' and balance:
                # prefer zero balance for closed accounts
                if abs(self._parse(balance)) > 0.01:
                    cross_score = 0.5
        except Exception:
            cross_score = 0.75

        # OCR quality: use provided ocr_confidence if exists on tradeline
        ocr_conf = tradeline.get('ocr_confidence')
        if isinstance(ocr_conf, (int, float)):
            ocr_quality = max(0.0, min(1.0, float(ocr_conf) / 100.0))
        else:
            ocr_quality = 0.8

        overall = (
            field_completeness * self.FIELD_COMPLETENESS_W
            + format_validity * self.FORMAT_VALIDITY_W
            + cross_score * self.CROSS_VALIDATION_W
            + ocr_quality * self.OCR_QUALITY_W
        )

        score_0_100 = round(max(0.0, min(1.0, overall)) * 100, 2)

        contributions = {
            'field_completeness': round(field_completeness * 100, 2),
            'format_validity': round(format_validity * 100, 2),
            'cross_validation': round(cross_score * 100, 2),
            'ocr_quality': round(ocr_quality * 100, 2),
        }

        return score_0_100, contributions

    def _parse(self, value: Any) -> float:
        if value is None:
            return 0.0
        s = str(value)
        s = s.replace('$', '').replace(',', '')
        try:
            return float(s)
        except Exception:
            return 0.0
