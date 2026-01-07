# Data Infrastructure Architecture

**Parent Document**: @analysis.md
**Framework Reference**: @../guidance-specification.md (Sections 4-5: System/Data Architect Decisions)

---

## Overview

This section details the data infrastructure architecture including database schemas, caching strategies, TimescaleDB integration, and data flow patterns across all phases.

---

## Current Database Architecture

### Supabase PostgreSQL Foundation

**Current Setup** (from existing codebase):
- **Database**: PostgreSQL 15 via Supabase managed service
- **Authentication**: Supabase Auth with JWT tokens
- **Row-Level Security**: Supabase RLS policies for multi-tenancy
- **Storage**: Supabase Storage for PDF uploads
- **Real-Time**: Supabase Realtime for live dashboard updates (optional)

**Benefits**:
- ✅ Managed infrastructure (automatic backups, scaling, security)
- ✅ Built-in authentication and authorization
- ✅ PostgreSQL compatibility (standard SQL, JSON support, extensions)
- ✅ Real-time subscriptions for live UI updates

---

## Phase 1: Core Data Models

### Tradelines Table

```sql
-- Credit report tradelines
CREATE TABLE tradelines (
    tradeline_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    report_upload_id UUID REFERENCES report_uploads(id) ON DELETE CASCADE,

    -- Account identification
    creditor_name VARCHAR(255) NOT NULL,
    account_number VARCHAR(50),  -- Last 4 digits only
    account_type VARCHAR(50),    -- credit_card, mortgage, auto_loan, etc.

    -- Account status
    account_status VARCHAR(100),  -- open, closed, charge-off, collection, etc.
    is_negative BOOLEAN DEFAULT FALSE,
    negative_confidence DECIMAL(3,2),  -- 0.00-1.00
    negative_factors JSONB,  -- Classification details

    -- Financial details
    balance DECIMAL(12,2),
    credit_limit DECIMAL(12,2),
    original_amount DECIMAL(12,2),
    monthly_payment DECIMAL(12,2),

    -- Dates
    date_opened DATE,
    date_closed DATE,
    date_last_activity DATE,

    -- Payment history
    payment_history TEXT,  -- 30/60/90/120 day late counts
    late_payments_30 INTEGER DEFAULT 0,
    late_payments_60 INTEGER DEFAULT 0,
    late_payments_90 INTEGER DEFAULT 0,
    late_payments_120 INTEGER DEFAULT 0,

    -- Bureau source
    bureau VARCHAR(20) CHECK (bureau IN ('Equifax', 'TransUnion', 'Experian', 'All')),

    -- Comments/remarks
    comments TEXT,
    remarks TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes
    INDEX idx_tradelines_user_id (user_id),
    INDEX idx_tradelines_negative (user_id, is_negative),
    INDEX idx_tradelines_bureau (user_id, bureau)
);

-- Enable Row-Level Security
ALTER TABLE tradelines ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only access their own tradelines
CREATE POLICY tradelines_user_policy ON tradelines
    FOR ALL
    USING (auth.uid() = user_id);
```

### Report Uploads Table

```sql
-- Credit report upload tracking
CREATE TABLE report_uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- File details
    original_filename VARCHAR(255),
    file_size_bytes BIGINT,
    file_hash VARCHAR(64),  -- SHA-256 hash for deduplication
    storage_path VARCHAR(500),  -- Supabase Storage path

    -- Processing status
    processing_status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, complete, failed
    progress_percentage INTEGER DEFAULT 0,
    progress_message TEXT,
    error_message TEXT,

    -- Results
    total_tradelines INTEGER,
    negative_tradelines INTEGER,
    processing_time_seconds DECIMAL(8,2),

    -- Metadata
    uploaded_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,

    -- Indexes
    INDEX idx_uploads_user_id (user_id),
    INDEX idx_uploads_status (user_id, processing_status),

    -- Deduplication constraint
    UNIQUE (user_id, file_hash)
);

-- Enable RLS
ALTER TABLE report_uploads ENABLE ROW LEVEL SECURITY;

CREATE POLICY uploads_user_policy ON report_uploads
    FOR ALL
    USING (auth.uid() = user_id);
```

### Disputes Table (Multi-Bureau Tracking)

