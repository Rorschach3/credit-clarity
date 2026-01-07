# Data Models & Schema Design

**Parent Document**: @analysis.md
**Reference**: @../guidance-specification.md Section 5 (Data Architect Decisions)

## 1. Data Architecture Overview

### Business Context
Credit Clarity operates as a B2C SaaS platform enabling individual consumers to manage credit report disputes across three major bureaus (Equifax, TransUnion, Experian). The data architecture must support:
- **Freemium monetization model**: 2 credit report uploads/month, 3 dispute letters/month for free users
- **Paid mailing service**: Per-letter pricing ($5-10) with certified mail tracking
- **AI-powered classification**: 95%+ accuracy negative tradeline detection
- **Multi-bureau tracking**: Parallel dispute status across all 3 bureaus for same tradeline
- **User analytics**: Personal success statistics (success rate, items removed, time to resolution)

### Data Strategy Principles
1. **Privacy-first design**: All credit data is user-scoped with Supabase RLS enforcing access controls
2. **Structured flexibility**: Relational model for core entities, structured JSON for variable tradeline details
3. **Multi-tenancy isolation**: Each user's data completely isolated at database query level
4. **Audit trail completeness**: All status changes and data modifications logged for dispute history
5. **Scalability from start**: TimescaleDB integration for time-series data prevents future migration complexity

### Success Criteria
- **Query performance**: <200ms for dashboard queries retrieving user's disputes and statistics
- **Data integrity**: Zero cross-user data leakage via RLS enforcement
- **Storage efficiency**: Structured JSON reduces schema complexity for variable tradeline formats
- **Compliance readiness**: Schema supports FCRA 7-year retention and data deletion requirements

## 2. Data Requirements Analysis

### Functional Requirements

**Data Entities**:
1. **Users**: Authentication, profile, subscription tier (free/paid), rate limiting counters
2. **Credit Reports**: Uploaded PDF metadata, processing status, bureau source, upload timestamp
3. **Tradelines**: Individual credit accounts with payment history, negative flags, dispute eligibility
4. **Disputes**: Dispute letters generated, mailing status, bureau-specific tracking, status history
5. **Mailing Records**: Tracking numbers, delivery status, Lob/USPS API integration data
6. **Analytics**: Aggregated user statistics, cached success rates, time-to-resolution metrics

**Data Operations (CRUD)**:
- **Create**: New credit report upload triggers tradeline extraction and negative item classification
- **Read**: Dashboard queries fetch multi-bureau dispute status for user's tradelines
- **Update**: Status changes (manual or OCR-based) trigger analytics recalculation
- **Delete**: User account deletion cascades to all associated credit data per FCRA right to erasure

**Data Transformations**:
- **AI Pipeline**: Google Document AI OCR → Gemini tradeline parsing → Negative item classification → PostgreSQL insert
- **Status Aggregation**: Individual dispute status changes → Personal statistics recalculation
- **Multi-bureau Merge**: Same tradeline reported by different bureaus → Unified display with per-bureau status

**Data Integrations**:
- **Inbound**: User-uploaded credit report PDFs, bureau response letter PDFs (OCR optional)
- **Outbound**: Lob.com API (mailing requests), USPS API (tracking updates), Gemini API (OCR/parsing)
- **Bidirectional**: Redis cache (rate limiting counters), TimescaleDB (historical score snapshots)

### Non-Functional Requirements (4 Vs of Big Data)

**Volume**:
- **Initial scale**: 100 active users in first 6 months
- **Growth target**: 1,000+ users by month 12
- **Data size per user**:
  - Credit report PDF: 1-5MB average
  - Tradelines per report: 10-30 average
  - Disputes per user: 5-15 average (covering negative items across 3 bureaus)
- **Total storage estimate Year 1**: 5GB (reports) + 500MB (structured data) = ~6GB

**Velocity**:
- **Report uploads**: 2 per user/month × 1,000 users = 2,000 uploads/month (steady state)
- **Dispute status updates**: 10-20 updates/day (manual or OCR-based)
- **Analytics recalculations**: Triggered on every status change (real-time requirement)
- **Rate limiting checks**: 100+ requests/second during peak usage (middleware + Redis)

