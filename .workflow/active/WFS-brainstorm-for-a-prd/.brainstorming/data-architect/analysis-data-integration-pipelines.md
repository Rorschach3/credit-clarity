# Data Integration & Pipeline Architecture

**Parent Document**: @analysis.md
**Reference**: @../guidance-specification.md Section 2 (Core Features), Section 6 (Cross-Role Integration)

## 1. Data Integration Overview

### 1.1 Integration Architecture Context

Credit Clarity's data architecture integrates multiple external services and internal processing pipelines:

**External Service Integrations**:
1. **Google Document AI**: OCR and form extraction for credit report PDFs
2. **Gemini AI**: Tradeline parsing, classification, and bureau response OCR (Phase 2)
3. **Lob.com API** (Phase 1): Certified mail service for dispute letter mailing
4. **USPS API Direct** (Phase 2): Cost-optimized mailing service replacement
5. **Pinecone/Weaviate** (Phase 3): Vector database for RAG chatbot knowledge base

**Internal Data Pipelines**:
1. **AI Processing Pipeline**: Credit report upload → OCR → Tradeline extraction → Negative item classification → PostgreSQL storage
2. **Mailing Service Pipeline**: Dispute letter generation → Payment processing → Lob/USPS API request → Tracking number storage
3. **Status Update Pipeline**: Manual status change or bureau response OCR → Status update → Analytics refresh → Audit trail logging
4. **Analytics Pipeline**: Status change trigger → Aggregation calculation → `user_analytics` cache update

**Integration Patterns**:
- **API-based integration**: RESTful APIs for Lob, USPS, Pinecone (JSON request/response)
- **Event-driven integration**: Database triggers for analytics refresh and audit logging
- **Batch processing**: Background jobs for large PDF processing (Celery task queue)
- **Streaming integration** (Phase 4): Real-time USPS tracking webhooks for delivery status updates

### 1.2 Data Flow Principles

1. **Asynchronous processing**: Long-running operations (OCR, AI inference) execute in background jobs
2. **Idempotency**: All API integrations designed to handle retries safely (duplicate request detection)
3. **Error handling**: Failed integrations logged and retried with exponential backoff
4. **Data validation**: Input validation at API boundaries, output validation before PostgreSQL insert
5. **Audit trail**: All external API calls logged with request/response payloads for debugging

## 2. AI Processing Pipeline

### 2.1 Credit Report Upload & OCR Pipeline

**Pipeline Flow**:

```
User Upload (Frontend)
    ↓ [Credit report PDF, 1-5MB]
Supabase Storage
    ↓ [File URL]
FastAPI Background Job (Celery)
    ↓ [PDF bytes]
Google Document AI OCR
    ↓ [Extracted text + confidence scores]
Gemini AI Tradeline Parsing
    ↓ [Structured tradeline data]
Negative Item Classification (Rule-based)
    ↓ [Tradeline + negative flags]
PostgreSQL Insert (tradelines table)
    ↓ [Stored tradeline records]
User Dashboard Display
```

**Pipeline Implementation**:

**Step 1: File Upload to Supabase Storage**
```python
# Frontend upload to Supabase Storage
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Upload PDF to storage bucket
file_path = supabase.storage.from_('credit-reports').upload(
    path=f"{user_id}/{report_id}.pdf",
    file=pdf_file_bytes,
    file_options={"content-type": "application/pdf"}
)

# Insert credit_reports record with file URL
supabase.table('credit_reports').insert({
    "id": report_id,
    "user_id": user_id,
    "bureau_source": "unknown",  # To be detected by AI
    "file_url": file_path,
    "processing_status": "pending"
}).execute()
```

**Step 2: Background Job Trigger**
```python
# FastAPI endpoint triggers Celery background job
from celery import Celery
from fastapi import FastAPI, UploadFile

app = FastAPI()
celery_app = Celery('tasks', broker='redis://localhost:6379/0')

@app.post("/api/v1/upload-credit-report")
async def upload_credit_report(file: UploadFile, user_id: str):
    # Upload to Supabase Storage (Step 1)
    report_id = upload_to_storage(file, user_id)

    # Trigger background processing job
    celery_app.send_task('process_credit_report', args=[report_id, user_id])

    return {"report_id": report_id, "status": "processing"}
```