```sql
-- Dispute tracking across 3 bureaus
CREATE TABLE disputes (
    dispute_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    tradeline_id UUID NOT NULL REFERENCES tradelines(tradeline_id) ON DELETE CASCADE,

    -- Bureau-specific dispute
    bureau VARCHAR(20) NOT NULL CHECK (bureau IN ('Equifax', 'TransUnion', 'Experian')),

    -- Dispute letter
    letter_content TEXT NOT NULL,
    letter_generated_at TIMESTAMP DEFAULT NOW(),
    dispute_reason TEXT,

    -- Mailing details
    mailing_service VARCHAR(50),  -- Lob, USPS, Manual
    mailing_date TIMESTAMP,
    tracking_number VARCHAR(100),
    payment_id VARCHAR(100),
    payment_amount_cents INTEGER,

    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'Draft' CHECK (
        status IN ('Draft', 'Pending', 'Investigating', 'Verified', 'Deleted', 'Updated', 'Escalated', 'Expired', 'Blank')
    ),
    status_updated_at TIMESTAMP DEFAULT NOW(),
    status_updated_by VARCHAR(50),  -- 'user' or 'system'

    -- Bureau response
    bureau_response_date DATE,
    bureau_response_summary TEXT,
    bureau_response_document_path VARCHAR(500),  -- Uploaded response PDF

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes
    INDEX idx_disputes_user_id (user_id),
    INDEX idx_disputes_status (user_id, status),
    INDEX idx_disputes_bureau (user_id, bureau),
    INDEX idx_disputes_tradeline (tradeline_id),

    -- Unique constraint: One dispute per tradeline per bureau
    UNIQUE (tradeline_id, bureau)
);

-- Enable RLS
ALTER TABLE disputes ENABLE ROW LEVEL SECURITY;

CREATE POLICY disputes_user_policy ON disputes
    FOR ALL
    USING (auth.uid() = user_id);
```

### Dispute Status History (Audit Trail)

```sql
-- Audit trail for status changes
CREATE TABLE dispute_status_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dispute_id UUID NOT NULL REFERENCES disputes(dispute_id) ON DELETE CASCADE,

    -- Status change details
    previous_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    changed_by VARCHAR(50) NOT NULL,  -- 'user' or 'system'
    change_reason TEXT,
    change_notes TEXT,

    -- Timestamp
    changed_at TIMESTAMP DEFAULT NOW(),

    -- Index
    INDEX idx_history_dispute (dispute_id, changed_at)
);

-- Enable RLS
ALTER TABLE dispute_status_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY history_user_policy ON dispute_status_history
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM disputes
            WHERE disputes.dispute_id = dispute_status_history.dispute_id
            AND disputes.user_id = auth.uid()
        )
    );
```

### User Dispute Statistics (Materialized View)

```sql
-- Pre-computed user statistics for dashboard
CREATE MATERIALIZED VIEW user_dispute_stats AS
SELECT
    user_id,
    COUNT(*) as total_disputes,
    COUNT(*) FILTER (WHERE status = 'Deleted') as successful_deletions,
    COUNT(*) FILTER (WHERE status IN ('Pending', 'Investigating')) as in_progress,
    COUNT(*) FILTER (WHERE status = 'Verified') as unsuccessful,
    ROUND(
        COUNT(*) FILTER (WHERE status = 'Deleted')::NUMERIC / NULLIF(COUNT(*), 0) * 100,
        2
    ) as success_rate_percentage,
    AVG(
        EXTRACT(EPOCH FROM (status_updated_at - created_at)) / 86400
    ) FILTER (WHERE status IN ('Deleted', 'Verified')) as avg_days_to_resolution,

    -- Bureau-specific stats
    COUNT(*) FILTER (WHERE bureau = 'Equifax' AND status = 'Deleted') as equifax_deletions,
    COUNT(*) FILTER (WHERE bureau = 'TransUnion' AND status = 'Deleted') as transunion_deletions,
    COUNT(*) FILTER (WHERE bureau = 'Experian' AND status = 'Deleted') as experian_deletions,

    -- Last updated
    MAX(updated_at) as last_update
FROM disputes
GROUP BY user_id;

-- Create unique index for concurrent refresh
CREATE UNIQUE INDEX idx_user_stats_user_id ON user_dispute_stats(user_id);
```