**Variety**:
- **Structured data**: User profiles, dispute records, mailing tracking (relational PostgreSQL)
- **Semi-structured data**: Tradeline details (structured JSON within PostgreSQL)
- **Unstructured data**: PDF credit reports, bureau response letters (object storage)
- **Time-series data**: Historical credit scores (TimescaleDB hypertables)
- **Vector embeddings** (Phase 3): Credit repair knowledge base (Pinecone/Weaviate)

**Veracity (Data Quality)**:
- **Accuracy target**: 95%+ for AI-classified negative tradelines (validation against user corrections)
- **Completeness**: All tradelines extracted from credit report must be stored
- **Consistency**: Same tradeline across 3 bureaus must maintain consistent identity (tradeline_id)
- **Timeliness**: OCR processing <30 seconds for PDFs <10MB, background jobs for larger files

### Data Quality Requirements

**Accuracy Standards**:
- **Negative tradeline classification**: 95%+ precision/recall validated against user edits
- **OCR extraction quality**: 98%+ text accuracy for structured credit report fields
- **Duplicate detection**: Zero duplicate tradelines within same credit report

**Completeness Standards**:
- **Mandatory fields**: User ID, tradeline account name, account type, status must never be null
- **Optional fields**: Payment history, balance, open date can be null if not present in report
- **Audit trail**: Every status change must have timestamp and user/system attribution

**Consistency Standards**:
- **Multi-bureau identity**: Same tradeline reported by multiple bureaus shares common tradeline_id
- **Status transitions**: Only valid state transitions allowed (e.g., "Pending" → "Investigating", not "Deleted" → "Pending")
- **Rate limit sync**: Middleware in-memory counters sync to Redis every 5 minutes to prevent drift

**Timeliness Standards**:
- **Real-time analytics**: Personal statistics updated within 1 second of status change
- **Status updates**: User-initiated status changes reflected in dashboard immediately
- **OCR processing**: Bureau response letter processing completes within 30 seconds

## 3. Data Model Design

### 3.1 Conceptual Data Model

**Core Business Entities**:

```
┌─────────────┐
│    User     │ (Individual consumer using platform)
└──────┬──────┘
       │
       ├──────┐ uploads         ┌──────────────────┐
       │      └─────────────────→│  Credit Report   │ (PDF uploaded from bureau)
       │                         └────────┬─────────┘
       │                                  │
       │                                  │ contains
       │                                  ↓
       │                         ┌──────────────────┐
       │                         │   Tradeline      │ (Individual credit account)
       │                         └────────┬─────────┘
       │                                  │
       │ initiates                        │ disputable?
       ↓                                  ↓
┌──────────────────┐          ┌──────────────────────┐
│  Dispute Letter  │ ←────────│ Negative Tradeline   │ (Late payment, charge-off, etc.)
└────────┬─────────┘          └──────────────────────┘
         │
         │ mailed via
         ↓
┌──────────────────┐          ┌──────────────────────┐
│ Mailing Record   │ ←────────│  Dispute Tracking    │ (Per-bureau status: Equifax, TransUnion, Experian)
└──────────────────┘          └──────────────────────┘
         │
         │ aggregates to
         ↓
┌──────────────────┐
│ User Analytics   │ (Success rate, items removed, time to resolution)
└──────────────────┘
```

**Entity Relationships**:
1. **User** → **Credit Report**: One-to-many (user uploads multiple reports over time)
2. **Credit Report** → **Tradeline**: One-to-many (each report contains 10-30 tradelines)
3. **Tradeline** → **Negative Tradeline**: Subtype relationship (negative flag indicates disputable)
4. **User** → **Dispute Letter**: One-to-many (user generates multiple dispute letters)
5. **Dispute Letter** → **Tradeline**: Many-to-one (multiple bureaus dispute same tradeline)
6. **Dispute Letter** → **Dispute Tracking**: One-to-many (one letter creates 3 bureau-specific tracking records)
7. **Dispute Tracking** → **Mailing Record**: One-to-one (each bureau dispute has one mailing record)
8. **Dispute Tracking** → **User Analytics**: Many-to-one (all disputes aggregate to user statistics)

