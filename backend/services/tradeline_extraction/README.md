# Tradeline Extraction Services

**Purpose:** Extract, parse, validate, and store tradeline data from PDF credit reports.

---

## Quick Start

```python
from services.tradeline_extraction.pipeline import TradelineExtractionPipeline

# Initialize
pipeline = TradelineExtractionPipeline(use_real_world_parser=True)

# Process PDF
result = await pipeline.process_credit_report(
    pdf_path="report.pdf",
    user_id="user_123",
    store_results=True
)

# Check results
print(f"Success: {result.success}")
print(f"Parsed: {result.tradelines_parsed}")
print(f"Stored: {result.tradelines_stored}")
```

---

## Components

### 1. `pipeline.py` - Orchestrator
Main pipeline that coordinates all stages.

**Key Class:** `TradelineExtractionPipeline`

**Methods:**
- `process_credit_report()` - Full pipeline execution
- `validate_pdf_file()` - PDF validation only
- `get_pipeline_statistics()` - Configuration info
- `health_check()` - Component status

### 2. `pdf_extractor.py` - PDF Processing
Extracts text from PDF files using multiple methods.

**Key Class:** `TransUnionPDFExtractor`

**Methods:**
- `extract_text_from_pdf()` - Extract text
- `validate_pdf_file()` - Validate PDF
- `extract_metadata()` - Get PDF metadata

**Supported Methods:**
- PyMuPDF (fast, structure-aware)
- pdfplumber (table detection)
- OCR (fallback for images)

### 3. `tradeline_parser.py` - Parsing
Parses tradeline data from extracted text.

**Key Classes:**
- `RealWorldTransUnionParser` - Recommended, bureau-agnostic
- `TransUnionTradelineParser` - Legacy, strict parsing

**Output:** `ParsedTradeline` objects

### 4. `real_world_parser.py` - Enhanced Parsing
Real-world credit report parser for messy data.

**Features:**
- Handles various bureau formats
- Pattern matching
- Error tolerance
- Multi-line data support

### 5. `validation_pipeline.py` - Validation
Validates tradeline data quality.

**Key Class:** `TradelineValidationPipeline`

**Checks:**
- Required fields present
- Data types correct
- Value ranges valid
- Business rules met

### 6. `data_storage.py` - Database
Stores tradelines in Supabase.

**Key Class:** `TradelineStorageService`

**Methods:**
- `store_tradelines()` - Batch upsert
- `upsert_tradeline()` - Single upsert
- `_is_valid_tradeline()` - Validation helper

---

## Usage Examples

### Basic Processing
```python
pipeline = TradelineExtractionPipeline()
result = await pipeline.process_credit_report("report.pdf")

if result.success:
    print(f"✅ {result.tradelines_stored} tradelines stored")
else:
    print(f"❌ {result.error}")
```

### Without Storage (Testing)
```python
result = await pipeline.process_credit_report(
    pdf_path="report.pdf",
    user_id="test_user",
    store_results=False  # Don't save to database
)
```

### PDF Validation Only
```python
validation = await pipeline.validate_pdf_file("report.pdf")
if validation['valid']:
    print("✅ PDF is valid")
else:
    print(f"❌ Errors: {validation['errors']}")
```

### Custom Parser
```python
from services.tradeline_extraction.real_world_parser import RealWorldTransUnionParser

pipeline = TradelineExtractionPipeline()
pipeline.parser = RealWorldTransUnionParser()
```

---

## Pipeline Flow

```
PDF Upload
    ↓
[1] PDF Validation
    ├─ Check file exists
    ├─ Valid PDF format
    ├─ Not corrupted
    └─ Size < 50MB
    ↓
[2] Text Extraction
    ├─ Try PyMuPDF (fast)
    ├─ Try pdfplumber (tables)
    └─ Fallback to OCR
    ↓
[3] Tradeline Parsing
    ├─ Identify sections
    ├─ Extract fields
    └─ Create ParsedTradeline objects
    ↓
[4] Data Normalization
    ├─ Format dates/currency
    ├─ Clean strings
    └─ Standardize values
    ↓
[5] Validation
    ├─ Required fields
    ├─ Data types
    ├─ Business rules
    └─ Confidence scoring
    ↓
[6] Storage (optional)
    ├─ Check duplicates
    ├─ Upsert to Supabase
    └─ Return IDs
    ↓
Result
```

