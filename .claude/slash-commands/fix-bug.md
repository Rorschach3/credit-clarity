---
name: fix-bug
description: Autonomously analyze, debug, and fix bugs using systematic investigation and specialized agents
usage: /fix-bug [bug description or issue]
example: /fix-bug "User authentication fails on mobile devices"
---

**Autonomous Bug Resolution Workflow**

This command triggers comprehensive bug analysis and resolution using the error-detective agent coordinated with specialized domain agents.

## Usage
```
/fix-bug "bug description or error details"
```

## Process
1. **Initial Investigation** (error-detective):
   - Gather comprehensive bug information and reproduction steps
   - Analyze error messages, logs, and stack traces
   - Identify affected components and potential root causes
   - Create systematic debugging plan

2. **Root Cause Analysis** (error-detective + domain specialists):
   - **Backend Issues** (backend-architect): Database queries, API logic, authentication
   - **Frontend Issues** (frontend-specialist): UI components, state management, user interactions
   - **Infrastructure Issues** (devops-orchestrator): Deployment, configuration, environment
   - Perform deep dive analysis using debugging tools and techniques

3. **Solution Development** (appropriate specialist agent):
   - Design fix that addresses root cause, not just symptoms
   - Consider multiple solution approaches and trade-offs
   - Implement fix with proper error handling and validation
   - Ensure solution doesn't introduce new issues

4. **Testing & Validation** (qa-automation):
   - Create test cases that reproduce the original bug
   - Implement regression tests to prevent recurrence
   - Perform thorough testing of the fix
   - Validate that existing functionality remains intact

5. **Code Review & Integration** (project-coordinator):
   - Review fix for code quality and best practices
   - Ensure proper documentation and comments
   - Coordinate integration with existing codebase
   - Plan deployment strategy for the fix

6. **Monitoring & Verification** (devops-orchestrator):
   - Deploy fix to staging environment
   - Monitor system behavior and performance
   - Set up alerts for related issues
   - Plan production deployment and rollback procedures

## Extended Thinking Trigger
```
Think systematically about this bug investigation:
- What are all possible root causes for this issue?
- How can we reproduce this bug consistently?
- What related systems or components might be affected?
- What testing strategies will prevent regression?
- How can we improve our detection of similar issues?
- What monitoring can we add to catch this earlier?
```

## Investigation Methodology
1. **Information Gathering**:
   - Collect error messages and stack traces
   - Identify reproduction steps and affected environments
   - Gather user reports and system logs
   - Document expected vs actual behavior

2. **Systematic Analysis**:
   - Check for common error patterns
   - Analyze code flow and logic
   - Verify data types and API responses
   - Investigate timing and concurrency issues

3. **Solution Validation**:
   - Test fix in isolated environment
   - Verify fix addresses root cause
   - Check for performance implications
   - Ensure no new bugs introduced

## Expected Deliverables
- Detailed bug analysis and root cause identification
- Comprehensive fix implementation
- Regression test suite
- Updated documentation
- Deployment plan with rollback procedures
- Monitoring and alerting improvements

## Success Criteria
- Bug completely resolved and verified
- Root cause analysis documented
- Regression tests prevent recurrence
- No new issues introduced
- System performance maintained or improved
- Proper monitoring in place

Start by gathering comprehensive bug information and creating systematic investigation plan.