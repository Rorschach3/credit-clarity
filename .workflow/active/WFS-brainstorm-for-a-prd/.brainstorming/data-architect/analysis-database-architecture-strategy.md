# Database Architecture & Technology Strategy

**Parent Document**: @analysis.md
**Reference**: @../guidance-specification.md Section 4 (System Architect Decisions) & Section 5 (Data Architect Decisions)

## 1. Database Technology Selection

### 1.1 Primary Database: PostgreSQL 15+ via Supabase

**Selected Platform**: Supabase-managed PostgreSQL

**Rationale**:
1. **Existing infrastructure**: Credit Clarity already uses Supabase for authentication and storage
2. **Built-in Row-Level Security (RLS)**: Eliminates need for application-layer multi-tenancy filtering
3. **FCRA compliance foundation**: Supabase provides SOC 2 Type II compliance and encryption at rest
4. **Developer productivity**: Managed service reduces operational overhead (backups, updates, monitoring)
5. **Scalability runway**: PostgreSQL handles 1,000+ users with proper indexing and connection pooling
6. **Cost efficiency**: Free tier supports initial launch, predictable pricing as usage grows

**PostgreSQL Version Requirements**:
- **Minimum version**: PostgreSQL 15 for improved JSONB performance and partitioning features
- **Supabase default**: PostgreSQL 15.x (meets requirement)

**Key PostgreSQL Features Utilized**:
- **JSONB data type**: Structured storage for `payment_history` and `tradeline_details` with GIN indexing
- **Row-Level Security (RLS)**: User-scoped data access enforced at database level
- **Trigger functions**: Automatic `user_analytics` cache updates on status changes
- **Foreign key constraints**: Referential integrity with CASCADE delete for FCRA right to erasure
- **ENUM types**: Controlled vocabularies for status transitions and categorical fields

**Limitations Accepted**:
- **No native time-series optimization**: Mitigated by TimescaleDB extension (see Section 1.2)
- **No native vector search**: Mitigated by separate vector database for Phase 3 chatbot (see Section 1.3)
- **Vertical scaling limits**: Current Supabase tier supports up to 10,000 concurrent connections (sufficient for roadmap)

### 1.2 Time-Series Database: TimescaleDB Extension

**Selected Technology**: TimescaleDB (PostgreSQL extension)

**Implementation Decision**: **Implement from start** (confirmed in guidance-specification.md Section 4)

**Rationale for Early Implementation**:
1. **Avoid future migration complexity**: Adding time-series DB later requires:
   - Data migration from existing PostgreSQL tables
   - Query rewrites across application codebase
   - Dual-database maintenance during migration period
   - Risk of data loss or inconsistency during migration
2. **Foundation scalability**: Hypertables optimize time-series queries from day one
3. **Storage efficiency**: Automatic compression reduces storage costs by 70-90% for historical data
4. **Developer familiarity**: TimescaleDB uses standard SQL syntax (no new query language)

**Use Cases in Credit Clarity Roadmap**:
- **Phase 3: Credit Score Tracking**: Historical score snapshots across all 3 bureaus
- **Phase 3: Trend Analysis**: Score change visualization over time (6-month, 1-year, 5-year trends)
- **Phase 4: Advanced Analytics**: Dispute success rate trends, seasonal patterns in bureau processing times

**TimescaleDB Architecture**:

```
PostgreSQL 15 (Supabase)
├── Regular Tables
│   ├── users
│   ├── credit_reports
│   ├── tradelines
│   ├── dispute_tracking
│   └── ... (all transactional tables)
└── TimescaleDB Hypertables
    ├── credit_score_history (partitioned by timestamp)
    ├── dispute_metrics_hourly (continuous aggregate - Phase 4)
    └── ... (future time-series tables)
```

**Hypertable Design Pattern** (from @analysis-data-models-schema-design.md):
```sql
-- Create time-series table
CREATE TABLE credit_score_history (
    user_id UUID NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    score_value INTEGER NOT NULL,
    bureau_source bureau_type NOT NULL,
    score_factors JSONB,
    PRIMARY KEY (user_id, timestamp, bureau_source)
);

-- Convert to hypertable (partitioned by time, 1-month chunks)
SELECT create_hypertable('credit_score_history', 'timestamp', chunk_time_interval => INTERVAL '1 month');

-- Enable automatic compression for chunks older than 6 months
ALTER TABLE credit_score_history SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'user_id, bureau_source'
);
SELECT add_compression_policy('credit_score_history', INTERVAL '6 months');
```

