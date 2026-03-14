# System Architect Analysis: Credit Clarity Platform Architecture

**Reference Framework**: @../guidance-specification.md
**Session**: WFS-brainstorm-for-a-prd
**Role**: System Architect
**Date**: 2026-01-03

---

## Executive Summary

This analysis addresses the system architecture requirements for the Credit Clarity platform's evolution from MVP to full-featured B2C SaaS platform. The architecture must support the confirmed monetization strategy (freemium + paid mailing service) while enabling viral growth through SEO and organic channels.

**Current State**: Modular Phase 3 architecture with clean separation of concerns
**Target State**: Scalable multi-tenant architecture supporting 1000+ users by month 12
**Key Challenge**: Balancing rapid MVP delivery with scalable foundation for phases 2-4

---

## Section Breakdown

This analysis is organized into focused sections addressing the key architectural domains from @../guidance-specification.md:

- **@analysis-ai-ml-architecture.md** - AI/ML pipeline design and integration strategy
- **@analysis-service-integration.md** - Mailing service, external APIs, and third-party integrations
- **@analysis-data-infrastructure.md** - Database architecture, caching, and data flow patterns
- **@analysis-scalability-performance.md** - Horizontal/vertical scaling, performance optimization
- **@analysis-security-compliance.md** - FCRA compliance, encryption, authentication architecture

---

## 1. Current Architecture Assessment

### Existing Foundation Strengths

**Phase 3 Modular Architecture** (from ARCHITECTURE_GUIDE.md):
- ✅ Clean layer separation: API → Business Logic → Data
- ✅ Versioned endpoints (`/api/v1/`) enabling future evolution
- ✅ Supabase integration for database and authentication
- ✅ Multi-level caching (Redis + in-memory)
- ✅ Background job processing capability (transitioning to Celery — see Section 9.2)
- ✅ Structured error handling and logging

**Current Technology Stack**:
- **Backend**: FastAPI (Python) with Pydantic validation
- **Database**: PostgreSQL via Supabase with RLS
- **AI/ML**: Google Document AI (OCR) + Gemini AI (parsing)
- **Caching**: Redis + in-memory LRU cache
- **Authentication**: Supabase Auth with JWT

### Architecture Gaps for PRD Requirements

**Phase 1 (MVP) Gaps**:
1. ❌ No rate limiting implementation (freemium tier enforcement)
2. ❌ No mailing service integration (Lob.com API)
3. ❌ No multi-bureau tracking data model
4. ❌ No negative tradeline AI classification pipeline
5. ❌ No dispute letter generation service
6. ❌ No Stripe webhook endpoint for payment reliability
7. ❌ No CROA disclosure verification in checkout flow
8. ❌ No email notification infrastructure

**Phase 2-4 Gaps**:
1. ❌ No time-series database (TimescaleDB for score tracking — see Section 8 for deployment decision)
2. ❌ No vector database (Pinecone/Weaviate for chatbot RAG)
3. ❌ No USPS API Direct integration path
4. ❌ No OCR for bureau response letters

---

## 2. AI & Machine Learning Architecture

**See**: @analysis-ai-ml-architecture.md for detailed AI/ML pipeline design

### Phase 1 AI Pipeline (MVP)

**Negative Tradeline Identification Flow**:
```
PDF Upload → Google Document AI (OCR) → Gemini AI (Parsing) →
Rule-Based Classifier → Negative Tradelines → Dashboard
```

**Existing Implementation**:
- ✅ `NegativeTradelineClassifier` with multi-factor weighted scoring (services/advanced_parsing/)
- ✅ Google Document AI service integration
- ✅ Gemini AI integration via `gemini_api_key`
- ✅ Background job processing framework (migrating to Celery workers)

**Architecture Decisions**:

**Decision 1: Hybrid AI Approach (Document AI + Gemini + Rules)**
- **Rationale**: Leverages specialized services at each layer
  - Document AI: Industry-leading OCR accuracy (95%+)
  - Gemini: Natural language understanding for tradeline parsing
  - Rules: Deterministic negative item classification (explainable)
- **Trade-off**: Higher cost vs. accuracy and explainability
- **Mitigation**: Cache OCR results, use Gemini only for complex parsing

**Decision 2: Rule-Based Classification Layer**
- **Rationale**: FCRA compliance requires explainable AI decisions
- **Implementation**: `NegativeTradelineClassifier` with weighted factors
  - Status keywords (40% weight): "charge off", "collection", "bankruptcy"
  - Payment history (30%): Late payment counts (30/60/90/120 days)
  - Balance analysis (15%): Charge-off amounts, settlement indicators
  - Creditor detection (10%): Collection agency identification
  - Remarks parsing (5%): Derogatory comment keywords
- **Accuracy Target**: 95%+ negative item detection rate
- **Confidence Scoring**: Threshold 0.50 for negative classification

**Decision 3: Celery Workers for PDF/AI Processing (EP-002)**
- **Rationale**: Large credit reports (10MB+) take 30-90 seconds to process; in-process FastAPI BackgroundTasks are permanently lost on server crash with no recovery path
- **Implementation**: Celery task queue using existing Redis infrastructure as broker
- **Worker Deployment**: One Celery worker process per API instance; workers can be scaled independently under load without scaling API instances
- **Error Handling**: 3 retry attempts with exponential backoff (4s, 16s, 64s); transition to `processing_status = 'failed'` with user notification on final failure
- **User Experience**: Real-time progress updates via polling (0% → 30% → 60% → 100%)
- **Migration Note**: Existing FastAPI `BackgroundTasks` references in the codebase are superseded by Celery task dispatch; no new vendor dependency is introduced (Redis already in infrastructure)

### Phase 3 AI Enhancements

**Credit Score Prediction Engine** (Hybrid Rules + ML):
- **Architecture**: Two-layer prediction system
  1. Rule-based baseline using FICO scoring factors (payment history 35%, utilization 30%, etc.)
  2. ML refinement layer (XGBoost/LightGBM) for personalized predictions
- **Training Data Strategy**: Hybrid sources
  - User uploads with consent (opt-in analytics)
  - Synthetic data generation (FICO rule simulations)
  - Public datasets (Kaggle credit behavior data)
- **Infrastructure Requirement**: TimescaleDB for historical score tracking (see Section 8)

