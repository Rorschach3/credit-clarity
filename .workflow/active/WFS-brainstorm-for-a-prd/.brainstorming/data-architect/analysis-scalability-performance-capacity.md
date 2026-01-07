# Scalability, Performance & Capacity Planning

**Parent Document**: @analysis.md
**Reference**: @../guidance-specification.md Section 7 (Risks & Constraints - Scalability)

## 1. Scalability Strategy Overview

### 1.1 Growth Projections from Business Model

**User Growth Timeline** (from guidance-specification.md Section 3):
- **Month 1-6 (MVP)**: 100+ active users
- **Month 7-12 (Optimization)**: 1,000+ users
- **Month 13-18 (AI Enhancement)**: 5,000+ users (estimated)
- **Month 19-24 (Scale & Monetization)**: 10,000+ users (target)

**Data Volume Projections**:

| Metric | Month 6 | Month 12 | Month 18 | Month 24 |
|--------|---------|----------|----------|----------|
| **Active Users** | 100 | 1,000 | 5,000 | 10,000 |
| **Credit Report Uploads** | 200/month | 2,000/month | 10,000/month | 20,000/month |
| **Tradelines** | 3,000 | 30,000 | 150,000 | 300,000 |
| **Dispute Letters** | 300 | 3,000 | 15,000 | 30,000 |
| **Mailed Letters** (15% conversion) | 45 | 450 | 2,250 | 4,500 |
| **PostgreSQL Database Size** | 500MB | 5GB | 25GB | 50GB |
| **TimescaleDB Score History** | N/A (Phase 3) | N/A | 5GB | 10GB |
| **Object Storage (PDFs)** | 1GB | 10GB | 50GB | 100GB |

**Traffic Projections**:

| Metric | Month 6 | Month 12 | Month 18 | Month 24 |
|--------|---------|----------|----------|----------|
| **Daily Active Users** | 30 | 300 | 1,500 | 3,000 |
| **Peak Concurrent Users** | 5 | 50 | 250 | 500 |
| **API Requests/Day** | 1,000 | 10,000 | 50,000 | 100,000 |
| **Peak Requests/Second** | 1 | 10 | 50 | 100 |
| **Dashboard Queries/Day** | 500 | 5,000 | 25,000 | 50,000 |

### 1.2 Scalability Architecture Principles

1. **Stateless backend design**: FastAPI application is stateless (existing architecture)
   - No server-side session storage
   - All state stored in PostgreSQL or Redis
   - Horizontal scaling: Add more FastAPI instances without state synchronization

2. **Database-centric architecture**: PostgreSQL as single source of truth
   - Supabase RLS enforces data access controls at database level
   - Eliminates application-layer caching complexity
   - Database scales vertically (CPU/memory upgrades) and horizontally (read replicas)

3. **Multi-level caching**: Redis for performance-critical queries
   - Rate limiting counters (middleware + Redis backup)
   - User analytics cache (`user_analytics` table)
   - Session tokens (Supabase Auth)

4. **Asynchronous processing**: Celery background jobs for long-running operations
   - PDF OCR processing (30-60 seconds)
   - Gemini AI tradeline parsing (10-30 seconds)
   - Analytics recalculation (100-200ms)

5. **CDN for static assets**: Frontend static files served via CDN
   - Reduces origin server load
   - Improves global latency (edge caching)

## 2. Database Performance Optimization

### 2.1 Query Performance Targets

**Performance SLAs**:

| Query Type | Target Latency | Current Latency | Optimization Strategy |
|------------|---------------|-----------------|----------------------|
| Dashboard load (all disputes + analytics) | <200ms | 120ms (Month 6) | Composite indexes, denormalized user_id, cached analytics |
| Status update + analytics refresh | <100ms | 80ms (Month 6) | Trigger-based analytics, background execution |
| Audit trail timeline | <50ms | 30ms (Month 6) | Index on dispute_tracking_id + changed_at |
| Multi-bureau dispute view | <150ms | 100ms (Month 6) | Composite index on user_id + tradeline_id + bureau |
| Credit report upload (background) | <60s | 45s (Month 6) | Parallel OCR + parsing, Gemini API optimization |
| Search queries | <300ms | N/A (not implemented) | Full-text search indexes (GIN on JSONB) |

