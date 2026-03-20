# Data Architect Analysis: Credit Clarity Negative Tradeline Dispute Management Platform

**Session**: WFS-brainstorm-for-a-prd
**Role**: Data Architect
**Date**: 2026-03-03
**Topic Framework**: @../guidance-specification.md

---

## Executive Summary

Credit Clarity requires a data architecture that simultaneously serves four concerns that pull in different directions: the high-flexibility needs of AI-extracted credit report data, the strict integrity requirements of FCRA-governed dispute records, the real-time performance expectations of a consumer dashboard, and the long-term time-series analytics needed to track credit score improvement. This analysis resolves those tensions through a single coherent data strategy anchored in PostgreSQL with TimescaleDB, enforced through Supabase Row-Level Security, and delivered via layered caching and asynchronous pipelines.

**Canonical Architecture Decisions**:
- **Primary store**: Supabase-managed PostgreSQL 15 with RLS as the sole multi-tenancy mechanism
- **Time-series store**: TimescaleDB extension enabled from Phase 1 to prevent migration debt in Phase 3
- **Semi-structured data**: JSONB within PostgreSQL for variable tradeline fields (payment history, bureau-specific fields)
- **Caching layer**: Redis for rate-limit state and analytics warming; `user_analytics` materialized table for dashboard speed
- **Encryption model**: Database-level AES-256 (Supabase) plus Fernet column-level encryption for SSN, full account numbers, user address
- **Pipeline model**: Celery async workers for OCR and AI parsing; synchronous database triggers for audit trail and analytics refresh

---

## 1. Core Data Requirements by Feature

This section maps every confirmed feature from guidance-specification.md Section 2 to the data entities, operations, and quality standards each feature demands.

### Feature 1: AI-Powered Negative Tradeline Scanner

**Data entities required**:
- `credit_reports`: stores metadata for each uploaded PDF, processing state, bureau source
- `tradelines`: one row per extracted credit account; stores account attributes, payment history JSONB, negative classification flags

**Data operations**:
- INSERT `credit_reports` record on upload (status = `pending`)
- Background pipeline: OCR (Google Document AI) → parse (Gemini AI) → classify (rule-based) → INSERT `tradelines`
- UPDATE `credit_reports.processing_status` to `completed` or `failed`

**Quality standards**:
- 95%+ negative item detection rate (validated by comparing AI flags to user corrections)
- Zero duplicate tradelines within one credit report (deduplication on `account_name + account_number_last_4`)
- Mandatory fields: `account_name`, `account_type`, `is_negative` — never null
- Confidence score from Document AI stored in `credit_reports.metadata` JSONB for audit

**Bureau-specific format handling**:
- Equifax, TransUnion, Experian each present tradeline data in distinct formats
- `tradeline_details` JSONB column stores the raw Gemini-parsed output per bureau format without forcing a rigid schema
- The structured columns (`account_type`, `status`, `balance`, `payment_history`) are normalized to a canonical form regardless of bureau

### Feature 2: Free Dispute Letter Generation

**Data entities required**:
- `dispute_letters`: stores generated letter text, which bureau it targets, generation date, whether it was ever mailed
- Rate limit counters in `users.rate_limit_reports` and `users.rate_limit_letters` (backed by Redis)

**Data operations**:
- INSERT `dispute_letters` record on generation
- INCREMENT rate limit counter (middleware in-memory + Redis sync)
- READ free tier limits: 2 credit report uploads/month, 3 dispute letters/month

**Rate limit state model**:
```
users.rate_limit_reports     INTEGER  — current month upload count
users.rate_limit_letters     INTEGER  — current month letter count
users.rate_limit_reset_date  DATE     — first day of next calendar month
```
Redis mirrors these counters under key `user:rate_limits:{user_id}:{type}:{YYYY-MM}` using atomic INCR. Middleware reads from in-memory, syncs to Redis every 5 minutes, reloads from Redis on restart.

### Feature 3: Paid Automated Dispute Letter Mailing Service

**Data entities required**:
- `mailing_records`: one row per paid mailing; stores mailing service used (`lob` or `usps_direct`), tracking number, delivery status, full API response JSONB
- `dispute_tracking`: one row per bureau-letter pair; initialized to `pending` when mail is sent; links to mailing record for tracking number display

**Data operations**:
- Verify payment (Stripe) → call Lob.com API → INSERT `mailing_records` → UPDATE `dispute_letters.is_mailed = TRUE` → INSERT `dispute_tracking` (status = `pending`)
- Phase 2: same flow via USPS API Direct; `mailing_records.mailing_service` differentiates the two

**Idempotency requirement**:
- Idempotency key = SHA-256 of `{letter_id}:{user_id}` sent to Lob/USPS APIs
- Prevents double-mailing on API retry; duplicate Lob response returns same tracking number

**Tracking data lifecycle**:
- Tracking number stored in both `mailing_records.tracking_number` and denormalized into `dispute_tracking.tracking_number` to avoid a JOIN on the dashboard

### Feature 4: Multi-Bureau Dispute Progress Dashboard

**Data entities required**:
- `dispute_tracking`: per-bureau status record (one tradeline can have up to 3 rows, one per bureau)
- `status_history`: immutable audit log of every status transition with timestamp and attribution (user vs OCR system)
- `user_analytics`: cached aggregation table refreshed by database trigger on every status change

**Status state machine** (CONFIRMED 8 statuses):
```
pending → investigating → verified
                       → deleted      (terminal)
                       → updated → escalated
                       → escalated
       → expired → escalated
blank                              (terminal, never reported by bureau)
```
Invalid transitions are rejected by the API layer before the database UPDATE is issued.

**Multi-bureau display model**:
- Dashboard LEFT JOINs `dispute_tracking` three times (once per bureau) against `tradelines`
- Result: one row per tradeline with three status columns (`equifax_status`, `transunion_status`, `experian_status`)
- Target query time: <150ms using composite index `(user_id, tradeline_id, bureau)`

**Personal analytics** (confirmed scope: personal stats only):
- `total_disputes_initiated`: COUNT(*) from `dispute_tracking` for user
- `total_items_deleted`: COUNT(*) WHERE `status = 'deleted'`
- `success_rate`: (items_deleted / total_disputes) * 100, stored as DECIMAL(5,2)
- `average_days_to_resolution`: average of `(deleted_at - pending_at)` in days, computed from `status_history`
- All four metrics are pre-computed in `user_analytics` and refreshed by trigger; dashboard reads one row at <5ms

---

## 2. Canonical Data Model

### 2.1 Entity Relationship Map

```
users (1)
 ├── credit_reports (many)         ← one upload per session
 │    └── tradelines (many)        ← 10-30 per report
 │         └── dispute_letters (many)  ← one per bureau per negative tradeline
 │              └── dispute_tracking (many)   ← one per bureau per letter
 │                   └── status_history (many)  ← immutable audit trail
 │                   └── mailing_records (one)  ← only when is_mailed = TRUE
 ├── payments (many)               ← EP-003: one per Stripe PaymentIntent (letter/bundle)
 ├── user_analytics (one)          ← cached aggregation, trigger-refreshed (EP-007)
 ├── notification_log (many)       ← EP-010: email notification audit trail
 └── credit_score_history (many)   ← TimescaleDB hypertable, Phase 3
stripe_webhook_events              ← EP-003: global Stripe event idempotency log (no user FK)
```

