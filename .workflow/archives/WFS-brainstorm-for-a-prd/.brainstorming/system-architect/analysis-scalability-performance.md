# Scalability & Performance Architecture

**Parent Document**: @analysis.md
**Framework Reference**: @../guidance-specification.md (Section 7: Risks & Constraints - Scalability)

---

## Overview

This section details the scalability and performance architecture to support viral growth from 100 users (Month 6) to 10,000+ users (Month 24) while maintaining performance targets.

---

## Current Performance Baseline

**Existing Capabilities** (from ARCHITECTURE_GUIDE.md):
- ✅ Stateless backend design (horizontal scaling ready)
- ✅ Multi-level caching (Redis + in-memory)
- ✅ Background job processing (async PDF processing)
- ✅ Database pooling (Supabase managed)

**Current Performance** (Phase 3 modular architecture):
- PDF Processing: <30s for <10MB files
- API Latency (p95): ~150ms for CRUD operations
- Rate Limit Check: <5ms (in-memory cache)
- Concurrent Users: Untested (estimated ~50-100)

---

## Performance Targets by Phase

### Phase 1 (MVP - 100 users by Month 6)

| Metric | Target | Measurement | Critical? |
|--------|--------|-------------|-----------|
| API Latency (p95) | <200ms | New Relic / Prometheus | ✅ Yes |
| PDF Processing | <30s for <10MB | Background job timing | ✅ Yes |
| Rate Limit Check | <5ms | Middleware timing | ✅ Yes |
| Uptime | 99.9% (43min/month) | Uptime monitoring | ✅ Yes |
| Concurrent Users | 100+ simultaneous | Load testing | ⚠️ Validate |

### Phase 2 (1,000 users by Month 12)

| Metric | Target | Measurement | Critical? |
|--------|--------|-------------|-----------|
| API Latency (p95) | <200ms | APM tools | ✅ Yes |
| Background Job Queue | <5min wait time | Redis queue depth | ✅ Yes |
| Database Queries | <100ms (p99) | Query performance monitoring | ✅ Yes |
| Concurrent Users | 500+ simultaneous | Load testing | ✅ Yes |
| Uptime | 99.95% (22min/month) | SLA monitoring | ✅ Yes |

### Phase 3-4 (10,000+ users by Month 24)

| Metric | Target | Measurement | Critical? |
|--------|--------|-------------|-----------|
| API Latency (p95) | <200ms | Auto-scaling metrics | ✅ Yes |
| Background Job Throughput | 10,000+ jobs/day | Queue metrics | ✅ Yes |
| Database Queries | <100ms (p99) | Query optimization | ✅ Yes |
| Concurrent Users | 2,000+ simultaneous | Stress testing | ✅ Yes |
| Uptime | 99.99% (4.3min/month) | Multi-region failover | ⚠️ Future |

---

## Horizontal Scaling Architecture

### Stateless Backend Design

**Current Architecture** (Phase 3):
```python
# Existing: backend/main.py
app = FastAPI(
    title="Credit Clarity API",
    version="3.0.0"
)

# Stateless configuration
# - No server-side sessions (JWT-based auth)
# - No in-memory state (Redis for shared cache)
# - No file uploads to local disk (Supabase Storage)
```

**Benefits**:
- ✅ Any instance can handle any request (no sticky sessions)
- ✅ Auto-scaling possible (add/remove instances dynamically)
- ✅ Zero-downtime deployments (rolling updates)

### Load Balancer Configuration

**Production Deployment Architecture**:
```
┌─────────────────────────────────────────────────────────┐
│                    Internet / CDN                        │
│               (CloudFlare or AWS CloudFront)             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│               Load Balancer (AWS ALB / Nginx)            │
│         - Health checks every 30s                        │
│         - Round-robin distribution                       │
│         - SSL termination                                │
└──────┬──────────┬──────────┬─────────────────────────────┘
       │          │          │
       ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│ FastAPI  │ │ FastAPI  │ │ FastAPI  │
│ Instance │ │ Instance │ │ Instance │
│    #1    │ │    #2    │ │    #3    │
└──────────┘ └──────────┘ └──────────┘
       │          │          │
       └──────────┴──────────┘
                  │
         ┌────────┴────────┐
         │                 │
         ▼                 ▼
┌─────────────────┐ ┌─────────────────┐
│  Redis Cluster  │ │    Supabase     │
│  (Shared Cache) │ │   PostgreSQL    │
└─────────────────┘ └─────────────────┘
```