**Query Optimization Checklist**:
- ✅ Composite indexes matching WHERE clause order (`user_id, is_negative, is_disputable`)
- ✅ Denormalized `user_id` in child tables (avoids JOINs for RLS filtering)
- ✅ Partial indexes for filtered queries (`WHERE is_negative = TRUE`)
- ✅ GIN indexes for JSONB querying (`payment_history`, `tradeline_details`)
- ✅ Covering indexes with INCLUDE clause (avoid heap lookups)
- ✅ Trigger-based analytics cache (`user_analytics` table)
- ⚠️ Query plan analysis (use `EXPLAIN ANALYZE` for slow queries)

### 2.2 Index Strategy at Scale

**Index Monitoring** (as database grows from 500MB to 50GB):

```sql
-- Monitor index usage and size
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan AS index_scans,
    idx_tup_read AS tuples_read,
    idx_tup_fetch AS tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Identify unused indexes (consider dropping if idx_scan = 0 after 1 month)
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;
```

**Index Bloat Monitoring**:

```sql
-- Detect index bloat (unused space in indexes)
SELECT
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
    idx_scan,
    CASE
        WHEN idx_scan = 0 THEN 'Unused'
        WHEN idx_scan < 100 THEN 'Low usage'
        ELSE 'Active'
    END AS usage_status
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;
```

**Index Maintenance Schedule**:
- **Weekly**: Analyze table statistics (`ANALYZE`) for query planner optimization
- **Monthly**: Reindex high-churn tables (`REINDEX TABLE dispute_tracking`)
- **Quarterly**: Review unused indexes (drop if no usage after 3 months)
- **Annually**: Full database vacuum (`VACUUM FULL`) during maintenance window

### 2.3 Connection Pooling Scaling Strategy

**Current Configuration** (Month 6, 100 users):
- **PgBouncer pool size**: 20 connections per database
- **FastAPI instances**: 1 instance
- **Total connections**: 20 (sufficient for 100 concurrent users)

**Scaling Plan**:

| Phase | Users | FastAPI Instances | Connections per Instance | Total Connections | Supabase Tier |
|-------|-------|-------------------|-------------------------|-------------------|---------------|
| **Month 6** | 100 | 1 | 20 | 20 | Free tier (60 connections) |
| **Month 12** | 1,000 | 3 | 20 | 60 | Pro tier (500 connections) |
| **Month 18** | 5,000 | 10 | 20 | 200 | Pro tier (500 connections) |
| **Month 24** | 10,000 | 20 | 20 | 400 | Pro tier (500 connections) |

**Horizontal Scaling Trigger Points**:
- **CPU utilization >70%**: Add 1 FastAPI instance (auto-scaling via cloud provider)
- **Database connections >80% utilized**: Increase PgBouncer pool size or add FastAPI instances
- **API response time >500ms**: Investigate slow queries, add read replicas if needed

**Read Replica Strategy** (Month 18+):
- **Primary database**: Write operations (INSERT, UPDATE, DELETE)
- **Read replica**: Read operations (SELECT) for dashboard queries
- **Query routing**: Application-layer routing or PgBouncer routing
- **Replication lag**: Monitor lag <1 second (acceptable for dashboard queries)

**Read Replica Configuration**:
```python
# SQLAlchemy engine with read replica routing
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Primary database (write operations)
primary_engine = create_engine(SUPABASE_PRIMARY_URL, pool_size=20)

# Read replica (read operations)
replica_engine = create_engine(SUPABASE_REPLICA_URL, pool_size=20)

# Route queries based on operation type
def get_db_session(read_only=False):
    if read_only:
        return sessionmaker(bind=replica_engine)()
    else:
        return sessionmaker(bind=primary_engine)()

# Example: Dashboard query uses read replica
@app.get("/api/v1/tradelines")
async def get_tradelines(user_id: str):
    session = get_db_session(read_only=True)  # Use read replica
    tradelines = session.query(Tradeline).filter_by(user_id=user_id).all()
    return tradelines
```

### 2.4 TimescaleDB Performance at Scale

**Hypertable Chunk Management** (Phase 3 - Month 13+):

**Chunk Size Strategy**:
- **Initial chunk interval**: 1 month (partition by `timestamp` monthly)
- **Chunk size estimate**: 1,000 users × 3 bureaus × 4 score snapshots/year = 12,000 records/month = ~1MB/chunk
- **Total chunks after 1 year**: 12 chunks × 1MB = 12MB (negligible overhead)

