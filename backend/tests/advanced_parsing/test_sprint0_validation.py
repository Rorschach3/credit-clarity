"""
Sprint 0 Validation: Real TransUnion PDF vs Ground Truth SQL
Tests the complete tradeline extraction pipeline against actual credit report PDF
and validates against 20 expected tradelines from ground truth SQL.
"""
import asyncio
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add backend directory to sys.path dynamically
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from services.tradeline_extraction.pipeline import TradelineExtractionPipeline
from utils.enhanced_tradeline_normalizer import EnhancedTradelineNormalizer


@dataclass
class GroundTruthTradeline:
    """Represents a tradeline from ground truth SQL."""
    creditor_name: str
    account_number: str
    account_status: str
    account_type: str
    date_opened: Optional[str] = None
    monthly_payment: Optional[str] = None
    credit_limit: Optional[str] = None
    account_balance: Optional[str] = None

    @classmethod
    def from_sql_values(cls, values: Dict[str, Any]) -> 'GroundTruthTradeline':
        """Create from SQL INSERT VALUES."""
        return cls(
            creditor_name=values.get('creditor_name', ''),
            account_number=values.get('account_number', ''),
            account_status=values.get('account_status', ''),
            account_type=values.get('account_type', ''),
            date_opened=values.get('date_opened'),
            monthly_payment=values.get('monthly_payment'),
            credit_limit=values.get('credit_limit'),
            account_balance=values.get('account_balance')
        )


@dataclass
class FieldComparison:
    """Comparison result for a single field."""
    field_name: str
    expected: Optional[str]
    actual: Optional[str]
    matches: bool
    normalized_expected: Optional[str] = None
    normalized_actual: Optional[str] = None
    is_critical: bool = False


@dataclass
class TradelineComparison:
    """Comparison result for a single tradeline."""
    account_number: str
    creditor_name: str
    found: bool
    field_comparisons: List[FieldComparison] = field(default_factory=list)
    critical_fields_match: bool = False
    optional_fields_match_rate: float = 0.0


@dataclass
class ValidationReport:
    """Complete validation report."""
    pdf_path: str
    sql_path: str
    timestamp: str
    expected_count: int
    extracted_count: int
    matched_count: int
    tradeline_comparisons: List[TradelineComparison] = field(default_factory=list)
    critical_accuracy: float = 0.0
    optional_accuracy: float = 0.0
    overall_accuracy: float = 0.0
    passed: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class SQLParser:
    """Parser for ground truth SQL file."""

    @staticmethod
    def parse_sql_file(sql_path: Path) -> List[GroundTruthTradeline]:
        """Parse tradeline_test_rows.sql and extract ground truth tradelines."""
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # Extract INSERT VALUES portion
        # Pattern: VALUES (...), (...), ...
        values_pattern = r"VALUES\s+(.+?)(?:;|$)"
        match = re.search(values_pattern, sql_content, re.DOTALL)

        if not match:
            raise ValueError("Could not find VALUES clause in SQL file")

        values_content = match.group(1)

        # Split by row (comma-separated tuples)
        # Pattern: ('val1', 'val2', ..., 'valN')
        row_pattern = r"\(([^)]+)\)"
        rows = re.findall(row_pattern, values_content)

        tradelines = []
        for row in rows:
            # Split by comma, handling quoted values
            parts = SQLParser._parse_sql_values(row)

            if len(parts) >= 13:  # Ensure we have all expected columns
                tradeline = GroundTruthTradeline.from_sql_values({
                    'creditor_name': SQLParser._clean_value(parts[1]),
                    'account_number': SQLParser._clean_value(parts[2]),
                    'account_status': SQLParser._clean_value(parts[3]),
                    'account_type': SQLParser._clean_value(parts[4]),
                    'date_opened': SQLParser._clean_value(parts[5]),
                    'monthly_payment': SQLParser._clean_value(parts[6]),
                    'credit_limit': SQLParser._clean_value(parts[7]),
                    'account_balance': SQLParser._clean_value(parts[8])
                })
                tradelines.append(tradeline)

        return tradelines

    @staticmethod
    def _parse_sql_values(row_str: str) -> List[str]:
        """Parse SQL VALUES row, handling quoted strings."""
        parts = []
        current = []
        in_quote = False

        for char in row_str + ',':
            if char == "'" and not in_quote:
                in_quote = True
            elif char == "'" and in_quote:
                in_quote = False
            elif char == ',' and not in_quote:
                parts.append(''.join(current).strip())
                current = []
            else:
                current.append(char)

        return parts

    @staticmethod
    def _clean_value(value: str) -> Optional[str]:
        """Clean SQL value (remove quotes, handle NULL)."""
        value = value.strip().strip("'\"")

        if value.lower() in ('null', 'none', ''):
            return None

        return value


