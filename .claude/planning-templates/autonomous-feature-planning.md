# Autonomous Feature Planning Template

Use this template with "think harder" mode to create comprehensive feature implementation plans that can be executed autonomously by specialized agents.

## Extended Thinking Prompt
```
Think deeply and comprehensively about implementing this feature:

FEATURE: [Feature Description]

Please analyze this feature implementation from multiple perspectives:

1. TECHNICAL ARCHITECTURE:
   - What backend APIs and data models are needed?
   - What frontend components and user interactions are required?
   - How does this integrate with existing system architecture?
   - What external services or dependencies are needed?

2. USER EXPERIENCE DESIGN:
   - What are the user workflows and interaction patterns?
   - How should the UI be structured for optimal usability?
   - What accessibility considerations are important?
   - How does this fit into the overall application navigation?

3. DATA FLOW AND INTEGRATION:
   - How does data flow through the system for this feature?
   - What validation and security measures are needed?
   - How does this integrate with existing APIs and databases?
   - What caching and performance optimizations are beneficial?

4. TESTING STRATEGY:
   - What unit tests are needed for backend logic?
   - What integration tests are needed for API endpoints?
   - What frontend component tests are required?
   - What end-to-end user scenarios should be tested?

5. DEPLOYMENT AND OPERATIONS:
   - What infrastructure changes or configurations are needed?
   - How should this be deployed safely to production?
   - What monitoring and alerting should be implemented?
   - What documentation is needed for operations?

6. IMPLEMENTATION SEQUENCE:
   - What is the optimal order of implementation tasks?
   - Which tasks can be done in parallel?
   - What are the critical dependencies between tasks?
   - How should the work be distributed across specialized agents?

Create a detailed implementation plan that specialized agents can execute autonomously.
```

## Planning Output Structure

### 1. Feature Overview
- **Description**: Clear feature description and purpose
- **User Stories**: Key user scenarios and acceptance criteria
- **Success Metrics**: Measurable outcomes and KPIs
- **Timeline**: Estimated implementation timeline with milestones

### 2. Technical Specification
- **Backend Requirements**: APIs, data models, business logic
- **Frontend Requirements**: Components, pages, user interactions
- **Integration Points**: External services, existing systems
- **Performance Requirements**: Response times, scalability needs

### 3. Implementation Plan
- **Phase 1 - Backend Foundation**: Core APIs and data layer
- **Phase 2 - Frontend Implementation**: UI components and user flows
- **Phase 3 - Integration & Testing**: End-to-end testing and validation
- **Phase 4 - Deployment & Monitoring**: Production deployment and operations

### 4. Agent Task Assignments
- **Backend Architect Tasks**: Specific backend implementation tasks
- **Frontend Specialist Tasks**: Specific frontend implementation tasks
- **QA Automation Tasks**: Testing strategy and implementation
- **DevOps Orchestrator Tasks**: Deployment and operational tasks

### 5. Quality Gates
- **Code Quality**: Standards and review criteria
- **Testing Coverage**: Required test coverage and types
- **Performance Benchmarks**: Response time and scalability targets
- **Security Validation**: Security requirements and checks

### 6. Risk Mitigation
- **Technical Risks**: Potential technical challenges and solutions
- **Timeline Risks**: Schedule risks and mitigation strategies
- **Integration Risks**: Dependency risks and fallback plans
- **Quality Risks**: Quality assurance and validation strategies

## Usage Instructions
1. Replace [Feature Description] with specific feature requirements
2. Use "think harder" prompt to generate comprehensive analysis
3. Review and refine the generated plan
4. Execute using /implement-feature command with specialized agents
5. Monitor progress and adjust plan as needed

This template ensures thorough planning that enables autonomous execution while maintaining quality and consistency across all aspects of feature development.