**Chunk Pruning Performance**:
```sql
-- Query performance with chunk pruning
EXPLAIN ANALYZE
SELECT * FROM credit_score_history
WHERE user_id = $1
AND timestamp > NOW() - INTERVAL '6 months';

-- Expected query plan:
-- Index Scan using idx_credit_score_user_bureau (cost=0.29..8.31 rows=1)
--   Index Cond: (user_id = $1)
--   Filter: (timestamp > (now() - '6 months'::interval))
-- Planning Time: 0.123 ms
-- Execution Time: 1.456 ms
-- (Chunk pruning eliminates older chunks automatically)
```

**Compression Policy Performance**:
```sql
-- Enable compression for chunks older than 6 months
ALTER TABLE credit_score_history SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'user_id, bureau_source'
);

SELECT add_compression_policy('credit_score_history', INTERVAL '6 months');

-- Compression ratio: 70-90% reduction
-- Before compression: 1MB chunk → After compression: 100-300KB chunk
```

**Continuous Aggregates for Downsampling** (Month 18+):
```sql
-- Create continuous aggregate for monthly score averages
CREATE MATERIALIZED VIEW credit_score_monthly
WITH (timescaledb.continuous) AS
SELECT
    user_id,
    bureau_source,
    time_bucket('1 month', timestamp) AS month,
    AVG(score_value) AS avg_score,
    MIN(score_value) AS min_score,
    MAX(score_value) AS max_score
FROM credit_score_history
GROUP BY user_id, bureau_source, month;

-- Query monthly trends (instant read from materialized view)
SELECT * FROM credit_score_monthly
WHERE user_id = $1
AND month > NOW() - INTERVAL '1 year';
-- Query time: <10ms (pre-aggregated)
```

## 3. Rate Limiting Scalability

### 3.1 Hybrid Rate Limiting Architecture (Confirmed in guidance-specification.md)

**Current Architecture** (Month 6):
- **Primary**: FastAPI middleware with in-memory counters (<1ms latency)
- **Backup**: Redis sync every 5 minutes (5ms latency)
- **Recovery**: Load counters from Redis on server restart

**Scalability Challenge**: In-memory counters don't share state across multiple FastAPI instances

**Distributed Rate Limiting Strategy** (Month 12+, multi-instance deployment):

**Option 1: Redis-Only Rate Limiting** (recommended for multi-instance)
```python
import redis
from fastapi import HTTPException

# Redis client
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Rate limiting check (uses Redis INCR atomic operation)
def check_rate_limit(user_id: str, limit_type: str, max_count: int):
    """
    Check rate limit using Redis atomic operations.

    limit_type: 'reports' or 'letters'
    max_count: 2 (reports) or 3 (letters)
    """
    # Redis key: user:rate_limits:{user_id}:{limit_type}:{month}
    month_key = f"user:rate_limits:{user_id}:{limit_type}:{datetime.now().strftime('%Y-%m')}"

    # Atomic increment
    current_count = redis_client.incr(month_key)

    # Set expiry on first increment (30 days)
    if current_count == 1:
        redis_client.expire(month_key, 2592000)  # 30 days in seconds

    # Check limit
    if current_count > max_count:
        raise HTTPException(status_code=429, detail=f"Rate limit exceeded for {limit_type}")

    return current_count

# Example usage
@app.post("/api/v1/upload-credit-report")
async def upload_credit_report(file: UploadFile, user_id: str):
    # Check rate limit (2 reports per month for free users)
    check_rate_limit(user_id, "reports", max_count=2)

    # Proceed with upload
    # ...
```

**Option 2: Distributed Cache (Redis Cluster)** (Month 18+, >5,000 users)
- **Redis Cluster**: Horizontally scale Redis across multiple nodes
- **Consistent hashing**: Rate limit keys distributed across cluster nodes
- **High availability**: Redis Sentinel for automatic failover

**Performance Comparison**:

| Implementation | Latency | Scalability | Consistency | Recovery |
|---------------|---------|-------------|-------------|----------|
| **In-memory (single instance)** | <1ms | Single instance only | Guaranteed | Lost on restart (Redis backup) |
| **Redis-only (multi-instance)** | 5ms | Horizontal (multiple FastAPI instances) | Guaranteed (atomic INCR) | Persistent (Redis RDB) |
| **Redis Cluster (10K+ users)** | 5-10ms | Horizontal (distributed cache) | Eventually consistent | Persistent + replicated |

