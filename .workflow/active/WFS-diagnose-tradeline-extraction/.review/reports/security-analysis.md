# Security Review

Reviewed 25 files.

## sec-001-7eaea5ad - Validation debug logging may expose sensitive tradeline details
Severity: medium
Location: backend/services/tradeline_extraction/validation_pipeline.py:107

Validation debug logs include creditor_name and full error/warning messages; these messages can contain account numbers or other PII from the tradeline payload.

Recommendation:
Redact or hash PII in log output, or downgrade to structured metrics without raw field values.

Snippet:
```
logger.debug(
    f"Validation result for {tradeline.get('creditor_name', 'unknown')} | "
    f"confidence={confidence:.2f}, severity={severity}, errors={errors}, warnings={warnings}"
)
```