**Business Rules**:
1. Users can only dispute tradelines flagged as "negative" by AI or manually marked
2. Each tradeline can have up to 3 concurrent disputes (one per bureau)
3. Free users limited to 2 credit report uploads and 3 dispute letters per month (rate limiting)
4. Dispute status transitions must follow valid state machine (e.g., "Investigating" can only follow "Pending")
5. Mailing records created only for paid dispute letters (not free generated letters)
6. User analytics recalculated automatically on every dispute status change

### 3.2 Logical Data Model

**Entity: Users**
```
users
├── id (UUID, PK) - Supabase auth user ID
├── email (TEXT, UNIQUE, NOT NULL)
├── created_at (TIMESTAMPTZ, NOT NULL)
├── subscription_tier (ENUM: 'free', 'paid') - Future use for subscription plans
├── rate_limit_reports (INTEGER, DEFAULT 0) - Monthly report upload counter
├── rate_limit_letters (INTEGER, DEFAULT 0) - Monthly letter generation counter
├── rate_limit_reset_date (DATE) - Next reset date for rate limits
└── metadata (JSONB) - Flexible storage for user preferences, settings
```

**Indexes**:
- Primary key index on `id` (automatic)
- Unique index on `email`
- Index on `rate_limit_reset_date` for periodic reset jobs

**Supabase RLS Policy**:
```sql
-- Users can only read/update their own record
CREATE POLICY "Users can view own profile" ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON users FOR UPDATE USING (auth.uid() = id);
```

---

**Entity: Credit Reports**
```
credit_reports
├── id (UUID, PK, DEFAULT gen_random_uuid())
├── user_id (UUID, FK → users.id, NOT NULL)
├── bureau_source (ENUM: 'equifax', 'transunion', 'experian', 'unknown')
├── upload_date (TIMESTAMPTZ, DEFAULT NOW())
├── file_url (TEXT) - Supabase Storage URL to PDF
├── processing_status (ENUM: 'pending', 'processing', 'completed', 'failed')
├── processing_error (TEXT) - Error message if processing_status = 'failed'
└── metadata (JSONB) - File size, page count, OCR confidence scores
```

**Indexes**:
- Primary key index on `id`
- Index on `user_id, upload_date DESC` for user's report history queries
- Index on `processing_status` for background job monitoring

**Supabase RLS Policy**:
```sql
-- Users can only access their own credit reports
CREATE POLICY "Users can view own reports" ON credit_reports FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own reports" ON credit_reports FOR INSERT WITH CHECK (auth.uid() = user_id);
```

---

**Entity: Tradelines**
```
tradelines
├── id (UUID, PK, DEFAULT gen_random_uuid())
├── credit_report_id (UUID, FK → credit_reports.id, NOT NULL, ON DELETE CASCADE)
├── user_id (UUID, FK → users.id, NOT NULL) - Denormalized for query performance
├── account_name (TEXT, NOT NULL) - "Chase Credit Card", "Wells Fargo Mortgage"
├── account_type (ENUM: 'credit_card', 'mortgage', 'auto_loan', 'student_loan', 'personal_loan', 'other')
├── account_number_last_4 (TEXT) - Last 4 digits of account number
├── status (TEXT) - "Open", "Closed", "Charge-off", "Collection"
├── balance (DECIMAL(12,2))
├── credit_limit (DECIMAL(12,2))
├── payment_history (JSONB) - Array of monthly payment statuses: [{"month": "2024-01", "status": "OK"}, ...]
├── open_date (DATE)
├── closed_date (DATE)
├── is_negative (BOOLEAN, DEFAULT FALSE) - AI-classified or user-marked
├── negative_type (ENUM: 'late_payment', 'charge_off', 'collection', 'bankruptcy', 'foreclosure', 'repossession', 'tax_lien', 'judgment', NULL)
├── negative_reason (TEXT) - Detailed explanation why flagged as negative
├── is_disputable (BOOLEAN, DEFAULT FALSE) - User-confirmed disputable
├── dispute_reason (TEXT) - User's reason for disputing
├── tradeline_details (JSONB) - Flexible storage for bureau-specific fields
└── created_at (TIMESTAMPTZ, DEFAULT NOW())
```

