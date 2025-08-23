---
name: deploy-system
description: Autonomously deploy the entire system with comprehensive infrastructure, monitoring, and operational setup
usage: /deploy-system [environment] [deployment-type]
example: /deploy-system production blue-green
---

**Autonomous System Deployment Workflow**

This command triggers complete system deployment using the devops-orchestrator agent with comprehensive infrastructure setup, monitoring, and operational procedures.

## Usage
```
/deploy-system [environment] [deployment-type]
```

**Environments**: development, staging, production
**Deployment Types**: rolling, blue-green, canary, fresh-install

## Process
1. **Pre-Deployment Assessment** (devops-orchestrator):
   - Analyze current system state and requirements
   - Verify code readiness and quality gates
   - Check infrastructure capacity and dependencies
   - Create deployment plan with rollback procedures

2. **Infrastructure Preparation** (devops-orchestrator):
   - Set up cloud resources and networking
   - Configure load balancers and auto-scaling
   - Set up databases with proper backup procedures
   - Configure SSL certificates and security policies

3. **Application Deployment** (devops-orchestrator + backend-architect):
   - Build and push container images
   - Deploy backend services with health checks
   - Configure environment variables and secrets
   - Set up database migrations and data seeding

4. **Frontend Deployment** (devops-orchestrator + frontend-specialist):
   - Build optimized frontend assets
   - Deploy to CDN or static hosting
   - Configure routing and redirects
   - Set up progressive web app features

5. **Testing & Validation** (qa-automation + devops-orchestrator):
   - Run smoke tests and health checks
   - Perform end-to-end testing in target environment
   - Validate performance and security metrics
   - Test backup and disaster recovery procedures

6. **Monitoring & Observability** (devops-orchestrator):
   - Set up comprehensive logging and metrics
   - Configure alerting and notification systems
   - Create operational dashboards
   - Set up automated monitoring and health checks

7. **Documentation & Handover** (project-coordinator):
   - Generate deployment documentation
   - Create operational runbooks and procedures
   - Document troubleshooting guides
   - Provide access credentials and contact information

## Extended Thinking Trigger
```
Think comprehensively about this deployment strategy:
- What are the optimal infrastructure patterns for this system?
- How can we ensure zero-downtime deployment?
- What monitoring and alerting strategies will ensure reliability?
- How do we handle data migration and backup procedures?
- What security configurations are required for production?
- How do we scale the system based on traffic patterns?
- What disaster recovery procedures should be in place?
```

## Deployment Strategies

### Rolling Deployment
- Gradual replacement of instances
- Minimal downtime with load balancing
- Easy rollback to previous version

### Blue-Green Deployment
- Complete environment duplication
- Instant traffic switching
- Zero downtime with full rollback capability

### Canary Deployment
- Gradual traffic shifting to new version
- Risk mitigation with partial rollout
- Data-driven deployment decisions

### Fresh Install
- Complete new environment setup
- Ideal for major version changes
- Full infrastructure provisioning

## Infrastructure Components
- **Compute**: Auto-scaling container orchestration
- **Database**: High-availability with automated backups
- **Storage**: Secure file storage with CDN
- **Networking**: Load balancers, firewalls, VPN access
- **Monitoring**: Comprehensive observability stack
- **Security**: SSL, WAF, DDoS protection, secret management

## Expected Deliverables
- Complete production infrastructure
- Deployed and validated application
- Comprehensive monitoring and alerting
- Operational documentation and runbooks
- Backup and disaster recovery procedures
- Performance and security validation

## Success Criteria
- Application successfully deployed and accessible
- All health checks and tests passing
- Monitoring and alerting operational
- Performance metrics within acceptable ranges
- Security configurations validated
- Operational procedures documented and tested

Start by assessing current system state and creating comprehensive deployment strategy.