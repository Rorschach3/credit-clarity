---
name: optimize-performance
description: Autonomously analyze and optimize system performance across all layers using specialized agents
usage: /optimize-performance [target-area] [performance-goal]
example: /optimize-performance database "reduce query time by 50%"
---

**Autonomous Performance Optimization Workflow**

This command triggers comprehensive performance analysis and optimization using all specialized agents coordinated by the project-coordinator.

## Usage
```
/optimize-performance [target-area] [performance-goal]
```

**Target Areas**: frontend, backend, database, infrastructure, full-system
**Performance Goals**: Custom metrics and targets (response time, throughput, memory usage, etc.)

## Process
1. **Performance Assessment** (project-coordinator):
   - Establish baseline performance metrics
   - Identify performance bottlenecks and pain points
   - Set measurable optimization targets
   - Create comprehensive optimization strategy

2. **Frontend Optimization** (frontend-specialist):
   - Analyze bundle size and implement code splitting
   - Optimize images and assets for faster loading
   - Implement lazy loading and caching strategies
   - Optimize rendering performance and Core Web Vitals
   - Add service worker for offline functionality

3. **Backend Optimization** (backend-architect):
   - Profile API endpoints and identify slow queries
   - Implement database query optimization and indexing
   - Add caching layers (Redis, in-memory caching)
   - Optimize algorithms and business logic
   - Implement async processing for heavy operations

4. **Database Optimization** (backend-architect + devops-orchestrator):
   - Analyze query performance and execution plans
   - Optimize database schema and indexing strategy
   - Implement connection pooling and query optimization
   - Set up read replicas and database clustering
   - Optimize data storage and archival strategies

5. **Infrastructure Optimization** (devops-orchestrator):
   - Analyze resource utilization and scaling patterns
   - Optimize container resource allocation
   - Implement auto-scaling and load balancing
   - Set up CDN and edge caching
   - Optimize network configuration and latency

6. **Performance Testing** (qa-automation):
   - Create comprehensive performance test suites
   - Implement load testing and stress testing
   - Monitor performance metrics during optimization
   - Validate optimization results against targets
   - Set up continuous performance monitoring

7. **Monitoring & Alerting** (devops-orchestrator):
   - Set up performance monitoring dashboards
   - Configure alerts for performance degradation
   - Implement automated performance regression detection
   - Create performance reporting and trending

## Extended Thinking Trigger
```
Think deeply about performance optimization strategies:
- Where are the actual bottlenecks in the system?
- What are the most impactful optimizations we can make?
- How do we balance performance with maintainability?
- What performance monitoring should we implement?
- How do we prevent performance regressions?
- What are the cost implications of performance improvements?
- How do we optimize for different user scenarios and locations?
```

## Optimization Areas

### Frontend Performance
- Bundle optimization and code splitting
- Image optimization and lazy loading
- Caching strategies and service workers
- Critical path optimization
- Third-party script optimization

### Backend Performance
- API response time optimization
- Database query performance
- Caching layer implementation
- Algorithm and logic optimization
- Async processing implementation

### Database Performance
- Query optimization and indexing
- Connection pooling and scaling
- Data partitioning and sharding
- Backup and maintenance optimization
- Read replica configuration

### Infrastructure Performance
- Auto-scaling and resource optimization
- CDN and edge caching setup
- Load balancing optimization
- Network latency reduction
- Container orchestration tuning

## Performance Metrics
- **Response Time**: API endpoints, page load times
- **Throughput**: Requests per second, transactions per minute
- **Resource Usage**: CPU, memory, disk, network utilization
- **User Experience**: Core Web Vitals, interaction metrics
- **Scalability**: Performance under load, scaling efficiency

## Expected Deliverables
- Comprehensive performance analysis report
- Optimized code and infrastructure configurations
- Performance monitoring and alerting setup
- Benchmarking and comparison reports
- Performance optimization documentation
- Continuous monitoring procedures

## Success Criteria
- Performance targets achieved and measured
- System can handle expected load efficiently
- Performance monitoring and alerting operational
- No functionality compromised during optimization
- Cost-effective performance improvements implemented
- Performance regression prevention measures in place

Start by establishing current performance baselines and identifying optimization opportunities across all system layers.