**Indexes**:
- Primary key index on `id`
- Index on `user_id, is_negative, is_disputable` for dispute dashboard queries
- Index on `credit_report_id` for report detail view
- GIN index on `payment_history` for JSON querying
- Index on `account_name, account_number_last_4` for duplicate detection

**Supabase RLS Policy**:
```sql
-- Users can only access their own tradelines
CREATE POLICY "Users can view own tradelines" ON tradelines FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can update own tradelines" ON tradelines FOR UPDATE USING (auth.uid() = user_id);
```

**Rationale for Structured JSON in `payment_history`**:
- Credit reports contain variable-length payment histories (1-7 years)
- Storing as JSONB array allows flexible querying: `payment_history @> '[{"status": "30"}]'` finds all 30-day late payments
- Avoids creating separate `payment_history_entries` table with millions of rows
- Maintains relational integrity while accommodating variable data

---

**Entity: Dispute Letters**
```
dispute_letters
├── id (UUID, PK, DEFAULT gen_random_uuid())
├── user_id (UUID, FK → users.id, NOT NULL)
├── tradeline_id (UUID, FK → tradelines.id, NOT NULL, ON DELETE CASCADE)
├── bureau (ENUM: 'equifax', 'transunion', 'experian', NOT NULL)
├── letter_content (TEXT, NOT NULL) - Full FCRA-compliant dispute letter text
├── dispute_reason (TEXT, NOT NULL) - User's selected/custom reason
├── generation_date (TIMESTAMPTZ, DEFAULT NOW())
├── is_mailed (BOOLEAN, DEFAULT FALSE) - TRUE if user paid for mailing service
├── mailing_date (TIMESTAMPTZ) - NULL if not mailed
└── tracking_number (TEXT) - USPS tracking number from Lob/USPS API
```

**Indexes**:
- Primary key index on `id`
- Index on `user_id, generation_date DESC` for user's letter history
- Index on `tradeline_id, bureau` for multi-bureau tracking
- Index on `is_mailed, mailing_date` for mailing service analytics

**Supabase RLS Policy**:
```sql
-- Users can only access their own dispute letters
CREATE POLICY "Users can view own letters" ON dispute_letters FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own letters" ON dispute_letters FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own letters" ON dispute_letters FOR UPDATE USING (auth.uid() = user_id);
```

---

**Entity: Dispute Tracking**
```
dispute_tracking
├── id (UUID, PK, DEFAULT gen_random_uuid())
├── user_id (UUID, FK → users.id, NOT NULL) - Denormalized for query performance
├── dispute_letter_id (UUID, FK → dispute_letters.id, NOT NULL, ON DELETE CASCADE)
├── tradeline_id (UUID, FK → tradelines.id, NOT NULL)
├── bureau (ENUM: 'equifax', 'transunion', 'experian', NOT NULL)
├── status (ENUM: 'pending', 'investigating', 'verified', 'deleted', 'updated', 'escalated', 'expired', 'blank', NOT NULL, DEFAULT 'pending')
├── status_updated_at (TIMESTAMPTZ, DEFAULT NOW())
├── status_updated_by (ENUM: 'user', 'ocr_system') - Attribution for manual vs automated updates
├── mailing_date (TIMESTAMPTZ) - Copied from dispute_letters for convenience
├── tracking_number (TEXT) - USPS tracking number
├── bureau_response_url (TEXT) - Supabase Storage URL to uploaded bureau response PDF
├── resolution_notes (TEXT) - User notes or OCR-extracted resolution details
└── created_at (TIMESTAMPTZ, DEFAULT NOW())
```

**Indexes**:
- Primary key index on `id`
- Composite index on `user_id, tradeline_id, bureau` (UNIQUE) for multi-bureau dashboard queries
- Index on `status, status_updated_at` for analytics queries
- Index on `dispute_letter_id` for letter-to-tracking lookup

**Supabase RLS Policy**:
```sql
-- Users can only access their own dispute tracking records
CREATE POLICY "Users can view own disputes" ON dispute_tracking FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can update own disputes" ON dispute_tracking FOR UPDATE USING (auth.uid() = user_id);
```