**Health Check Endpoint**:
```python
# Existing: backend/api/v1/routes/health.py
@router.get("/health")
async def health_check():
    """Load balancer health check."""

    checks = {
        "status": "healthy",
        "database": await check_database(),
        "redis": await check_redis(),
        "timestamp": datetime.utcnow().isoformat()
    }

    # Return 200 if all critical services healthy
    if checks["database"] and checks["redis"]:
        return checks
    else:
        # Return 503 Service Unavailable
        raise HTTPException(status_code=503, detail="Unhealthy")

async def check_database() -> bool:
    """Verify Supabase connection."""
    try:
        result = await supabase.table("users").select("id").limit(1).execute()
        return True
    except Exception:
        return False

async def check_redis() -> bool:
    """Verify Redis connection."""
    try:
        if cache_service.redis:
            await cache_service.redis.ping()
            return True
        return True  # Redis optional
    except Exception:
        return False
```

**Auto-Scaling Rules** (AWS ECS / Kubernetes):
```yaml
# Example: AWS ECS Auto Scaling
TargetTrackingScaling:
  TargetValue: 70.0  # Target 70% CPU utilization
  ScaleInCooldown: 300   # 5 minutes before scale-in
  ScaleOutCooldown: 60   # 1 minute before scale-out

MinCapacity: 2  # Minimum 2 instances (high availability)
MaxCapacity: 10 # Maximum 10 instances (cost limit)
```

---

## Vertical Scaling: Multi-Worker Deployment

### Gunicorn Configuration

**Production Deployment**:
```bash
# scripts/start_production.sh
gunicorn main:app \
  --workers $(( 2 * $(nproc) + 1 )) \  # (2 × CPU cores) + 1
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --timeout 120 \
  --keepalive 5 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
```

**Worker Configuration Rationale**:
- **Workers**: `(2 × CPU cores) + 1` for I/O-bound workloads (database, API calls)
- **Max Requests**: Restart workers after 1000 requests (prevent memory leaks)
- **Timeout**: 120 seconds (accommodate large PDF processing)
- **Keepalive**: 5 seconds (reduce connection overhead)

**Resource Allocation** (per instance):
```yaml
# Example: Docker container resources
Resources:
  CPU: 2 vCPU
  Memory: 4 GB
  Workers: 5  # (2 × 2) + 1
  Estimated Concurrent Requests: ~100-200
```

---

## Database Performance Optimization

### Connection Pooling

**Supabase Connection Pool**:
```python
# core/config.py
class Settings(BaseSettings):
    # Database connection pool settings
    database_pool_size: int = Field(default=20, env="DB_POOL_SIZE")
    database_max_overflow: int = Field(default=10, env="DB_MAX_OVERFLOW")
    database_pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")
    database_pool_recycle: int = Field(default=3600, env="DB_POOL_RECYCLE")
```

**Pool Sizing**:
- **Pool Size**: 20 connections per instance
- **Max Overflow**: 10 additional connections if pool exhausted
- **Total Connections**: 3 instances × 30 connections = 90 connections
- **Supabase Limit**: 100 connections (Free tier: 50, Pro tier: 500)

**Connection Pool Monitoring**:
```python
# Monitoring connection pool health
async def monitor_connection_pool():
    pool_stats = await get_pool_stats()

    logger.info(f"Connection pool: {pool_stats['active']}/{pool_stats['total']} active")

    if pool_stats['active'] > pool_stats['total'] * 0.8:
        logger.warning("Connection pool >80% utilized, consider scaling")
```

### Query Optimization

**Slow Query Detection**:
```python
# Middleware to log slow queries
@app.middleware("http")
async def log_slow_queries(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time

    if duration > 1.0:  # 1 second threshold
        logger.warning(f"Slow request: {request.url.path} took {duration:.2f}s")

    return response
```

**Index Strategy** (from data infrastructure):
```sql
-- Critical indexes for performance

-- Tradelines: User queries
CREATE INDEX idx_tradelines_user_id ON tradelines(user_id);
CREATE INDEX idx_tradelines_negative ON tradelines(user_id, is_negative);
CREATE INDEX idx_tradelines_bureau ON tradelines(user_id, bureau);

-- Disputes: Status filtering
CREATE INDEX idx_disputes_user_id ON disputes(user_id);
CREATE INDEX idx_disputes_status ON disputes(user_id, status);
CREATE INDEX idx_disputes_bureau ON disputes(user_id, bureau);

-- Status History: Audit trail queries
CREATE INDEX idx_history_dispute ON dispute_status_history(dispute_id, changed_at);

-- Report Uploads: User dashboard queries
CREATE INDEX idx_uploads_user_id ON report_uploads(user_id);
CREATE INDEX idx_uploads_status ON report_uploads(user_id, processing_status);
```

