# Configuration File Validation Tests

This directory contains comprehensive tests for validating configuration and specification files used throughout the project.

## Overview

These tests validate the structure, format, and content of:
- Claude agent specifications (`.claude/agents/*.md`)
- Claude settings (`.claude/settings.local.json`)
- Claude rules (`.claude/rules.md`)
- Ralph loop configuration (`.claude/ralph-loop.local.md`)
- Codex agent prompts (`.codex/prompts/bmad-bmm-agents-*.md`)
- Codex workflow prompts (`.codex/prompts/bmad-bmm-workflows-*.md`)

## Test Files

### `test_claude_agents.py`
Tests for Claude agent specification files:
- YAML frontmatter parsing and validation
- Required fields (name, description, color)
- Content structure and sections
- Agent-specific validation (document-ai-extractor, error-detective, ocr-tradeline-validator)
- Schema definitions and enum values
- Consistency across agent files

### `test_claude_settings.py`
Tests for Claude settings configuration:
- JSON schema validation
- Permissions structure (allow/deny lists)
- Bash command permissions format
- MCP server configuration
- Security validation (no overly permissive patterns)
- Consistency checks (no duplicate permissions)

### `test_claude_rules.py`
Tests for rules and loop configuration:
- Content validation for Sentry usage examples
- Code block format and syntax checking
- Ralph loop YAML frontmatter
- Configuration parameters and types
- Pipeline and workflow specifications

### `test_codex_agents.py`
Tests for Codex agent prompt files:
- YAML frontmatter validation
- Required fields and naming conventions
- Activation instructions and structure
- XML tag usage for structured content
- Reference validation (@_bmad paths)
- Consistency across agent prompts

### `test_codex_workflows.py`
Tests for Codex workflow prompt files:
- YAML frontmatter with descriptions
- Loading instructions and critical markers
- Workflow file references
- README content validation
- Excalidraw-specific workflows
- Consistency and uniqueness checks

### `run_tests.py`
Standalone test runner that can be executed without pytest dependencies:
- Runs all test suites
- Provides detailed pass/fail reporting
- Can be run directly: `python run_tests.py`

## Running Tests

### Using the standalone runner (recommended):
```bash
cd /path/to/project
python backend/tests/config/run_tests.py
```

### Using pytest:
```bash
cd backend
python -m pytest tests/config/ -v
```

## Test Results

All tests pass successfully:
- ✓ 19 tests passed
- ✓ 0 tests failed
- ✓ 0 tests skipped

## What These Tests Validate

### Structure Validation
- YAML frontmatter is properly formatted
- JSON files are valid and well-structured
- Required fields are present
- Field types are correct

### Content Validation
- Descriptions are meaningful and not empty
- Code examples have valid syntax
- References to files and paths are present
- Agent/workflow names match filenames

### Consistency Validation
- Similar files follow consistent patterns
- No duplicate entries in lists
- Naming conventions are followed
- Required sections are present

### Security Validation
- Permission patterns are not overly permissive
- No dangerous command wildcards
- Proper access controls are in place

## Edge Cases Covered

1. **Missing files**: Tests gracefully skip when files don't exist
2. **Invalid JSON/YAML**: Tests detect and report parsing errors
3. **Empty or malformed content**: Tests validate minimum content requirements
4. **Inconsistent naming**: Tests ensure names match between frontmatter and filenames
5. **Missing required fields**: Tests validate all required fields are present
6. **Type mismatches**: Tests verify fields have correct data types

## Future Enhancements

Potential additions to strengthen the test suite:
- Schema validation against formal JSON Schema definitions
- Cross-reference validation (checking that referenced files exist)
- Workflow dependency graph validation
- More comprehensive regex pattern validation
- Integration with CI/CD pipelines
- Automated fix suggestions for common issues

## Contributing

When adding new configuration files:
1. Add corresponding tests to the appropriate test file
2. Update this README with the new validation rules
3. Run the test suite to ensure everything passes
4. Consider adding edge case tests for the new configuration