**Rationale for Denormalized `user_id`**:
- Avoids JOIN to `dispute_letters` table for common dashboard queries
- Supabase RLS policies require `user_id` in every table for efficient row filtering
- Storage overhead minimal (UUID = 16 bytes per record)

---

**Entity: Status History (Audit Trail)**
```
status_history
├── id (UUID, PK, DEFAULT gen_random_uuid())
├── dispute_tracking_id (UUID, FK → dispute_tracking.id, NOT NULL, ON DELETE CASCADE)
├── user_id (UUID, FK → users.id, NOT NULL) - Denormalized for RLS
├── old_status (ENUM: 'pending', 'investigating', 'verified', 'deleted', 'updated', 'escalated', 'expired', 'blank')
├── new_status (ENUM: 'pending', 'investigating', 'verified', 'deleted', 'updated', 'escalated', 'expired', 'blank', NOT NULL)
├── changed_at (TIMESTAMPTZ, DEFAULT NOW())
├── changed_by (ENUM: 'user', 'ocr_system')
└── change_notes (TEXT) - Reason for change or OCR confidence score
```

**Indexes**:
- Primary key index on `id`
- Index on `dispute_tracking_id, changed_at DESC` for timeline visualization
- Index on `user_id` for user's full audit trail

**Supabase RLS Policy**:
```sql
-- Users can only view their own status history (insert-only, no updates)
CREATE POLICY "Users can view own status history" ON status_history FOR SELECT USING (auth.uid() = user_id);
```

**Rationale for Separate Audit Table**:
- Maintains complete history of all status transitions for dispute timeline view
- Immutable records (no UPDATE policy) ensure audit trail integrity
- Enables time-to-resolution calculations: `changed_at WHERE new_status = 'deleted' - changed_at WHERE old_status = 'pending'`

---

**Entity: Mailing Records**
```
mailing_records
├── id (UUID, PK, DEFAULT gen_random_uuid())
├── user_id (UUID, FK → users.id, NOT NULL) - Denormalized for RLS
├── dispute_letter_id (UUID, FK → dispute_letters.id, NOT NULL, ON DELETE CASCADE)
├── mailing_service (ENUM: 'lob', 'usps_direct') - Track which API used
├── tracking_number (TEXT, NOT NULL)
├── mailing_date (TIMESTAMPTZ, DEFAULT NOW())
├── delivery_status (ENUM: 'sent', 'in_transit', 'delivered', 'failed', 'returned')
├── delivery_date (TIMESTAMPTZ)
├── api_response (JSONB) - Full Lob/USPS API response for debugging
└── created_at (TIMESTAMPTZ, DEFAULT NOW())
```

**Indexes**:
- Primary key index on `id`
- Index on `user_id, mailing_date DESC` for user's mailing history
- Index on `tracking_number` for USPS tracking webhook lookups
- Index on `delivery_status` for monitoring failed deliveries

**Supabase RLS Policy**:
```sql
-- Users can only view their own mailing records
CREATE POLICY "Users can view own mailing" ON mailing_records FOR SELECT USING (auth.uid() = user_id);
```

---

**Entity: User Analytics (Cached Aggregations)**
```
user_analytics
├── user_id (UUID, PK, FK → users.id, NOT NULL)
├── total_disputes_initiated (INTEGER, DEFAULT 0)
├── total_items_deleted (INTEGER, DEFAULT 0) - Count of status = 'deleted'
├── success_rate (DECIMAL(5,2)) - Percentage: (items_deleted / total_disputes) * 100
├── average_days_to_resolution (DECIMAL(6,2)) - Average time from 'pending' to 'deleted'
├── disputes_by_bureau (JSONB) - {"equifax": 10, "transunion": 8, "experian": 12}
├── last_updated (TIMESTAMPTZ, DEFAULT NOW())
└── created_at (TIMESTAMPTZ, DEFAULT NOW())
```

**Indexes**:
- Primary key index on `user_id`

**Supabase RLS Policy**:
```sql
-- Users can only view their own analytics
CREATE POLICY "Users can view own analytics" ON user_analytics FOR SELECT USING (auth.uid() = user_id);
```