### 2.2 Physical Schema — Core Tables

**Table: users**
```sql
CREATE TABLE users (
    id                          UUID PRIMARY KEY,  -- Supabase auth user ID
    email                       TEXT UNIQUE NOT NULL,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- EP-004: 'premium' = active $15/month Stripe subscription; 'free' covers both
    --         rate-limited freemium users AND per-letter purchasers (payment events,
    --         not a tier change). Per-letter buyers remain 'free'.
    subscription_tier           TEXT NOT NULL DEFAULT 'free' CHECK (subscription_tier IN ('free','premium')),
    -- EP-004: Stripe subscription tracking (NULL for free-tier users)
    premium_subscription_id     TEXT,             -- Stripe subscription ID
    premium_started_at          TIMESTAMPTZ,
    premium_expires_at          TIMESTAMPTZ,
    premium_cancelled_at        TIMESTAMPTZ,
    rate_limit_reports          INTEGER NOT NULL DEFAULT 0,
    rate_limit_letters          INTEGER NOT NULL DEFAULT 0,
    rate_limit_reset_date       DATE,
    -- FCRA consent (required before credit report upload)
    fcra_consent_given          BOOLEAN NOT NULL DEFAULT FALSE,
    fcra_consent_timestamp      TIMESTAMPTZ,
    -- EP-008: CROA consent (required before any paid mailing is accepted)
    --         Distinct from fcra_consent_given; CROA applies when user pays for services.
    croa_disclosure_accepted    BOOLEAN NOT NULL DEFAULT FALSE,
    croa_disclosure_timestamp   TIMESTAMPTZ,
    ai_training_consent         BOOLEAN NOT NULL DEFAULT FALSE,
    ai_training_consent_timestamp TIMESTAMPTZ,
    data_retention_expiry       DATE,  -- 7 years from account creation (FCRA)
    ssn_encrypted               TEXT,  -- Fernet-encrypted, never sent to frontend
    address_encrypted           JSONB, -- Fernet-encrypted address for mailing service
    metadata                    JSONB  -- user preferences, settings
);

CREATE INDEX idx_users_rate_limit_reset ON users (rate_limit_reset_date);

-- RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY "users_select_own" ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "users_update_own" ON users FOR UPDATE USING (auth.uid() = id);
```

**Table: credit_reports**
```sql
CREATE TABLE credit_reports (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bureau_source     bureau_type NOT NULL DEFAULT 'unknown',
    upload_date       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    file_url          TEXT,  -- Supabase Storage URL; set to NULL after 30-day cleanup
    processing_status processing_status NOT NULL DEFAULT 'pending',
    processing_error  TEXT,
    metadata          JSONB  -- OCR confidence, page count, file size
);

CREATE INDEX idx_credit_reports_user_date ON credit_reports (user_id, upload_date DESC);
CREATE INDEX idx_credit_reports_status   ON credit_reports (processing_status)
    WHERE processing_status IN ('pending', 'processing');

ALTER TABLE credit_reports ENABLE ROW LEVEL SECURITY;
CREATE POLICY "credit_reports_select_own" ON credit_reports FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "credit_reports_insert_own" ON credit_reports FOR INSERT WITH CHECK (auth.uid() = user_id);
```

**Table: tradelines**
```sql
CREATE TABLE tradelines (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    credit_report_id          UUID NOT NULL REFERENCES credit_reports(id) ON DELETE CASCADE,
    user_id                   UUID NOT NULL REFERENCES users(id),  -- denormalized for RLS
    account_name              TEXT NOT NULL,
    account_type              account_type NOT NULL,
    account_number_last_4     TEXT,
    status                    TEXT,          -- "Open", "Closed", "Charge-off", "Collection"
    balance                   DECIMAL(12,2),
    credit_limit              DECIMAL(12,2),
    payment_history           JSONB,         -- [{"month":"2024-01","status":"OK"}, ...]
    open_date                 DATE,
    closed_date               DATE,
    is_negative               BOOLEAN NOT NULL DEFAULT FALSE,
    negative_type             negative_type,
    negative_reason           TEXT,
    is_disputable             BOOLEAN NOT NULL DEFAULT FALSE,
    dispute_reason            TEXT,
    tradeline_details         JSONB,         -- raw bureau-specific fields
    created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tradelines_user_negative
    ON tradelines (user_id, is_negative, is_disputable)
    WHERE is_negative = TRUE;
CREATE INDEX idx_tradelines_report       ON tradelines (credit_report_id);
CREATE INDEX idx_tradelines_dedup        ON tradelines (user_id, account_name, account_number_last_4);
CREATE INDEX idx_tradelines_payment_gin  ON tradelines USING GIN (payment_history);
CREATE INDEX idx_tradelines_details_gin  ON tradelines USING GIN (tradeline_details);

ALTER TABLE tradelines ENABLE ROW LEVEL SECURITY;
CREATE POLICY "tradelines_select_own" ON tradelines FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "tradelines_update_own" ON tradelines FOR UPDATE USING (auth.uid() = user_id);
```

**Table: dispute_letters**
```sql
CREATE TABLE dispute_letters (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    tradeline_id    UUID NOT NULL REFERENCES tradelines(id) ON DELETE CASCADE,
    bureau          bureau_type NOT NULL,
    letter_content  TEXT NOT NULL,
    dispute_reason  TEXT NOT NULL,
    generation_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_mailed       BOOLEAN NOT NULL DEFAULT FALSE,
    mailing_date    TIMESTAMPTZ,
    tracking_number TEXT
);

CREATE INDEX idx_dispute_letters_user_date  ON dispute_letters (user_id, generation_date DESC);
CREATE INDEX idx_dispute_letters_tradeline  ON dispute_letters (tradeline_id, bureau);
CREATE INDEX idx_dispute_letters_mailed     ON dispute_letters (is_mailed, mailing_date)
    WHERE is_mailed = TRUE;

ALTER TABLE dispute_letters ENABLE ROW LEVEL SECURITY;
CREATE POLICY "dispute_letters_select_own" ON dispute_letters FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "dispute_letters_insert_own" ON dispute_letters FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "dispute_letters_update_own" ON dispute_letters FOR UPDATE USING (auth.uid() = user_id);
```