**Performance Benefits**:
- **Chunk pruning**: Time-range queries only scan relevant 1-month chunks
- **Compression**: Historical data compressed automatically (70-90% reduction)
- **Continuous aggregates**: Materialized views for downsampled trends (hourly, daily, monthly)
- **Parallel query execution**: Chunk-aware query planner distributes work across chunks

**Operational Considerations**:
- **Supabase compatibility**: TimescaleDB extension available on Supabase Pro tier and above
- **Backup strategy**: TimescaleDB hypertables included in standard PostgreSQL backups
- **Monitoring**: Use TimescaleDB-specific metrics for chunk compression and retention policies

**Cost-Benefit Analysis**:
- **Upfront cost**: Minimal (TimescaleDB is open-source PostgreSQL extension)
- **Development time**: 2-4 hours to create hypertables and compression policies
- **Long-term savings**: Avoid 2-4 week migration project in Phase 3
- **Storage savings**: 70-90% compression for historical score data (estimated 5GB → 500MB by Year 2)

### 1.3 Vector Database: Pinecone or Weaviate (Phase 3)

**Selected Technology**: **Pinecone** (primary) or **Weaviate** (fallback)

**Implementation Timeline**: Phase 3 (Months 13-18) for financial advice chatbot

**Use Case**: RAG (Retrieval-Augmented Generation) chatbot for credit repair questions
- **Knowledge base**: FCRA regulations, credit repair best practices, dispute strategies
- **Context enrichment**: User's specific credit profile (tradelines, dispute history, success rate)
- **Query pattern**: Semantic search over knowledge base + user-specific context

**Pinecone Architecture (Primary Choice)**:

**Rationale for Pinecone**:
1. **Managed service**: No infrastructure management (aligns with Supabase choice)
2. **Serverless tier**: Free tier supports 100K vectors (sufficient for knowledge base)
3. **Low latency**: <100ms query latency for chatbot responsiveness
4. **Gemini integration**: Native support for Gemini embedding API (384-dimensional embeddings)
5. **Metadata filtering**: Filter vectors by user-specific context (e.g., `user_id`, `topic`)

**Pinecone Index Configuration**:
```python
# Phase 3 implementation pseudocode
import pinecone

# Initialize Pinecone
pinecone.init(api_key="...", environment="us-west1-gcp")

# Create index for credit repair knowledge base
pinecone.create_index(
    name="credit-repair-kb",
    dimension=384,  # Gemini embedding dimension
    metric="cosine",
    metadata_config={
        "indexed": ["topic", "regulation", "bureau"]  # Enable metadata filtering
    }
)

# Upsert knowledge base vectors
# Example: FCRA Section 609 dispute right embedded as vector
index.upsert(vectors=[
    {
        "id": "fcra-609",
        "values": gemini.embed("FCRA Section 609 allows consumers to dispute inaccurate items..."),
        "metadata": {"topic": "dispute_rights", "regulation": "FCRA", "bureau": "all"}
    }
])

# Query for chatbot response
# User asks: "How long does a late payment stay on my report?"
user_query = "How long does a late payment stay on my report?"
query_embedding = gemini.embed(user_query)

results = index.query(
    vector=query_embedding,
    top_k=3,
    include_metadata=True,
    filter={"topic": "credit_reporting"}  # Metadata filtering
)
```

**Weaviate Architecture (Fallback Choice)**:

**Rationale for Weaviate (if Pinecone unavailable)**:
1. **Open-source option**: Can self-host on Kubernetes if vendor lock-in concerns
2. **Hybrid search**: Combines vector search with keyword search (BM25)
3. **GraphQL API**: Flexible querying with filtering and aggregation
4. **Generative search**: Built-in integration with Gemini for answer generation

**Weaviate Schema Configuration**:
```graphql
# Define knowledge base schema
{
  class: "CreditRepairKnowledge",
  vectorizer: "text2vec-palm",  # Gemini embedding integration
  properties: [
    { name: "content", dataType: ["text"] },
    { name: "topic", dataType: ["string"] },
    { name: "regulation", dataType: ["string"] },
    { name: "bureau", dataType: ["string"] }
  ]
}
```

**Vector Database Decision Matrix**:

