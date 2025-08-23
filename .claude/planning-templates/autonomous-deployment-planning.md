# Autonomous Deployment Planning Template

Use this template with "think harder" mode to create comprehensive deployment strategies that can be executed autonomously by specialized agents.

## Extended Thinking Prompt
```
Think comprehensively about deploying this system to [ENVIRONMENT]:

DEPLOYMENT TARGET: [Environment and Requirements]

Please analyze this deployment from multiple operational perspectives:

1. INFRASTRUCTURE ARCHITECTURE:
   - What cloud resources and services are needed?
   - How should the infrastructure be organized for optimal performance?
   - What scaling and availability requirements must be met?
   - How should networking, security, and access control be configured?

2. APPLICATION DEPLOYMENT STRATEGY:
   - What is the optimal deployment pattern (rolling, blue-green, canary)?
   - How should different components be deployed and coordinated?
   - What are the database migration and data seeding requirements?
   - How should configuration and secrets be managed?

3. MONITORING AND OBSERVABILITY:
   - What monitoring, logging, and alerting systems are needed?
   - What key metrics and KPIs should be tracked?
   - How should we detect and respond to issues?
   - What dashboards and operational views are required?

4. SECURITY AND COMPLIANCE:
   - What security configurations and hardening are required?
   - How should access control and authentication be implemented?
   - What compliance requirements must be met?
   - How should sensitive data and secrets be protected?

5. PERFORMANCE AND SCALING:
   - What performance characteristics are expected?
   - How should auto-scaling and load balancing be configured?
   - What caching and optimization strategies should be implemented?
   - How should the system handle traffic spikes and growth?

6. OPERATIONAL PROCEDURES:
   - What backup and disaster recovery procedures are needed?
   - How should deployments, rollbacks, and maintenance be handled?
   - What troubleshooting and support procedures are required?
   - What documentation and runbooks need to be created?

7. RISK MANAGEMENT:
   - What are the potential deployment risks and failure modes?
   - How should we minimize downtime and service disruption?
   - What rollback and recovery procedures should be in place?
   - How should we validate deployment success and system health?

Create a detailed deployment plan that specialized agents can execute autonomously.
```

## Planning Output Structure

### 1. Deployment Overview
- **Target Environment**: Environment specification and requirements
- **Deployment Strategy**: Chosen deployment pattern and approach
- **Timeline**: Deployment schedule with milestones and dependencies
- **Success Criteria**: Measurable outcomes and validation requirements

### 2. Infrastructure Specification
- **Cloud Resources**: Compute, storage, networking, and managed services
- **Architecture Diagram**: System architecture and component relationships
- **Scaling Configuration**: Auto-scaling policies and capacity planning
- **Security Configuration**: Firewalls, VPNs, access controls, and hardening

### 3. Application Deployment Plan
- **Build Process**: Application build and artifact creation
- **Database Migration**: Schema changes and data migration procedures
- **Configuration Management**: Environment variables and secrets handling
- **Service Orchestration**: Service startup order and health checks

### 4. Monitoring and Observability Setup
- **Logging Infrastructure**: Log aggregation and management
- **Metrics Collection**: Application and infrastructure metrics
- **Alerting Configuration**: Alert rules and notification channels
- **Dashboard Creation**: Operational dashboards and visualizations

### 5. Agent Task Assignments
- **DevOps Orchestrator Tasks**: Infrastructure and deployment automation
- **Backend Architect Tasks**: Database migrations and service configuration
- **Frontend Specialist Tasks**: Frontend build and CDN deployment
- **QA Automation Tasks**: Deployment testing and validation

### 6. Quality Gates and Validation
- **Pre-deployment Checks**: Code quality, testing, and security validation
- **Deployment Validation**: Health checks and smoke tests
- **Performance Validation**: Load testing and performance benchmarks
- **Security Validation**: Security scans and compliance checks

### 7. Operational Procedures
- **Backup and Recovery**: Data backup and disaster recovery procedures
- **Maintenance Procedures**: Regular maintenance and update processes
- **Troubleshooting Guides**: Common issues and resolution procedures
- **Support Documentation**: Operational runbooks and contact information

## Deployment Strategies

### Rolling Deployment
- **Description**: Gradual replacement of instances with zero downtime
- **Advantages**: Minimal risk, easy rollback, load balancer friendly
- **Considerations**: Requires compatible versions, slower deployment
- **Best For**: Regular updates, stable systems

### Blue-Green Deployment
- **Description**: Complete environment duplication with instant switch
- **Advantages**: Zero downtime, instant rollback, full testing capability
- **Considerations**: Double resource cost, complex data synchronization
- **Best For**: Major releases, high-availability requirements

### Canary Deployment
- **Description**: Gradual traffic shifting to new version
- **Advantages**: Risk mitigation, real-world validation, data-driven decisions
- **Considerations**: Complex traffic management, longer deployment time
- **Best For**: New features, uncertain changes, large user bases

### Fresh Install
- **Description**: Complete new environment from scratch
- **Advantages**: Clean state, latest configurations, testing new setups
- **Considerations**: Longer deployment time, data migration complexity
- **Best For**: Major version upgrades, infrastructure changes

## Infrastructure Components

### Compute Resources
- **Application Servers**: Container orchestration and scaling
- **Load Balancers**: Traffic distribution and health checking
- **Auto-scaling**: Dynamic resource adjustment based on demand
- **Network Configuration**: VPCs, subnets, and security groups

### Data Layer
- **Primary Database**: High-availability database setup
- **Read Replicas**: Read scaling and geographic distribution
- **Caching Layer**: Redis/Memcached for performance optimization
- **Backup Systems**: Automated backup and point-in-time recovery

### Security Layer
- **SSL/TLS**: Certificate management and encryption
- **WAF**: Web application firewall for attack protection
- **DDoS Protection**: Traffic filtering and rate limiting
- **Secret Management**: Secure storage and rotation of secrets

### Monitoring Stack
- **Metrics**: Prometheus, CloudWatch, or equivalent
- **Logging**: ELK stack, CloudWatch Logs, or equivalent
- **Alerting**: PagerDuty, Slack, or equivalent notification systems
- **Dashboards**: Grafana, CloudWatch, or equivalent visualization

## Usage Instructions
1. Replace [Environment and Requirements] with specific deployment target
2. Use "think harder" prompt to generate comprehensive deployment analysis
3. Review and refine the generated deployment plan
4. Execute using /deploy-system command with specialized agents
5. Monitor deployment progress and validate success criteria

This template ensures comprehensive deployment planning that covers all aspects of production readiness while enabling autonomous execution by specialized agents.