**Table: dispute_tracking**
```sql
CREATE TABLE dispute_tracking (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id),   -- denormalized for RLS
    dispute_letter_id   UUID NOT NULL REFERENCES dispute_letters(id) ON DELETE CASCADE,
    tradeline_id        UUID NOT NULL REFERENCES tradelines(id),
    bureau              bureau_type NOT NULL,
    status              dispute_status NOT NULL DEFAULT 'pending',
    status_updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status_updated_by   update_attribution NOT NULL DEFAULT 'user',
    mailing_date        TIMESTAMPTZ,        -- denormalized from dispute_letters
    tracking_number     TEXT,               -- denormalized from mailing_records
    bureau_response_url TEXT,               -- Supabase Storage URL for uploaded response PDF
    resolution_notes    TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, tradeline_id, bureau)  -- one tracking record per bureau per tradeline
);

CREATE INDEX idx_dispute_tracking_user         ON dispute_tracking (user_id);
CREATE INDEX idx_dispute_tracking_tradeline_bureau
    ON dispute_tracking (tradeline_id, bureau);
CREATE INDEX idx_dispute_tracking_status_date  ON dispute_tracking (status, status_updated_at);
CREATE INDEX idx_dispute_tracking_letter       ON dispute_tracking (dispute_letter_id);

ALTER TABLE dispute_tracking ENABLE ROW LEVEL SECURITY;
CREATE POLICY "dispute_tracking_select_own" ON dispute_tracking FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "dispute_tracking_update_own" ON dispute_tracking FOR UPDATE USING (auth.uid() = user_id);
```

**Table: status_history** (immutable audit trail)
```sql
CREATE TABLE status_history (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dispute_tracking_id  UUID NOT NULL REFERENCES dispute_tracking(id) ON DELETE CASCADE,
    user_id              UUID NOT NULL REFERENCES users(id),  -- denormalized for RLS
    old_status           dispute_status,  -- NULL on first insert
    new_status           dispute_status NOT NULL,
    changed_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    changed_by           update_attribution NOT NULL,
    change_notes         TEXT
);

CREATE INDEX idx_status_history_tracking_date ON status_history (dispute_tracking_id, changed_at ASC);
CREATE INDEX idx_status_history_user          ON status_history (user_id);

ALTER TABLE status_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "status_history_select_own" ON status_history FOR SELECT USING (auth.uid() = user_id);
-- No UPDATE policy: records are immutable
```

**Table: mailing_records**
```sql
CREATE TABLE mailing_records (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES users(id),  -- denormalized for RLS
    dispute_letter_id UUID NOT NULL REFERENCES dispute_letters(id) ON DELETE CASCADE,
    mailing_service   mailing_service NOT NULL,
    tracking_number   TEXT NOT NULL,
    mailing_date      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    delivery_status   delivery_status NOT NULL DEFAULT 'sent',
    delivery_date     TIMESTAMPTZ,
    api_response      JSONB,  -- full Lob/USPS API response for debugging
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_mailing_records_user_date    ON mailing_records (user_id, mailing_date DESC);
CREATE INDEX idx_mailing_records_tracking     ON mailing_records (tracking_number);
CREATE INDEX idx_mailing_records_status       ON mailing_records (delivery_status)
    WHERE delivery_status NOT IN ('delivered', 'returned');

ALTER TABLE mailing_records ENABLE ROW LEVEL SECURITY;
CREATE POLICY "mailing_records_select_own" ON mailing_records FOR SELECT USING (auth.uid() = user_id);
-- No INSERT policy for users (inserted by backend service role only)
```

**Tables: payments and stripe_webhook_events** (EP-003 — payment and Stripe idempotency model)

> EP-003 rationale: without a payments schema, failed mailings cannot be linked to their payment
> for refund processing, real revenue metrics cannot be computed, and duplicate Stripe webhooks
> will reprocess causing double-mailings. Stripe's documentation states only webhook events are
> authoritative for payment confirmation — synchronous charge responses are not final.

```sql
CREATE TYPE payment_status_enum AS ENUM ('pending','succeeded','failed','refunded','partially_refunded');
CREATE TYPE bundle_type_enum    AS ENUM ('single','bundle_3','bundle_5');

-- Payments table: one row per Stripe PaymentIntent (covers single letters or bundles)
CREATE TABLE payments (
    payment_id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    stripe_payment_intent_id    TEXT UNIQUE NOT NULL,  -- idempotency key; also used for refund lookup
    stripe_charge_id            TEXT,
    amount_cents                INTEGER NOT NULL,
    currency                    TEXT NOT NULL DEFAULT 'usd',
    payment_status              payment_status_enum NOT NULL DEFAULT 'pending',
    dispute_letter_ids          UUID[] NOT NULL DEFAULT '{}',  -- letters covered by this payment
    bundle_type                 bundle_type_enum NOT NULL DEFAULT 'single',
    stripe_fee_cents            INTEGER,
    net_revenue_cents           INTEGER GENERATED ALWAYS AS
                                    (amount_cents - COALESCE(stripe_fee_cents, 0)) STORED,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    refunded_at                 TIMESTAMPTZ
);

CREATE INDEX idx_payments_user_date       ON payments (user_id, created_at DESC);
CREATE INDEX idx_payments_intent          ON payments (stripe_payment_intent_id);
CREATE INDEX idx_payments_status          ON payments (payment_status)
    WHERE payment_status NOT IN ('succeeded','refunded');

ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
CREATE POLICY "payments_select_own" ON payments FOR SELECT USING (auth.uid() = user_id);
-- No user INSERT: payments are created by backend service role only

-- Stripe webhook events: idempotency log for all incoming Stripe events
-- No RLS on this table — backend-only access via service role; never exposed to frontend
CREATE TABLE stripe_webhook_events (
    event_id            TEXT PRIMARY KEY,  -- Stripe event ID (e.g. evt_xxx); natural PK for dedup
    event_type          TEXT NOT NULL,
    received_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at        TIMESTAMPTZ,
    processing_status   TEXT NOT NULL DEFAULT 'received'
                            CHECK (processing_status IN ('received','processed','failed')),
    payload             JSONB NOT NULL
);

CREATE INDEX idx_stripe_webhook_type     ON stripe_webhook_events (event_type, received_at DESC);
CREATE INDEX idx_stripe_webhook_status   ON stripe_webhook_events (processing_status)
    WHERE processing_status IN ('received','failed');
-- No RLS: service-role access only; webhook processor runs as service account
```

**Table: user_analytics** (trigger-refreshed cache — EP-007 confirmed approach)

> EP-007: `user_analytics` as a regular TABLE with trigger-based UPSERT is the confirmed
> canonical design. The System Architect's MATERIALIZED VIEW (user_dispute_stats with
> REFRESH MATERIALIZED VIEW CONCURRENTLY) has been superseded by this approach. Rationale:
> Supabase MATERIALIZED VIEW + RLS requires additional policy configuration that does not
> work out of the box; the trigger-based UPSERT is atomic, always consistent, and achieves
> <5ms dashboard reads versus the <100ms MV target. Implementation must use this TABLE,
> not a MATERIALIZED VIEW.

```sql
CREATE TABLE user_analytics (
    user_id                      UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    total_disputes_initiated     INTEGER NOT NULL DEFAULT 0,
    total_items_deleted          INTEGER NOT NULL DEFAULT 0,
    success_rate                 DECIMAL(5,2),
    average_days_to_resolution   DECIMAL(6,2),
    disputes_by_bureau           JSONB,  -- {"equifax": 5, "transunion": 4, "experian": 6}
    last_updated                 TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE user_analytics ENABLE ROW LEVEL SECURITY;
CREATE POLICY "user_analytics_select_own" ON user_analytics FOR SELECT USING (auth.uid() = user_id);
-- No direct user write: maintained exclusively by triggers
```