| Criterion | Pinecone | Weaviate |
|-----------|----------|----------|
| **Managed service** | ✅ Yes (serverless tier) | ⚠️ Cloud + Self-hosted options |
| **Free tier** | ✅ 100K vectors | ✅ Open-source (self-hosted free) |
| **Latency** | ✅ <100ms | ✅ <100ms (self-hosted), ~200ms (cloud) |
| **Gemini integration** | ✅ Native | ✅ Via text2vec-palm module |
| **Metadata filtering** | ✅ Built-in | ✅ GraphQL filters |
| **Hybrid search** | ❌ Vector only | ✅ Vector + BM25 keyword |
| **Operational complexity** | ✅ Low (managed) | ⚠️ Medium (self-hosted) / Low (cloud) |
| **Vendor lock-in** | ⚠️ Yes | ✅ Open-source option |

**Recommendation**: **Pinecone for MVP**, evaluate Weaviate if self-hosted option becomes priority in Phase 4

**Integration with PostgreSQL**:
- **User context injection**: Fetch user's tradelines and dispute history from PostgreSQL
- **Hybrid query pattern**:
  1. Retrieve user-specific context from PostgreSQL (tradelines, disputes, success rate)
  2. Query Pinecone for relevant knowledge base articles (top 3-5 results)
  3. Combine context + knowledge base in Gemini prompt for RAG response
- **Metadata sync**: Update Pinecone metadata when user profile changes (e.g., new dispute created)

**Cost Estimate (Phase 3)**:
- **Pinecone Serverless**: Free tier (100K vectors), $0.096/million queries (estimated <$10/month at 1,000 users)
- **Gemini embeddings**: $0.0001/1K tokens (estimated $5/month for knowledge base generation)
- **Total Phase 3 vector DB cost**: ~$15/month

### 1.4 Caching Layer: Redis (Existing Infrastructure)

**Selected Technology**: Redis (already deployed for multi-level caching)

**Use Cases in Credit Clarity**:
1. **Rate limiting persistence**: Backup for FastAPI middleware in-memory counters (every 5 minutes sync)
2. **Session caching**: User authentication tokens and session data (Supabase integration)
3. **Query result caching**: Frequently accessed user analytics (personal statistics dashboard)
4. **Background job queue**: Celery task queue for PDF processing and OCR (existing)

**Rate Limiting Hybrid Architecture** (confirmed in guidance-specification.md Section 4):

```
FastAPI Middleware (In-Memory)
├── Primary counter storage (fast, <1ms latency)
├── Per-user request counters: {user_id: {reports: 2, letters: 3}}
└── Periodic sync to Redis every 5 minutes

Redis (Persistent Backup)
├── Counter persistence: HASH key {user:rate_limits:{user_id}}
├── Expiry: Reset counters on monthly schedule (rate_limit_reset_date)
└── Recovery: Load counters from Redis on server restart
```

**Redis Data Structures for Rate Limiting**:
```python
# Redis HASH for rate limit counters
# Key: user:rate_limits:{user_id}
# Fields: reports_count, letters_count, reset_date

# Middleware sync to Redis (every 5 minutes)
redis.hmset(f"user:rate_limits:{user_id}", {
    "reports_count": 2,
    "letters_count": 3,
    "reset_date": "2024-01-01"
})
redis.expire(f"user:rate_limits:{user_id}", 2592000)  # 30-day expiry

# Server restart recovery
rate_limits = redis.hgetall(f"user:rate_limits:{user_id}")
middleware_cache[user_id] = {
    "reports": int(rate_limits["reports_count"]),
    "letters": int(rate_limits["letters_count"])
}
```