**Step 3: Google Document AI OCR**
```python
# Celery task: OCR processing
from google.cloud import documentai_v1 as documentai

@celery_app.task(name='process_credit_report')
def process_credit_report(report_id: str, user_id: str):
    # Download PDF from Supabase Storage
    pdf_bytes = download_from_storage(report_id)

    # Google Document AI OCR
    client = documentai.DocumentProcessorServiceClient()
    request = documentai.ProcessRequest(
        name=DOCUMENT_AI_PROCESSOR_NAME,
        raw_document=documentai.RawDocument(
            content=pdf_bytes,
            mime_type="application/pdf"
        )
    )
    result = client.process_document(request=request)

    # Extract text with confidence scores
    ocr_text = result.document.text
    ocr_confidence = result.document.pages[0].layout.confidence

    # Update processing status
    update_report_status(report_id, "processing", {
        "ocr_confidence": ocr_confidence,
        "page_count": len(result.document.pages)
    })

    # Next step: Gemini AI parsing
    parse_tradelines_with_gemini(report_id, user_id, ocr_text)
```

**Step 4: Gemini AI Tradeline Parsing**
```python
# Gemini AI tradeline extraction
import google.generativeai as genai

def parse_tradelines_with_gemini(report_id: str, user_id: str, ocr_text: str):
    # Gemini prompt for structured tradeline extraction
    prompt = f"""
    Extract all tradeline accounts from the following credit report text.
    For each tradeline, extract:
    - Account Name (creditor name)
    - Account Type (credit_card, mortgage, auto_loan, student_loan, personal_loan, other)
    - Account Number (last 4 digits only)
    - Status (Open, Closed, Charge-off, Collection)
    - Balance, Credit Limit, Open Date, Closed Date
    - Payment History (array of monthly statuses: OK, 30, 60, 90, 120+)

    Return JSON array of tradelines.

    Credit Report Text:
    {ocr_text}
    """

    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    response = model.generate_content(prompt)

    # Parse JSON response
    tradelines_data = json.loads(response.text)

    # Next step: Classify negative items
    classify_negative_tradelines(report_id, user_id, tradelines_data)
```

**Step 5: Negative Item Classification (Rule-Based)**
```python
# Rule-based negative tradeline classification
def classify_negative_tradelines(report_id: str, user_id: str, tradelines_data: list):
    negative_keywords = {
        'late_payment': ['30 days late', '60 days late', '90 days late', '120+ days late'],
        'charge_off': ['charge-off', 'charged off'],
        'collection': ['collection', 'collections'],
        'bankruptcy': ['bankruptcy', 'chapter 7', 'chapter 13'],
        'foreclosure': ['foreclosure', 'foreclosed'],
        'repossession': ['repossession', 'repo'],
        'tax_lien': ['tax lien'],
        'judgment': ['judgment', 'civil judgment']
    }

    for tradeline in tradelines_data:
        # Check payment history for late payments
        payment_history = tradeline.get('payment_history', [])
        has_late_payment = any(status in ['30', '60', '90', '120+'] for status in payment_history)

        # Check status field for derogatory keywords
        status_lower = tradeline.get('status', '').lower()
        negative_type = None
        negative_reason = None

        for neg_type, keywords in negative_keywords.items():
            if any(keyword in status_lower for keyword in keywords):
                negative_type = neg_type
                negative_reason = f"Status contains derogatory keyword: {status_lower}"
                break

        if has_late_payment and not negative_type:
            negative_type = 'late_payment'
            negative_reason = f"Payment history contains late payments: {payment_history}"

        is_negative = negative_type is not None

        # Insert tradeline into PostgreSQL
        insert_tradeline(
            report_id=report_id,
            user_id=user_id,
            account_name=tradeline['account_name'],
            account_type=tradeline['account_type'],
            account_number_last_4=tradeline.get('account_number_last_4'),
            status=tradeline.get('status'),
            balance=tradeline.get('balance'),
            credit_limit=tradeline.get('credit_limit'),
            payment_history=payment_history,
            open_date=tradeline.get('open_date'),
            closed_date=tradeline.get('closed_date'),
            is_negative=is_negative,
            negative_type=negative_type,
            negative_reason=negative_reason,
            is_disputable=is_negative,  # Default: all negative items are disputable
            tradeline_details=tradeline  # Store full Gemini response as JSONB
        )

    # Update report processing status
    update_report_status(report_id, "completed")
```

