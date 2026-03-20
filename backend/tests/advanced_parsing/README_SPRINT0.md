# Sprint 0 Validation - Quick Start Guide

## What is Sprint 0 Validation?

Sprint 0 validation tests the tradeline extraction pipeline against:
- **Real PDF**: `backend/TransUnion-06-10-2025.pdf`
- **Ground Truth**: `backend/tradeline_test_rows.sql` (20 expected tradelines)

This validates actual production behavior, not synthetic test cases.

## Quick Start

### Option 1: Interactive Menu (Recommended)
```bash
cd /home/rorschache/credit-clarity/backend/tests/advanced_parsing
python3 run_tests.py
```

**Choose Option 1** for fastest Sprint 0 validation (~2 minutes)

### Option 2: Direct Execution
```bash
cd /home/rorschache/credit-clarity/backend/tests/advanced_parsing
python3 test_sprint0_validation.py
```

### Option 3: Command Line with Arguments
```bash
cd /home/rorschache/credit-clarity/backend/tests/advanced_parsing
python3 test_runner.py --sprint0 --no-accuracy --no-performance --no-real-world --no-edge-cases
```

## Expected Output

### Success Example
```
🧪 Sprint 0 Validation: TransUnion PDF vs Ground Truth SQL
================================================================================

📄 Parsing ground truth from: /home/rorschache/credit-clarity/backend/tradeline_test_rows.sql
✅ Parsed 20 expected tradelines

🔍 Extracting tradelines from: /home/rorschache/credit-clarity/backend/TransUnion-06-10-2025.pdf
✅ Extracted 20 tradelines

🔎 Matching extracted tradelines against ground truth...

📊 Validation Results:
   Expected:  20
   Extracted: 20
   Matched:   20
   Critical Accuracy:  100.0%
   Optional Accuracy:  97.5%
   Overall Accuracy:   98.5%
   Status: ✅ PASSED

📄 JSON report: /home/rorschache/credit-clarity/backend/tests/reports/sprint0_validation_report.json
📄 Markdown report: /home/rorschache/credit-clarity/backend/tests/reports/sprint0_validation_report.md
```

### Failure Example
```
📊 Validation Results:
   Expected:  20
   Extracted: 18
   Matched:   17
   Critical Accuracy:  85.0%
   Optional Accuracy:  90.5%
   Overall Accuracy:   87.2%
   Status: ❌ FAILED
```

## Output Files

### JSON Report
**Location**: `backend/tests/reports/sprint0_validation_report.json`

Contains:
- Complete field-by-field comparison
- Normalized values for debugging
- Detailed error messages
- Machine-readable format for CI/CD

### Markdown Report
**Location**: `backend/tests/reports/sprint0_validation_report.md`

Contains:
- Executive summary with pass/fail status
- Tradeline-by-tradeline comparison tables
- Visual indicators (✅/❌/⭐)
- Actionable recommendations

## Acceptance Criteria

Sprint 0 validation PASSES when ALL criteria are met:

1. ✅ **20 tradelines extracted** (100% extraction rate)
2. ✅ **100% critical field accuracy**:
   - creditor_name
   - account_number
   - account_status
   - account_type
3. ✅ **≥95% optional field accuracy**:
   - monthly_payment
   - credit_limit
   - date_opened
   - account_balance

## Troubleshooting

### File Not Found Errors

**Error**: `PDF not found: backend/TransUnion-06-10-2025.pdf`

**Solution**: Ensure the PDF exists at the correct path:
```bash
ls /home/rorschache/credit-clarity/backend/TransUnion-06-10-2025.pdf
```

**Error**: `SQL ground truth not found: backend/tradeline_test_rows.sql`

**Solution**: Ensure the SQL file exists:
```bash
ls /home/rorschache/credit-clarity/backend/tradeline_test_rows.sql
```

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'services'`

**Solution**: Run from the correct directory:
```bash
cd /home/rorschache/credit-clarity/backend/tests/advanced_parsing
```

### Pipeline Failures

**Error**: `Pipeline failed: PDF extraction returned no text`

**Possible Causes**:
1. PDF is corrupted
2. OCR libraries not installed
3. Insufficient permissions

**Solution**: Check pipeline logs for detailed error messages

## Understanding Results

### Critical Accuracy = 100%
✅ **GOOD**: All mandatory fields extracted correctly
- creditor_name matches exactly
- account_number matches (handles masking)
- account_status correct (Current/Closed)
- account_type correct (Revolving/Installment)

### Critical Accuracy < 100%
❌ **REQUIRES FIX**: One or more critical fields missing/incorrect
- Check error messages in report
- Review field comparison table
- Fix parser or extractor

### Optional Accuracy ≥ 95%
✅ **GOOD**: Most optional fields extracted correctly
- Minor issues acceptable
- May have null values (expected)

### Optional Accuracy < 95%
⚠️ **NEEDS IMPROVEMENT**: Too many optional field errors
- Review field normalization
- Check date/currency parsing
- Improve extraction quality

## Next Steps After Validation

### If PASSED ✅
1. Review detailed report for any warnings
2. Proceed with further testing
3. Consider production deployment

### If FAILED ❌
1. **Review Reports**:
   ```bash
   cat /home/rorschache/credit-clarity/backend/tests/reports/sprint0_validation_report.md
   ```

2. **Identify Issues**:
   - Check "Errors" section
   - Review field comparison tables
   - Look for patterns (all dates wrong? all currency wrong?)

3. **Fix Issues**:
   - Critical field failures: High priority
   - Optional field failures: Medium priority
   - Update parser/extractor/normalizer as needed

4. **Re-run Validation**:
   ```bash
   python3 test_sprint0_validation.py
   ```

5. **Iterate** until PASSED

## Advanced Usage

### Run All Tests Including Sprint 0
```bash
python3 test_runner.py  # All tests enabled by default
```

### Skip Sprint 0 (Synthetic Tests Only)
```bash
python3 test_runner.py --no-sprint0
```

### Custom Output Directory
```bash
python3 test_runner.py --output-dir /tmp/my_test_results
```

## CI/CD Integration

### Example GitHub Actions Workflow
```yaml
name: Sprint 0 Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run Sprint 0 Validation
        run: |
          cd backend/tests/advanced_parsing
          python3 test_sprint0_validation.py
      - name: Upload Reports
        if: always()
        uses: actions/upload-artifact@v2
        with:
          name: sprint0-reports
          path: backend/tests/reports/
```

### Exit Codes
- **0**: Validation PASSED
- **1**: Validation FAILED

Use exit code for CI/CD pipeline decisions.

## Support

For issues or questions:
1. Check `IMPLEMENTATION_SUMMARY.md` for technical details
2. Review error messages in JSON/Markdown reports
3. Check pipeline logs for extraction/parsing errors

## Summary

Sprint 0 validation provides **production-ready** validation of the tradeline extraction pipeline using **real data** instead of synthetic test cases. This ensures the system works correctly with actual credit report PDFs before deployment.

**Quick Command**:
```bash
cd /home/rorschache/credit-clarity/backend/tests/advanced_parsing && python3 test_sprint0_validation.py
```

**Expected Result**: ✅ PASSED with 100% critical accuracy and ≥95% optional accuracy.
