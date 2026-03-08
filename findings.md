# Findings & Decisions

## Requirements
- Working tradeline extraction process from credit report PDFs
- Extract structured tradeline data (creditor, account number, balance, status, etc.)
- Store tradelines in Supabase database
- Handle duplicate detection and updates
- Support multiple credit bureaus (TransUnion, Experian, Equifax)
- Identify negative accounts for dispute generation

## Research Findings

### Existing Architecture (Discovered 2026-01-16)

**Backend Components:**
- `backend/main.py` - FastAPI application (26901 tokens, very large)
- `backend/services/tradeline_extraction/pipeline.py` - Main orchestration pipeline
- `backend/services/tradeline_extraction/pdf_extractor.py` - PDF text extraction
- `backend/services/tradeline_extraction/tradeline_parser.py` - Parse text to tradelines
- `backend/services/tradeline_extraction/validation_pipeline.py` - Validation logic
- `backend/routers/upload_router.py` - Upload API endpoint
- `backend/services/document_processor_service.py` - Background processing
- `backend/services/job_service.py` - Job tracking system

**Frontend Components:**
- `frontend/src/utils/document-ai-parser.ts` - Client-side Document AI integration
- `frontend/src/utils/tradeline-types.ts` - TypeScript type definitions
- `frontend/src/utils/tradelineParser.ts` - Additional parsing logic
- `frontend/src/components/ui/tradelines-status.tsx` - UI component

**Processing Flow (As Documented in README):**
1. User uploads PDF via Web App
2. Frontend converts to base64 (`document-ai-parser.ts`)
3. Sends to FastAPI backend endpoint (`/api/upload`)
4. Backend tries Google Document AI (Python client)
5. Fallback: Node/Express proxy server for Document AI REST API
6. Fallback: Supabase Edge Function for OCR
7. Text extraction success → LLM parser (`llm_parser.py`)
8. Parsed tradeline data (JSON)
9. Backend returns to frontend
10. Frontend saves to Supabase DB

**Key Features Implemented:**
- Background job processing with status tracking
- Multiple OCR fallback mechanisms
- Tradeline validation and normalization
- Duplicate detection via unique constraint (user_id, account_number, creditor_name)
- Negative account classification
- Comprehensive test suite (tests/unit, tests/integration)

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| FastAPI for backend | Modern async Python framework, good performance |
| Google Document AI | High-accuracy OCR for credit reports |
| Gemini fallback | Backup when Document AI unavailable |
| Background job processing | Handle long-running OCR/parsing without blocking |
| Supabase | Managed PostgreSQL with real-time capabilities |
| Unique constraint on tradelines | Prevent duplicates: (user_id, creditor_name, account_number) |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| Large main.py file (26901 tokens) | Need to use offset/limit or grep for specific sections |
| Multiple OCR fallbacks complexity | Documented flow, need to test which path works |

## Resources
- Backend codebase: `backend/`
- Frontend codebase: `frontend/src/`
- README.md: Architecture diagrams and flow documentation
- Test fixtures: `backend/tests/test_fixtures/tradeline_test_data.py`