**Recommendation**:
- **Month 6-12**: Hybrid middleware + Redis (single FastAPI instance)
- **Month 12-18**: Redis-only rate limiting (multiple FastAPI instances)
- **Month 18+**: Redis Cluster (distributed cache for 10K+ users)

### 3.2 Rate Limit Monitoring & Alerting

**Metrics to Track**:
```python
from prometheus_client import Counter, Gauge

# Rate limit metrics
rate_limit_checks = Counter('rate_limit_checks_total', 'Total rate limit checks', ['user_tier', 'limit_type'])
rate_limit_exceeded = Counter('rate_limit_exceeded_total', 'Rate limit exceeded count', ['user_tier', 'limit_type'])
rate_limit_usage = Gauge('rate_limit_current_usage', 'Current rate limit usage', ['user_id', 'limit_type'])

# Instrument rate limit check
@app.post("/api/v1/upload-credit-report")
async def upload_credit_report(file: UploadFile, user_id: str):
    try:
        current_count = check_rate_limit(user_id, "reports", max_count=2)
        rate_limit_checks.labels(user_tier='free', limit_type='reports').inc()
        rate_limit_usage.labels(user_id=user_id, limit_type='reports').set(current_count)
    except HTTPException as e:
        rate_limit_exceeded.labels(user_tier='free', limit_type='reports').inc()
        raise e
```

**Alerts**:
- **High rate limit exceeded rate**: >10% of users hitting rate limits (consider increasing limits or prompting upgrades)
- **Redis unavailable**: Fallback to in-memory rate limiting (log alert for Redis recovery)
- **Rate limit abuse**: Single user attempting >100 requests/minute (potential abuse, block IP)

## 4. Background Job Scalability (Celery)

### 4.1 Celery Task Queue Performance

**Current Architecture** (Month 6):
- **Celery workers**: 2 workers (CPU-bound OCR tasks)
- **Redis broker**: Single Redis instance (task queue + result backend)
- **Task types**:
  1. `process_credit_report`: OCR + Gemini parsing (30-60s)
  2. `parse_bureau_response`: OCR bureau response letter (30s) [Phase 2]
  3. `send_email_notification`: Email notifications (5s)

**Scaling Celery Workers** (Month 12+):

| Phase | Users | Credit Report Uploads/Day | Celery Workers | Average Queue Time |
|-------|-------|---------------------------|----------------|-------------------|
| **Month 6** | 100 | 10 | 2 | <30s |
| **Month 12** | 1,000 | 100 | 5 | <60s |
| **Month 18** | 5,000 | 500 | 15 | <120s |
| **Month 24** | 10,000 | 1,000 | 30 | <180s |

**Worker Auto-Scaling Strategy**:
```yaml
# Kubernetes HPA (Horizontal Pod Autoscaler) for Celery workers
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: celery-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: celery-worker
  minReplicas: 2
  maxReplicas: 30
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70  # Scale up if CPU >70%
  - type: External
    external:
      metric:
        name: celery_queue_length
      target:
        type: AverageValue
        averageValue: "10"  # Scale up if queue length >10 tasks
```

**Celery Task Monitoring**:
```python
from celery import Celery
from prometheus_client import Counter, Histogram

celery_app = Celery('tasks', broker='redis://localhost:6379/0')

# Metrics
celery_task_duration = Histogram('celery_task_duration_seconds', 'Task duration', ['task_name'])
celery_task_failures = Counter('celery_task_failures_total', 'Task failures', ['task_name'])

# Instrument task
@celery_app.task(name='process_credit_report', bind=True)
@celery_task_duration.labels(task_name='process_credit_report').time()
def process_credit_report(self, report_id: str, user_id: str):
    try:
        # Task logic
        pass
    except Exception as e:
        celery_task_failures.labels(task_name='process_credit_report').inc()
        raise
```

### 4.2 Task Prioritization Strategy

**Priority Levels**:
1. **High priority**: Paid user requests (mailed dispute letters)
2. **Medium priority**: Free user credit report uploads
3. **Low priority**: Background analytics recalculations