**Pipeline Performance Characteristics**:
- **OCR processing**: 5-15 seconds per page (Google Document AI)
- **Gemini parsing**: 10-30 seconds per credit report (depends on tradeline count)
- **Negative classification**: <1 second (rule-based logic)
- **Total pipeline time**: 30-60 seconds for typical 3-page credit report
- **Large file handling**: Files >10MB processed in background with progress tracking

**Error Handling Strategy**:
```python
# Retry logic with exponential backoff
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
def call_document_ai_with_retry(pdf_bytes):
    return client.process_document(request=request)

# Error logging and status update
try:
    ocr_text = call_document_ai_with_retry(pdf_bytes)
except Exception as e:
    update_report_status(report_id, "failed", {
        "processing_error": str(e),
        "retry_count": 3
    })
    raise
```

### 2.2 Bureau Response OCR Pipeline (Phase 2 - Optional)

**Pipeline Flow**:

```
User Upload (Bureau Response PDF)
    ↓ [Bureau letter PDF]
Supabase Storage
    ↓ [File URL]
FastAPI Background Job (Celery)
    ↓ [PDF bytes]
Gemini AI OCR + Status Extraction
    ↓ [Extracted status: "deleted", "verified", etc.]
Confidence Score Validation (>80%)
    ↓ [Validated status update]
Update dispute_tracking.status
    ↓ [Trigger analytics refresh]
Update user_analytics (cached aggregations)
```

**Gemini Prompt for Bureau Response Parsing**:
```python
def parse_bureau_response_with_gemini(dispute_id: str, response_pdf_bytes: bytes):
    # Convert PDF to text using Gemini Vision API
    prompt = """
    This is a credit bureau response letter regarding a dispute.
    Extract the following information:
    - Bureau name (Equifax, TransUnion, or Experian)
    - Account name or tradeline being disputed
    - Resolution status (choose one):
      * "deleted" - Item removed from report
      * "verified" - Item confirmed accurate, remains on report
      * "updated" - Item modified but not removed
      * "investigating" - Bureau is still investigating
    - Resolution reason (brief explanation)

    Return JSON: {"bureau": "...", "account_name": "...", "status": "...", "reason": "..."}
    """

    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    response = model.generate_content([prompt, {"mime_type": "application/pdf", "data": response_pdf_bytes}])

    result = json.loads(response.text)

    # Validate confidence score (if available from Gemini)
    if result.get('confidence', 1.0) < 0.80:
        # Low confidence - flag for manual review
        return {
            "status": "manual_review_required",
            "extracted_data": result,
            "confidence": result.get('confidence')
        }

    # Update dispute tracking status
    update_dispute_status(
        dispute_id=dispute_id,
        new_status=result['status'],
        status_updated_by='ocr_system',
        resolution_notes=result['reason'],
        bureau_response_url=response_pdf_url
    )
```

**User Experience Flow**:
1. User receives bureau response letter in mail
2. User uploads PDF to Credit Clarity dashboard
3. OCR extracts status automatically (30 seconds processing)
4. User confirms extracted status (or corrects if OCR incorrect)
5. Status update triggers analytics refresh and audit trail logging

**Fallback to Manual Updates**:
- If OCR confidence <80%, prompt user for manual status selection
- User can always override OCR-extracted status
- Manual updates bypass OCR pipeline entirely (direct status update)