**Financial Advice Chatbot** (Hybrid RAG + Rules):
- **Architecture**: Two-tier query routing
  1. Rule-based responses for common questions (fast, cheap)
     - "How long do late payments stay?" → Template response
  2. RAG system for complex queries (Pinecone/Weaviate + Gemini)
     - "Should I pay off charge-off or settle collection first for 700+ score?"
- **Context Sources**:
  - Credit repair knowledge base (FCRA regulations, dispute strategies)
  - User's credit profile (personalized recommendations)
- **Vector Database Selection**: Pinecone (managed) vs. Weaviate (self-hosted)
  - **Recommendation**: Start with Pinecone for Phase 3 (faster GTM)

---

## 3. Mailing Service Integration Architecture

**See**: @analysis-service-integration.md for detailed integration patterns

### Phase 1: Lob.com Integration (MVP)

**Architecture Pattern**: Celery task dispatch via background job

```python
# Simplified integration flow (dispatched as Celery task)
async def send_dispute_letter(user_id: str, letter_content: str, bureau: str):
    # 1. Generate PDF from letter content
    pdf_bytes = generate_letter_pdf(letter_content, bureau)

    # 2. Create Lob.com letter via API
    lob_response = await lob_client.letters.create(
        to_address={...},
        from_address={...},
        file=pdf_bytes,
        mail_type="certified",
        return_envelope=True
    )

    # 3. Store tracking number in database
    await create_dispute_record(
        user_id=user_id,
        bureau=bureau,
        tracking_number=lob_response.tracking_number,
        status="Pending"
    )

    # 4. Return tracking number to user
    return lob_response.tracking_number
```

**Cost Structure**:
- Lob.com certified mail: ~$1.50-2.00 per letter
- Pricing model: $5-10 per letter (60-85% gross margin)
- Expected margin pressure: Phase 2 USPS migration for cost reduction

**Error Handling**:
- Lob API failures: Retry with exponential backoff (3 attempts, 4s/16s/64s intervals)
- Payment failures: Hold letter, notify user, retry after 24h
- Invalid address: Validate with Lob address verification before send

### Phase 2: USPS API Direct Migration

**Migration Strategy**: Phased rollout with A/B testing
1. **Month 7**: Implement USPS API integration in parallel
2. **Month 8**: A/B test 10% of letters via USPS
3. **Month 9**: Increase to 50% USPS if success metrics met
4. **Month 10**: Full migration, deprecate Lob for new letters

**USPS Integration Complexity**:
- ❌ No managed SDK (REST API only)
- ❌ Manual certified mail tracking setup
- ❌ Address standardization required (CASS certification)
- ✅ Lower cost (~$0.50-0.75 per letter including certified mail)
- ✅ Same tracking capabilities (USPS tracking numbers)

**Architecture Decision**: Abstraction Layer for Mailing Service

```python
# Mailing service interface
class MailingServiceInterface:
    async def send_letter(...) -> TrackingNumber
    async def get_tracking_status(...) -> LetterStatus

class LobMailingService(MailingServiceInterface):
    # Lob.com implementation

class USPSMailingService(MailingServiceInterface):
    # USPS API Direct implementation

# Factory pattern for service selection
def get_mailing_service(user_id: str) -> MailingServiceInterface:
    # A/B testing logic, user preferences, cost optimization
    if should_use_usps(user_id):
        return USPSMailingService()
    return LobMailingService()
```

**Benefits**:
- Zero-downtime migration
- A/B testing capability
- Fallback to Lob if USPS issues
- Cost optimization per user segment

---

## 4. Rate Limiting Architecture

**See**: @analysis-scalability-performance.md for performance optimization details

### Freemium Tier Enforcement

**Rate Limit Requirements** (from guidance-specification.md):
- 2 credit report uploads per month per user
- 3 dispute letters generated per month per user
- Expected conversion: 15-20% to paid mailing

**Selected Approach**: Hybrid Persistence (Middleware + Redis Backup)

**Architecture**:
```python
# FastAPI middleware for rate limiting
class RateLimitMiddleware:
    def __init__(self, redis_client, sync_interval=300):
        self.in_memory_cache = {}  # Fast lookup
        self.redis = redis_client  # Persistent backup
        self.sync_interval = sync_interval  # 5 minutes

    async def check_rate_limit(self, user_id: str, action: str):
        # 1. Check in-memory cache (fast)
        cache_key = f"{user_id}:{action}"
        current_count = self.in_memory_cache.get(cache_key, 0)

        # 2. Validate against limits (tier-aware)
        subscription_tier = await get_user_tier(user_id)
        limit = RATE_LIMITS[subscription_tier][action]
        # free: {'uploads': 2, 'letters': 3}
        # premium: {'uploads': unlimited, 'letters': unlimited}
        if current_count >= limit:
            raise RateLimitExceeded(action, limit, reset_date)

        # 3. Increment counter
        self.in_memory_cache[cache_key] = current_count + 1

        # 4. Periodic sync to Redis (every 5 minutes)
        if should_sync():
            await self.sync_to_redis()
```

**Tier-Aware Rate Limits** (EP-004):
- **Free tier**: 2 uploads/month, 3 letter generations/month
- **Premium tier** ($15/month): No letter generation limit; upload limits may be relaxed
- **Middleware reads `subscription_tier`** from the users table at each request; premium tier is set/revoked via Stripe subscription webhooks (see Section 5.2)

**Persistence Strategy**:
1. **In-Memory Cache**: Primary storage for request handling (sub-ms latency)
2. **Redis Backup**: Periodic sync every 5 minutes or on threshold
3. **Recovery**: On server restart, load counters from Redis
4. **Reset Logic**: Monthly counter reset via scheduled task

**Benefits**:
- ✅ Fast request handling (in-memory lookup)
- ✅ Survives server restarts (Redis persistence)
- ✅ Leverages existing Redis infrastructure
- ✅ Minimal performance overhead

**Trade-offs**:
- ⚠️ Counter drift risk (max 5 minutes of data loss on crash)
- **Mitigation**: Acceptable for freemium limits (user impact minimal)

---

## 5. Stripe Payment & Webhook Architecture

**See**: @analysis-service-integration.md for detailed integration patterns

### 5.1 Checkout Flow with CROA Compliance (EP-008)

**Architecture**: The checkout flow enforces two compliance gates before payment is processed.