**Table: notification_log** (EP-010 — email notification tracking)

> EP-010 rationale: the PM defines 5 critical email touchpoints including the Day 25 FCRA
> deadline reminder, which requires a scheduled job (no application event fires 25 days after
> a dispute). Without this table, delivery tracking and the Day 25 reminder that drives the
> 30% repeat purchase target cannot be implemented.

```sql
CREATE TYPE notification_type_enum AS ENUM (
    'onboarding_day1',
    'onboarding_day3',
    'fcra_deadline_warning',
    'item_deleted',
    'item_verified',
    'delivery_confirmed',
    'upgrade_prompt'
);

CREATE TABLE notification_log (
    notification_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notification_type   notification_type_enum NOT NULL,
    sent_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    provider_message_id TEXT,         -- SendGrid/Postmark message ID for delivery tracking
    opened_at           TIMESTAMPTZ,  -- populated via email provider webhook
    clicked_at          TIMESTAMPTZ   -- populated via email provider webhook
);

CREATE INDEX idx_notification_log_user ON notification_log (user_id, sent_at DESC);
CREATE INDEX idx_notification_log_type ON notification_log (notification_type, sent_at DESC);

ALTER TABLE notification_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY "notification_log_user_select" ON notification_log
    FOR SELECT USING (auth.uid() = user_id);
-- No user INSERT/UPDATE: inserted by backend notification service only
```

### 2.3 ENUM Type Definitions

```sql
-- EP-004: 'paid' replaced by 'premium' to distinguish active $15/month subscribers
--         from free-tier per-letter purchasers. subscription_tier stored as TEXT with
--         CHECK constraint (not a PG ENUM) to allow future values without DDL migration.
-- Note: the original ENUM definition below is superseded; users table uses TEXT + CHECK.
-- CREATE TYPE subscription_tier   AS ENUM ('free', 'paid');  -- SUPERSEDED by EP-004
CREATE TYPE bureau_type         AS ENUM ('equifax', 'transunion', 'experian', 'unknown');
CREATE TYPE processing_status   AS ENUM ('pending', 'processing', 'completed', 'failed');
CREATE TYPE account_type        AS ENUM ('credit_card', 'mortgage', 'auto_loan', 'student_loan', 'personal_loan', 'other');
CREATE TYPE negative_type       AS ENUM ('late_payment', 'charge_off', 'collection', 'bankruptcy', 'foreclosure', 'repossession', 'tax_lien', 'judgment');
CREATE TYPE dispute_status      AS ENUM ('pending', 'investigating', 'verified', 'deleted', 'updated', 'escalated', 'expired', 'blank');
CREATE TYPE update_attribution  AS ENUM ('user', 'ocr_system');
CREATE TYPE mailing_service     AS ENUM ('lob', 'usps_direct');
CREATE TYPE delivery_status     AS ENUM ('sent', 'in_transit', 'delivered', 'failed', 'returned');
```

### 2.4 TimescaleDB Hypertable — Historical Credit Scores (Phase 3, enabled from Phase 1)

> EP-001: The single-database extension approach (TimescaleDB as a Supabase PostgreSQL
> extension) is confirmed as the canonical topology, superseding the System Architect's
> separate-instance dual-write design. Verification required in Week 1 of implementation
> planning: confirm the chosen Supabase plan tier (Pro or higher) supports the TimescaleDB
> extension. If unavailable, fallback is PostgreSQL BRIN index on timestamp (documented in
> Risk 3 of Section 9). Do not implement the separate-instance approach until this check
> is completed and the extension is confirmed unavailable.

```sql
CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE credit_score_history (
    user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    timestamp     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    score_value   INTEGER NOT NULL CHECK (score_value BETWEEN 300 AND 850),
    bureau_source bureau_type NOT NULL,
    score_factors JSONB,  -- {"payment_history": 35, "utilization": 30, ...}
    PRIMARY KEY (user_id, timestamp, bureau_source)
);

-- Convert to hypertable: monthly time partitions
SELECT create_hypertable('credit_score_history', 'timestamp',
    chunk_time_interval => INTERVAL '1 month');

-- Index for user-specific bureau queries
CREATE INDEX idx_credit_score_user_bureau
    ON credit_score_history (user_id, bureau_source, timestamp DESC);

-- Automatic compression for chunks older than 6 months (70-90% storage reduction)
ALTER TABLE credit_score_history SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'user_id, bureau_source'
);
SELECT add_compression_policy('credit_score_history', INTERVAL '6 months');

ALTER TABLE credit_score_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "credit_score_select_own" ON credit_score_history FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "credit_score_insert_own" ON credit_score_history FOR INSERT WITH CHECK (auth.uid() = user_id);
```

**Rationale for enabling from Phase 1**: Adding TimescaleDB in Phase 3 would require a 2-4 week migration project involving data backfill, query rewrites, and dual-database operation. The DDL cost at Phase 1 is one 30-minute setup task. The extension is dormant until Phase 3 score-tracking writes begin.

---

## 3. Database Architecture Strategy

### 3.1 Technology Selection Rationale

**PostgreSQL 15 via Supabase** (primary):
- Existing infrastructure: Credit Clarity already uses Supabase for auth and storage; no new vendor
- RLS enforces multi-tenancy at database layer; application code cannot accidentally omit user filter
- JSONB handles semi-structured tradeline data without a separate document store
- SOC 2 Type II, AES-256 at rest, managed backups and PITR included

**TimescaleDB** (time-series extension):
- Same SQL syntax; no new query language for the development team
- Chunk pruning makes time-range queries on credit score history sub-2ms regardless of history length
- 70-90% compression for historical data; 5GB of raw score history compresses to ~1.5GB by Month 24

**Redis** (caching and rate limiting):
- Already deployed in existing architecture; no new infrastructure
- Rate limit counters use atomic INCR (no race conditions across multiple requests)
- `noeviction` policy ensures rate limit data is never lost to memory pressure

**Pinecone / Weaviate** (vector database, Phase 3 only):
- Separate from PostgreSQL; no schema impact on Phases 1-2
- Pinecone serverless tier free up to 100K vectors (sufficient for credit repair knowledge base)
- Integration pattern: PostgreSQL provides user context → Pinecone provides knowledge retrieval → Gemini generates response

### 3.2 Multi-Tenancy Pattern

Every table in the schema carries `user_id` directly (denormalized from parent tables where needed). This means:
- RLS policies are a single `auth.uid() = user_id` check, with no JOIN overhead
- Composite indexes always lead with `user_id`, matching the WHERE clause order for RLS-filtered queries
- Cross-user data leakage is impossible: the database rejects mismatched `user_id` queries at execution time, not at application layer

**Performance overhead of RLS**: 1-2ms per query (acceptable given <200ms dashboard target).