## 3. Mailing Service Integration Pipeline

### 3.1 Phase 1: Lob.com API Integration

**Pipeline Flow**:

```
User Clicks "Mail Letter" (Frontend)
    ↓ [Dispute letter ID, payment confirmed]
FastAPI Payment Processing
    ↓ [Stripe payment success]
Lob.com API Request (Certified Mail)
    ↓ [Letter content, recipient address, certified mail option]
Lob API Response
    ↓ [Tracking number, mailing ID, expected delivery date]
Insert mailing_records (PostgreSQL)
    ↓ [Store tracking number, delivery status]
Update dispute_letters.is_mailed = TRUE
    ↓ [Mark letter as mailed]
Create dispute_tracking record (status = "pending")
    ↓ [Initialize bureau dispute tracking]
User Dashboard Display (Tracking Number)
```

**Lob.com API Implementation**:

```python
import lob

# Configure Lob API client
lob.api_key = LOB_API_KEY

@app.post("/api/v1/mail-dispute-letter")
async def mail_dispute_letter(letter_id: str, user_id: str, payment_id: str):
    # Verify payment processed (Stripe)
    payment_verified = verify_stripe_payment(payment_id)
    if not payment_verified:
        raise HTTPException(status_code=402, detail="Payment required")

    # Fetch dispute letter content
    letter = fetch_dispute_letter(letter_id, user_id)

    # Fetch user address (from user profile)
    user_address = fetch_user_address(user_id)

    # Determine bureau address
    bureau_address = get_bureau_mailing_address(letter['bureau'])

    # Lob.com API request
    try:
        lob_response = lob.Letter.create(
            description=f"Dispute letter for {letter['tradeline_id']}",
            to_address={
                "name": bureau_address['name'],
                "address_line1": bureau_address['address_line1'],
                "address_city": bureau_address['city'],
                "address_state": bureau_address['state'],
                "address_zip": bureau_address['zip']
            },
            from_address={
                "name": user_address['name'],
                "address_line1": user_address['address_line1'],
                "address_city": user_address['city'],
                "address_state": user_address['state'],
                "address_zip": user_address['zip']
            },
            file=letter['letter_content'],  # HTML or PDF letter content
            color=False,  # Black & white printing (cost optimization)
            extra_service="certified",  # Certified mail with tracking
            mail_type="usps_first_class"
        )

        # Extract tracking number and mailing details
        tracking_number = lob_response.tracking_number
        expected_delivery_date = lob_response.expected_delivery_date

        # Insert mailing record
        insert_mailing_record(
            user_id=user_id,
            dispute_letter_id=letter_id,
            mailing_service='lob',
            tracking_number=tracking_number,
            mailing_date=datetime.now(),
            delivery_status='sent',
            api_response=lob_response.to_dict()
        )

        # Update dispute letter
        update_dispute_letter(letter_id, {
            "is_mailed": True,
            "mailing_date": datetime.now(),
            "tracking_number": tracking_number
        })

        # Create dispute tracking record
        create_dispute_tracking(
            user_id=user_id,
            dispute_letter_id=letter_id,
            tradeline_id=letter['tradeline_id'],
            bureau=letter['bureau'],
            status='pending',
            mailing_date=datetime.now(),
            tracking_number=tracking_number
        )

        return {
            "tracking_number": tracking_number,
            "expected_delivery_date": expected_delivery_date,
            "status": "mailed"
        }

    except lob.error.LobError as e:
        # Log error and retry
        log_integration_error('lob', str(e), letter_id)
        raise HTTPException(status_code=500, detail="Mailing service error")
```

**Bureau Mailing Addresses** (stored in application config):
```python
BUREAU_ADDRESSES = {
    "equifax": {
        "name": "Equifax Information Services LLC",
        "address_line1": "P.O. Box 740256",
        "city": "Atlanta",
        "state": "GA",
        "zip": "30374"
    },
    "transunion": {
        "name": "TransUnion Consumer Solutions",
        "address_line1": "P.O. Box 2000",
        "city": "Chester",
        "state": "PA",
        "zip": "19016"
    },
    "experian": {
        "name": "Experian National Consumer Assistance Center",
        "address_line1": "P.O. Box 4500",
        "city": "Allen",
        "state": "TX",
        "zip": "75013"
    }
}
```