**Query Performance Monitoring**:
```sql
-- Enable pg_stat_statements extension (Supabase)
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Find slow queries
SELECT
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
WHERE mean_time > 100  -- >100ms average
ORDER BY mean_time DESC
LIMIT 20;
```

---

## Background Job Processing Optimization

### Redis Queue Architecture

**Current Implementation**:
```python
# Existing: backend/services/background_jobs.py
class BackgroundJobService:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.job_queue = "background_jobs"

    async def enqueue_job(self, job_type: str, job_data: Dict[str, Any]) -> str:
        """Add job to Redis queue."""

        job_id = str(uuid.uuid4())
        job = {
            "job_id": job_id,
            "job_type": job_type,
            "job_data": job_data,
            "status": "queued",
            "created_at": datetime.utcnow().isoformat()
        }

        # Push to Redis queue
        await self.redis.rpush(self.job_queue, json.dumps(job))

        return job_id
```

**Worker Process**:
```python
# background_worker.py
async def process_jobs():
    """Background worker to process job queue."""

    while True:
        # Pop job from queue (blocking)
        job_json = await redis.blpop(job_queue, timeout=1)

        if job_json:
            job = json.loads(job_json[1])

            try:
                if job['job_type'] == 'process_credit_report':
                    await process_credit_report_job(job['job_data'])
                elif job['job_type'] == 'send_letter_mailing':
                    await send_letter_mailing_job(job['job_data'])

                # Mark job complete
                await update_job_status(job['job_id'], 'complete')

            except Exception as e:
                logger.error(f"Job {job['job_id']} failed: {e}")
                await update_job_status(job['job_id'], 'failed', error=str(e))
                await retry_job(job)
```

**Scaling Background Workers**:
```yaml
# Docker Compose: Multiple worker instances
services:
  api:
    image: credit-clarity-api
    replicas: 3  # 3 API instances

  worker:
    image: credit-clarity-worker
    command: python background_worker.py
    replicas: 2  # 2 dedicated worker instances
```

**Queue Monitoring**:
```python
async def monitor_job_queue():
    """Monitor job queue health."""

    queue_depth = await redis.llen(job_queue)

    logger.info(f"Job queue depth: {queue_depth}")

    if queue_depth > 100:
        logger.warning("Job queue >100, consider adding workers")

    # Alert if queue depth exceeds threshold
    if queue_depth > 500:
        await send_alert("Job queue critically high: {queue_depth}")
```

---

## Caching Strategy Optimization

### Cache Hit Rate Optimization

**Target Hit Rates**:
- In-Memory Cache: >90% hit rate
- Redis Cache: >70% hit rate
- Overall Cache: >80% hit rate

**Cache Key Strategy** (from data infrastructure):
```python
# Optimized cache keys
CACHE_KEYS = {
    "user_stats": "user_stats:{user_id}",  # TTL: 5 minutes
    "tradelines": "tradelines:{user_id}:{report_id}",  # TTL: 1 hour
    "disputes": "disputes:{user_id}",  # TTL: 5 minutes
    "ocr_result": "ocr:{file_hash}",  # TTL: 24 hours
}

# Cache warming on user login
async def warm_user_cache(user_id: str):
    """Pre-load frequently accessed data."""

    # Warm user stats
    stats = await get_user_stats(user_id)
    await cache_service.set(f"user_stats:{user_id}", stats, ttl=300)

    # Warm recent tradelines
    tradelines = await get_user_tradelines(user_id)
    await cache_service.set(f"tradelines:{user_id}:recent", tradelines, ttl=3600)
```

**Cache Monitoring**:
```python
# Monitor cache performance
cache_stats = cache_service.stats()

logger.info(f"Cache hit rate: {cache_stats['hit_rate']:.1f}%")
logger.info(f"Cache size: {cache_stats['size']}/{cache_stats['max_size']}")

if cache_stats['hit_rate'] < 70:
    logger.warning("Low cache hit rate, review cache strategy")
```

---

## Rate Limiting Performance

