"""Field-level validators for tradeline extraction.

Provides dedicated validation functions for bureau, creditor, account numbers,
balances, and dates. Returns tuples of (ok: bool, message: str) and richer
structures for dates.
"""

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple


class FieldValidators:
    VALID_BUREAUS = {'experian': 'Experian', 'equifax': 'Equifax', 'transunion': 'TransUnion', 'tu': 'TransUnion'}

    def validate_bureau(self, value: Any) -> Tuple[bool, str]:
        if not value:
            return False, 'Missing credit_bureau'

        text = str(value).strip().lower()
        # fuzzy corrections for common OCR errors
        normalized = text.replace(' ', '').replace('-', '')
        for key, canonical in self.VALID_BUREAUS.items():
            if key in normalized:
                return True, f'Normalized bureau to {canonical}'

        return False, f'Invalid credit bureau: {value}'

    def validate_creditor(self, value: Any) -> Tuple[bool, str]:
        if not value:
            return False, 'Missing creditor_name'
        text = str(value).strip()
        if len(text) < 3:
            return False, 'Creditor name too short'
        # detect placeholder/test data
        if re.search(r'^(test|placeholder|xxx|n/a)$', text, flags=re.IGNORECASE):
            return False, 'Placeholder creditor detected'
        return True, 'Creditor looks valid'

    def validate_account_number(self, value: Any, creditor: Any = None) -> Tuple[bool, str]:
        if not value:
            return False, 'Missing account_number'
        acct = str(value)
        acct_clean = re.sub(r'[^A-Za-z0-9]', '', acct)
        if len(acct_clean) < 4:
            return False, 'Account number too short or masked'

        # Luhn check for likely card numbers (13-19 digits)
        digits = re.sub(r'\D', '', acct_clean)
        if 13 <= len(digits) <= 19:
            if not self._luhn_check(digits):
                return False, 'Account number fails Luhn checksum'

        return True, 'Account number format OK'

    def _luhn_check(self, digits: str) -> bool:
        total = 0
        reverse = digits[::-1]
        for i, ch in enumerate(reverse):
            d = int(ch)
            if i % 2 == 1:
                d *= 2
                if d > 9:
                    d -= 9
            total += d
        return total % 10 == 0

    def validate_balance(self, value: Any, status: Any = None) -> Tuple[bool, str]:
        if value is None:
            return False, 'Missing account_balance'
        num = self._parse_numeric(value)
        if num is None:
            return False, f'Unable to parse balance: {value}'
        if num < -100000 or num > 1000000:
            return False, f'Balance out of reasonable range: {num}'
        if status and str(status).lower() == 'closed' and abs(num) > 0.01:
            return False, 'Closed account with non-zero balance'
        return True, 'Balance looks valid'

    def validate_dates(self, opened: Any, last_activity: Any, closed: Any) -> Tuple[Dict[str, Any], List[Tuple[bool, str, str]]]:
        msgs: List[Tuple[bool, str, str]] = []
        checks: Dict[str, Any] = {}

        def parse_date(v: Any) -> Optional[datetime]:
            if not v:
                return None
            if isinstance(v, datetime):
                return v
            s = str(v).strip()
            # handle common formats
            # try ISO
            for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%b %d, %Y', '%m/%Y', '%m/%y'):
                try:
                    dt = datetime.strptime(s, fmt)
                    # handle two-digit year patterns
                    if fmt == '%m/%y':
                        year = dt.year
                        if year >= 0 and year < 100:
                            # intelligent century detection
                            year = 1900 + (year if year > 30 else 2000 + year - 2000)
                    return dt
                except Exception:
                    continue
            # relative dates
            rl = s.lower()
            if 'last month' in rl:
                return datetime.utcnow() - timedelta(days=30)
            m = re.search(r'(\d+)\s*days?\s*ago', rl)
            if m:
                return datetime.utcnow() - timedelta(days=int(m.group(1)))
            # fallback: try extract year
            y = re.search(r'(19|20)\d{2}', s)
            if y:
                return datetime(int(y.group()), 1, 1)
            return None

        opened_dt = parse_date(opened)
        last_dt = parse_date(last_activity)
        closed_dt = parse_date(closed)

        checks['date_opened'] = opened_dt.isoformat() if opened_dt else None
        checks['date_of_last_activity'] = last_dt.isoformat() if last_dt else None
        checks['date_closed'] = closed_dt.isoformat() if closed_dt else None

        # validations and messages
        if opened_dt is None:
            msgs.append((False, 'date_opened missing or unparseable', 'CRITICAL'))
        else:
            if opened_dt.year < 1950 or opened_dt > datetime.utcnow():
                msgs.append((False, 'date_opened out of reasonable range', 'ERROR'))
            else:
                msgs.append((True, 'date_opened ok', 'INFO'))

        if last_dt and opened_dt and last_dt < opened_dt:
            msgs.append((False, 'date_of_last_activity earlier than date_opened', 'ERROR'))
        elif last_dt:
            msgs.append((True, 'date_of_last_activity ok', 'INFO'))

        if closed_dt and opened_dt and closed_dt < opened_dt:
            msgs.append((False, 'date_closed earlier than date_opened', 'CRITICAL'))
        elif closed_dt and closed_dt > datetime.utcnow():
            msgs.append((False, 'date_closed in the future', 'ERROR'))
        elif closed_dt:
            msgs.append((True, 'date_closed ok', 'INFO'))

        return checks, msgs

    def _parse_numeric(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            text = str(value)
            numeric = re.sub(r'[^0-9.-]', '', text)
            return float(numeric)
        except Exception:
            return None