**Rationale for Cached Analytics**:
- Personal statistics dashboard requires real-time performance (<200ms)
- Calculating aggregations on every page load would scan `dispute_tracking` table
- Trigger-based updates ensure cache refreshes on every status change
- JSONB `disputes_by_bureau` avoids separate table for bureau-specific counts

---

### 3.3 Physical Data Model

**Database Platform**: PostgreSQL 15+ (via Supabase managed service)

**Table Creation Strategy**:

```sql
-- Enable UUID extension for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable JSONB GIN indexing extension
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create ENUM types (shared across tables)
CREATE TYPE subscription_tier AS ENUM ('free', 'paid');
CREATE TYPE bureau_type AS ENUM ('equifax', 'transunion', 'experian', 'unknown');
CREATE TYPE processing_status AS ENUM ('pending', 'processing', 'completed', 'failed');
CREATE TYPE account_type AS ENUM ('credit_card', 'mortgage', 'auto_loan', 'student_loan', 'personal_loan', 'other');
CREATE TYPE negative_type AS ENUM ('late_payment', 'charge_off', 'collection', 'bankruptcy', 'foreclosure', 'repossession', 'tax_lien', 'judgment');
CREATE TYPE dispute_status AS ENUM ('pending', 'investigating', 'verified', 'deleted', 'updated', 'escalated', 'expired', 'blank');
CREATE TYPE update_attribution AS ENUM ('user', 'ocr_system');
CREATE TYPE mailing_service AS ENUM ('lob', 'usps_direct');
CREATE TYPE delivery_status AS ENUM ('sent', 'in_transit', 'delivered', 'failed', 'returned');

-- Physical table definitions (see logical model above for column details)
-- Tables include:
-- 1. users
-- 2. credit_reports
-- 3. tradelines
-- 4. dispute_letters
-- 5. dispute_tracking
-- 6. status_history
-- 7. mailing_records
-- 8. user_analytics
```

**Partitioning Strategy** (Future Optimization):
- No partitioning required for initial scale (1,000 users, ~15K tradeline records)
- Consider partitioning `tradelines` by `user_id` HASH when exceeding 1M records
- Consider partitioning `status_history` by `changed_at` (monthly) when exceeding 10M records

**Index Optimization Guidelines**:
1. **Composite indexes**: Create indexes matching common query WHERE clauses (e.g., `user_id, is_negative, is_disputable`)
2. **GIN indexes for JSONB**: Use GIN indexes on `payment_history` and `tradeline_details` for JSON querying
3. **Covering indexes**: Add frequently queried columns to index INCLUDE clause to avoid table lookups
4. **Partial indexes**: Create indexes with WHERE clauses for status-specific queries (e.g., `WHERE is_negative = TRUE`)

**Connection Pooling Configuration**:
- **Supabase Pooler**: Use PgBouncer in transaction mode for FastAPI connection pooling
- **Connection limits**: 100 max connections (sufficient for 1,000+ concurrent users)
- **Timeout settings**: 30-second query timeout, 5-minute idle connection timeout

## 4. TimescaleDB Integration for Historical Credit Scores (Phase 3)

**Rationale for Early Implementation**:
- **Migration complexity**: Adding time-series DB later requires data migration and query rewrites
- **Foundation scalability**: TimescaleDB hypertables optimize time-series queries from day one
- **Storage efficiency**: Automatic compression for historical data reduces storage costs

**Hypertable Design**:

```sql
-- Install TimescaleDB extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create time-series table for credit scores
CREATE TABLE credit_score_history (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    score_value INTEGER NOT NULL CHECK (score_value BETWEEN 300 AND 850),
    bureau_source bureau_type NOT NULL,
    score_factors JSONB, -- FICO score factors: {"payment_history": 35, "credit_utilization": 30, ...}
    PRIMARY KEY (user_id, timestamp, bureau_source)
);

-- Convert to TimescaleDB hypertable (partitioned by time)
SELECT create_hypertable('credit_score_history', 'timestamp', chunk_time_interval => INTERVAL '1 month');

-- Create index for user-specific score queries
CREATE INDEX idx_credit_score_user_bureau ON credit_score_history (user_id, bureau_source, timestamp DESC);

-- Enable automatic compression for chunks older than 6 months
ALTER TABLE credit_score_history SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'user_id, bureau_source'
);

SELECT add_compression_policy('credit_score_history', INTERVAL '6 months');
```