**Materialized View Refresh Strategy**:
```sql
-- Trigger to refresh stats on dispute updates
CREATE OR REPLACE FUNCTION refresh_user_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Refresh materialized view concurrently (non-blocking)
    REFRESH MATERIALIZED VIEW CONCURRENTLY user_dispute_stats;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_refresh_user_stats
AFTER INSERT OR UPDATE ON disputes
FOR EACH STATEMENT
EXECUTE FUNCTION refresh_user_stats();
```

---

## Multi-Bureau Dispute Visualization Query

**Side-by-Side Bureau Comparison**:
```sql
-- Get same tradeline status across all 3 bureaus
SELECT
    t.tradeline_id,
    t.creditor_name,
    t.account_number,
    t.account_type,
    t.balance,

    -- Bureau-specific status
    COALESCE(eq.status, 'Blank') as equifax_status,
    COALESCE(eq.tracking_number, '') as equifax_tracking,
    COALESCE(eq.status_updated_at, NULL) as equifax_last_update,

    COALESCE(tu.status, 'Blank') as transunion_status,
    COALESCE(tu.tracking_number, '') as transunion_tracking,
    COALESCE(tu.status_updated_at, NULL) as transunion_last_update,

    COALESCE(ex.status, 'Blank') as experian_status,
    COALESCE(ex.tracking_number, '') as experian_tracking,
    COALESCE(ex.status_updated_at, NULL) as experian_last_update

FROM tradelines t
LEFT JOIN disputes eq ON t.tradeline_id = eq.tradeline_id AND eq.bureau = 'Equifax'
LEFT JOIN disputes tu ON t.tradeline_id = tu.tradeline_id AND tu.bureau = 'TransUnion'
LEFT JOIN disputes ex ON t.tradeline_id = ex.tradeline_id AND ex.bureau = 'Experian'

WHERE t.user_id = :user_id
  AND t.is_negative = TRUE

ORDER BY t.created_at DESC;
```

**Example Result**:
| creditor_name | account_number | equifax_status | transunion_status | experian_status |
|---------------|----------------|----------------|-------------------|-----------------|
| Capital One | ***1234 | Deleted | Investigating | Blank |
| Midland Funding | ***5678 | Verified | Pending | Deleted |
| Wells Fargo | ***9012 | Pending | Deleted | Deleted |

---

## Caching Strategy

### Multi-Level Caching Architecture

**Existing Implementation** (from `backend/services/cache_service.py`):

```
┌─────────────┐     Cache Miss     ┌──────────────┐     Cache Miss     ┌──────────────┐
│  In-Memory  │───────────────────▶│  Redis Cache │───────────────────▶│  PostgreSQL  │
│  LRU Cache  │◀───────────────────│  (Persistent)│◀───────────────────│  (Database)  │
│  (1000 max) │     Cache Hit      │  (1GB max)   │     Query Result   │              │
└─────────────┘                    └──────────────┘                    └──────────────┘
   ~1ms latency                       ~5ms latency                       ~50-100ms
```

**Layer 1: In-Memory LRU Cache**:
```python
# Existing: backend/services/cache_service.py
class InMemoryCache:
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, Any] = {}
        self._access_times: Dict[str, datetime] = {}
        self._expiry_times: Dict[str, datetime] = {}

    def get(self, key: str) -> Optional[Any]:
        self._cleanup_expired()
        if key in self._cache:
            self._access_times[key] = datetime.now()
            return self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        self._cleanup_expired()
        self._evict_lru()  # Evict if at capacity
        # ... store value
```

**Layer 2: Redis Persistent Cache**:
```python
# Redis cache with automatic failover to in-memory
class CacheService:
    def __init__(self):
        self.redis = redis.from_url(settings.redis_url) if settings.redis_url else None
        self.memory_cache = InMemoryCache()

    async def get(self, key: str) -> Optional[Any]:
        # Try in-memory first
        value = self.memory_cache.get(key)
        if value is not None:
            return value

        # Try Redis
        if self.redis:
            value = await self.redis.get(key)
            if value:
                # Promote to in-memory cache
                self.memory_cache.set(key, pickle.loads(value))
                return pickle.loads(value)

        return None

    async def set(self, key: str, value: Any, ttl: int = 3600):
        # Write to both layers
        self.memory_cache.set(key, value, ttl)
        if self.redis:
            await self.redis.setex(key, ttl, pickle.dumps(value))
```