### 3.3 Denormalization Strategy

| Denormalized Field | Location | Source | Why |
|--------------------|----------|--------|-----|
| `user_id` | `tradelines` | `credit_reports.user_id` | Dashboard queries skip one JOIN; RLS check is direct |
| `user_id` | `dispute_tracking` | `dispute_letters.user_id` | Status update API doesn't JOIN through letters |
| `user_id` | `status_history` | `dispute_tracking.user_id` | Audit trail queries don't traverse three tables |
| `user_id` | `mailing_records` | `dispute_letters.user_id` | Mailing history page has direct user filter |
| `mailing_date`, `tracking_number` | `dispute_tracking` | `mailing_records` | Dashboard displays tracking without extra JOIN |

Denormalized fields are kept consistent by database triggers (not application code) to prevent drift.

### 3.4 Trigger Architecture

**Trigger 1: Analytics refresh on status change**
```sql
CREATE OR REPLACE FUNCTION refresh_user_analytics(target_user_id UUID)
RETURNS VOID AS $$
BEGIN
    INSERT INTO user_analytics (
        user_id,
        total_disputes_initiated,
        total_items_deleted,
        success_rate,
        average_days_to_resolution,
        disputes_by_bureau,
        last_updated
    )
    SELECT
        target_user_id,
        COUNT(*) AS total_disputes_initiated,
        COUNT(*) FILTER (WHERE status = 'deleted') AS total_items_deleted,
        ROUND(
            100.0 * COUNT(*) FILTER (WHERE status = 'deleted')
            / NULLIF(COUNT(*), 0), 2
        ) AS success_rate,
        AVG(
            EXTRACT(EPOCH FROM (sh_del.changed_at - sh_pen.changed_at)) / 86400.0
        ) AS average_days_to_resolution,
        jsonb_build_object(
            'equifax',    COUNT(*) FILTER (WHERE bureau = 'equifax'),
            'transunion', COUNT(*) FILTER (WHERE bureau = 'transunion'),
            'experian',   COUNT(*) FILTER (WHERE bureau = 'experian')
        ) AS disputes_by_bureau,
        NOW() AS last_updated
    FROM dispute_tracking dt
    LEFT JOIN status_history sh_pen
        ON sh_pen.dispute_tracking_id = dt.id AND sh_pen.old_status IS NULL
    LEFT JOIN status_history sh_del
        ON sh_del.dispute_tracking_id = dt.id AND sh_del.new_status = 'deleted'
    WHERE dt.user_id = target_user_id
    GROUP BY target_user_id
    ON CONFLICT (user_id) DO UPDATE SET
        total_disputes_initiated   = EXCLUDED.total_disputes_initiated,
        total_items_deleted        = EXCLUDED.total_items_deleted,
        success_rate               = EXCLUDED.success_rate,
        average_days_to_resolution = EXCLUDED.average_days_to_resolution,
        disputes_by_bureau         = EXCLUDED.disputes_by_bureau,
        last_updated               = EXCLUDED.last_updated;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION trigger_analytics_refresh() RETURNS TRIGGER AS $$
BEGIN
    PERFORM refresh_user_analytics(NEW.user_id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER after_dispute_status_change
AFTER INSERT OR UPDATE ON dispute_tracking
FOR EACH ROW EXECUTE FUNCTION trigger_analytics_refresh();
```

**Trigger 2: Immutable audit trail on status change**
```sql
CREATE OR REPLACE FUNCTION log_status_change() RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO status_history (
            dispute_tracking_id, user_id,
            old_status, new_status,
            changed_at, changed_by, change_notes
        ) VALUES (
            NEW.id, NEW.user_id,
            OLD.status, NEW.status,
            NOW(), NEW.status_updated_by,
            'Status changed: ' || OLD.status || ' → ' || NEW.status
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER after_status_update
AFTER UPDATE ON dispute_tracking
FOR EACH ROW EXECUTE FUNCTION log_status_change();
```

**Performance**: Both triggers execute within the same database transaction as the status UPDATE. Analytics recalculation takes 100-200ms; the API response returns immediately after the status UPDATE completes (trigger is synchronous but lightweight relative to the overall request budget).

---

## 4. Data Pipeline Architecture

### 4.1 AI Processing Pipeline: Credit Report Upload to Tradeline Storage

```
User Upload (Frontend)
    ↓ PDF (1-5MB, <30s for <10MB)
Supabase Storage → INSERT credit_reports (status='pending')
    ↓ Celery background task triggered
Google Document AI OCR
    ↓ Extracted text + confidence scores
Gemini AI (structured extraction)
    ↓ JSON array: [{account_name, account_type, balance, payment_history, ...}]
Rule-Based Negative Classification
    ↓ is_negative, negative_type, negative_reason per tradeline
Duplicate Check: SELECT WHERE user_id + account_name + account_number_last_4
    ↓ new tradelines only
INSERT tradelines (batch)
    ↓
UPDATE credit_reports (status='completed')
    ↓
Frontend polling notified: tradelines ready for review
```

**Negative classification rules**:
```python
NEGATIVE_KEYWORDS = {
    'late_payment':   ['30 days late', '60 days late', '90 days late', '120+'],
    'charge_off':     ['charge-off', 'charged off'],
    'collection':     ['collection', 'collections'],
    'bankruptcy':     ['bankruptcy', 'chapter 7', 'chapter 13'],
    'foreclosure':    ['foreclosure', 'foreclosed'],
    'repossession':   ['repossession', 'repo'],
    'tax_lien':       ['tax lien'],
    'judgment':       ['judgment', 'civil judgment']
}
# Payment history late-payment detection:
has_late = any(status in ['30', '60', '90', '120+'] for status in payment_history_array)
```

**Pipeline timing targets**:
- Files <10MB: end-to-end <60 seconds (OCR 15s, Gemini 30s, classification + INSERT <5s)
- Files >10MB: background job with progress polling endpoint
- OCR confidence <85%: flagged in `credit_reports.metadata`; user notified to verify extracted items

**Error handling**: 3 retry attempts with exponential backoff (4s, 8s, 10s). On final failure: `processing_status = 'failed'`, error stored in `processing_error`, user notified via dashboard.

### 4.2 Bureau Response OCR Pipeline (Phase 2)

```
User Uploads Bureau Response PDF
    ↓
Supabase Storage → Celery background task
    ↓
Gemini Vision API: extract bureau name, account name, resolution status
    ↓
Confidence ≥ 80%?
  YES → pre-fill status update form for user confirmation
  NO  → prompt user for manual status selection
    ↓
User confirms or corrects
    ↓
UPDATE dispute_tracking.status (triggers audit trail + analytics refresh)
```

**Confidence threshold rationale**: Gemini extracts structured data from unstructured bureau letters. Below 80% confidence, the auto-fill is shown as a suggestion with explicit user confirmation required, not an automatic update. This satisfies the hybrid approach confirmed in guidance-specification.md Section 2 (Feature 4).

### 4.3 Mailing Service Pipeline