**Lob.com Cost Estimates**:
- **Certified mail**: $1.65 per letter (Lob pricing as of 2024)
- **Credit Clarity pricing**: $5-10 per letter
- **Gross margin**: $3.35-8.35 per letter (67-83% margin)

### 3.2 Phase 2: USPS API Direct Integration (Cost Optimization)

**Migration Timeline**: Months 7-12 (after validating demand with Lob.com)

**USPS API Advantages**:
- **Lower cost**: $0.60-1.00 per certified mail letter (vs $1.65 Lob)
- **Direct tracking**: USPS Tracking API integration for delivery updates
- **Higher margin**: $4-9 per letter gross profit (80-90% margin)

**USPS API Implementation** (pseudocode):
```python
import usps  # USPS Web Tools API wrapper

@app.post("/api/v1/mail-dispute-letter-usps")
async def mail_dispute_letter_usps(letter_id: str, user_id: str):
    # Same payment verification and letter fetch as Lob

    # USPS API request
    usps_client = usps.USPSApi(USPS_USER_ID)

    # Generate PDF letter (Credit Clarity rendering)
    letter_pdf = render_dispute_letter_pdf(letter['letter_content'])

    # Upload letter to USPS eVS (Electronic Verification System)
    evs_response = usps_client.upload_letter(
        letter_pdf=letter_pdf,
        mail_class="certified",
        destination_address=bureau_address,
        return_address=user_address
    )

    tracking_number = evs_response.tracking_number

    # Same mailing record creation and dispute tracking as Lob
    # ...
```

**USPS Integration Complexity**:
- **Higher implementation effort**: 2-4 weeks vs 2-3 days for Lob
- **PDF generation requirement**: Credit Clarity must render letter PDFs (Lob handles this)
- **Address validation**: USPS API requires pre-validated addresses (Lob validates automatically)
- **Tracking webhook setup**: USPS Tracking API requires webhook endpoint for delivery updates

**Migration Strategy**:
1. **Month 7-8**: Implement USPS API integration in parallel with Lob
2. **Month 9**: A/B test 10% of mailings via USPS (monitor delivery success rate)
3. **Month 10-11**: Gradually increase USPS percentage (50% → 80% → 100%)
4. **Month 12**: Deprecate Lob integration (keep as fallback for failed USPS requests)

## 4. Status Update & Analytics Pipeline

### 4.1 Manual Status Update Flow

**Pipeline Flow**:

```
User Selects New Status (Frontend)
    ↓ [Dispute ID, new status, resolution notes]
FastAPI Status Update API
    ↓ [Validate status transition]
Update dispute_tracking.status
    ↓ [Trigger: log_status_change()]
Insert status_history (Audit Trail)
    ↓ [Trigger: trigger_analytics_refresh()]
Recalculate user_analytics (Cached Aggregations)
    ↓ [Update success rate, items deleted, etc.]
Dashboard Refresh (Frontend)
```

**Status Transition Validation**:
```python
# Valid status transitions (state machine)
VALID_STATUS_TRANSITIONS = {
    "pending": ["investigating", "expired"],
    "investigating": ["verified", "deleted", "updated", "escalated"],
    "verified": ["escalated"],
    "deleted": [],  # Terminal state
    "updated": ["escalated"],
    "escalated": ["investigating", "verified", "deleted", "updated"],
    "expired": ["escalated"],
    "blank": []  # Terminal state (never reported by bureau)
}

@app.put("/api/v1/dispute-tracking/{dispute_id}/status")
async def update_dispute_status(dispute_id: str, new_status: str, user_id: str, notes: str):
    # Fetch current status
    dispute = fetch_dispute_tracking(dispute_id, user_id)
    current_status = dispute['status']

    # Validate transition
    if new_status not in VALID_STATUS_TRANSITIONS.get(current_status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition: {current_status} → {new_status}"
        )

    # Update status (triggers database trigger)
    update_dispute_tracking_status(
        dispute_id=dispute_id,
        new_status=new_status,
        status_updated_by='user',
        resolution_notes=notes
    )

    return {"status": "updated", "new_status": new_status}
```