**Cache Keys Strategy**:
```python
# Cache key patterns
CACHE_KEYS = {
    "user_stats": "user_stats:{user_id}",
    "tradelines": "tradelines:{user_id}:{report_id}",
    "disputes": "disputes:{user_id}",
    "bureau_comparison": "bureau_comparison:{user_id}:{tradeline_id}",
    "ocr_result": "ocr:{file_hash}",
    "rate_limit": "rate_limit:{user_id}:{action}",
}

# Example usage
cache_key = CACHE_KEYS["user_stats"].format(user_id=user_id)
stats = await cache_service.get(cache_key)

if stats is None:
    # Cache miss - query database
    stats = await get_user_stats_from_db(user_id)
    await cache_service.set(cache_key, stats, ttl=300)  # 5 minutes
```

**Cache Invalidation Strategy**:
```python
# Invalidate cache on data updates
async def update_dispute_status(dispute_id: str, new_status: str):
    # Update database
    await execute_sql("""
        UPDATE disputes
        SET status = :status, status_updated_at = NOW()
        WHERE dispute_id = :dispute_id
    """, {"status": new_status, "dispute_id": dispute_id})

    # Invalidate affected caches
    user_id = await get_user_id_from_dispute(dispute_id)
    await cache_service.delete(f"user_stats:{user_id}")
    await cache_service.delete(f"disputes:{user_id}")
    await cache_service.delete_pattern(f"bureau_comparison:{user_id}:*")

    # Trigger materialized view refresh
    await refresh_user_stats_async()
```

---

## Phase 3: TimescaleDB Integration

### Time-Series Database for Historical Score Tracking

**Architecture Decision** (from guidance-specification.md):
- ✅ Implement from start for scalable foundation
- ✅ PostgreSQL extension (familiar tooling, compatible with Supabase)
- ✅ Easier to build right than migrate later

**Deployment Strategy**:

**Option 1: Separate TimescaleDB Instance + Dual-Write Pattern**
```
┌────────────────┐     Write      ┌────────────────────┐
│   FastAPI App  │───────────────▶│  Supabase (Main)   │
│                │                │  - Users           │
│                │                │  - Tradelines      │
│                │                │  - Disputes        │
└────────────────┘                └────────────────────┘
        │
        │ Dual-Write
        ▼
┌────────────────────┐
│  TimescaleDB       │
│  (Time-Series)     │
│  - Credit Scores   │
│  - Metrics         │
└────────────────────┘
```

**Rationale**: Preserves Supabase managed service benefits while adding specialized time-series capabilities

**Implementation**:
```python
# backend/services/score_tracking_service.py
import asyncpg
from datetime import datetime, timedelta

class ScoreTrackingService:
    def __init__(self):
        self.supabase = get_supabase_client()
        self.timescale_pool = None

    async def init_timescale_pool(self):
        """Initialize TimescaleDB connection pool."""
        self.timescale_pool = await asyncpg.create_pool(
            host=settings.timescale_host,
            port=settings.timescale_port,
            database=settings.timescale_database,
            user=settings.timescale_user,
            password=settings.timescale_password
        )

    async def record_score(
        self,
        user_id: str,
        score_value: int,
        bureau: str,
        score_type: str = "FICO"
    ):
        """Dual-write: Save to Supabase + TimescaleDB."""

        # Write to Supabase (main database)
        await self.supabase.table("credit_scores").insert({
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "score_value": score_value,
            "bureau": bureau,
            "score_type": score_type
        }).execute()

        # Write to TimescaleDB (time-series)
        async with self.timescale_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO credit_scores (user_id, timestamp, score_value, bureau, score_type)
                VALUES ($1, $2, $3, $4, $5)
            """, user_id, datetime.utcnow(), score_value, bureau, score_type)

    async def get_score_history(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
        bureau: str = None
    ) -> List[Dict[str, Any]]:
        """Query time-series score history from TimescaleDB."""

        async with self.timescale_pool.acquire() as conn:
            query = """
                SELECT
                    time_bucket('1 day', timestamp) AS day,
                    bureau,
                    AVG(score_value) AS avg_score,
                    MIN(score_value) AS min_score,
                    MAX(score_value) AS max_score
                FROM credit_scores
                WHERE user_id = $1
                  AND timestamp BETWEEN $2 AND $3
            """

            params = [user_id, start_date, end_date]

            if bureau:
                query += " AND bureau = $4"
                params.append(bureau)

            query += """
                GROUP BY day, bureau
                ORDER BY day ASC
            """

            rows = await conn.fetch(query, *params)

            return [dict(row) for row in rows]
```