### High-Performance Rate Limiting

**Current Implementation** (from guidance-specification.md):
```python
# Existing: Hybrid middleware + Redis
class RateLimitMiddleware:
    def __init__(self, redis_client, sync_interval=300):
        self.in_memory_cache = {}  # Fast lookup
        self.redis = redis_client
        self.sync_interval = sync_interval  # 5 minutes

    async def check_rate_limit(self, user_id: str, action: str):
        # In-memory check (<5ms)
        cache_key = f"{user_id}:{action}"
        current_count = self.in_memory_cache.get(cache_key, 0)

        limit = RATE_LIMITS[action]
        if current_count >= limit:
            raise RateLimitExceeded(action, limit)

        # Increment counter
        self.in_memory_cache[cache_key] = current_count + 1

        # Periodic sync to Redis
        if should_sync():
            await self.sync_to_redis()
```

**Performance**:
- In-Memory Lookup: <1ms (dictionary access)
- Redis Sync: Every 5 minutes (non-blocking)
- Total Overhead: <5ms per request

---

## Load Testing Strategy

### Phase 1 Load Testing (Before MVP Launch)

**Test Scenarios**:
```python
# locust_load_test.py
from locust import HttpUser, task, between

class CreditClarityUser(HttpUser):
    wait_time = between(1, 5)  # 1-5 seconds between requests

    @task(3)
    def view_dashboard(self):
        """Most common: View dashboard."""
        self.client.get("/api/v1/users/me/stats")

    @task(2)
    def view_tradelines(self):
        """Common: View tradelines."""
        self.client.get("/api/v1/tradelines")

    @task(1)
    def upload_report(self):
        """Less common: Upload credit report."""
        files = {'file': ('report.pdf', open('test_report.pdf', 'rb'), 'application/pdf')}
        self.client.post("/api/v1/reports/upload", files=files)

# Run load test
# locust -f locust_load_test.py --host=https://api.creditclarity.com --users 100 --spawn-rate 10
```

**Success Criteria**:
- 100 concurrent users: <200ms p95 latency
- 500 concurrent users: <500ms p95 latency
- 0 errors under normal load
- <1% error rate under peak load

### Phase 2 Load Testing (Before 1,000 Users)

**Stress Testing**:
```bash
# Stress test with 500 concurrent users
locust -f locust_load_test.py --host=https://api.creditclarity.com \
  --users 500 --spawn-rate 50 --run-time 10m

# Expected results:
# - API latency: <300ms p95
# - Error rate: <2%
# - Database connections: <70% pool utilization
# - Redis hit rate: >75%
```

---

## Monitoring & Observability

### Performance Metrics

**Application Performance Monitoring (APM)**:
```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
request_latency = Histogram('http_request_duration_seconds', 'HTTP request latency', ['method', 'endpoint'])

# Business metrics
pdf_processing_time = Histogram('pdf_processing_seconds', 'PDF processing time')
pdf_processing_count = Counter('pdf_processing_total', 'Total PDFs processed', ['status'])

# Infrastructure metrics
cache_hit_rate = Gauge('cache_hit_rate_percentage', 'Cache hit rate')
job_queue_depth = Gauge('job_queue_depth', 'Background job queue depth')
```

**Alerting Rules**:
```yaml
# Prometheus alerting rules
groups:
  - name: performance_alerts
    rules:
      - alert: HighAPILatency
        expr: http_request_duration_seconds{quantile="0.95"} > 0.2
        for: 5m
        annotations:
          summary: "API latency >200ms for 5 minutes"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 2m
        annotations:
          summary: "Error rate >5% for 2 minutes"

      - alert: HighJobQueueDepth
        expr: job_queue_depth > 500
        for: 10m
        annotations:
          summary: "Job queue >500 for 10 minutes"
```

---

## Conclusion

The scalability architecture supports viral growth through horizontal scaling (stateless design, load balancing) and vertical optimization (multi-worker deployment, connection pooling). The multi-level caching strategy and background job processing enable high performance while managing costs.

**Key Strengths**:
- ✅ Stateless design enables horizontal scaling
- ✅ Multi-worker deployment maximizes instance utilization
- ✅ Hybrid rate limiting provides <5ms overhead
- ✅ Load testing validates performance under growth scenarios

**Phase 1 Deliverables**:
- Load balancer health checks
- Gunicorn multi-worker configuration
- Connection pool tuning
- Load testing suite
- Performance monitoring dashboards