**Supabase RLS Policy for Time-Series Data**:
```sql
-- Users can only access their own credit score history
CREATE POLICY "Users can view own score history" ON credit_score_history FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own score history" ON credit_score_history FOR INSERT WITH CHECK (auth.uid() = user_id);
```

**Query Performance Benefits**:
- **Time-range queries**: `SELECT * FROM credit_score_history WHERE user_id = $1 AND timestamp > NOW() - INTERVAL '1 year'` uses hypertable chunk pruning
- **Downsampling**: TimescaleDB continuous aggregates for monthly/yearly score trends
- **Compression**: Automatic compression reduces storage by 70-90% for historical data

**Integration with Existing Schema**:
- `credit_score_history` references `users(id)` via foreign key
- Score snapshots triggered by credit report uploads (extracted from report or predicted by AI in Phase 3)
- Dashboard displays historical score chart using TimescaleDB downsampling functions

## 5. Multi-Bureau Data Modeling Strategy

**Challenge**: Same tradeline appears in reports from multiple bureaus with different statuses

**Solution**: Unified tradeline identity with per-bureau dispute tracking

**Data Model Pattern**:

```
Tradeline (Master Record)
├── id: UUID (shared across all bureaus)
├── account_name: "Chase Credit Card"
├── account_number_last_4: "1234"
└── user_id: UUID

Dispute Tracking (Per-Bureau Records)
├── id: UUID (unique per bureau)
├── tradeline_id: UUID (references master tradeline)
├── bureau: 'equifax' | 'transunion' | 'experian'
├── status: 'deleted' | 'investigating' | 'blank'
└── user_id: UUID
```

**Example Multi-Bureau Query**:

```sql
-- Fetch all disputes for a tradeline across all bureaus
SELECT
    t.account_name,
    dt.bureau,
    dt.status,
    dt.status_updated_at
FROM tradelines t
LEFT JOIN dispute_tracking dt ON dt.tradeline_id = t.id
WHERE t.id = 'tradeline-uuid-123'
ORDER BY dt.bureau;

-- Result:
-- account_name         | bureau      | status        | status_updated_at
-- "Chase Credit Card"  | equifax     | deleted       | 2024-12-01
-- "Chase Credit Card"  | transunion  | investigating | 2024-12-10
-- "Chase Credit Card"  | experian    | blank         | NULL
```

**Dashboard Visualization Strategy**:
- **Master tradeline row**: Display tradeline details once (account name, balance, type)
- **Bureau status columns**: Show 3 columns (Equifax, TransUnion, Experian) with color-coded status badges
- **Timeline view**: Horizontal timeline showing progression of each bureau's investigation

**Duplicate Detection Logic**:
- **Matching criteria**: `account_name` + `account_number_last_4` + `user_id`
- **Bureau merge**: If same tradeline found in multiple report uploads, reuse existing `tradeline_id`
- **Conflict resolution**: If tradeline details differ across bureaus, store bureau-specific fields in `tradeline_details` JSONB

## Summary of Key Schema Design Decisions

1. **Supabase PostgreSQL as primary database**: Leverages managed service with built-in RLS for multi-tenancy
2. **Structured JSON for variable data**: `payment_history` and `tradeline_details` stored as JSONB for flexibility
3. **Denormalized `user_id` in child tables**: Optimizes RLS performance and eliminates JOIN overhead
4. **Separate audit trail table**: `status_history` maintains immutable record of all status transitions
5. **Cached analytics table**: `user_analytics` provides real-time personal statistics without expensive aggregations
6. **TimescaleDB integration from start**: Avoids future migration complexity for Phase 3 score tracking
7. **Multi-bureau dispute tracking**: Per-bureau `dispute_tracking` records enable parallel dispute management
8. **ENUM types for controlled vocabularies**: Ensures data integrity for status transitions and categorical fields

**Next Steps**:
- **@analysis-database-architecture-strategy.md**: Database technology selection and architectural patterns
- **@analysis-data-integration-pipelines.md**: Data flow design for AI pipeline, mailing service, and analytics