**Celery Queue Configuration**:
```python
# Configure separate queues for priority levels
celery_app.conf.task_routes = {
    'process_credit_report': {'queue': 'high_priority'},
    'parse_bureau_response': {'queue': 'medium_priority'},
    'send_email_notification': {'queue': 'low_priority'}
}

# Start workers with queue priority
# High priority workers (process paid requests first)
celery -A tasks worker --queues=high_priority,medium_priority,low_priority -n high@%h

# Medium priority workers (process free requests)
celery -A tasks worker --queues=medium_priority,low_priority -n medium@%h
```

## 5. Object Storage Scalability (Credit Report PDFs)

### 5.1 Supabase Storage Scaling

**Current Configuration** (Month 6):
- **Storage bucket**: `credit-reports` (public-read, authenticated-write)
- **File size limit**: 10MB per PDF
- **Total storage**: 1GB (100 users × 2 reports × 5MB average)

**Scaling Plan**:

| Phase | Users | Total PDFs | Storage Size | Supabase Tier | Cost |
|-------|-------|------------|--------------|---------------|------|
| **Month 6** | 100 | 200 | 1GB | Free tier (1GB included) | $0 |
| **Month 12** | 1,000 | 2,000 | 10GB | Pro tier (100GB included) | $25/month |
| **Month 18** | 5,000 | 10,000 | 50GB | Pro tier (100GB included) | $25/month |
| **Month 24** | 10,000 | 20,000 | 100GB | Pro tier (100GB included) | $25/month |

**Cost Optimization**:
- **Automatic cleanup**: Delete PDFs after 30 days (user can re-upload if needed)
- **Compression**: Store PDFs in compressed format (reduce storage by 30-50%)
- **Lifecycle policies**: Move PDFs >90 days old to cheaper cold storage (AWS S3 Glacier)

**Automatic Cleanup Policy**:
```python
from datetime import datetime, timedelta

# Scheduled job: Delete PDFs older than 30 days
def cleanup_old_pdfs():
    """
    Delete credit report PDFs older than 30 days.
    User can re-upload if needed.
    """
    cutoff_date = datetime.now() - timedelta(days=30)

    # Find old credit reports
    old_reports = supabase.table('credit_reports').select('id, file_url').lt('upload_date', cutoff_date.isoformat()).execute()

    for report in old_reports.data:
        # Delete PDF from Supabase Storage
        file_path = report['file_url'].split('/')[-1]
        supabase.storage.from_('credit-reports').remove([file_path])

        # Update credit_reports record (set file_url to NULL)
        supabase.table('credit_reports').update({'file_url': None}).eq('id', report['id']).execute()

# Schedule monthly cleanup
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(cleanup_old_pdfs, 'cron', day=1)  # Run on 1st of each month
scheduler.start()
```

## 6. Capacity Planning & Cost Estimates

### 6.1 Infrastructure Cost Projections

**Monthly Cost Breakdown**:

| Component | Month 6 (100 users) | Month 12 (1,000 users) | Month 18 (5,000 users) | Month 24 (10,000 users) |
|-----------|---------------------|------------------------|------------------------|-------------------------|
| **Supabase (Database + Storage)** | $0 (free tier) | $25 (Pro tier) | $25 (Pro tier) | $25-50 (Pro tier + overages) |
| **FastAPI Hosting (Cloud Run/Heroku)** | $10 (1 instance) | $30 (3 instances) | $100 (10 instances) | $200 (20 instances) |
| **Redis Cache** | $10 (managed Redis 512MB) | $20 (1GB) | $50 (2GB) | $100 (Redis Cluster 4GB) |
| **Celery Workers** | $20 (2 workers) | $50 (5 workers) | $150 (15 workers) | $300 (30 workers) |
| **Google Document AI** | $15 (200 pages/month @ $0.065/page) | $130 (2,000 pages) | $650 (10,000 pages) | $1,300 (20,000 pages) |
| **Gemini AI** | $5 (200 reports × 10K tokens @ $0.0025/1K tokens) | $50 (2,000 reports) | $250 (10,000 reports) | $500 (20,000 reports) |
| **Lob.com Mailing** (Phase 1) | $74 (45 letters × $1.65) | $743 (450 letters) | $3,713 (2,250 letters) | N/A (migrated to USPS) |
| **USPS API Direct** (Phase 2) | N/A | N/A | N/A | $4,500 (4,500 letters × $1.00) |
| **CDN (Cloudflare)** | $0 (free tier) | $20 (Pro tier) | $20 (Pro tier) | $20 (Pro tier) |
| **Monitoring (Prometheus + Grafana)** | $0 (self-hosted) | $50 (managed service) | $100 (managed service) | $200 (managed service) |
| **Total Infrastructure Cost** | **$134/month** | **$1,118/month** | **$5,058/month** | **$7,195/month** |