**TimescaleDB Schema**:
```sql
-- TimescaleDB database
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

-- Create index for user queries
CREATE INDEX idx_scores_user_bureau ON credit_scores (user_id, bureau, timestamp DESC);

-- Retention policy: Keep 7 years of data (FCRA compliance)
SELECT add_retention_policy('credit_scores', INTERVAL '7 years');

-- Continuous aggregate for monthly averages
CREATE MATERIALIZED VIEW credit_scores_monthly
WITH (timescaledb.continuous) AS
SELECT
    user_id,
    bureau,
    time_bucket('1 month', timestamp) AS month,
    AVG(score_value) AS avg_score,
    MIN(score_value) AS min_score,
    MAX(score_value) AS max_score,
    COUNT(*) AS sample_count
FROM credit_scores
GROUP BY user_id, bureau, month;
```

**Configuration**:
```python
# core/config.py additions
class Settings(BaseSettings):
    # TimescaleDB settings
    timescale_host: str = Field(default="localhost", env="TIMESCALE_HOST")
    timescale_port: int = Field(default=5432, env="TIMESCALE_PORT")
    timescale_database: str = Field(default="timescale_db", env="TIMESCALE_DATABASE")
    timescale_user: str = Field(default="timescale_user", env="TIMESCALE_USER")
    timescale_password: str = Field(default=None, env="TIMESCALE_PASSWORD")
```

---

## Data Flow Patterns

### Credit Report Processing Flow

```
User Upload PDF
      │
      ▼
┌─────────────────────────────────────┐
│ 1. Save to Supabase Storage         │
│    - Generate unique path           │
│    - Calculate file hash            │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│ 2. Create report_uploads record     │
│    - status: 'pending'              │
│    - progress: 0%                   │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│ 3. Queue background job              │
│    - job_id linked to upload_id     │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│ 4. OCR + Parsing (background)       │
│    - Document AI OCR (30%)          │
│    - Gemini parsing (60%)           │
│    - Negative classification (90%)  │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│ 5. Save tradelines to database      │
│    - Insert into tradelines table   │
│    - Link to report_upload_id       │
│    - Mark is_negative flags         │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│ 6. Update upload record              │
│    - status: 'complete'             │
│    - progress: 100%                 │
│    - total_tradelines count         │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│ 7. Notify user                       │
│    - "Found 8 negative items"       │
└─────────────────────────────────────┘
```

### Dispute Letter Mailing Flow

```
User Clicks "Send Letter"
      │
      ▼
┌─────────────────────────────────────┐
│ 1. Create Stripe Checkout session   │
│    - amount: $5-10                  │
│    - metadata: user_id, letter_id   │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│ 2. User completes payment            │
│    - Stripe webhook: session.completed │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│ 3. Trigger mailing service           │
│    - Lob.com API call               │
│    - certified mail + tracking      │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│ 4. Create dispute record             │
│    - status: 'Pending'              │
│    - tracking_number from Lob       │
│    - payment_id from Stripe         │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│ 5. Log status history                │
│    - previous: NULL                 │
│    - new: 'Pending'                 │
│    - changed_by: 'system'           │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│ 6. Notify user                       │
│    - "Letter sent! Tracking: ..."   │
│    - Email + in-app notification    │
└─────────────────────────────────────┘
```

---

## Conclusion

The data infrastructure leverages Supabase's managed PostgreSQL for core application data with RLS-based multi-tenancy, multi-level caching for performance, and TimescaleDB integration for time-series score tracking. The architecture balances simplicity (managed services) with scalability (specialized databases for time-series workloads).

**Key Strengths**:
- ✅ Supabase RLS provides automatic multi-tenancy security
- ✅ Multi-level caching (in-memory + Redis) optimizes performance
- ✅ Materialized views pre-compute expensive statistics
- ✅ TimescaleDB enables efficient historical analytics

**Phase 1 Deliverables**:
- PostgreSQL schemas for tradelines, disputes, status history
- Multi-bureau dispute tracking with unique constraints
- Materialized view for user statistics
- Cache invalidation on data updates