```python
@router.post("/api/v1/checkout/letter/{letter_id}")
async def checkout_letter_mailing(
    letter_id: str,
    payment: PaymentMethod,
    current_user: User = Depends(get_current_user)
):
    # Gate 1: Verify CROA disclosure accepted before charging (EP-008)
    if not current_user.croa_disclosure_accepted:
        raise HTTPException(
            status_code=403,
            detail="CROA disclosure must be accepted before mailing services can be purchased"
        )

    # Gate 2: Dispatch payment via Stripe (async confirmation via webhook)
    payment_intent = await stripe_client.payment_intents.create(
        amount=500,  # $5.00 in cents
        currency="usd",
        metadata={"letter_id": letter_id, "user_id": str(current_user.user_id)}
    )

    # Record payment intent as 'pending' — final confirmation via webhook
    await create_payment_record(
        user_id=current_user.user_id,
        stripe_payment_intent_id=payment_intent.id,
        amount_cents=500,
        payment_status="pending",
        dispute_letter_ids=[letter_id]
    )

    return {
        'client_secret': payment_intent.client_secret,
        'status': 'pending',
        'note': 'Payment confirmation will be received via webhook'
    }
```

**CROA Disclosure Check**: The `croa_disclosure_accepted` field in the `users` table must be `TRUE` before `process_payment()` is called. This field is set during first checkout via a mandatory disclosure acknowledgment step distinct from the FCRA consent at registration. CROA applies specifically when users pay for the mailing service (15 U.S.C. § 1679 et seq.).

### 5.2 Stripe Webhook Architecture (EP-005)

**Endpoint**: `POST /api/v1/webhooks/stripe`

**Three Non-Negotiable Requirements**:
1. **Signature Verification**: Validate `Stripe-Signature` header using `STRIPE_WEBHOOK_SECRET` environment variable before processing any event; reject unverified requests with HTTP 400
2. **Idempotent Processing**: Check `stripe_webhook_events` table for existing `event_id` before processing; mark event as processed after completion to handle Stripe's retry behavior
3. **Event Handlers**: Route each event type to a dedicated handler function

**Event Handler Map**:

| Stripe Event | Handler Action |
|---|---|
| `payment_intent.succeeded` | Update `payments.payment_status` to `'succeeded'`; dispatch Celery task to send letter via Lob.com |
| `payment_intent.payment_failed` | Update `payments.payment_status` to `'failed'`; cancel queued mailing; send user failure notification email |
| `charge.refunded` | Update `mailing_records.delivery_status`; update `payments.payment_status` to `'refunded'` |
| `customer.subscription.created` | Set `users.subscription_tier` to `'premium'`; update `premium_expires_at`; set `premium_started_at` |
| `customer.subscription.deleted` | Set `users.subscription_tier` back to `'free'`; set `premium_cancelled_at` |
| `customer.subscription.updated` | Update `premium_expires_at`; handle plan changes and trial endings |

**Implementation Sketch**:

```python
@router.post("/api/v1/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")

    # Requirement 1: Signature verification
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Requirement 2: Idempotency check
    if await webhook_event_exists(event["id"]):
        return {"status": "already_processed"}
    await record_webhook_event(event["id"], event["type"], status="received")

    # Requirement 3: Route to handler
    handler = WEBHOOK_HANDLERS.get(event["type"])
    if handler:
        await handler(event["data"]["object"])
        await mark_webhook_processed(event["id"])

    return {"status": "processed"}
```

**Rationale**: Stripe's documentation states that only webhook events are authoritative for payment confirmation — synchronous charge responses can succeed client-side while the charge fails backend authorization. Without webhooks, the system will dispatch mailings for payments that subsequently fail, incurring ~$1.65 Lob API cost per letter with no revenue recovery.

---

## 6. Multi-Bureau Dispute Tracking Data Model

**See**: @analysis-data-infrastructure.md for complete data architecture

### Database Schema Design

**Dispute Tracking Tables** (PostgreSQL):

```sql
-- Dispute records table
CREATE TABLE disputes (
    dispute_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    tradeline_id UUID NOT NULL REFERENCES tradelines(id),
    bureau VARCHAR(20) NOT NULL CHECK (bureau IN ('Equifax', 'TransUnion', 'Experian')),
    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    letter_content TEXT NOT NULL,
    mailing_date TIMESTAMP,
    tracking_number VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT unique_dispute UNIQUE (tradeline_id, bureau)
);

-- Status history table (audit trail)
CREATE TABLE dispute_status_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dispute_id UUID NOT NULL REFERENCES disputes(dispute_id),
    previous_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    changed_by VARCHAR(50) NOT NULL, -- 'user' or 'system'
    change_reason TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

**User Analytics — Trigger-Based TABLE Approach (EP-007)**:

The `user_analytics` table is a **regular TABLE** updated by a trigger-based UPSERT within the same transaction as each status change. This replaces the previously considered `MATERIALIZED VIEW` design.

**Rationale for regular TABLE over MATERIALIZED VIEW**:
- PostgreSQL MATERIALIZED VIEWs in Supabase have documented limitations with RLS policies that require additional configuration not supported out of the box
- `REFRESH MATERIALIZED VIEW CONCURRENTLY` requires a share lock during refresh; the trigger-based UPSERT is a targeted single-row write with no table-level lock
- The trigger-based approach ensures the analytics row is updated within the same transaction as the status change — always consistent with no staleness window
- `<5ms` dashboard read on a primary key lookup outperforms the `<100ms` materialized view read target

```sql
-- User analytics as a regular TABLE (not a MATERIALIZED VIEW)
-- Updated by trigger on disputes status change
CREATE TABLE user_analytics (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id),
    total_disputes INTEGER NOT NULL DEFAULT 0,
    successful_deletions INTEGER NOT NULL DEFAULT 0,
    success_rate NUMERIC(5,2) NOT NULL DEFAULT 0,
    avg_days_to_resolution NUMERIC(8,2),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Trigger function: UPSERT analytics on status change (no REFRESH MATERIALIZED VIEW)
CREATE OR REPLACE FUNCTION update_user_analytics()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_analytics (
        user_id,
        total_disputes,
        successful_deletions,
        success_rate,
        avg_days_to_resolution,
        updated_at
    )
    SELECT
        NEW.user_id,
        COUNT(*),
        COUNT(*) FILTER (WHERE status = 'Deleted'),
        ROUND(COUNT(*) FILTER (WHERE status = 'Deleted')::NUMERIC / NULLIF(COUNT(*), 0) * 100, 2),
        AVG(EXTRACT(EPOCH FROM (updated_at - created_at)) / 86400) FILTER (WHERE status IN ('Deleted', 'Verified')),
        NOW()
    FROM disputes
    WHERE user_id = NEW.user_id
    ON CONFLICT (user_id) DO UPDATE SET
        total_disputes = EXCLUDED.total_disputes,
        successful_deletions = EXCLUDED.successful_deletions,
        success_rate = EXCLUDED.success_rate,
        avg_days_to_resolution = EXCLUDED.avg_days_to_resolution,
        updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_analytics