**Revenue vs Cost Analysis**:

| Phase | Users | Mailed Letters/Month | Revenue ($7.50 avg price) | Infrastructure Cost | Gross Profit | Margin |
|-------|-------|----------------------|---------------------------|---------------------|--------------|--------|
| **Month 6** | 100 | 45 | $338 | $134 | $204 | 60% |
| **Month 12** | 1,000 | 450 | $3,375 | $1,118 | $2,257 | 67% |
| **Month 18** | 5,000 | 2,250 | $16,875 | $5,058 | $11,817 | 70% |
| **Month 24** | 10,000 | 4,500 | $33,750 | $7,195 | $26,555 | 79% |

**Key Insights**:
- **Positive unit economics**: Revenue exceeds infrastructure cost at all scales
- **Improving margins**: Margin increases from 60% to 79% as scale increases (economies of scale)
- **USPS migration critical**: Phase 2 USPS migration reduces mailing cost by 40% ($1.65 → $1.00)

### 6.2 Database Storage Capacity Planning

**PostgreSQL Storage Growth**:

| Data Type | Month 6 | Month 12 | Month 18 | Month 24 | Growth Rate |
|-----------|---------|----------|----------|----------|-------------|
| **Users** | 100 rows (10KB) | 1,000 rows (100KB) | 5,000 rows (500KB) | 10,000 rows (1MB) | Linear |
| **Credit Reports** | 200 rows (20KB) | 2,000 rows (200KB) | 10,000 rows (1MB) | 20,000 rows (2MB) | Linear |
| **Tradelines** | 3,000 rows (3MB) | 30,000 rows (30MB) | 150,000 rows (150MB) | 300,000 rows (300MB) | Linear |
| **Dispute Tracking** | 500 rows (500KB) | 5,000 rows (5MB) | 25,000 rows (25MB) | 50,000 rows (50MB) | Linear |
| **Status History** | 1,500 rows (150KB) | 15,000 rows (1.5MB) | 75,000 rows (7.5MB) | 150,000 rows (15MB) | Linear |
| **Mailing Records** | 45 rows (5KB) | 450 rows (50KB) | 2,250 rows (250KB) | 4,500 rows (500KB) | Linear |
| **Indexes** | 50MB | 500MB | 2.5GB | 5GB | 10x data size |
| **Total Database Size** | **500MB** | **5GB** | **25GB** | **50GB** | 10x/year |

**TimescaleDB Storage Growth** (Phase 3 - Month 13+):

| Data Type | Month 18 | Month 24 | Growth Rate |
|-----------|----------|----------|-------------|
| **Credit Score History** | 5,000 users × 12 snapshots × 3 bureaus = 180K rows (5GB) | 10,000 users × 24 snapshots × 3 bureaus = 720K rows (10GB) | Linear |
| **Compressed (70% reduction)** | 1.5GB | 3GB | Linear |

**Supabase Storage Limits**:
- **Free tier**: 500MB database + 1GB object storage
- **Pro tier**: 8GB database + 100GB object storage
- **Enterprise tier**: Unlimited (custom pricing)

**Scaling Trigger Points**:
- **Database >6GB**: Upgrade to Supabase Enterprise tier or migrate to self-hosted PostgreSQL
- **Database >50GB**: Consider table partitioning by `user_id` or `created_at`
- **Object storage >100GB**: Implement PDF cleanup policy or migrate to AWS S3

## 7. Performance Monitoring & Observability

### 7.1 Monitoring Stack

**Metrics Collection**: Prometheus + Grafana

**Key Metrics to Monitor**:

1. **Application Metrics**:
   - API request rate (requests/second)
   - API response time (p50, p95, p99 latency)
   - Error rate (5xx errors/total requests)
   - Rate limit checks and exceeded count

