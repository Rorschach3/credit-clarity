from decimal import Decimal, InvalidOperation
from datetime import date, datetime
import re
from typing import Optional, Any, Dict, List, Union

class CurrencyNormalizer:
    @staticmethod
    def normalize(value: Any) -> Optional[Decimal]:
        if value is None:
            return None
        if isinstance(value, Decimal):
            return value
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        try:
            s = str(value).strip().upper()
            if s in {"", "N/A", "--", "INVALID"}:
                return None
            # Remove currency symbols and letters
            s = re.sub(r"[^0-9\.\-,\(\)]", "", s)
            # Handle negative in parentheses or CR
            negative = False
            if s.startswith("(") and s.endswith(")"):
                negative = True
                s = s[1:-1]
            if "CR" in str(value).upper():
                negative = True
                s = s.replace("CR", "")
            s = s.replace(",", "")
            d = Decimal(s)
            if s.startswith("-"):
                negative = True
            if negative:
                d = -abs(d)
            return d
        except (InvalidOperation, ValueError, AttributeError):
            return None

class DateNormalizer:
    @staticmethod
    def normalize(value: Any) -> Optional[date]:
        if value is None:
            return None
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        s = str(value).strip()
        if s in {"", "N/A"}:
            return None
        # Try various formats
        fmts = [
            "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y",
            "%m/%Y", "%Y"
        ]
        for fmt in fmts:
            try:
                dt = datetime.strptime(s, fmt)
                if fmt == "%m/%Y":
                    return date(dt.year, dt.month, 1)
                if fmt == "%Y":
                    return date(dt.year, 1, 1)
                return dt.date()
            except Exception:
                continue
        return None

class TextNormalizer:
    CREDITOR_MAP = {
        "CHASE": "Chase Bank",
        "CITI": "Citibank",
        "BOA": "Bank of America",
        "AMEX": "American Express",
    }
    ACCOUNT_TYPE_MAP = {
        "CREDIT CARD": "Credit Card",
        "CC": "Credit Card",
        "MORTGAGE": "Mortgage",
        "AUTO LOAN": "Auto Loan",
        "STUDENT": "Student Loan",
        "STUDENT LOAN": "Student Loan",
    }
    PAYMENT_STATUS_MAP = {
        "CURRENT": "Current",
        "OK": "Current",
        "30": "30 days late",
        "30 DAYS": "30 days late",
        "60": "60 days late",
        "60 DAYS": "60 days late",
        "CHARGED OFF": "Charged off",
        "COLLECTION": "Collection"
    }
    @staticmethod
    def normalize_creditor_name(name: str) -> str:
        if not name:
            return ""
        key = name.strip().upper()
        if key in TextNormalizer.CREDITOR_MAP:
            return TextNormalizer.CREDITOR_MAP[key]
        # Title case fallback
        return " ".join([w.capitalize() for w in key.split()])
    @staticmethod
    def normalize_account_type(t: str) -> str:
        if not t:
            return "Unknown Type"
        key = t.strip().upper()
        return TextNormalizer.ACCOUNT_TYPE_MAP.get(key, "Unknown Type")
    @staticmethod
    def normalize_payment_status(status: str) -> str:
        if not status:
            return ""
        key = status.strip().upper()
        # Try to match number of days late
        if re.match(r"^\d+$", key):
            return f"{int(key)} days late"
        for k, v in TextNormalizer.PAYMENT_STATUS_MAP.items():
            if k in key:
                return v
        return status.capitalize()
    @staticmethod
    def normalize_name(name: str) -> str:
        if not name:
            return ""
        # Special cases
        def special_case(word):
            if word.lower() in {"mc", "o'"}:
                return word.capitalize()
            return word.capitalize()
        # Handle O'Connor, McDonald, etc.
        parts = re.split(r"[\s\-]", name)
        result = []
        for part in parts:
            if "'" in part:
                subparts = part.split("'")
                result.append("'".join([p.capitalize() for p in subparts]))
            elif part.lower().startswith("mc") and len(part) > 2:
                result.append("Mc" + part[2:].capitalize())
            else:
                result.append(part.capitalize())
        return " ".join(result)

class AccountNumberNormalizer:
    @staticmethod
    def normalize(number: str, mask_digits: bool = True) -> Optional[str]:
        if not number:
            return None
        s = str(number)
        if mask_digits:
            if "*" in s:
                return s
            if len(s) <= 4:
                return "*" * len(s)
            return "*" * (len(s) - 4) + s[-4:]
        return s

class SSNNormalizer:
    @staticmethod
    def normalize(ssn: str, mask: bool = True) -> Optional[str]:
        if not ssn or len(ssn) < 9:
            return None
        s = re.sub(r"[^\dX]", "", str(ssn))
        if len(s) == 9:
            if mask:
                return f"XXX-XX-{s[-4:]}"
            else:
                return f"{s[:3]}-{s[3:5]}-{s[5:]}"
        if s.startswith("XXX") or s.startswith("xxx"):
            return "XXX-XX-" + s[-4:]
        return None

class PhoneNumberNormalizer:
    @staticmethod
    def normalize(phone: str) -> Optional[str]:
        if not phone:
            return None
        s = re.sub(r"[^\d]", "", str(phone))
        if len(s) == 11 and s.startswith("1"):
            s = s[1:]
        if len(s) == 10:
            return f"({s[:3]}) {s[3:6]}-{s[6:]}"
        if len(s) == 7:
            return f"(000) {s[:3]}-{s[3:]}"
        return None

class ComprehensiveNormalizer:
    def normalize_tradeline_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = dict(data)
        stats = {"fields_processed": 0, "success_rate": 0}
        # Normalize known fields
        if "creditor_name" in result:
            result["creditor_name"] = TextNormalizer.normalize_creditor_name(result["creditor_name"])
            stats["fields_processed"] += 1
        if "account_number" in result:
            result["account_number"] = AccountNumberNormalizer.normalize(result["account_number"])
            stats["fields_processed"] += 1
        if "account_type" in result:
            result["account_type"] = TextNormalizer.normalize_account_type(result["account_type"])
            stats["fields_processed"] += 1
        if "balance" in result:
            result["balance"] = CurrencyNormalizer.normalize(result["balance"])
            stats["fields_processed"] += 1
        if "credit_limit" in result:
            result["credit_limit"] = CurrencyNormalizer.normalize(result["credit_limit"])
            stats["fields_processed"] += 1
        if "payment_status" in result:
            result["payment_status"] = TextNormalizer.normalize_payment_status(result["payment_status"])
            stats["fields_processed"] += 1
        if "date_opened" in result:
            result["date_opened"] = DateNormalizer.normalize(result["date_opened"])
            stats["fields_processed"] += 1
        # Add stats
        stats["success_rate"] = stats["fields_processed"] / max(len(data), 1)
        result["_normalization_stats"] = stats
        return result

    def normalize_consumer_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = dict(data)
        if "name" in result:
            result["name"] = TextNormalizer.normalize_name(result["name"])
        if "ssn" in result:
            result["ssn"] = SSNNormalizer.normalize(result["ssn"])
        if "date_of_birth" in result:
            result["date_of_birth"] = DateNormalizer.normalize(result["date_of_birth"])
        if "addresses" in result and isinstance(result["addresses"], list):
            for addr in result["addresses"]:
                if "city" in addr:
                    addr["city"] = TextNormalizer.normalize_name(addr["city"])
        if "phone_numbers" in result and isinstance(result["phone_numbers"], list):
            result["phone_numbers"] = [PhoneNumberNormalizer.normalize(p) for p in result["phone_numbers"]]
        return result