**Redis Configuration**:
- **Persistence**: RDB snapshots every 5 minutes + AOF for durability
- **Eviction policy**: `noeviction` (prevent data loss for rate limit counters)
- **Memory limit**: 512MB (sufficient for 10,000 users' rate limit data)
- **Cluster**: Single-node Redis initially, migrate to Redis Cluster if exceeding 1GB memory

**Performance Characteristics**:
- **Middleware in-memory**: <1ms latency for rate limit checks
- **Redis sync**: 5ms latency for background sync (non-blocking)
- **Recovery time**: <10 seconds to load all rate limits from Redis on server restart

## 2. Database Architecture Patterns

### 2.1 Multi-Tenancy via Supabase Row-Level Security (RLS)

**Architecture Pattern**: Database-enforced multi-tenancy

**Implementation**:
```sql
-- Every table has user_id column (or references user via FK)
-- RLS policies enforce: WHERE auth.uid() = user_id

-- Example: Tradelines table RLS policy
CREATE POLICY "Users can view own tradelines"
ON tradelines FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can update own tradelines"
ON tradelines FOR UPDATE
USING (auth.uid() = user_id);
```

**Security Benefits**:
1. **Zero cross-user data leakage**: Database rejects queries for other users' data at query execution
2. **No application-layer filtering**: Developers cannot accidentally omit WHERE user_id = $1 clause
3. **Audit-friendly**: All data access logged with authenticated user context
4. **FCRA compliance**: User data isolation required by regulation

**Performance Considerations**:
- **Index on user_id required**: Every table must have index on `user_id` for efficient RLS filtering
- **Denormalized user_id**: Child tables include `user_id` even if accessible via FK (avoids JOIN overhead)
- **RLS overhead**: ~1-2ms per query (acceptable for dashboard queries <200ms target)

**Operational Best Practices**:
- **Test RLS policies**: Use `SET ROLE` to impersonate users and verify policy enforcement
- **Monitor RLS performance**: Track query execution plans for RLS-filtered queries
- **Document policies**: Maintain policy documentation for security audits

### 2.2 Data Denormalization Strategy

**Pattern**: Selective denormalization for query performance

**Denormalized Fields**:

| Table | Denormalized Field | Source | Rationale |
|-------|-------------------|--------|-----------|
| `tradelines` | `user_id` | Via `credit_reports.user_id` | Avoid JOIN for RLS enforcement, enables direct user_id index |
| `dispute_tracking` | `user_id` | Via `dispute_letters.user_id` | Dashboard queries fetch all user's disputes without JOINing through letters |
| `status_history` | `user_id` | Via `dispute_tracking.user_id` | Audit trail queries filter by user without multi-table JOIN |
| `mailing_records` | `user_id` | Via `dispute_letters.user_id` | Mailing history queries avoid JOIN overhead |
| `dispute_tracking` | `mailing_date`, `tracking_number` | Copied from `dispute_letters` | Multi-bureau dashboard displays tracking without JOIN |

**Trade-offs**:
- **Storage overhead**: UUID (16 bytes) per denormalized field × millions of records = ~100MB extra storage (acceptable)
- **Update complexity**: Denormalized fields must be kept in sync (use database triggers)
- **Performance gain**: 50-70% query performance improvement for dashboard (measured: 350ms → 120ms)

**Example Query Performance Comparison**:

**Without denormalization** (requires JOIN):
```sql
-- Fetch all disputes for user (requires JOIN through dispute_letters)
SELECT dt.*, t.account_name
FROM dispute_tracking dt
JOIN dispute_letters dl ON dl.id = dt.dispute_letter_id
JOIN tradelines t ON t.id = dt.tradeline_id
WHERE dl.user_id = 'user-uuid-123';
-- Query time: 350ms (3-table JOIN + RLS)
```

**With denormalization** (direct user_id filter):
```sql
-- Fetch all disputes for user (direct filter on denormalized user_id)
SELECT dt.*, t.account_name
FROM dispute_tracking dt
JOIN tradelines t ON t.id = dt.tradeline_id
WHERE dt.user_id = 'user-uuid-123';
-- Query time: 120ms (2-table JOIN, user_id indexed)
```

**Denormalization Maintenance Pattern**:
```sql
-- Trigger to keep denormalized user_id in sync
CREATE OR REPLACE FUNCTION sync_denormalized_user_id()
RETURNS TRIGGER AS $$
BEGIN
    -- When dispute_letter is created, copy user_id to dispute_tracking
    UPDATE dispute_tracking
    SET user_id = NEW.user_id
    WHERE dispute_letter_id = NEW.id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER after_dispute_letter_insert
AFTER INSERT ON dispute_letters
FOR EACH ROW EXECUTE FUNCTION sync_denormalized_user_id();
```

### 2.3 Trigger-Based Analytics Cache Pattern

**Pattern**: Materialized aggregations with trigger-based refresh

**Use Case**: `user_analytics` table for personal statistics dashboard

**Implementation**:

```sql
-- Function to recalculate user analytics
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
        ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'deleted') / NULLIF(COUNT(*), 0), 2) AS success_rate,
        AVG(EXTRACT(EPOCH FROM (sh_deleted.changed_at - sh_pending.changed_at)) / 86400) AS average_days_to_resolution,
        jsonb_build_object(
            'equifax', COUNT(*) FILTER (WHERE bureau = 'equifax'),
            'transunion', COUNT(*) FILTER (WHERE bureau = 'transunion'),
            'experian', COUNT(*) FILTER (WHERE bureau = 'experian')
        ) AS disputes_by_bureau,
        NOW() AS last_updated
    FROM dispute_tracking dt
    LEFT JOIN status_history sh_pending ON sh_pending.dispute_tracking_id = dt.id AND sh_pending.old_status IS NULL
    LEFT JOIN status_history sh_deleted ON sh_deleted.dispute_tracking_id = dt.id AND sh_deleted.new_status = 'deleted'
    WHERE dt.user_id = target_user_id
    GROUP BY target_user_id
    ON CONFLICT (user_id) DO UPDATE SET
        total_disputes_initiated = EXCLUDED.total_disputes_initiated,
        total_items_deleted = EXCLUDED.total_items_deleted,
        success_rate = EXCLUDED.success_rate,
        average_days_to_resolution = EXCLUDED.average_days_to_resolution,
        disputes_by_bureau = EXCLUDED.disputes_by_bureau,
        last_updated = EXCLUDED.last_updated;
END;
$$ LANGUAGE plpgsql;

-- Trigger to refresh analytics on status change
CREATE OR REPLACE FUNCTION trigger_analytics_refresh()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM refresh_user_analytics(NEW.user_id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER after_dispute_status_change
AFTER INSERT OR UPDATE ON dispute_tracking
FOR EACH ROW EXECUTE FUNCTION trigger_analytics_refresh();
```

**Performance Characteristics**:
- **Dashboard query**: `SELECT * FROM user_analytics WHERE user_id = $1` (5ms, single-row lookup)
- **Analytics refresh**: Triggered on status change, executes in background (100-200ms, non-blocking)
- **Consistency**: Eventually consistent (1-2 second delay acceptable for personal statistics)

**Alternative Rejected**: Real-time aggregation queries
- **Performance**: 500-1000ms to calculate success rate from `dispute_tracking` table
- **Scalability**: Query cost increases linearly with dispute count
- **User experience**: Dashboard load time >1 second unacceptable

### 2.4 Audit Trail Pattern with Immutable Records

**Pattern**: Separate audit table with insert-only policy

**Use Case**: `status_history` table for dispute timeline and compliance

**Implementation**:
```sql
-- Trigger to log status changes in audit trail
CREATE OR REPLACE FUNCTION log_status_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Insert into status_history whenever dispute_tracking.status changes
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO status_history (
            dispute_tracking_id,
            user_id,
            old_status,
            new_status,
            changed_at,
            changed_by,
            change_notes
        ) VALUES (
            NEW.id,
            NEW.user_id,
            OLD.status,
            NEW.status,
            NOW(),
            NEW.status_updated_by,
            'Status changed from ' || OLD.status || ' to ' || NEW.status
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER after_status_update
AFTER UPDATE ON dispute_tracking
FOR EACH ROW EXECUTE FUNCTION log_status_change();
```

**Immutability Enforcement**:
```sql
-- No UPDATE or DELETE policies on status_history
-- Only SELECT (view audit trail) and INSERT (via trigger)
CREATE POLICY "Users can view own status history"
ON status_history FOR SELECT
USING (auth.uid() = user_id);

-- No UPDATE policy = immutable records
```

**Audit Trail Benefits**:
1. **Compliance**: FCRA requires audit trail of all data modifications
2. **Dispute timeline**: Users can see complete history of status changes
3. **Analytics**: Calculate average time to resolution: `(status = 'deleted' timestamp) - (status = 'pending' timestamp)`
4. **Debugging**: Identify when/why status changes occurred (user manual update vs OCR system)

**Storage Efficiency**:
- **Record size**: ~100 bytes per status change
- **Estimate**: 15 disputes × 3 status changes × 1,000 users = 45K records × 100 bytes = 4.5MB (negligible)
- **Retention**: Keep indefinitely for compliance (no automatic deletion)

## 3. Database Partitioning & Indexing Strategy

### 3.1 Index Design Principles

**Indexing Strategy**:

1. **User-scoped composite indexes**: All queries filter by `user_id` first (RLS requirement)
   ```sql
   -- Composite index matches common query pattern
   CREATE INDEX idx_tradelines_user_negative ON tradelines (user_id, is_negative, is_disputable);
   ```

2. **Covering indexes**: Include frequently selected columns to avoid table lookups
   ```sql
   -- Covering index includes account_name to avoid heap fetch
   CREATE INDEX idx_tradelines_user_negative_covering ON tradelines (user_id, is_negative)
   INCLUDE (account_name, account_type, status);
   ```

3. **Partial indexes**: Filter index entries for status-specific queries
   ```sql
   -- Partial index only for negative tradelines (reduces index size by 80%)
   CREATE INDEX idx_tradelines_negative_only ON tradelines (user_id, is_negative)
   WHERE is_negative = TRUE;
   ```

4. **GIN indexes for JSONB**: Enable JSON querying on `payment_history` and `tradeline_details`
   ```sql
   -- GIN index for payment history JSON queries
   CREATE INDEX idx_tradelines_payment_history_gin ON tradelines USING GIN (payment_history);

   -- Example query using GIN index:
   -- Find all tradelines with 30-day late payment in payment history
   SELECT * FROM tradelines
   WHERE user_id = $1
   AND payment_history @> '[{"status": "30"}]';
   ```

**Index Maintenance**:
- **Auto-vacuum**: Enable auto-vacuum for all tables (default Supabase setting)
- **Reindex schedule**: Monthly `REINDEX` on high-churn tables (`dispute_tracking`, `status_history`)
- **Index bloat monitoring**: Track index size growth via `pg_stat_user_indexes`

### 3.2 Query Optimization Patterns

**Common Query Patterns**:

**Pattern 1: Dashboard multi-bureau dispute view**
```sql
-- Fetch all user's disputes with tradeline details and per-bureau status
EXPLAIN ANALYZE
SELECT
    t.account_name,
    t.account_type,
    t.balance,
    t.negative_type,
    dt_eq.status AS equifax_status,
    dt_tu.status AS transunion_status,
    dt_ex.status AS experian_status,
    dt_eq.tracking_number AS equifax_tracking,
    dt_tu.tracking_number AS transunion_tracking,
    dt_ex.tracking_number AS experian_tracking
FROM tradelines t
LEFT JOIN dispute_tracking dt_eq ON dt_eq.tradeline_id = t.id AND dt_eq.bureau = 'equifax'
LEFT JOIN dispute_tracking dt_tu ON dt_tu.tradeline_id = t.id AND dt_tu.bureau = 'transunion'
LEFT JOIN dispute_tracking dt_ex ON dt_ex.tradeline_id = t.id AND dt_ex.bureau = 'experian'
WHERE t.user_id = $1 AND t.is_negative = TRUE
ORDER BY t.created_at DESC;

-- Index usage:
-- 1. Index scan on idx_tradelines_user_negative (user_id, is_negative)
-- 2. Index scan on idx_dispute_tracking_tradeline_bureau (tradeline_id, bureau)
-- Expected query time: <150ms
```

**Pattern 2: Personal statistics aggregation** (cached in `user_analytics`)
```sql
-- This query runs in trigger, not on dashboard load
SELECT
    COUNT(*) AS total_disputes_initiated,
    COUNT(*) FILTER (WHERE status = 'deleted') AS total_items_deleted,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'deleted') / NULLIF(COUNT(*), 0), 2) AS success_rate
FROM dispute_tracking
WHERE user_id = $1;

-- Index usage: Index scan on idx_dispute_tracking_user (user_id)
-- Dashboard reads from: SELECT * FROM user_analytics WHERE user_id = $1 (5ms)
```

**Pattern 3: Dispute timeline audit trail**
```sql
-- Fetch complete status change history for a dispute
SELECT
    old_status,
    new_status,
    changed_at,
    changed_by,
    change_notes
FROM status_history
WHERE dispute_tracking_id = $1
ORDER BY changed_at ASC;

-- Index usage: Index scan on idx_status_history_dispute (dispute_tracking_id, changed_at)
-- Expected query time: <50ms
```

**Query Performance Targets**:
- **Dashboard load**: <200ms for all disputes + analytics
- **Status update**: <100ms to update status and refresh analytics
- **Audit trail**: <50ms to fetch complete status history
- **Search queries**: <300ms for complex multi-table searches

### 3.3 Connection Pooling Configuration

**Supabase Pooler (PgBouncer)**:

**Configuration**:
```python
# FastAPI SQLAlchemy engine with Supabase pooler
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# Supabase connection string with pooler
DATABASE_URL = "postgresql://user:password@db.supabase.co:6543/postgres"  # Port 6543 = pooler

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,  # Max connections per FastAPI instance
    max_overflow=10,  # Allow 10 additional connections during spikes
    pool_timeout=30,  # 30-second timeout waiting for connection
    pool_recycle=3600,  # Recycle connections every 1 hour
    pool_pre_ping=True  # Test connection health before use
)
```

**PgBouncer Settings**:
- **Pool mode**: Transaction (connection released after transaction completes)
- **Max client connections**: 100 (sufficient for 1,000+ concurrent users)
- **Default pool size**: 20 connections per database
- **Reserve pool**: 5 connections for admin tasks

**Connection Pool Monitoring**:
```sql
-- Monitor connection pool usage
SELECT
    datname,
    numbackends,
    xact_commit,
    xact_rollback,
    blks_read,
    blks_hit
FROM pg_stat_database
WHERE datname = 'postgres';

-- Monitor active queries
SELECT
    pid,
    usename,
    application_name,
    state,
    query,
    query_start
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY query_start;
```

**Scaling Connection Pool**:
- **Initial**: 20 connections per FastAPI instance (1 instance = 20 connections)
- **Horizontal scaling**: 5 FastAPI instances = 100 total connections (within Supabase limit)
- **Supabase Pro tier**: 500 max connections (supports 25 FastAPI instances)

## 4. Backup & Disaster Recovery Strategy

### 4.1 Automated Backup Schedule

**Supabase Managed Backups**:
- **Daily backups**: Full database backup at 2:00 AM UTC (retained 7 days)
- **Weekly backups**: Full database backup every Sunday (retained 4 weeks)
- **Point-in-time recovery (PITR)**: WAL archiving for recovery to any point in last 7 days (Pro tier)

**Backup Verification**:
```bash
# Monthly backup restore test (verify integrity)
pg_restore --dbname=credit_clarity_test --verbose backup_file.dump
```

### 4.2 Disaster Recovery Plan

**Recovery Time Objective (RTO)**: <4 hours (time to restore service)
**Recovery Point Objective (RPO)**: <24 hours (acceptable data loss window)

**Disaster Scenarios**:

1. **Database corruption**: Restore from most recent daily backup (2-4 hour RTO)
2. **Accidental data deletion**: Use PITR to restore to 5 minutes before deletion (1 hour RTO)
3. **Supabase region outage**: Migrate to Supabase failover region (manual intervention, 8-12 hour RTO)

**Manual Backup Export** (monthly offsite backup):
```bash
# Export database to offsite storage (AWS S3)
pg_dump -h db.supabase.co -U postgres -d credit_clarity | gzip > backup_$(date +%Y%m%d).sql.gz
aws s3 cp backup_$(date +%Y%m%d).sql.gz s3://credit-clarity-backups/
```

## Summary of Database Architecture Decisions

1. **PostgreSQL via Supabase**: Managed service with RLS for multi-tenancy and FCRA compliance
2. **TimescaleDB integration from start**: Avoid future migration complexity for Phase 3 time-series data
3. **Pinecone vector database (Phase 3)**: Managed service for RAG chatbot knowledge base
4. **Redis caching layer**: Hybrid rate limiting with middleware + Redis backup
5. **RLS-enforced multi-tenancy**: Database-level data isolation eliminates application-layer filtering
6. **Selective denormalization**: Duplicate `user_id` in child tables for query performance
7. **Trigger-based analytics cache**: `user_analytics` table with automatic refresh on status changes
8. **Immutable audit trail**: `status_history` table with insert-only policy for compliance
9. **Composite indexing strategy**: User-scoped indexes matching RLS query patterns
10. **Connection pooling**: PgBouncer transaction mode with 20 connections per FastAPI instance

**Next Steps**:
- **@analysis-data-integration-pipelines.md**: Data flow design for AI pipeline, mailing service, and analytics
- **@analysis-security-compliance-governance.md**: FCRA compliance and data protection framework