AFTER INSERT OR UPDATE ON disputes
FOR EACH ROW EXECUTE FUNCTION update_user_analytics();
```

**Status Types** (8 statuses from guidance-specification.md):
1. **Pending**: Letter sent, awaiting bureau processing
2. **Investigating**: Bureau acknowledged, investigation in progress
3. **Verified**: Bureau kept the item (dispute unsuccessful)
4. **Deleted**: Successfully removed from credit report
5. **Updated**: Item modified but not removed (e.g., balance corrected)
6. **Escalated**: Second-round dispute initiated
7. **Expired**: 30-day FCRA window passed without response
8. **Blank**: Never reported by this bureau

**Multi-Bureau Visualization Query**:
```sql
-- Get same tradeline status across all 3 bureaus
SELECT
    t.tradeline_id,
    t.creditor_name,
    t.account_number,
    MAX(CASE WHEN d.bureau = 'Equifax' THEN d.status ELSE 'Blank' END) as equifax_status,
    MAX(CASE WHEN d.bureau = 'TransUnion' THEN d.status ELSE 'Blank' END) as transunion_status,
    MAX(CASE WHEN d.bureau = 'Experian' THEN d.status ELSE 'Blank' END) as experian_status
FROM tradelines t
LEFT JOIN disputes d ON t.tradeline_id = d.tradeline_id
WHERE t.user_id = :user_id
GROUP BY t.tradeline_id, t.creditor_name, t.account_number;
```

---

## 7. Security & Compliance Architecture

**See**: @analysis-security-compliance.md for detailed security design

### FCRA Compliance Requirements

**Key Regulations**:
1. **15 U.S.C. § 1681**: Fair Credit Reporting Act
   - Users have right to dispute inaccurate information
   - Bureaus must investigate within 30 days
   - Automated dispute systems must be FCRA-compliant

2. **Data Privacy**:
   - Credit data retention: 7-year limit
   - User consent required for data collection
   - Right to data deletion (CCPA/GDPR)

### CROA Compliance Requirements (EP-008)

**15 U.S.C. § 1679 et seq.**: Credit Repair Organizations Act

The paid mailing service at $5-10/letter is unambiguously a credit repair service for compensation. CROA mandates:
- Specific written disclosures before providing services for compensation
- Prohibition on false representations about creditworthiness
- Prohibition on guaranteeing dispute outcomes

**Architecture Implementation**:
- `croa_disclosure_accepted` (BOOLEAN, NOT NULL, DEFAULT FALSE) field in `users` table
- `croa_disclosure_timestamp` (TIMESTAMPTZ) field in `users` table
- Checkout endpoint verifies `croa_disclosure_accepted = TRUE` before calling `process_payment()` (see Section 5.1)
- CROA disclosure step is distinct from FCRA consent at registration — CROA applies specifically at the point of paid service purchase
- Legal expert review covering both FCRA and CROA must be completed as a Phase 1 gate before letter template development begins

**CROA vs. FCRA Consent Fields**:

| Field | Regulation | When Collected | Required For |
|---|---|---|---|
| `fcra_consent_given` | FCRA | Registration | All users, data collection |
| `croa_disclosure_accepted` | CROA | First checkout | Paid mailing services only |

### Encryption Architecture

**Architecture Decisions**:

**Decision 1: Supabase RLS + Selective Encryption**
- **Row-Level Security (RLS)**: Supabase policies ensure users only access own data
- **At-Rest Encryption**: PostgreSQL full database encryption
- **In-Transit Encryption**: HTTPS/TLS for all API calls
- **Column-Level Encryption**: SSN, account numbers encrypted at application level

**Encryption Implementation**:
```python
from cryptography.fernet import Fernet

class FieldEncryption:
    def __init__(self, encryption_key: str):
        self.cipher = Fernet(encryption_key)

    def encrypt_ssn(self, ssn: str) -> str:
        return self.cipher.encrypt(ssn.encode()).decode()

    def decrypt_ssn(self, encrypted_ssn: str) -> str:
        return self.cipher.decrypt(encrypted_ssn.encode()).decode()

# Usage in tradeline storage
tradeline_data['ssn'] = field_encryption.encrypt_ssn(tradeline_data['ssn'])
```

**Decision 2: Audit Trail for Data Access**
- **Requirement**: Track who accessed credit data and when
- **Implementation**: `dispute_status_history` table with `changed_by` field
- **Use Case**: FCRA compliance audits, security incident investigation

**Decision 3: User Consent Management**
- **ML Training Consent**: Opt-in checkbox during registration
- **Data Retention Policy**: Auto-delete credit data after 7 years
- **Right to Deletion**: User-initiated data deletion endpoint

---

## 8. TimescaleDB Integration (Phase 3)

**See**: @analysis-data-infrastructure.md for time-series database design

### Deployment Decision (EP-001)

**Decision**: Adopt the Data Architect's single-database extension approach — enable TimescaleDB as an extension within the existing Supabase PostgreSQL instance.

**Rationale**: The extension approach is operationally simpler and eliminates synchronization logic that the previous separate-instance recommendation required. A dual-write pattern adds engineering complexity (second database connection, connection pooler configuration, cross-instance consistency handling) that is not justified when a single unified database is available.

**Prerequisites**:
- Verify TimescaleDB extension availability on the chosen Supabase plan tier (typically available on Pro plan) during Week 1 of implementation planning
- If the extension is unavailable on the chosen plan, fall back to the separate-instance approach with documented dual-write patterns and a dedicated connection pool

**The previous "Option 2: Separate TimescaleDB Instance + Dual-Write Pattern" recommendation is superseded by this decision.** Both approaches cannot coexist — a single topology must be selected before Phase 1 DDL is written to avoid schema incompatibilities.

### Why TimescaleDB from Start?

**Decision Rationale** (from guidance-specification.md):
- ✅ Easier to build right from beginning than migrate later
- ✅ Scalable foundation for historical score tracking
- ✅ PostgreSQL extension (familiar tooling, Supabase compatible)

**Schema Design** (within Supabase PostgreSQL via extension):
```sql
-- TimescaleDB hypertable for credit scores
CREATE TABLE credit_scores (
    user_id UUID NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    score_value INTEGER NOT NULL,
    bureau VARCHAR(20) NOT NULL,
    score_type VARCHAR(50) DEFAULT 'FICO',
    PRIMARY KEY (user_id, timestamp)
);