**Phase 1: Lob.com API**
```
User clicks "Mail Letter" (letter_id confirmed)
    ↓
Stripe payment verification
    ↓
Idempotency key = SHA-256(letter_id + user_id)
    ↓
Lob.com API: POST /letters (certified mail, bureau address, user return address)
    ↓
Lob response: tracking_number, expected_delivery_date
    ↓
INSERT mailing_records (mailing_service='lob', tracking_number, delivery_status='sent')
UPDATE dispute_letters (is_mailed=TRUE, mailing_date, tracking_number)
INSERT dispute_tracking (status='pending', tracking_number denormalized)
    ↓
Return tracking_number to frontend within 3 seconds
```

**Bureau mailing addresses** (stored in application config, not database — these are static constants):
```
equifax:    Equifax Information Services LLC, P.O. Box 740256, Atlanta GA 30374
transunion: TransUnion Consumer Solutions, P.O. Box 2000, Chester PA 19016
experian:   Experian National Consumer Assistance Center, P.O. Box 4500, Allen TX 75013
```

**Phase 2 migration to USPS API Direct** (Month 7-12):
- `mailing_records.mailing_service` field differentiates API source
- Same downstream schema: tracking number flows into `dispute_tracking` identically
- Migration: A/B route 10% → 50% → 100% of new mailings to USPS; Lob retained as fallback
- Cost impact: Lob ~$1.65/letter → USPS ~$0.60-1.00/letter; improves gross margin from ~67% to ~80%

### 4.4 Analytics Refresh Pipeline

```
dispute_tracking.status UPDATE (manual or OCR)
    ↓ PostgreSQL trigger (synchronous, same transaction)
log_status_change() → INSERT status_history (immutable)
trigger_analytics_refresh() → refresh_user_analytics()
    → UPSERT user_analytics (all 4 metrics recalculated)
    ↓
Frontend reads: SELECT * FROM user_analytics WHERE user_id = $1
    → 5ms query on PK lookup
```

**Why trigger-based refresh instead of real-time aggregation query**:
- Real-time aggregation over `dispute_tracking` grows to 500-1000ms as dispute count grows
- Cached `user_analytics` is always a single-row PK lookup at <5ms regardless of scale
- Eventual consistency: analytics lag is <200ms (trigger duration), acceptable for personal stats

---

## 5. FCRA Compliance — Schema Controls and Code Controls

### 5.1 Data Retention: 7-Year Policy

**Schema control**:
```sql
-- users.data_retention_expiry = created_at + 7 years (set at account creation)
ALTER TABLE users ADD COLUMN data_retention_expiry DATE;
```

**Automated deletion** (monthly pg_cron job):
```sql
CREATE OR REPLACE FUNCTION delete_expired_user_data() RETURNS VOID AS $$
BEGIN
    -- CASCADE deletes all related records via FK ON DELETE CASCADE
    DELETE FROM users WHERE data_retention_expiry < CURRENT_DATE;
END;
$$ LANGUAGE plpgsql;

SELECT cron.schedule('delete-expired-data', '0 2 1 * *', 'SELECT delete_expired_user_data()');
```

**User-requested deletion** (GDPR/CCPA right to erasure):
- If no active disputes: immediate cascade delete
- If active disputes within 7-year window: anonymize PII fields in `users` row, retain dispute records for FCRA compliance, delete PDF files from Supabase Storage

### 5.2 User Consent Schema

All consent fields are defined in the `users` table DDL (Section 2.2). Represented here as ALTER statements for documentation of initialization order:

```sql
ALTER TABLE users ADD COLUMN fcra_consent_given           BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE users ADD COLUMN fcra_consent_timestamp        TIMESTAMPTZ;
-- EP-008: CROA disclosure (Credit Repair Organizations Act, 15 U.S.C. § 1679 et seq.)
ALTER TABLE users ADD COLUMN croa_disclosure_accepted      BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE users ADD COLUMN croa_disclosure_timestamp     TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN ai_training_consent           BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE users ADD COLUMN ai_training_consent_timestamp TIMESTAMPTZ;
```

**Consent field semantics and enforcement**:

| Field | Gate | Legal Basis | Applies When |
|-------|------|-------------|--------------|
| `fcra_consent_given` | Credit report upload API | FCRA § 1681 | Before any PDF upload is accepted |
| `croa_disclosure_accepted` | Paid mailing checkout API | CROA 15 U.S.C. § 1679 | Before any paid mailing is processed |
| `ai_training_consent` | None (optional) | Voluntary | Controls Phase 3 ML training data inclusion |

**CROA enforcement note** (EP-008): `croa_disclosure_accepted` must be `TRUE` before the backend
calls `process_payment()` at the checkout endpoint. This field is distinct from `fcra_consent_given`:
FCRA governs credit report access rights; CROA governs paid credit repair services specifically.
The checkout endpoint must verify both fields are `TRUE` before proceeding. CROA civil liability
includes actual damages, punitive damages, and attorney fees (15 U.S.C. § 1679g); this field
provides the auditable proof of disclosure acceptance required in regulatory inquiries.

- All consent timestamps stored for audit purposes; consent timestamps may not be NULL when the corresponding boolean is TRUE (enforced at application layer, not DB constraint, to allow future index coverage)

### 5.3 Adverse Action Transparency

FCRA 15 U.S.C. § 1681m requires users to be notified when AI classifies a tradeline as negative and explains the basis. The `negative_reason` field in `tradelines` stores the classification rationale:
```
"Status contains derogatory keyword: charge-off"
"Payment history contains 30-day late payments: ['30', '30', 'OK']"
```

This text is surfaced in the dispute dashboard so users understand why each tradeline was flagged, satisfying transparency requirements without requiring external notification.

### 5.4 Audit Trail for Data Access (FCRA § 1681e)

```sql
CREATE TABLE data_access_log (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID NOT NULL REFERENCES users(id),
    accessed_by      UUID,   -- NULL for user self-access; admin UUID for support access
    access_type      TEXT NOT NULL CHECK (access_type IN ('read', 'write', 'delete')),
    table_name       TEXT NOT NULL,
    record_id        UUID,
    access_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ip_address       TEXT,
    user_agent       TEXT
);

CREATE INDEX idx_data_access_log_user_time ON data_access_log (user_id, access_timestamp DESC);
```

Admin access events are inserted by a trigger on each table. User self-access is logged by the API middleware for credit report read and dispute read operations.

### 5.5 PII Encryption Controls

**Column-level encryption** for Restricted-classified data (Fernet symmetric encryption, key stored in environment variable, not in code):

```python
from cryptography.fernet import Fernet

FERNET_KEY = os.getenv('COLUMN_ENCRYPTION_KEY')  # 32-byte, base64-encoded
cipher = Fernet(FERNET_KEY.encode())

def encrypt_field(plaintext: str) -> str:
    if plaintext is None:
        return None
    return base64.b64encode(cipher.encrypt(plaintext.encode())).decode()

def decrypt_field(ciphertext: str) -> str:
    if ciphertext is None:
        return None
    return cipher.decrypt(base64.b64decode(ciphertext.encode())).decode()
```

