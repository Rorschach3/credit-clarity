# Autonomous Bug Resolution Planning Template

Use this template with "think harder" mode to create systematic bug investigation and resolution plans that can be executed autonomously by specialized agents.

## Extended Thinking Prompt
```
Think systematically and comprehensively about resolving this bug:

BUG DESCRIPTION: [Bug Description and Error Details]

Please analyze this bug from multiple investigative angles:

1. SYMPTOM ANALYSIS:
   - What are the exact symptoms and error manifestations?
   - When does this bug occur (timing, conditions, environment)?
   - What is the expected vs actual behavior?
   - How does this impact users and system functionality?

2. ROOT CAUSE INVESTIGATION:
   - What are all possible root causes for these symptoms?
   - Which system components could be responsible?
   - Are there recent changes that might have introduced this bug?
   - What environmental factors could contribute to this issue?

3. REPRODUCTION STRATEGY:
   - How can we reliably reproduce this bug?
   - What specific steps, data, or conditions are needed?
   - In which environments does this occur (dev, staging, production)?
   - What tools or techniques can help us observe the bug in action?

4. DEBUGGING APPROACH:
   - What logging or monitoring data should we examine?
   - What debugging tools and techniques are most appropriate?
   - How can we isolate the problematic component or code path?
   - What experiments can we run to test our hypotheses?

5. SOLUTION STRATEGIES:
   - What are the potential approaches to fix this bug?
   - What are the trade-offs between different solution approaches?
   - How can we ensure the fix doesn't introduce new issues?
   - What is the safest way to implement and deploy the fix?

6. TESTING AND VALIDATION:
   - How do we verify the bug is completely resolved?
   - What regression tests are needed to prevent recurrence?
   - What additional testing should be performed?
   - How do we validate the fix in different environments?

7. PREVENTION MEASURES:
   - How can we prevent similar bugs in the future?
   - What improvements to code quality, testing, or monitoring are needed?
   - What additional safeguards or validation should be implemented?
   - What documentation or knowledge sharing would help prevent recurrence?

Create a detailed investigation and resolution plan that specialized agents can execute autonomously.
```

## Planning Output Structure

### 1. Bug Analysis Summary
- **Description**: Clear bug description and symptoms
- **Impact Assessment**: User impact and business criticality
- **Affected Components**: Systems, services, or features affected
- **Environment Details**: Where the bug occurs and under what conditions

### 2. Investigation Plan
- **Reproduction Steps**: Detailed steps to reproduce the bug
- **Data Collection**: Logs, metrics, and diagnostic data to gather
- **Hypothesis Testing**: Theories to test and validation methods
- **Debugging Tools**: Tools and techniques to use for investigation

### 3. Resolution Strategy
- **Root Cause Analysis**: Systematic approach to identify root cause
- **Solution Options**: Multiple approaches with pros/cons analysis
- **Implementation Plan**: Step-by-step fix implementation
- **Risk Assessment**: Potential risks and mitigation strategies

### 4. Agent Task Assignments
- **Error Detective Tasks**: Investigation and root cause analysis
- **Backend Architect Tasks**: Backend-specific debugging and fixes
- **Frontend Specialist Tasks**: Frontend-specific debugging and fixes
- **DevOps Orchestrator Tasks**: Infrastructure and deployment issues
- **QA Automation Tasks**: Testing strategy and validation

### 5. Testing and Validation
- **Reproduction Tests**: Tests that demonstrate the original bug
- **Fix Validation**: Tests that verify the fix works correctly
- **Regression Testing**: Tests to ensure no new issues introduced
- **Integration Testing**: Tests to verify system integration intact

### 6. Deployment and Monitoring
- **Deployment Strategy**: Safe deployment approach for the fix
- **Monitoring Plan**: Additional monitoring to track fix effectiveness
- **Rollback Procedures**: Plan for rolling back if issues occur
- **Communication Plan**: Stakeholder communication and updates

### 7. Prevention Measures
- **Code Quality Improvements**: Standards and practices to prevent similar bugs
- **Testing Enhancements**: Additional tests or testing processes
- **Monitoring Improvements**: Better detection and alerting
- **Documentation Updates**: Knowledge sharing and process improvements

## Investigation Methodology

### Phase 1: Information Gathering
- Collect all available error messages and stack traces
- Gather user reports and reproduction scenarios
- Review recent code changes and deployments
- Analyze system logs and monitoring data

### Phase 2: Hypothesis Formation
- Develop theories about potential root causes
- Prioritize hypotheses based on likelihood and impact
- Design experiments to test each hypothesis
- Plan systematic investigation approach

### Phase 3: Root Cause Analysis
- Execute debugging experiments systematically
- Use appropriate tools and techniques for investigation
- Document findings and eliminate possibilities
- Identify definitive root cause

### Phase 4: Solution Implementation
- Design fix that addresses root cause
- Implement solution with proper error handling
- Add appropriate tests and validation
- Prepare for safe deployment

### Phase 5: Validation and Prevention
- Thoroughly test the fix in all environments
- Implement measures to prevent recurrence
- Update documentation and processes
- Monitor for any related issues

## Usage Instructions
1. Replace [Bug Description and Error Details] with specific bug information
2. Use "think harder" prompt to generate comprehensive analysis
3. Review and refine the generated investigation plan
4. Execute using /fix-bug command with specialized agents
5. Monitor progress and adjust approach as new information emerges

This template ensures systematic bug resolution that addresses root causes and prevents recurrence while maintaining system stability.