-- Convert to hypertable (partitioned by time)
SELECT create_hypertable('credit_scores', 'timestamp');

-- Efficient time-range queries
SELECT
    time_bucket('1 day', timestamp) AS day,
    AVG(score_value) AS avg_score
FROM credit_scores
WHERE user_id = :user_id
  AND timestamp > NOW() - INTERVAL '6 months'
GROUP BY day
ORDER BY day;
```

---

## 9. Cross-Component Integration Patterns

### 9.1 AI Pipeline → Dashboard Integration

**Flow**: Negative tradelines identified by AI automatically populate dispute dashboard

**Implementation**:
```python
async def process_credit_report(file_path: str, user_id: str):
    # 1. OCR + Parsing (dispatched as Celery task)
    tradelines = await extract_tradelines(file_path)

    # 2. Negative classification
    classifier = NegativeTradelineClassifier()
    for tradeline in tradelines:
        result = classifier.classify(tradeline)
        tradeline['is_negative'] = result.is_negative
        tradeline['confidence'] = result.confidence
        tradeline['negative_factors'] = result.indicators

    # 3. Save to database
    await save_tradelines(user_id, tradelines)

    # 4. Auto-populate dispute dashboard (negative items only)
    negative_tradelines = [t for t in tradelines if t['is_negative']]
    await create_draft_disputes(user_id, negative_tradelines)

    return {
        'total_tradelines': len(tradelines),
        'negative_count': len(negative_tradelines),
        'ready_for_dispute': True
    }
```

**User Experience**:
- Upload credit report → AI identifies 8 negative items → Dashboard shows 8 draft disputes
- User can review, edit, or exclude items before generating letters

### 9.2 Letter Generation → Checkout → Mailing Service Integration

**Flow**: Seamless one-click upgrade from generated letter to paid mailing

**Implementation**:
```python
@router.post("/api/v1/letters/generate")
async def generate_dispute_letter(request: GenerateLetterRequest):
    # 1. Generate FCRA-compliant letter
    letter_content = await generate_letter(
        tradeline=request.tradeline,
        bureau=request.bureau,
        dispute_reason=request.reason
    )

    # 2. Save letter to database (free tier)
    letter_id = await save_letter(user_id, letter_content)

    # 3. Return letter with mailing option
    return {
        'letter_id': letter_id,
        'letter_content': letter_content,
        'letter_pdf_url': f"/api/v1/letters/{letter_id}/download",
        'mailing_available': True,
        'mailing_price_cents': 500,  # $5.00
        'checkout_url': f"/api/v1/checkout/letter/{letter_id}"
    }

@router.post("/api/v1/checkout/letter/{letter_id}")
async def checkout_letter_mailing(letter_id: str, payment: PaymentMethod):
    # Gate 1: CROA disclosure check (EP-008)
    if not current_user.croa_disclosure_accepted:
        raise HTTPException(status_code=403, detail="CROA disclosure required")

    # Gate 2: Create Stripe payment intent (confirmation via webhook, not sync)
    payment_intent = await create_stripe_payment_intent(letter_id, amount_cents=500)

    # 3. Record payment as 'pending' — mailing dispatched after webhook confirmation
    await create_payment_record(letter_id=letter_id, status="pending",
                                stripe_payment_intent_id=payment_intent.id)

    return {
        'client_secret': payment_intent.client_secret,
        'status': 'pending',
        'message': 'Letter will be dispatched upon payment confirmation'
    }
    # Mailing dispatch occurs in stripe_webhook handler on payment_intent.succeeded
```

**Conversion Optimization**:
- Show convenience messaging: "Save 30 minutes of manual work"
- Display tracking number immediately after webhook confirms payment
- One-click checkout (stored payment method) for subsequent purchases

### 9.3 Status Updates → Analytics Integration (EP-007)

**Flow**: Every status change triggers synchronous update of user analytics via database trigger

**Implementation**:
```python
# Status update endpoint — analytics refresh handled by DB trigger
@router.patch("/api/v1/disputes/{dispute_id}/status")
async def update_dispute_status(dispute_id: str, new_status: str):
    # 1. Update dispute record (trigger fires automatically within same transaction)
    await update_dispute(dispute_id, status=new_status)

    # 2. Log status change history
    await log_status_change(dispute_id, new_status)

    # 3. Invalidate dashboard cache (analytics table already updated by trigger)
    cache_key = f"user_stats:{user_id}"
    await cache_service.delete(cache_key)

    # 4. Notify user and dispatch scheduled emails (if deletion successful)
    if new_status == "Deleted":
        await send_success_notification(user_id, dispute_id)

    return {'status': new_status, 'updated_at': datetime.utcnow()}

