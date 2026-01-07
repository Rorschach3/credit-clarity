"""
Unified Tradeline Normalizer
Combines bookkeeping from the previous tradeline normalizers and adds OCR corrections plus classifier-driven negative detection.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


class EnhancedTradelineNormalizer:
    """Normalizer that merges the prior tradeline_normalizer and improved_tradeline_normalizer logic."""

    OCR_CORRECTIONS = {
        '0': 'O',
        'O': '0',
        'l': '1',
        'I': '1',
        'S': '5',
        's': '5',
    }

    CREDIT_BUREAUS = {"experian": "Experian", "equifax": "Equifax", "transunion": "TransUnion"}

    ACCOUNT_TYPE_MAPPING = {
        "credit card": "Revolving",
        "store card": "Revolving",
        "revolving": "Revolving",
        "line of credit": "Revolving",
        "credit line": "Revolving",
        "auto loan": "Installment",
        "student loan": "Installment",
        "personal loan": "Installment",
        "mortgage": "Installment",
        "installment loan": "Installment",
        "installment": "Installment",
        "loan": "Installment",
    }

    ACCOUNT_STATUS_MAPPING = {
        "current": "Current",
        "current account": "Current",
        "open": "Current",
        "good standing": "Current",
        "paid as agreed": "Current",
        "up to date": "Current",
        "closed": "Closed",
        "paid": "Closed",
        "paid, closed": "Closed",
        "account closed": "Closed",
        "satisfied": "Closed",
        "late": "Late",
        "past due": "Late",
        "delinquent": "Late",
        "30 days late": "Late",
        "60 days late": "Late",
        "90 days late": "Late",
        "collection": "Collection",
        "in collection": "Collection",
        "charged off": "Collection",
        "charge off": "Collection",
        "write off": "Collection",
    }

    NEGATIVE_KEYWORD_WEIGHTS = {
        'charge off': 0.65,
        'charged off': 0.65,
        'paid charge off': 0.65,
        'chargeoff': 0.65,
        'charge-off': 0.65,
        'collection': 0.5,
        'collections': 0.5,
        'in collection': 0.5,
        'collection account': 0.5,
        'placed for collection': 0.5,
        'late': 0.35,
        'late payment': 0.4,
        'late 30': 0.45,
        'late 60': 0.45,
        'late 90': 0.45,
        'late 120': 0.45,
        '30 days late': 0.45,
        '60 days late': 0.45,
        '90 days late': 0.45,
        '120+ days late': 0.45,
        'past due': 0.45,
        'delinquent': 0.4,
        'delinquency': 0.4,
        'seriously delinquent': 0.45,
        'default': 0.5,
        'defaulted': 0.5,
        'in default': 0.5,
        'repossession': 0.55,
        'repo': 0.55,
        'repossessed': 0.55,
        'voluntary repossession': 0.55,
        'foreclosure': 0.55,
        'foreclosed': 0.55,
        'pre-foreclosure': 0.55,
        'settled': 0.4,
        'settlement': 0.4,
        'settled for less': 0.55,
        'settled less than full balance': 0.55,
        'bankruptcy': 0.6,
        'chapter 7': 0.6,
        'chapter 13': 0.6,
        'chapter 11': 0.6,
        'included in bankruptcy': 0.6,
        'discharged in bankruptcy': 0.6,
        'write off': 0.5,
        'written off': 0.5,
        'write-off': 0.5
    }

    COLLECTION_AGENCY_TOKENS = [
        "collection", "recovery", "portfolio", "midland", "cavalry", "lvnv", "resurgent", "radius"
    ]

    def normalize_tradeline(self, tradeline: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a single tradeline entry."""
        normalized = {
            'creditor_name': self._normalize_creditor_name(tradeline.get('creditor_name', '')),
            'account_number': self._normalize_account_number(tradeline.get('account_number', '')),
            'account_balance': self._normalize_currency(
                tradeline.get('account_balance', ''), field_name='account_balance'
            ),
            'credit_limit': self._normalize_currency(
                tradeline.get('credit_limit', ''), field_name='credit_limit'
            ),
            'monthly_payment': self._normalize_currency(
                tradeline.get('monthly_payment', ''), field_name='monthly_payment'
            ),
            # dates: normalized to ISO format and preserve original
            'date_opened': None,
            'date_opened_original': tradeline.get('date_opened', None),
            'date_opened_confidence': 0.0,
            'account_type': self._normalize_account_type(tradeline.get('account_type', '')),
            'account_status': self._normalize_account_status(tradeline.get('account_status', '')),
            'credit_bureau': self._normalize_credit_bureau(tradeline.get('credit_bureau', '')),
            'payment_history': tradeline.get('payment_history', ''),
            'comments': tradeline.get('comments', ''),
            'user_id': tradeline.get('user_id'),
        }

        # Classifier-driven negative detection
        # normalize dates with confidence
        parsed_date, date_conf = self._normalize_date(tradeline.get('date_opened', ''))
        normalized['date_opened'] = parsed_date
        normalized['date_opened_confidence'] = date_conf

        is_negative, confidence, indicators = self._determine_negative_status(normalized)
        normalized['is_negative'] = is_negative
        normalized['negative_confidence'] = confidence
        normalized['negative_indicators'] = indicators

        return normalized

    def normalize_tradelines(self, tradelines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize a batch of tradelines."""
        return [self.normalize_tradeline(tr) for tr in tradelines]

    def _normalize_creditor_name(self, value: str) -> Optional[str]:
        if not value or not str(value).strip():
            return None

        cleaned = self._apply_ocr_corrections(str(value)).upper()
        creditor_mappings = {
            "BANK 0F": "BANK OF",
            "CHAS[E3]": "CHASE",
            "CHAS[E3] BANK": "CHASE BANK",
            "CITI[B8]ANK": "CITIBANK",
            "AM[E3]RICAN EXPRESS": "AMERICAN EXPRESS",
            "W[E3]LLS FARG[O0]": "WELLS FARGO",
            "CAPITAL 0NE": "CAPITAL ONE",
            "CAPITAL ONE N.A.": "CAPITAL ONE",
            "SYNCHRONY BANK": "SYNCHRONY BANK",
            "DISCOVER": "DISCOVER BANK",
            "SELF FINANCIAL INC/ LEAD BANK": "SELF FINANCIAL INC/LEAD BANK",
        }

        for pattern, replacement in creditor_mappings.items():
            if re.search(pattern, cleaned, flags=re.IGNORECASE):
                cleaned = replacement
                break

        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        if cleaned.isdigit():
            return None

        return cleaned.title()

    def _normalize_account_number(self, value: str) -> Optional[str]:
        if not value or not str(value).strip():
            return None

        account = str(value)
        account = self._apply_ocr_corrections(account)
        cleaned = re.sub(r'[^A-Za-z0-9]', '', account)

        if len(cleaned) < 4 or not any(char.isdigit() for char in cleaned):
            return None

        return cleaned.upper()

    def _apply_ocr_corrections(self, value: str) -> str:
        corrected = value
        for wrong, right in self.OCR_CORRECTIONS.items():
            corrected = corrected.replace(wrong, right)
        return corrected

    def _normalize_currency(self, value: str, field_name: str = "") -> Optional[str]:
        if not value or not str(value).strip():
            return None

        text = str(value).strip()
        text = self._apply_ocr_corrections(text)
        text = re.sub(r'[$,\s]', '', text)

        is_negative = text.startswith('-') or ('(' in text and ')' in text)
        text = text.replace('(', '').replace(')', '').replace('-', '')

        if not text:
            return None

        try:
            amount = float(text)
        except ValueError:
            return None

        abs_amount = abs(amount)
        formatted = f"${abs_amount:,.2f}"

        return f"-{formatted}" if amount < 0 else formatted

    def _normalize_date(self, value: str) -> Tuple[Optional[str], float]:
        """Return (ISO_date_str_or_None, confidence_score[0.0-1.0])."""
        if not value or not str(value).strip():
            return None, 0.0

        text = str(value).strip()
        text = self._apply_ocr_corrections(text)
        text = text.replace('-', '/')

        confidence = 0.0

        patterns = [
            (r'^(\d{1,2})/(\d{1,2})/(\d{4})$', '%m/%d/%Y'),
            (r'^(\d{1,2})/(\d{2})$', '%m/%y'),
            (r'^(\d{4})/(\d{1,2})/(\d{1,2})$', '%Y/%m/%d'),
            (r'^(\d{1,2})-(\d{1,2})-(\d{4})$', '%m-%d-%Y'),
            (r'^(\d{4})-(\d{1,2})-(\d{1,2})$', '%Y-%m-%d'),
            (r'^[A-Za-z]{3} \d{1,2}, \d{4}$', '%b %d, %Y'),
        ]

        for pattern, fmt in patterns:
            match = re.match(pattern, text)
            if match:
                try:
                    parsed = datetime.strptime(text, fmt)
                    iso = parsed.strftime('%Y-%m-%d')
                    return iso, 1.0
                except Exception:
                    continue

        # relative dates
        rl = text.lower()
        if 'last month' in rl:
            dt = datetime.utcnow() - timedelta(days=30)
            return dt.strftime('%Y-%m-%d'), 0.6
        m = re.search(r'(\d+)\s*days?\s*ago', rl)
        if m:
            dt = datetime.utcnow() - timedelta(days=int(m.group(1)))
            return dt.strftime('%Y-%m-%d'), 0.6

        # year-only fallback
        year_match = re.search(r'(19|20)\d{2}', text)
        if year_match:
            year = int(year_match.group())
            return f"{year}-01-01", 0.5

        # cannot parse
        return None, 0.0

    def _normalize_account_type(self, value: str) -> str:
        if not value:
            return "Unknown"

        cleaned = self._apply_ocr_corrections(value).lower().strip()
        for key, mapped in self.ACCOUNT_TYPE_MAPPING.items():
            if key in cleaned:
                return mapped
        return "Revolving" if "card" in cleaned else "Installment"

    def _normalize_account_status(self, value: str) -> str:
        if not value:
            return "Unknown"

        cleaned = self._apply_ocr_corrections(value).lower().strip()
        for key, mapped in self.ACCOUNT_STATUS_MAPPING.items():
            if key in cleaned:
                return mapped
        return "Current" if "open" in cleaned else "Late" if "late" in cleaned else "Unknown"

    def _normalize_credit_bureau(self, value: str) -> Optional[str]:
        if not value:
            return None

        cleaned = str(value).lower()
        for key, bureau in self.CREDIT_BUREAUS.items():
            if key in cleaned:
                return bureau
        return None

    def _determine_negative_status(self, tradeline: Dict[str, Any]) -> Tuple[bool, float, List[str]]:
        score = 0.0
        indicators: List[str] = []
        status = (tradeline.get('account_status') or '').lower()
        payment_history = (tradeline.get('payment_history') or '').lower()
        comments = (tradeline.get('comments') or '').lower()
        creditor = (tradeline.get('creditor_name') or '').lower()

        for keyword, weight in self.NEGATIVE_KEYWORD_WEIGHTS.items():
            if keyword in status or keyword in payment_history or keyword in comments:
                score += weight
                indicators.append(keyword)

        if 'charge' in status and 'off' in status:
            score += 0.2
            indicators.append('status_charge_off')

        if any(token in creditor for token in self.COLLECTION_AGENCY_TOKENS):
            score += 0.35
            indicators.append('collection_agency_creditor')

        if any(str(i) in payment_history for i in (30, 60, 90, 120)):
            score += 0.15
            indicators.append('payment_history_late')

        balance = self._parse_numeric(tradeline.get('account_balance'))
        limit = self._parse_numeric(tradeline.get('credit_limit'))

        if balance is not None and balance > 0 and status == 'closed':
            score += 0.1
            indicators.append('closed_with_balance')

        if limit and balance and limit > 0 and balance > limit * 1.05:
            score += 0.1
            indicators.append('over_limit')

        confidence = min(1.0, score)
        is_negative = confidence >= 0.35
        return is_negative, confidence, indicators

    def _parse_numeric(self, value: Any) -> Optional[float]:
        if value is None:
            return None

        text = str(value)
        numeric = re.sub(r'[^\d.-]', '', text)
        try:
            return float(numeric)
        except ValueError:
            return None
