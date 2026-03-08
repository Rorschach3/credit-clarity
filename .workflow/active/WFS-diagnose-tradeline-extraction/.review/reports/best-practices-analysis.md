# Best-Practices Review

Reviewed 25 files.

## bes-001-119b153b - Deprecated sample text helper remains in production extractor
Severity: low
Location: backend/services/tradeline_extraction/pdf_extractor.py:370

A deprecated test helper lives in the production extractor and returns sample report text. This increases the risk of accidental test behavior in production.

Recommendation:
Move the sample text helper into test utilities or guard it behind explicit test-only flags.

Snippet:
```
async def _get_sample_transunion_text(self) -> str:
    logger.warning("Using sample text for testing purposes only")
```