# Note: refresh_user_statistics() no longer calls
# REFRESH MATERIALIZED VIEW CONCURRENTLY user_dispute_stats
# The user_analytics TABLE is updated by the database trigger
# within the same transaction as the disputes status change.
```

**Real-Time Updates**:
- Frontend polls `/api/v1/users/me/stats` endpoint every 30 seconds
- Cache invalidation ensures fresh data after status updates
- Analytics are always consistent — no staleness window from deferred view refresh

### 9.4 Email Notification Infrastructure (EP-010)

**Email Service Provider**: SendGrid or Postmark (both provide transactional email APIs with FastAPI-compatible Python SDKs and delivery webhooks). Selection to be finalized in Week 1 of Phase 1 implementation planning.

**Notification Types**:

| Type | Trigger Mechanism | Timing |
|---|---|---|
| `onboarding_day1` | Celery beat scheduled job | Day 1 after signup, if no credit report uploaded |
| `onboarding_day3` | Celery beat scheduled job | Day 3 after signup, if no credit report uploaded |
| `fcra_deadline_warning` | Celery beat scheduled job | Day 25 after dispute creation (cannot be event-driven) |
| `item_deleted` | Status update endpoint (event-driven) | Immediately on status → Deleted |
| `item_verified` | Status update endpoint (event-driven) | Immediately on status → Verified |
| `delivery_confirmed` | Stripe webhook handler (event-driven) | On Lob.com delivery confirmation |
| `upgrade_prompt` | Celery beat scheduled job | Periodic, based on user activity signals |

**Scheduled Job Architecture** (Celery beat):
```python
# celery_config.py — beat schedule for time-based notifications
CELERYBEAT_SCHEDULE = {
    'daily-onboarding-day1-emails': {
        'task': 'tasks.notifications.send_onboarding_day1',
        'schedule': crontab(hour=9, minute=0),  # 9 AM daily
    },
    'daily-onboarding-day3-emails': {
        'task': 'tasks.notifications.send_onboarding_day3',
        'schedule': crontab(hour=9, minute=0),
    },
    'daily-fcra-deadline-warnings': {
        'task': 'tasks.notifications.send_fcra_deadline_warnings',
        'schedule': crontab(hour=8, minute=0),  # 8 AM daily
        # Query: disputes WHERE created_at = NOW() - INTERVAL '25 days'
        #         AND status NOT IN ('Deleted', 'Verified', 'Expired')
    },
}
```

**Day 25 FCRA Deadline Warning**: This notification requires a scheduled job, not an event-driven trigger — there is no application event that fires 25 days after a dispute is created. The Celery beat scheduler runs daily and queries for qualifying disputes.

**Notification Log**: All sent notifications are recorded in the `notification_log` table (see Data Architect schema) with `provider_message_id` for delivery tracking via SendGrid/Postmark webhooks.

---

## 10. PDF Processing SLA & Retry Policy (EP-009)

### Tiered SLA Definition

| File Size | Processing Target | Delivery Mode |
|---|---|---|
| < 5 MB | End-to-end in < 45 seconds | Synchronous response with progress polling |
| 5 – 10 MB | End-to-end in < 90 seconds | Synchronous response with progress polling |
| > 10 MB | Dispatched as background job | Async: polling endpoint + email notification on completion |

**Note**: The previous "<30 seconds for <10MB files" target has been replaced by this tiered SLA. The 30-second figure may have been measured under specific conditions (small files, low tradeline count); the 45-second target for <5MB files and 90-second target for 5-10MB files represent a conservative, measurable commitment. Benchmark results from actual file processing should be documented during Phase 1 development to validate or adjust these targets.

**Gunicorn Timeout Configuration**:
- Synchronous request workers: 120 seconds (covers 5-10MB files with margin)
- Background Celery job workers: 300 seconds (covers >10MB files)

### Unified Retry Policy

Applied consistently across the entire AI pipeline (not only the Lob API):

```
Attempt 1 → fail → wait 4s
Attempt 2 → fail → wait 16s
Attempt 3 → fail → processing_status = 'failed'
            → send user notification email
            → log error with file metadata for investigation
```

This matches the Data Architect's defined retry policy and provides crash recovery through Celery's durable task queue.

---

## 11. Risk Assessment & Mitigation

### Technical Risks

**Risk 1: USPS API Direct Integration Complexity**
- **Impact**: Phase 2 cost optimization may be delayed 2-3 months
- **Probability**: Medium (60%)
- **Mitigation**:
  - Start Lob.com integration in Phase 1 (fast GTM)
  - Allocate dedicated 2-week sprint for USPS integration in Month 7
  - Maintain Lob fallback for critical failures
  - A/B test USPS with 10% traffic before full migration

**Risk 2: OCR Accuracy for Bureau Response Letters**
- **Impact**: Phase 2 OCR feature may have <80% accuracy for some bureau formats
- **Probability**: Medium (50%)
- **Mitigation**:
  - Start with manual status updates (always available)
  - Add OCR as optional feature with confidence scores (see CQ-006 in Clarifications)
  - Show extracted data for user verification before saving
  - Bureau-specific OCR tuning based on user feedback

**Risk 3: Rate Limiting State Loss on Server Restart**
- **Impact**: Users may exceed free tier limits during 5-minute sync window
- **Probability**: Low (20%)
- **Mitigation**:
  - Hybrid persistence with Redis backup (selected approach)
  - Acceptable impact: Max 5 minutes of counter drift
  - User notification: "You're approaching your monthly limit"
  - Sync interval tuning: Reduce to 1 minute if abuse detected

**Risk 4: Viral Growth Overwhelming Infrastructure**
- **Impact**: Unexpected traffic spike (1000+ users in Month 3 instead of Month 12)
- **Probability**: Low (10%)
- **Mitigation**:
  - Horizontal scaling ready (stateless design)
  - Load testing before launch (simulate 500+ concurrent users)
  - Auto-scaling rules in production (CPU > 70% → add instance)
  - Background job queue throttling via Celery concurrency limits (prevent Redis overload)

**Risk 5: FCRA / CROA Compliance Violation**
- **Impact**: Legal liability, user trust damage; CROA civil liability includes actual damages, punitive damages, costs, and attorney fees (15 U.S.C. § 1679g)
- **Probability**: Low (10%)
- **Mitigation**:
  - Consult credit repair legal expert covering both FCRA and CROA before Phase 1 letter template development begins (not at launch — at development start)
  - FCRA-compliant letter templates (professional review)
  - CROA disclosure accepted before any paid mailing proceeds (enforced in checkout endpoint)
  - Audit trail for all data access and modifications
  - Disclaimer language: "This service provides tools to exercise your FCRA rights"

**Risk 6: TimescaleDB Extension Unavailable on Supabase Plan**
- **Impact**: TimescaleDB deployment topology must fall back to separate instance, adding dual-write engineering
- **Probability**: Low (15% — Pro plan typically supports extensions)
- **Mitigation**:
  - Verify extension availability in Week 1 of Phase 1 planning before DDL is written
  - Maintain documented dual-write fallback pattern (previous Option 2 design)
  - Extension verification is a zero-cost action that prevents multi-week migration later

### Operational Risks

**Risk 7: Gemini API Cost Escalation**
- **Impact**: AI costs exceed revenue in early months
- **Probability**: Medium (40%)
- **Mitigation**:
  - Cache OCR results (avoid re-processing same files)
  - Rate limit free tier aggressively (2 uploads/month)
  - Monitor API usage per user (alert on anomalies)
  - Gemini 1.5 Flash for simple queries (cheaper than Pro)

**Risk 8: Lob.com Service Outage**
- **Impact**: Unable to send dispute letters for hours/days
- **Probability**: Low (5%)
- **Mitigation**:
  - Queue letters in database via Celery (retry after outage with exponential backoff)
  - User notification: "Your letter is queued, will send when service restores"
  - USPS fallback in Phase 2 (dual provider strategy)
  - SLA monitoring (Lob status page integration)

**Risk 9: Stripe Webhook Delivery Failure**
- **Impact**: Payment confirmed client-side but mailing never dispatched; or mailing dispatched for a payment that subsequently fails
- **Probability**: Low (5%)
- **Mitigation**:
  - Idempotent webhook processing via `stripe_webhook_events` table
  - Stripe retries webhook delivery for up to 72 hours on failures
  - Monitor `stripe_webhook_events` for events stuck in `received` status
  - Manual reconciliation endpoint for support team to resolve edge cases

---

## 12. Scalability & Performance Architecture

**See**: @analysis-scalability-performance.md for detailed scaling strategies

### Horizontal Scaling Strategy

**Current Stateless Design**:
- ✅ No server-side session storage (JWT-based auth)
- ✅ Redis for shared state (cache, rate limits, Celery broker)
- ✅ Supabase for centralized database
- ✅ Celery workers for distributed background job processing

**Load Balancer Configuration** (for production):
```
[Internet] → [Load Balancer] → [FastAPI Instance 1] → [Celery Worker 1]
                             → [FastAPI Instance 2] → [Celery Worker 2]
                             → [FastAPI Instance 3] → [Celery Worker 3]
                                     ↓
                          [Redis Cluster] ← Shared cache/Celery broker
                                     ↓
                          [Supabase PostgreSQL + TimescaleDB extension]