2. **Database Metrics**:
   - Query execution time (slow query log for queries >100ms)
   - Database connection pool usage (active connections / max connections)
   - Table size and index size growth
   - Replication lag (if using read replicas)

3. **Background Job Metrics**:
   - Celery queue length (tasks waiting in queue)
   - Task execution time (OCR, Gemini parsing)
   - Task failure rate
   - Worker CPU/memory utilization

4. **Infrastructure Metrics**:
   - FastAPI instance CPU/memory usage
   - Redis cache hit rate
   - Object storage usage (GB)
   - CDN cache hit rate

**Grafana Dashboard Example**:
```yaml
# Dashboard panels
- API Request Rate (requests/second)
  - Panel type: Graph
  - Metric: rate(http_requests_total[5m])

- API Response Time (latency percentiles)
  - Panel type: Graph
  - Metrics: histogram_quantile(0.50, http_request_duration_seconds), p95, p99

- Database Query Performance
  - Panel type: Graph
  - Metric: histogram_quantile(0.95, pg_query_duration_seconds)

- Celery Queue Length
  - Panel type: Gauge
  - Metric: celery_queue_length
  - Alert threshold: >50 tasks (scale up workers)

- Database Connection Pool
  - Panel type: Gauge
  - Metric: pg_active_connections / pg_max_connections
  - Alert threshold: >80% utilization
```

### 7.2 Alerting Rules

**Critical Alerts** (PagerDuty/Slack notification):
- API error rate >5% for 5 minutes
- Database connection pool >90% utilized
- Celery queue length >100 tasks
- Redis cache unavailable
- Database disk usage >80%

**Warning Alerts** (Slack notification):
- API p95 latency >500ms for 10 minutes
- Slow queries detected (>1 second execution time)
- Celery task failure rate >10%
- Database connection pool >70% utilized

**Alert Example** (Prometheus AlertManager):
```yaml
groups:
- name: api_alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status="5xx"}[5m]) / rate(http_requests_total[5m]) > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High API error rate detected"
      description: "Error rate is {{ $value | humanizePercentage }} for the last 5 minutes"

  - alert: HighLatency
    expr: histogram_quantile(0.95, http_request_duration_seconds) > 0.5
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "High API latency detected"
      description: "p95 latency is {{ $value }}s for the last 10 minutes"
```

## Summary of Scalability, Performance & Capacity Decisions

1. **Stateless backend**: FastAPI horizontal scaling (1 → 20 instances) with load balancer
2. **Database scaling**: Vertical scaling (CPU/memory upgrades) + read replicas (Month 18+)
3. **Connection pooling**: PgBouncer with 20 connections per instance, auto-scale to 400 total connections
4. **Query optimization**: Composite indexes, denormalized user_id, trigger-based analytics cache
5. **TimescaleDB hypertables**: Monthly chunk partitioning, 70-90% compression for historical data
6. **Rate limiting**: Hybrid middleware + Redis (Month 6-12), Redis-only (Month 12+), Redis Cluster (Month 18+)
7. **Celery workers**: Auto-scaling based on CPU (70% threshold) and queue length (>10 tasks)
8. **Object storage**: 30-day PDF cleanup policy, compression, cold storage migration (>90 days)
9. **Cost efficiency**: Revenue exceeds infrastructure cost at all scales (60-79% margin)
10. **Monitoring**: Prometheus + Grafana for metrics, AlertManager for critical alerts

**Scalability Confidence**:
- ✅ **100 users (Month 6)**: Current architecture supports with free/low-cost tiers
- ✅ **1,000 users (Month 12)**: Horizontal scaling to 3 FastAPI instances, Supabase Pro tier
- ✅ **5,000 users (Month 18)**: 10 FastAPI instances, read replicas, Redis Cluster
- ✅ **10,000 users (Month 24)**: 20 FastAPI instances, database partitioning, enterprise tier

**Critical Path to Scale**:
1. **Month 12**: Migrate to Redis-only rate limiting (multi-instance support)
2. **Month 12**: Upgrade to Supabase Pro tier (500 connection limit)
3. **Month 18**: Implement read replicas for dashboard queries (reduce primary DB load)
4. **Month 18**: Deploy Redis Cluster for distributed caching (5,000+ users)
5. **Month 24**: Consider database partitioning if >50GB database size