Encrypted fields: `users.ssn_encrypted`, `users.address_encrypted`. These are never sent to the frontend; decryption happens in the backend service layer only.

Key rotation schedule: annually, with re-encryption of all affected rows in a maintenance window.

---

## 6. Analytics Infrastructure

### 6.1 Personal Statistics Dashboard (Phase 1)

The `user_analytics` table is the sole source for the personal stats dashboard. It stores four metrics:

| Metric | Column | Calculation | Update Trigger |
|--------|--------|-------------|----------------|
| Total disputes initiated | `total_disputes_initiated` | COUNT(*) FROM dispute_tracking WHERE user_id | STATUS change or INSERT |
| Items successfully deleted | `total_items_deleted` | COUNT(*) FILTER (WHERE status = 'deleted') | STATUS → 'deleted' |
| Success rate | `success_rate` | (deleted / total) * 100, DECIMAL(5,2) | Any status change |
| Average days to resolution | `average_days_to_resolution` | AVG(deleted_at - pending_at) in days | STATUS → 'deleted' |

Dashboard query (target <5ms):
```sql
SELECT
    total_disputes_initiated,
    total_items_deleted,
    success_rate,
    average_days_to_resolution,
    disputes_by_bureau
FROM user_analytics
WHERE user_id = $1;
```

### 6.2 Multi-Bureau Dispute View Query

```sql
-- Target: <150ms; uses composite index idx_dispute_tracking_tradeline_bureau
SELECT
    t.account_name,
    t.account_type,
    t.balance,
    t.negative_type,
    t.negative_reason,
    dt_eq.status          AS equifax_status,
    dt_eq.tracking_number AS equifax_tracking,
    dt_eq.status_updated_at AS equifax_updated,
    dt_tu.status          AS transunion_status,
    dt_tu.tracking_number AS transunion_tracking,
    dt_tu.status_updated_at AS transunion_updated,
    dt_ex.status          AS experian_status,
    dt_ex.tracking_number AS experian_tracking,
    dt_ex.status_updated_at AS experian_updated
FROM tradelines t
LEFT JOIN dispute_tracking dt_eq
    ON dt_eq.tradeline_id = t.id AND dt_eq.bureau = 'equifax'   AND dt_eq.user_id = $1
LEFT JOIN dispute_tracking dt_tu
    ON dt_tu.tradeline_id = t.id AND dt_tu.bureau = 'transunion' AND dt_tu.user_id = $1
LEFT JOIN dispute_tracking dt_ex
    ON dt_ex.tradeline_id = t.id AND dt_ex.bureau = 'experian'   AND dt_ex.user_id = $1
WHERE t.user_id = $1 AND t.is_negative = TRUE
ORDER BY t.created_at DESC;
```

### 6.3 TimescaleDB Analytics Strategy (Phase 3)

```sql
-- Continuous aggregate: monthly score average per bureau
CREATE MATERIALIZED VIEW credit_score_monthly
WITH (timescaledb.continuous) AS
SELECT
    user_id,
    bureau_source,
    time_bucket('1 month', timestamp) AS month,
    AVG(score_value)  AS avg_score,
    MIN(score_value)  AS min_score,
    MAX(score_value)  AS max_score,
    COUNT(*)          AS snapshot_count
FROM credit_score_history
GROUP BY user_id, bureau_source, month;

-- Target: <10ms for 12-month trend query (pre-aggregated)
SELECT * FROM credit_score_monthly
WHERE user_id = $1
ORDER BY month DESC
LIMIT 12;
```

---

## 7. Scalability and Performance Targets

### 7.1 Quantified Performance Targets by Query Type

| Query | Target | Optimization |
|-------|--------|-------------|
| Dashboard load (disputes + analytics) | <200ms | Composite index, denormalized user_id, cached analytics |
| Personal stats fetch | <5ms | Single-row PK lookup on `user_analytics` |
| Multi-bureau dispute view | <150ms | Partial index on `is_negative = TRUE`, 3-way LEFT JOIN |
| Status update + analytics refresh | <300ms total | Trigger-based, synchronous within transaction |
| Audit trail timeline | <50ms | Index on `(dispute_tracking_id, changed_at)` |
| Credit score history 12-month | <10ms (Phase 3) | Continuous aggregate on TimescaleDB hypertable |
| Rate limit check | <1ms | In-memory middleware (Redis sync backup, 5ms) |

### 7.2 Storage Projections

| Phase | Users | PostgreSQL | Object Storage (PDFs) | TimescaleDB |
|-------|-------|-----------|----------------------|------------|
| Month 6 | 100 | 500MB | 1GB | — |
| Month 12 | 1,000 | 5GB | 10GB | — |
| Month 18 | 5,000 | 25GB | 50GB | 1.5GB (compressed) |
| Month 24 | 10,000 | 50GB | 100GB | 3GB (compressed) |

**PDF cleanup policy**: Delete from Supabase Storage after 30 days (structured data in PostgreSQL is retained); user may re-upload if needed.

### 7.3 Rate Limiting Scalability Path

| Phase | Users | Implementation | Latency |
|-------|-------|---------------|---------|
| Month 1-12 | 1 FastAPI instance | In-memory + Redis backup | <1ms |
| Month 12-18 | 3-10 instances | Redis-only (atomic INCR) | 5ms |
| Month 18+ | 10+ instances | Redis Cluster | 5-10ms |

The single-instance to multi-instance transition (Month 12) requires switching the primary rate limit check from in-memory to Redis-only, since in-memory state is not shared across instances. The schema (`users.rate_limit_reports`, `users.rate_limit_letters`) serves as the persistent source of truth and is synced from Redis on each monthly reset.

### 7.4 Connection Pooling Configuration

```python
# SQLAlchemy engine with Supabase PgBouncer pooler (transaction mode)
engine = create_engine(
    "postgresql://user:pass@db.supabase.co:6543/postgres",  # port 6543 = pooler
    poolclass=QueuePool,
    pool_size=20,        # 20 connections per FastAPI instance
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True
)
```

Supabase Pro tier supports 500 max connections. At 20 connections per FastAPI instance, the architecture supports up to 25 concurrent instances before requiring Enterprise tier.

---

## 8. Data Governance

### 8.1 Data Classification

| Data | Classification | Encryption | Access |
|------|---------------|------------|--------|
| User email | Confidential | TLS + AES-256 at rest | RLS user-scoped |
| SSN | Restricted | TLS + AES-256 + Fernet column | Backend decrypt only |
| Full account number | Restricted | TLS + AES-256 + Fernet column | Backend decrypt only |
| User mailing address | Restricted | TLS + AES-256 + Fernet column | Backend decrypt only |
| Credit report PDF | Confidential | TLS + AES-256 at rest | RLS user-scoped |
| Tradeline details | Confidential | TLS + AES-256 at rest | RLS user-scoped |
| Dispute letters | Confidential | TLS + AES-256 at rest | RLS user-scoped |
| user_analytics | Internal | TLS + AES-256 at rest | RLS user-scoped |