```

**Worker Scaling**: Celery workers can be scaled independently from API instances. Under high PDF processing load, add workers without adding API capacity. Under high API request load, add API instances without adding worker capacity.

**Health Check Endpoint** (for load balancer):
```python
@router.get("/health")
async def health_check():
    # Verify critical services
    checks = {
        "database": await check_database_connection(),
        "redis": await check_redis_connection(),
        "celery": await check_celery_worker_ping(),
        "gemini_api": await check_gemini_api()
    }

    # Return 200 if all healthy, 503 if any unhealthy
    all_healthy = all(checks.values())
    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "checks": checks,
        "timestamp": datetime.utcnow()
    }
```

### Vertical Scaling Optimizations

**Multi-Worker Deployment** (Gunicorn):
```bash
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --timeout 120
```

**Configuration Tuning**:
- **Workers**: `(2 × CPU cores) + 1` for I/O-bound workloads
- **Max Requests**: Restart workers after 1000 requests (prevent memory leaks)
- **Timeout**: 120 seconds for synchronous PDF processing requests

### Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| PDF Processing (<5MB) | < 45s end-to-end | Tiered SLA (EP-009) |
| PDF Processing (5-10MB) | < 90s end-to-end | Tiered SLA (EP-009) |
| PDF Processing (>10MB) | Background job | Progress polling + email |
| API Response Time (p95) | < 200ms | CRUD operations |
| Rate Limit Check | < 5ms | In-memory cache |
| Multi-Bureau Query | < 100ms | Query optimization needed |
| User Analytics Read | < 5ms | PK lookup on user_analytics TABLE |
| Concurrent Users | 100+ simultaneous | Load testing required pre-launch |

---

## 13. Implementation Roadmap

### Phase 1 (Months 1-6): MVP Launch

**Architecture Deliverables**:
1. ✅ **Rate Limiting System**
   - Hybrid middleware + Redis persistence
   - Tier-aware limits: free (2 uploads, 3 letters/month), premium (unlimited)
   - Month: 1

2. ✅ **Celery Worker Infrastructure**
   - Replace FastAPI BackgroundTasks with Celery task dispatch
   - Redis as broker (existing infrastructure)
   - One worker per API instance; independent scaling path
   - Month: 1

3. ✅ **Lob.com Integration**
   - Direct API integration via Celery tasks
   - Certified mail with tracking numbers
   - Month: 2

4. ✅ **Stripe Integration + Webhook Endpoint**
   - Checkout flow with CROA disclosure gate
   - `/api/v1/webhooks/stripe` with signature verification
   - Idempotent webhook processing via `stripe_webhook_events` table
   - Handlers: payment_intent events, subscription events
   - Month: 2

5. ✅ **Multi-Bureau Dispute Tracking**
   - PostgreSQL schema with 8 status types
   - Status history audit trail
   - User analytics TABLE with trigger-based UPSERT
   - Month: 2-3

6. ✅ **CROA Compliance Infrastructure**
   - `croa_disclosure_accepted` field in users table
   - Disclosure step in checkout flow (pre-payment gate)
   - Legal expert review completed before letter template development
   - Month: 1 (legal review), Month: 2-3 (implementation)

7. ✅ **AI Negative Tradeline Pipeline**
   - Google Document AI OCR
   - Gemini AI parsing
   - Rule-based classification
   - Month: 3-4

8. ✅ **Dispute Letter Generation**
   - FCRA-compliant templates
   - Bureau-specific formatting
   - One-click mailing upgrade
   - Month: 4-5

9. ✅ **Email Notification Infrastructure**
   - SendGrid or Postmark integration
   - Celery beat scheduler for Day 1, Day 3, Day 25 jobs
   - Event-driven emails for status changes and delivery confirmation
   - Month: 4-5

10. ✅ **Production Deployment**
    - Gunicorn multi-worker setup
    - Load balancer health checks
    - Monitoring and logging
    - Month: 6

### Phase 2 (Months 7-12): Optimization

**Architecture Deliverables**:
1. **USPS API Direct Migration**
   - Abstraction layer for mailing services
   - A/B testing framework (10% → 50% → 100%)
   - Cost reduction: $2/letter → $0.75/letter
   - Month: 7-10

2. **OCR for Bureau Response Letters**
   - Tesseract/Google Vision integration
   - Bureau-specific parsing rules
   - Confidence scoring and user verification (strategy per CQ-006)
   - Month: 9-10

3. **Personal Success Statistics**
   - Real-time dashboard metrics (served from user_analytics TABLE)
   - Historical trend charts
   - Success rate by bureau
   - Month: 11-12

### Phase 3 (Months 13-18): AI Enhancement

**Architecture Deliverables**:
1. **TimescaleDB Integration**
   - Enable TimescaleDB extension within Supabase PostgreSQL (verified in Phase 1 Week 1)
   - Historical score tracking hypertable
   - Month: 13-14

2. **Credit Score Prediction Engine**
   - Rule-based FICO baseline
   - ML refinement layer (XGBoost)
   - Training pipeline with synthetic data
   - Month: 14-16

3. **Financial Advice Chatbot**
   - Pinecone vector database setup
   - RAG system with Gemini
   - Rule-based query routing
   - Month: 16-18

### Phase 4 (Months 19-24): Scale & Monetization

**Architecture Deliverables**:
1. **Advanced Analytics**
   - Multi-bureau comparison insights
   - Credit utilization optimizer
   - Timeline projections
   - Month: 19-20

2. **Mobile App Architecture**
   - React Native shared components
   - Same backend API (versioned endpoints)
   - Push notifications for status updates
   - Month: 20-22

3. **B2B Pilot Program**
   - Multi-tenant architecture
   - White-label capabilities
   - Admin dashboards for credit repair professionals
   - Month: 22-24

---

## 14. Success Metrics & Monitoring

### System Performance Metrics

**Availability Targets**:
- **Uptime**: 99.9% (Phase 1), 99.95% (Phase 2+)
- **API Latency (p95)**: <200ms for CRUD operations
- **PDF Processing**: Tiered SLA — <45s for <5MB, <90s for 5-10MB, background for >10MB
- **Background Jobs**: <5min queue time under normal load
- **Celery Worker Health**: Monitor via Flower or Celery events; alert on worker process death

**Infrastructure Monitoring**:
- CPU/Memory usage per instance
- Redis cache hit rate (target: >80%)
- Database connection pool utilization
- Celery task queue depth and processing rate
- Stripe webhook event processing lag

**Cost Metrics**:
- Gemini API cost per user per month (target: <$0.50)
- Lob.com mailing cost per letter (actual: ~$1.75)
- Redis/Supabase infrastructure cost per 100 users
- SendGrid/Postmark email cost per notification
- Total COGS target: <30% of revenue

### Business Metrics (Architecture Impact)

**User Growth** (Viral GTM Strategy):
- Month 6: 100+ active users
- Month 12: 1,000+ active users
- Month 24: 10,000+ active users

**Conversion Funnel** (Architecture-Enabled):
- Free tier signup → Credit report upload (80% conversion)
- Upload → Negative items identified (95% accuracy target)
- Negative items → Dispute letters generated (60% conversion)
- Letters → Paid mailing upgrade (15% conversion, $5-10/letter)
- Day 25 FCRA reminder email → Repeat purchase (30% repeat purchase target, PM milestone)

**System Scalability Validation**:
- Concurrent users supported: 100+ (Phase 1), 500+ (Phase 2)
- PDF processing throughput: 1000+ reports/day
- Celery job processing: 10,000+ jobs/day
- Database query performance: <100ms for 99% of queries

---

## Conclusion

The Credit Clarity platform architecture is well-positioned for the confirmed monetization strategy and viral growth roadmap. The existing Phase 3 modular foundation provides a solid base, with clear implementation paths for the PRD requirements.

**Key Architectural Strengths**:
- ✅ Modular design enables rapid feature development
- ✅ Scalable infrastructure ready for viral growth
- ✅ Hybrid AI approach balances accuracy with explainability
- ✅ Multi-level caching optimizes performance and cost
- ✅ Celery-based durable task queue provides crash-safe PDF processing
- ✅ Stripe webhook architecture ensures financial integrity
- ✅ CROA + FCRA compliance enforced at checkout and data layers

**Critical Path Items** (Phase 1 MVP):
1. Legal expert review for FCRA + CROA (Month 1, before template development)
2. Celery worker infrastructure + Stripe webhook endpoint (Month 1-2)
3. Lob.com integration (Month 2)
4. Multi-bureau dispute tracking + CROA disclosure gate (Month 2-3)
5. AI negative tradeline pipeline (Month 3-4)
6. Email notification infrastructure (Month 4-5)

**Long-Term Success Factors**:
- USPS migration for cost optimization (Phase 2)
- TimescaleDB extension (Supabase-native, verified Week 1 of Phase 1)
- Vector database for AI chatbot (Phase 3)
- Mobile app architecture (Phase 4)

The architecture roadmap aligns with the 12-24 month timeline and supports the expected user growth from 100 to 10,000+ users while maintaining FCRA and CROA compliance and operational excellence.

---

## Clarifications

The following open questions have architectural impact on this role's design decisions. They are derived from the cross-role synthesis and require resolution before or during Phase 1 implementation planning.

### CQ-001: TimescaleDB Deployment Location

**Question**: Should TimescaleDB be enabled as an extension within the existing Supabase PostgreSQL instance, or deployed as a separate dedicated instance with a dual-write pattern?

**Recommended Resolution**: Supabase extension (single database) — adopted in Section 8 of this analysis. Verify Pro plan tier supports the extension in Week 1 of implementation planning. If unavailable, revert to the documented separate-instance fallback.

**Impact on this analysis**: Section 8 has been updated to reflect the extension approach. If the fallback is required, the dual-write pattern and connection pool configuration documented in the original Option 2 design must be reinstated.

### CQ-002: Background Processing Framework

**Question**: Should PDF processing and AI parsing use FastAPI BackgroundTasks (in-process) or Celery workers (distributed, durable)?

**Recommended Resolution**: Celery — adopted throughout this analysis. Celery uses the existing Redis infrastructure as broker, provides crash recovery for the 30-90 second AI pipeline, and maps naturally to the Data Architect's retry policy design.

**Impact on this analysis**: All references to FastAPI BackgroundTasks for PDF/AI processing have been replaced with Celery task dispatch. Worker deployment is specified as one worker per API instance with independent scaling capability.

### CQ-006: OCR Confidence Threshold Strategy for Bureau Response Letters

**Question**: What confidence threshold strategy should be applied when OCR processes bureau response letters? Options include a single 80% threshold (DA approach), a dual-tier threshold (90% auto-confirm / 60-90% user-confirm / <60% manual), or always requiring user confirmation for Phase 2 initial release (most conservative).

**Impact on this analysis**: The OCR feature appears in Phase 2 (Months 9-10). The threshold strategy affects the frontend UX design for OCR result display, the data accuracy of FCRA audit records, and Risk 2 (OCR accuracy) mitigation approach. The conservative option (always require user confirmation) is recommended for Phase 2 initial release to establish accuracy baselines before introducing automated confirmation.

**Resolution Required By**: Phase 2 planning (Month 6-7 of development).