**Database Trigger for Analytics Refresh** (from @analysis-database-architecture-strategy.md):
```sql
-- Trigger automatically fires on dispute_tracking.status UPDATE
CREATE TRIGGER after_dispute_status_change
AFTER UPDATE ON dispute_tracking
FOR EACH ROW EXECUTE FUNCTION trigger_analytics_refresh();

-- Function recalculates user_analytics
CREATE OR REPLACE FUNCTION trigger_analytics_refresh()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM refresh_user_analytics(NEW.user_id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### 4.2 Analytics Calculation Logic

**Analytics Aggregation Function** (see @analysis-database-architecture-strategy.md for full SQL):

```sql
-- refresh_user_analytics() function calculates:
-- 1. total_disputes_initiated: COUNT(*)
-- 2. total_items_deleted: COUNT(*) FILTER (WHERE status = 'deleted')
-- 3. success_rate: (items_deleted / total_disputes) * 100
-- 4. average_days_to_resolution: AVG(deleted_timestamp - pending_timestamp)
-- 5. disputes_by_bureau: JSONB count per bureau
```

**Performance Optimization**:
- **Cached results**: Analytics stored in `user_analytics` table (dashboard reads cached data)
- **Trigger-based refresh**: Recalculation only on status change (not on every dashboard load)
- **Background execution**: Trigger runs asynchronously (non-blocking for user request)

**Dashboard Query** (fast cached read):
```sql
-- Dashboard fetches cached analytics (5ms query)
SELECT
    total_disputes_initiated,
    total_items_deleted,
    success_rate,
    average_days_to_resolution,
    disputes_by_bureau
FROM user_analytics
WHERE user_id = $1;
```

## 5. Third-Party API Error Handling & Retry Strategy

### 5.1 Retry Logic with Exponential Backoff

**Pattern**: Retry failed API calls with increasing delays

**Implementation**:
```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Retry configuration for external API calls
@retry(
    stop=stop_after_attempt(3),  # Max 3 attempts
    wait=wait_exponential(multiplier=1, min=4, max=10),  # 4s, 8s, 10s delays
    retry=retry_if_exception_type((requests.exceptions.Timeout, requests.exceptions.ConnectionError)),
    reraise=True
)
def call_external_api_with_retry(url, payload):
    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()
```

**Error Logging**:
```python
# Log all API errors for debugging
def log_integration_error(service: str, error_message: str, context: dict):
    logger.error(f"Integration error: {service}", extra={
        "service": service,
        "error": error_message,
        "context": context,
        "timestamp": datetime.now().isoformat()
    })

    # Store in database for monitoring
    insert_api_error_log(
        service=service,
        error_message=error_message,
        context=json.dumps(context),
        timestamp=datetime.now()
    )
```

### 5.2 Idempotency for Safe Retries

**Pattern**: Use idempotency keys to prevent duplicate operations on retry

**Example: Lob.com Mailing**:
```python
# Generate idempotent request ID
import hashlib

def generate_idempotency_key(letter_id: str, user_id: str):
    return hashlib.sha256(f"{letter_id}:{user_id}".encode()).hexdigest()

# Lob API request with idempotency
lob_response = lob.Letter.create(
    idempotency_key=generate_idempotency_key(letter_id, user_id),
    # ... (rest of parameters)
)
```

**Benefits**:
- **Safe retries**: If request fails and retries, Lob recognizes duplicate and returns original response
- **Prevents double-mailing**: User won't be charged twice if retry succeeds
- **Audit trail**: All retry attempts logged with same idempotency key

### 5.3 Circuit Breaker Pattern (Future Enhancement)

**Pattern**: Stop calling failing service after threshold of errors

**Implementation** (Phase 4):
```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
def call_lob_api(payload):
    return lob.Letter.create(**payload)