class Sprint0Validator:
    """Validates extraction pipeline against ground truth."""

    # Critical fields that must have 100% accuracy
    CRITICAL_FIELDS = ['creditor_name', 'account_number', 'account_status', 'account_type']

    # Optional fields that should have ≥95% accuracy
    OPTIONAL_FIELDS = ['monthly_payment', 'credit_limit', 'date_opened', 'account_balance']

    def __init__(self):
        self.pipeline = TradelineExtractionPipeline(use_real_world_parser=True)
        self.normalizer = EnhancedTradelineNormalizer()

    async def run_validation(
        self,
        pdf_path: Path,
        sql_path: Path,
        output_dir: Path
    ) -> ValidationReport:
        """Run complete Sprint 0 validation."""

        print("=" * 80)
        print("🧪 Sprint 0 Validation: TransUnion PDF vs Ground Truth SQL")
        print("=" * 80)

        # Step 1: Parse ground truth from SQL
        print(f"\n📄 Parsing ground truth from: {sql_path}")
        ground_truth = SQLParser.parse_sql_file(sql_path)
        print(f"✅ Parsed {len(ground_truth)} expected tradelines")

        # Step 2: Run real extraction pipeline
        print(f"\n🔍 Extracting tradelines from: {pdf_path}")
        pipeline_result = await self.pipeline.process_credit_report(
            pdf_path=pdf_path,
            store_results=False  # Don't store during validation
        )

        if not pipeline_result.success:
            return ValidationReport(
                pdf_path=str(pdf_path),
                sql_path=str(sql_path),
                timestamp=datetime.now().isoformat(),
                expected_count=len(ground_truth),
                extracted_count=0,
                matched_count=0,
                errors=[pipeline_result.error or "Pipeline failed"]
            )

        print(f"✅ Extracted {pipeline_result.tradelines_parsed} tradelines")

        # Step 3: Get extracted tradelines from pipeline
        # Re-run parsing to get ParsedTradeline objects
        extraction = await self.pipeline.pdf_extractor.extract_text_from_pdf(pdf_path)
        extracted_tradelines = self.pipeline.parser.parse_tradelines_from_text(extraction.text)

        # Step 4: Match and compare
        print(f"\n🔎 Matching extracted tradelines against ground truth...")
        comparisons = self._match_and_compare(ground_truth, extracted_tradelines)

        # Step 5: Calculate accuracy metrics
        report = self._generate_report(
            pdf_path=pdf_path,
            sql_path=sql_path,
            ground_truth=ground_truth,
            extracted_tradelines=extracted_tradelines,
            comparisons=comparisons
        )

        # Step 6: Generate output files
        output_dir.mkdir(parents=True, exist_ok=True)
        self._write_json_report(report, output_dir)
        self._write_markdown_report(report, output_dir)

        print(f"\n📊 Validation Results:")
        print(f"   Expected:  {report.expected_count}")
        print(f"   Extracted: {report.extracted_count}")
        print(f"   Matched:   {report.matched_count}")
        print(f"   Critical Accuracy:  {report.critical_accuracy:.1f}%")
        print(f"   Optional Accuracy:  {report.optional_accuracy:.1f}%")
        print(f"   Overall Accuracy:   {report.overall_accuracy:.1f}%")
        print(f"   Status: {'✅ PASSED' if report.passed else '❌ FAILED'}")

        return report

    def _match_and_compare(
        self,
        ground_truth: List[GroundTruthTradeline],
        extracted: List[Any]
    ) -> List[TradelineComparison]:
        """Match extracted tradelines to ground truth and compare fields."""
        comparisons = []

        for gt in ground_truth:
            # Find matching extracted tradeline by account number
            matched_tradeline = self._find_matching_tradeline(gt, extracted)

            if not matched_tradeline:
                # Tradeline not found
                comparison = TradelineComparison(
                    account_number=gt.account_number,
                    creditor_name=gt.creditor_name,
                    found=False
                )
                comparisons.append(comparison)
                continue

            # Compare all fields
            field_comparisons = []

            for field_name in self.CRITICAL_FIELDS + self.OPTIONAL_FIELDS:
                expected_value = getattr(gt, field_name, None)
                actual_value = getattr(matched_tradeline, field_name, None)

                is_critical = field_name in self.CRITICAL_FIELDS
                matches = self._compare_field(field_name, expected_value, actual_value)

                field_comp = FieldComparison(
                    field_name=field_name,
                    expected=expected_value,
                    actual=actual_value,
                    matches=matches,
                    normalized_expected=self._normalize_for_comparison(field_name, expected_value),
                    normalized_actual=self._normalize_for_comparison(field_name, actual_value),
                    is_critical=is_critical
                )
                field_comparisons.append(field_comp)

            # Calculate match rates
            critical_matches = [fc for fc in field_comparisons if fc.is_critical and fc.matches]
            critical_fields_match = len(critical_matches) == len(self.CRITICAL_FIELDS)

            optional_comps = [fc for fc in field_comparisons if not fc.is_critical and fc.expected is not None]
            optional_matches = [fc for fc in optional_comps if fc.matches]
            optional_match_rate = (len(optional_matches) / len(optional_comps) * 100) if optional_comps else 100.0

            comparison = TradelineComparison(
                account_number=gt.account_number,
                creditor_name=gt.creditor_name,
                found=True,
                field_comparisons=field_comparisons,
                critical_fields_match=critical_fields_match,
                optional_fields_match_rate=optional_match_rate
            )
            comparisons.append(comparison)

        return comparisons

    def _find_matching_tradeline(self, gt: GroundTruthTradeline, extracted: List[Any]) -> Optional[Any]:
        """Find extracted tradeline matching ground truth by account number."""
        gt_account_normalized = self._normalize_account_number(gt.account_number)

        for ext in extracted:
            ext_account = getattr(ext, 'account_number', '')
            ext_account_normalized = self._normalize_account_number(ext_account)

            if self._accounts_match(gt_account_normalized, ext_account_normalized):
                return ext

        return None

    def _normalize_account_number(self, account: Optional[str]) -> str:
        """Normalize account number for comparison."""
        if not account:
            return ''

        # Remove all non-alphanumeric characters
        normalized = re.sub(r'[^a-zA-Z0-9]', '', account.upper())
        return normalized

    def _accounts_match(self, account1: str, account2: str) -> bool:
        """Check if two account numbers match (handle masking)."""
        if not account1 or not account2:
            return False

        # Exact match
        if account1 == account2:
            return True

        # Match by last 4 digits (handling masked accounts)
        if len(account1) >= 4 and len(account2) >= 4:
            last4_1 = account1[-4:]
            last4_2 = account2[-4:]

            if last4_1.isdigit() and last4_2.isdigit() and last4_1 == last4_2:
                return True

        return False

    def _compare_field(self, field_name: str, expected: Optional[str], actual: Optional[str]) -> bool:
        """Compare a single field with normalization."""
        norm_expected = self._normalize_for_comparison(field_name, expected)
        norm_actual = self._normalize_for_comparison(field_name, actual)

        # Handle null cases
        if norm_expected is None and norm_actual is None:
            return True
        if norm_expected is None or norm_actual is None:
            return False

        return norm_expected == norm_actual

    def _normalize_for_comparison(self, field_name: str, value: Optional[str]) -> Optional[str]:
        """Normalize field value for comparison."""
        if value is None or value == '':
            return None

        value_str = str(value).strip()

        if field_name == 'account_number':
            return self._normalize_account_number(value_str)

        elif field_name in ['monthly_payment', 'credit_limit', 'account_balance']:
            # Normalize currency: remove $, commas, spaces
            clean = re.sub(r'[$,\s]', '', value_str)
            # Convert to float and back to remove trailing zeros
            try:
                amount = float(clean)
                return f"{amount:.2f}"
            except (ValueError, TypeError):
                return clean.upper()

        elif field_name == 'date_opened':
            # Normalize date format
            # Support: MM/DD/YYYY, MM-DD-YYYY, YYYY-MM-DD, etc.
            clean = re.sub(r'[^\d]', '', value_str)
            if len(clean) == 8:
                # Assume MMDDYYYY or YYYYMMDD
                if int(clean[:2]) > 12:
                    # YYYYMMDD
                    return f"{clean[4:6]}/{clean[6:8]}/{clean[:4]}"
                else:
                    # MMDDYYYY
                    return f"{clean[:2]}/{clean[2:4]}/{clean[4:]}"
            return value_str

        else:
            # Default: uppercase and trim
            return value_str.upper().strip()

    def _generate_report(
        self,
        pdf_path: Path,
        sql_path: Path,
        ground_truth: List[GroundTruthTradeline],
        extracted_tradelines: List[Any],
        comparisons: List[TradelineComparison]
    ) -> ValidationReport:
        """Generate validation report with accuracy metrics."""

        matched_count = sum(1 for c in comparisons if c.found)

        # Critical accuracy: 100% of critical fields must match
        critical_perfect_count = sum(1 for c in comparisons if c.found and c.critical_fields_match)
        critical_accuracy = (critical_perfect_count / len(ground_truth) * 100) if ground_truth else 0.0

        # Optional accuracy: average match rate across all optional fields
        optional_rates = [c.optional_fields_match_rate for c in comparisons if c.found]
        optional_accuracy = (sum(optional_rates) / len(optional_rates)) if optional_rates else 0.0

        # Overall accuracy: weighted average (critical: 60%, optional: 40%)
        overall_accuracy = (critical_accuracy * 0.6) + (optional_accuracy * 0.4)

        # Pass criteria:
        # - All tradelines found (100%)
        # - Critical accuracy = 100%
        # - Optional accuracy ≥ 95%
        passed = (
            matched_count == len(ground_truth) and
            critical_accuracy == 100.0 and
            optional_accuracy >= 95.0
        )

        warnings = []
        errors = []

        # Generate warnings for missing tradelines
        for c in comparisons:
            if not c.found:
                errors.append(f"Tradeline not found: {c.creditor_name} ({c.account_number})")

        # Generate warnings for field mismatches
        for c in comparisons:
            if c.found and not c.critical_fields_match:
                mismatched = [fc.field_name for fc in c.field_comparisons if fc.is_critical and not fc.matches]
                errors.append(
                    f"Critical field mismatch in {c.creditor_name}: {', '.join(mismatched)}"
                )

            if c.found and c.optional_fields_match_rate < 95.0:
                warnings.append(
                    f"Optional field accuracy below 95% for {c.creditor_name}: {c.optional_fields_match_rate:.1f}%"
                )

        return ValidationReport(
            pdf_path=str(pdf_path),
            sql_path=str(sql_path),
            timestamp=datetime.now().isoformat(),
            expected_count=len(ground_truth),
            extracted_count=len(extracted_tradelines),
            matched_count=matched_count,
            tradeline_comparisons=comparisons,
            critical_accuracy=critical_accuracy,
            optional_accuracy=optional_accuracy,
            overall_accuracy=overall_accuracy,
            passed=passed,
            errors=errors,
            warnings=warnings
        )

    def _write_json_report(self, report: ValidationReport, output_dir: Path):
        """Write JSON validation report."""
        json_path = output_dir / 'sprint0_validation_report.json'

        # Convert to dict for JSON serialization
        report_dict = {
            'pdf_path': report.pdf_path,
            'sql_path': report.sql_path,
            'timestamp': report.timestamp,
            'expected_count': report.expected_count,
            'extracted_count': report.extracted_count,
            'matched_count': report.matched_count,
            'critical_accuracy': report.critical_accuracy,
            'optional_accuracy': report.optional_accuracy,
            'overall_accuracy': report.overall_accuracy,
            'passed': report.passed,
            'errors': report.errors,
            'warnings': report.warnings,
            'tradeline_comparisons': [
                {
                    'account_number': c.account_number,
                    'creditor_name': c.creditor_name,
                    'found': c.found,
                    'critical_fields_match': c.critical_fields_match,
                    'optional_fields_match_rate': c.optional_fields_match_rate,
                    'field_comparisons': [
                        {
                            'field_name': fc.field_name,
                            'expected': fc.expected,
                            'actual': fc.actual,
                            'matches': fc.matches,
                            'normalized_expected': fc.normalized_expected,
                            'normalized_actual': fc.normalized_actual,
                            'is_critical': fc.is_critical
                        }
                        for fc in c.field_comparisons
                    ]
                }
                for c in report.tradeline_comparisons
            ]
        }

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)

        print(f"\n📄 JSON report: {json_path}")

    def _write_markdown_report(self, report: ValidationReport, output_dir: Path):
        """Write Markdown validation report."""
        md_path = output_dir / 'sprint0_validation_report.md'

        md_content = f"""# Sprint 0 Validation Report

## Test Configuration

- **PDF Source**: `{report.pdf_path}`
- **Ground Truth**: `{report.sql_path}`
- **Timestamp**: {report.timestamp}
- **Status**: {'✅ PASSED' if report.passed else '❌ FAILED'}

## Summary

| Metric | Value |
|--------|-------|
| Expected Tradelines | {report.expected_count} |
| Extracted Tradelines | {report.extracted_count} |
| Matched Tradelines | {report.matched_count} |
| **Critical Accuracy** | **{report.critical_accuracy:.1f}%** (Target: 100%) |
| **Optional Accuracy** | **{report.optional_accuracy:.1f}%** (Target: ≥95%) |
| **Overall Accuracy** | **{report.overall_accuracy:.1f}%** |

## Acceptance Criteria

- ✅ 20 tradelines extracted: {report.extracted_count == 20}
- {'✅' if report.critical_accuracy == 100 else '❌'} 100% match on critical fields (creditor_name, account_number, account_status, account_type): {report.critical_accuracy:.1f}%
- {'✅' if report.optional_accuracy >= 95 else '❌'} ≥95% match on optional fields (monthly_payment, credit_limit, date_opened, account_balance): {report.optional_accuracy:.1f}%

## Detailed Results

"""

        # Add tradeline-by-tradeline results
        for i, comp in enumerate(report.tradeline_comparisons, 1):
            status_icon = '✅' if comp.found and comp.critical_fields_match else '❌'
            md_content += f"\n### {i}. {comp.creditor_name} ({comp.account_number})\n\n"
            md_content += f"**Status**: {status_icon} {'Found' if comp.found else 'NOT FOUND'}\n\n"

            if comp.found:
                md_content += f"- Critical Fields Match: {'✅ Yes' if comp.critical_fields_match else '❌ No'}\n"
                md_content += f"- Optional Fields Match Rate: {comp.optional_fields_match_rate:.1f}%\n\n"

                # Field comparison table
                md_content += "| Field | Expected | Actual | Match | Critical |\n"
                md_content += "|-------|----------|--------|-------|----------|\n"

                for fc in comp.field_comparisons:
                    match_icon = '✅' if fc.matches else '❌'
                    crit_icon = '⭐' if fc.is_critical else ''
                    expected_display = fc.expected or 'NULL'
                    actual_display = fc.actual or 'NULL'

                    md_content += f"| {fc.field_name} | {expected_display} | {actual_display} | {match_icon} | {crit_icon} |\n"

                md_content += "\n"

        # Add errors and warnings
        if report.errors:
            md_content += "\n## Errors\n\n"
            for error in report.errors:
                md_content += f"- ❌ {error}\n"

        if report.warnings:
            md_content += "\n## Warnings\n\n"
            for warning in report.warnings:
                md_content += f"- ⚠️ {warning}\n"

        # Conclusion
        md_content += "\n## Conclusion\n\n"
        if report.passed:
            md_content += "✅ **VALIDATION PASSED**: All acceptance criteria met. The tradeline extraction pipeline successfully processes the TransUnion PDF with 100% accuracy on critical fields and ≥95% accuracy on optional fields.\n"
        else:
            md_content += "❌ **VALIDATION FAILED**: One or more acceptance criteria not met. See errors and warnings above for details.\n"
            md_content += "\n### Required Improvements:\n\n"

            if report.critical_accuracy < 100:
                md_content += f"- Fix critical field extraction (current: {report.critical_accuracy:.1f}%, target: 100%)\n"

            if report.optional_accuracy < 95:
                md_content += f"- Improve optional field extraction (current: {report.optional_accuracy:.1f}%, target: ≥95%)\n"

            if report.matched_count < report.expected_count:
                md_content += f"- Extract all {report.expected_count} tradelines (current: {report.matched_count})\n"

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        print(f"📄 Markdown report: {md_path}")


async def run_sprint0_validation():
    """Main function to run Sprint 0 validation."""

    # Paths
    backend_dir = Path(__file__).resolve().parents[2]
    pdf_path = backend_dir / 'TransUnion-06-10-2025.pdf'
    sql_path = backend_dir / 'tradeline_test_rows.sql'
    output_dir = backend_dir / 'tests' / 'reports'

    # Validate paths
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if not sql_path.exists():
        raise FileNotFoundError(f"SQL ground truth not found: {sql_path}")

    # Run validation
    validator = Sprint0Validator()
    report = await validator.run_validation(
        pdf_path=pdf_path,
        sql_path=sql_path,
        output_dir=output_dir
    )

    # Return status code
    return 0 if report.passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_sprint0_validation())
    sys.exit(exit_code)
