# Maintainability Review

Reviewed 25 files.

## mai-001-5503328a - Ralph loop extractor module is extremely large
Severity: medium
Location: backend/services/tradeline_extraction/ralph_loop_extractor.py:1

ralph_loop_extractor.py is ~960 lines, which increases cognitive load and raises risk of regressions when modifying extraction logic.

Recommendation:
Split the module into smaller components (OCR orchestration, quality scoring, AI extraction, retries) and add unit tests per component.

Snippet:
```
"""Ralph loop extractor"""
```