```

**Behavior**:
- After 5 consecutive failures, circuit "opens" and stops calling Lob API
- Returns cached failure response immediately (fail fast)
- After 60 seconds, circuit "half-opens" and allows 1 test request
- If test succeeds, circuit "closes" and resumes normal operation

## 6. Data Pipeline Monitoring & Observability

### 6.1 Pipeline Metrics

**Metrics to Track**:
1. **OCR pipeline**:
   - Average OCR processing time per page
   - OCR confidence score distribution
   - Failed OCR attempts (retry count)
2. **Gemini AI pipeline**:
   - Average parsing time per credit report
   - Tradeline extraction accuracy (validated against user corrections)
   - Classification accuracy for negative items
3. **Mailing service**:
   - Mailing success rate (Lob API response 200)
   - Average time to tracking number assignment
   - Delivery status distribution (sent, delivered, failed)
4. **Analytics pipeline**:
   - Analytics refresh trigger frequency
   - Average analytics calculation time
   - Cache hit rate for user_analytics queries

**Monitoring Implementation** (Prometheus + Grafana):
```python
from prometheus_client import Counter, Histogram

# Define metrics
ocr_processing_time = Histogram('ocr_processing_seconds', 'OCR processing time')
gemini_parsing_time = Histogram('gemini_parsing_seconds', 'Gemini parsing time')
mailing_success_rate = Counter('mailing_requests_total', 'Total mailing requests', ['status'])

# Instrument code
@ocr_processing_time.time()
def process_ocr(pdf_bytes):
    # OCR processing logic
    pass

# Increment counters
mailing_success_rate.labels(status='success').inc()
```

### 6.2 Data Quality Monitoring

**Automated Data Quality Checks**:
```sql
-- Daily data quality report (run via cron job)
SELECT
    COUNT(*) FILTER (WHERE is_negative = TRUE) AS negative_tradelines,
    COUNT(*) FILTER (WHERE is_negative = TRUE AND negative_type IS NULL) AS missing_negative_type,
    COUNT(*) FILTER (WHERE payment_history IS NULL) AS missing_payment_history,
    AVG(jsonb_array_length(payment_history)) AS avg_payment_history_length
FROM tradelines
WHERE created_at >= NOW() - INTERVAL '1 day';
```

**Alerts**:
- **High failure rate**: >10% OCR failures in 1-hour window
- **Low classification accuracy**: <90% negative item detection rate
- **Mailing failures**: >5% Lob API errors in 24 hours
- **Data quality**: >5% tradelines missing negative_type when is_negative = TRUE

## Summary of Data Integration Pipeline Decisions

1. **Asynchronous AI pipeline**: Celery background jobs for OCR and Gemini parsing (30-60s processing)
2. **Rule-based negative classification**: Keyword matching + payment history analysis (95%+ accuracy target)
3. **Lob.com Phase 1 mailing**: Fast GTM with $1.65/letter cost, migrate to USPS in Phase 2
4. **USPS API Phase 2 migration**: Reduce unit cost to $0.60-1.00/letter (80-90% margin)
5. **Trigger-based analytics refresh**: Automatic `user_analytics` cache update on status change
6. **Retry with exponential backoff**: 3 attempts for external API calls (4s, 8s, 10s delays)
7. **Idempotency for safe retries**: Prevent duplicate mailings on API retry
8. **Gemini OCR for bureau responses** (Phase 2): Optional OCR with 80% confidence threshold, manual fallback
9. **Status transition validation**: State machine prevents invalid status changes
10. **Comprehensive monitoring**: Prometheus metrics for pipeline performance and data quality

**Next Steps**:
- **@analysis-security-compliance-governance.md**: FCRA compliance and data protection framework
- **@analysis-scalability-performance-capacity.md**: Performance optimization and capacity planning