---

## Configuration

### Pipeline Settings
```python
pipeline.max_processing_time_seconds = 300  # Timeout
pipeline.min_tradelines_expected = 1        # Min expected
pipeline.max_tradelines_expected = 50       # Max expected
```

### PDF Extractor Settings
```python
extractor = pipeline.pdf_extractor
extractor.max_file_size_mb = 50            # Max file size
extractor.extraction_timeout_seconds = 60  # Extraction timeout
```

### Storage Settings
```python
storage = pipeline.storage_service
storage.table_name = "tradelines"          # Database table
storage.batch_size = 100                   # Batch insert size
```

---

## Error Handling

### Common Errors

**PDF Validation Failed**
```python
if not result.pdf_processed:
    print(f"PDF validation failed: {result.error}")
```

**No Tradelines Found**
```python
if result.tradelines_parsed == 0:
    print("No tradelines found in PDF")
    print(f"Warnings: {result.warnings}")
```

**Validation Failures**
```python
for entry in result.validation_summary:
    if not entry.get('valid'):
        print(f"Invalid: {entry.get('errors')}")
```

**Storage Issues**
```python
if result.tradelines_stored == 0:
    print("No tradelines stored")
    print(f"Warnings: {result.warnings}")
```

---

## Testing

### Unit Tests
```bash
pytest tests/test_tradeline_extraction_pipeline.py -v
pytest tests/test_pdf_extractor.py -v
pytest tests/test_tradeline_parser.py -v
```

### Integration Test
```python
import asyncio
from services.tradeline_extraction.pipeline import TradelineExtractionPipeline

async def test_full_pipeline():
    pipeline = TradelineExtractionPipeline()
    
    # Test with sample PDF
    result = await pipeline.process_credit_report(
        pdf_path="test_data/sample_report.pdf",
        user_id="test_user",
        store_results=False
    )
    
    assert result.success
    assert result.tradelines_parsed > 0
    assert result.tradelines_validated > 0
    
    print(f"✅ Pipeline test passed")
    print(f"   Parsed: {result.tradelines_parsed}")
    print(f"   Valid: {result.tradelines_validated}")
    print(f"   Time: {result.processing_time_ms}ms")

asyncio.run(test_full_pipeline())
```

---

## Performance

### Typical Processing Times
- **PDF Validation:** 50-100ms
- **Text Extraction:** 500ms-2s
- **Parsing:** 100-500ms per page
- **Normalization:** 10-50ms per tradeline
- **Validation:** 50-100ms per tradeline
- **Storage:** 100-300ms batch

**Total:** 2-10 seconds per report

### Accuracy Targets
- **Overall:** 98% per-field accuracy
- **Critical fields:** 100% (bureau, creditor, account#, balance)
- **Date fields:** 95%+
- **Status fields:** 98%+

---

## Debugging

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

pipeline = TradelineExtractionPipeline()
result = await pipeline.process_credit_report("report.pdf")
```

### Inspect Validation Results
```python
for i, entry in enumerate(result.validation_summary):
    print(f"Tradeline {i+1}:")
    print(f"  Valid: {entry.get('valid')}")
    print(f"  Score: {entry.get('score')}")
    print(f"  Errors: {entry.get('errors')}")
    print(f"  Warnings: {entry.get('warnings')}")
```

### Check Pipeline Health
```python
health = await pipeline.health_check()
print(f"Components healthy: {health.get('healthy')}")
print(f"Details: {health.get('components')}")
```

---

## Related Files

- `../../utils/enhanced_tradeline_normalizer.py` - Data normalization
- `../../utils/field_validator.py` - Field validation
- `../../utils/date_parser.py` - Date parsing
- `../advanced_parsing/` - AI-enhanced parsing (optional)

---

## Documentation

- `/TRADELINE_EXTRACTION_PIPELINE.md` - Full architecture guide
- `/docs/TRADELINE_EXTRACTION_SUMMARY.md` - High-level summary
- `/docs/ARCHITECTURE_GUIDE.md` - System architecture

---

## Support

For issues or questions:
1. Check logs for detailed error messages
2. Review validation_summary in PipelineResult
3. Test with smaller/simpler PDFs first
4. Verify Supabase connection for storage issues

---

**Status:** Production-ready  
**Version:** 3.0  
**Last Updated:** 2026-01-05
