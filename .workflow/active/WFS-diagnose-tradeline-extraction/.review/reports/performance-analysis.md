# Performance Review

Reviewed 25 files.

## per-001-42f3975e - Document AI fallback can be invoked for low-quality OCR without caching
Severity: medium
Location: backend/services/tradeline_extraction/pdf_extractor.py:790

When OCR quality is low, the extractor falls back to Document AI. There is no caching or reuse of prior extraction for the same file, which can increase latency and cost.

Recommendation:
Cache extraction results per file hash and add a guard to avoid repeated Document AI calls for the same input.

Snippet:
```
logger.warning(f"Using expensive Document AI for {path.name}")
```