### 8.2 AI Training Data Governance (Phase 3)

Only tradelines from users where `ai_training_consent = TRUE` may be used for ML training. Before use:
1. Remove: `account_name` → `"ANONYMIZED"`, `account_number_last_4` → `"XXXX"`, `user_id` → hashed synthetic ID
2. Retain: `account_type`, `status`, `balance`, `credit_limit`, `payment_history`, `is_negative`, `negative_type` (these are the training signal)
3. Store in a separate isolated PostgreSQL database with no foreign key links to production `users` table
4. User cannot request deletion of anonymized training data after anonymization (no linkage exists)

### 8.3 Backup and Recovery

- **Daily backups**: Supabase managed, retained 7 days
- **Weekly backups**: Retained 4 weeks
- **PITR**: Point-in-time recovery to any point in last 7 days (Supabase Pro)
- **RTO**: <4 hours (restore from daily backup)
- **RPO**: <24 hours (daily backup cycle)
- **Monthly offsite export**: `pg_dump` to encrypted S3 bucket

---

## 9. Risks and Mitigations — Data Architecture Perspective

**Risk 1: OCR accuracy varies by bureau format**
- Mitigation: `tradeline_details` JSONB stores raw Gemini output; users can correct AI classifications; corrections improve accuracy signal for Phase 3 ML training

**Risk 2: Rate limiting state lost on multi-instance rollout**
- Mitigation: Month 12 transition to Redis-only rate limiting before deploying second FastAPI instance; no state loss risk

**Risk 3: TimescaleDB extension unavailability on current Supabase plan**
- Mitigation: TimescaleDB is available on Supabase Pro tier; `credit_score_history` table created immediately but writes are deferred until Phase 3. If TimescaleDB unavailable, fallback is PostgreSQL BRIN index on timestamp (less efficient but functional)

**Risk 4: Data deletion complexity (FCRA vs GDPR right to erasure)**
- Mitigation: Anonymize-not-delete path for users with active disputes; retain dispute records for 7-year FCRA window; full cascade delete only when no active disputes exist

**Risk 5: Column encryption key management**
- Mitigation: Key stored in environment variable via secret manager (AWS Secrets Manager or Supabase secrets); key rotation scheduled annually; no key stored in code or configuration files

---

## 10. Summary of Data Architect Decisions Mapped to guidance-specification.md Section 5

| Decision | Specification Reference | Implementation |
|----------|------------------------|----------------|
| Credit report storage | Section 5: "PostgreSQL with structured JSON" | `credit_reports` + `tradelines` tables; `payment_history` and `tradeline_details` as JSONB |
| Dispute tracking schema | Section 5: "relational model, 8 status types" | `dispute_tracking` with `dispute_status` ENUM; `status_history` audit trail |
| Historical score storage | Section 5: "TimescaleDB, implement from start" | `credit_score_history` hypertable created at Phase 1; writes begin Phase 3 |
| Training data | Section 5: "Hybrid sources with user consent" | `ai_training_consent` field; anonymization pipeline; separate training DB |
| Analytics infrastructure | Section 5: "Real-time queries on PostgreSQL" | `user_analytics` trigger-refreshed TABLE (EP-007); <5ms dashboard reads |
| Data privacy | Section 5: "Supabase RLS + Selective Encryption" | RLS on all tables; Fernet column encryption for SSN, address, full account number |
| Rate limiting persistence | Section 5 / D-018: "Hybrid persistence" | In-memory middleware + Redis HASH backup; 5-minute sync; Redis reload on restart |
| Analytics DB timing | D-019: "Implement Time-Series now" | TimescaleDB hypertable DDL in Phase 1 as extension (EP-001); avoids 2-4 week Phase 3 migration |
| FCRA 7-year retention | Section 5: "7-year limit for credit data" | `data_retention_expiry` field; monthly pg_cron deletion job |
| Audit trails | Section 5: "Audit trails for data access" | `status_history` (immutable, trigger-inserted); `data_access_log` for admin access |
| Payment model | EP-003: Stripe payment integrity | `payments` table + `stripe_webhook_events` idempotency log |
| Subscription tiers | EP-004: 'free' vs 'premium' distinction | `subscription_tier` TEXT CHECK ('free','premium') + premium lifecycle fields in `users` |
| CROA compliance | EP-008: CROA § 1679 written disclosure | `croa_disclosure_accepted` + `croa_disclosure_timestamp` in `users`; checkout gate |
| Notification tracking | EP-010: Email notification infrastructure | `notification_log` table with `notification_type_enum`; supports Day 25 FCRA reminder |

---

## 11. Clarifications

These open questions were identified during cross-role synthesis. They require a decision before
Phase 1 DDL is finalized and implementation planning begins.

---

**CQ-001 — TimescaleDB Deployment Topology** (Architecture)

The Data Architect's extension-within-Supabase approach is confirmed as the canonical topology
(EP-001). The System Architect's separate-instance design has been superseded.

Remaining action: verify in Week 1 of implementation planning that the chosen Supabase plan
tier (Pro or higher) includes the TimescaleDB extension. If unavailable, the fallback is a
PostgreSQL BRIN index on `credit_score_history.timestamp` (documented in Risk 3, Section 9).
No implementation work should begin on the separate-instance approach until this check fails.

Status: **topology decided (extension); plan-tier verification pending**

---

**CQ-004 — Premium Subscription Tier Benefits Scope** (Requirements)

The `subscription_tier` model has been updated to `('free','premium')` (EP-004). The data model
supports all three benefit structures described in the enhancement recommendations:

- Option A (AI features only, mailing still per-letter): `premium_expires_at` gates AI feature
  access; payments table handles per-letter billing independently
- Option B (fixed monthly mailing credits + AI): requires an additional `monthly_mailing_credits_used`
  counter in `users` (one integer field, low-cost addition)
- Option C (unlimited mailing): no additional schema; Lob cost risk must be mitigated by an
  application-layer monthly mailing cap

The data model is neutral across all three options. The business decision on Option A/B/C
determines whether the additional mailing credit counter field is needed. This must be decided
before the checkout endpoint is implemented; it does not block schema migration.

Status: **schema foundation complete; benefit scope requires product decision**

---

**CQ-006 — OCR Confidence Threshold Strategy** (Architecture)

The Data Architect specified a single 80% threshold (pre-fill form below 80% requires manual
input). This impacts the `processing_status` transitions in the `credit_reports` table and the
user confirmation flow for bureau response OCR in Section 4.2.

Three options exist:
- Single threshold at 80% (current DA spec, simplest)
- Dual threshold (>=90% strong suggestion, 60-90% confirmation required, <60% manual)
- Always-confirm regardless of confidence (most conservative, recommended for initial release)

The `credit_reports.metadata` JSONB column already stores the OCR confidence score (Section 1,
Feature 1). The schema is threshold-agnostic; only the application-layer confirmation logic
and the UI differ between the three options. This is a UX decision with no schema migration cost.

Status: **schema is threshold-agnostic; threshold strategy requires UX/product decision**
