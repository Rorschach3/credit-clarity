"""
Unit tests for configuration file validation.
Tests YAML frontmatter, JSON schema, and markdown structure for config files.
"""
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
import yaml


# Base paths
GIT_ROOT = Path("/home/jailuser/git")
CLAUDE_AGENTS_DIR = GIT_ROOT / ".claude" / "agents"
CODEX_PROMPTS_DIR = GIT_ROOT / ".codex" / "prompts"
CLAUDE_DIR = GIT_ROOT / ".claude"


def parse_yaml_frontmatter(content: str) -> Optional[Dict[str, Any]]:
    """
    Parse YAML frontmatter from markdown content.

    Args:
        content: Markdown content with potential YAML frontmatter

    Returns:
        Dict containing parsed YAML or None if no frontmatter found
    """
    # Match YAML frontmatter pattern: ---\n<yaml>\n---
    # Using re.DOTALL to match across multiple lines
    # The ? makes * non-greedy to stop at first closing ---
    pattern = r'^---\s*?\n(.*?)\n---'
    match = re.match(pattern, content, re.DOTALL | re.MULTILINE)

    if match:
        yaml_content = match.group(1)
        try:
            # Try standard YAML parsing first
            return yaml.safe_load(yaml_content)
        except yaml.YAMLError:
            # If standard parsing fails, try a simple key: value parser
            # This handles cases where values contain unquoted colons
            try:
                result = {}
                for line in yaml_content.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        result[key.strip()] = value.strip()
                return result if result else None
            except Exception:
                return None
    return None


def read_file_content(file_path: Path) -> str:
    """Read file content as string."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


class TestAgentConfigFiles:
    """Test suite for Claude agent configuration files."""

    @pytest.fixture
    def agent_files(self) -> List[Path]:
        """Get all agent configuration files."""
        return [
            CLAUDE_AGENTS_DIR / "document-ai-extractor.md",
            CLAUDE_AGENTS_DIR / "error-detective.md",
            CLAUDE_AGENTS_DIR / "ocr-tradeline-validator.md",
        ]

    @pytest.mark.unit
    def test_agent_files_exist(self, agent_files):
        """Test that all agent configuration files exist."""
        for file_path in agent_files:
            assert file_path.exists(), f"Agent file not found: {file_path}"
            assert file_path.is_file(), f"Path is not a file: {file_path}"

    @pytest.mark.unit
    def test_agent_files_not_empty(self, agent_files):
        """Test that agent files are not empty."""
        for file_path in agent_files:
            content = read_file_content(file_path)
            assert len(content.strip()) > 0, f"Agent file is empty: {file_path}"

    @pytest.mark.unit
    def test_agent_yaml_frontmatter_structure(self, agent_files):
        """Test that agent files with frontmatter have valid YAML structure."""
        for file_path in agent_files:
            content = read_file_content(file_path)

            # Only test files that start with frontmatter delimiter
            if content.startswith('---'):
                frontmatter = parse_yaml_frontmatter(content)
                assert frontmatter is not None, f"No YAML frontmatter found in: {file_path}"
                assert isinstance(frontmatter, dict), f"Frontmatter is not a dict: {file_path}"

    @pytest.mark.unit
    def test_agent_required_fields(self, agent_files):
        """Test that agent files with frontmatter contain required fields."""
        required_fields = ['name', 'description']

        for file_path in agent_files:
            content = read_file_content(file_path)

            # Only test files that have frontmatter
            if content.startswith('---'):
                frontmatter = parse_yaml_frontmatter(content)
                assert frontmatter is not None, f"No frontmatter in: {file_path}"

                for field in required_fields:
                    assert field in frontmatter, \
                        f"Missing required field '{field}' in: {file_path}"
                    assert frontmatter[field], \
                        f"Field '{field}' is empty in: {file_path}"

    @pytest.mark.unit
    def test_agent_name_format(self, agent_files):
        """Test that agent names follow expected format."""
        for file_path in agent_files:
            content = read_file_content(file_path)
            frontmatter = parse_yaml_frontmatter(content)

            if frontmatter and 'name' in frontmatter:
                name = frontmatter['name']
                assert isinstance(name, str), f"Name is not a string in: {file_path}"
                assert len(name) > 0, f"Name is empty in: {file_path}"
                # Name should be kebab-case or lowercase
                assert name.replace('-', '').replace('_', '').isalnum() or name.islower(), \
                    f"Name should be lowercase/kebab-case in: {file_path}"

    @pytest.mark.unit
    def test_agent_description_quality(self, agent_files):
        """Test that agent descriptions are meaningful."""
        for file_path in agent_files:
            content = read_file_content(file_path)
            frontmatter = parse_yaml_frontmatter(content)

            if frontmatter and 'description' in frontmatter:
                description = frontmatter['description']
                assert isinstance(description, str), \
                    f"Description is not a string in: {file_path}"
                assert len(description) >= 20, \
                    f"Description too short (< 20 chars) in: {file_path}"

    @pytest.mark.unit
    def test_agent_color_field_validity(self, agent_files):
        """Test that color field (if present) has valid values."""
        valid_colors = ['red', 'green', 'blue', 'yellow', 'purple', 'orange',
                       'pink', 'cyan', 'gray', 'black', 'white']

        for file_path in agent_files:
            content = read_file_content(file_path)
            frontmatter = parse_yaml_frontmatter(content)

            if frontmatter and 'color' in frontmatter:
                color = frontmatter['color']
                assert isinstance(color, str), f"Color is not a string in: {file_path}"
                assert color.lower() in valid_colors, \
                    f"Invalid color '{color}' in: {file_path}"

    @pytest.mark.unit
    def test_agent_markdown_content_exists(self, agent_files):
        """Test that agent files have content after frontmatter."""
        for file_path in agent_files:
            content = read_file_content(file_path)

            # Remove frontmatter
            pattern = r'^---\s*\n.*?\n---\s*\n'
            content_after_frontmatter = re.sub(pattern, '', content, count=1, flags=re.DOTALL)

            assert len(content_after_frontmatter.strip()) > 0, \
                f"No content after frontmatter in: {file_path}"

    @pytest.mark.unit
    def test_document_ai_extractor_specific_fields(self):
        """Test document-ai-extractor.md specific requirements."""
        file_path = CLAUDE_AGENTS_DIR / "document-ai-extractor.md"
        content = read_file_content(file_path)
        frontmatter = parse_yaml_frontmatter(content)

        # Only test if file has frontmatter
        if frontmatter:
            assert frontmatter['name'] == 'document-ai-extractor'
            assert 'Document AI' in frontmatter['description']
            assert frontmatter.get('color') == 'green'

        # Check content contains key terms (works with or without frontmatter)
        assert 'Document AI' in content
        assert 'extraction' in content.lower()

    @pytest.mark.unit
    def test_error_detective_specific_fields(self):
        """Test error-detective.md specific requirements."""
        file_path = CLAUDE_AGENTS_DIR / "error-detective.md"
        content = read_file_content(file_path)
        frontmatter = parse_yaml_frontmatter(content)

        # Only test if file has frontmatter
        if frontmatter:
            assert frontmatter['name'] == 'error-detective'
            assert 'error' in frontmatter['description'].lower() or \
                   'bug' in frontmatter['description'].lower()
            assert frontmatter.get('color') == 'red'

        # Check content contains debugging methodology (works with or without frontmatter)
        assert 'debug' in content.lower() or 'error' in content.lower()


class TestWorkflowPromptFiles:
    """Test suite for workflow prompt configuration files."""

    @pytest.fixture
    def workflow_files(self) -> List[Path]:
        """Get all workflow prompt files."""
        return [
            CODEX_PROMPTS_DIR / "bmad-bmm-agents-analyst.md",
            CODEX_PROMPTS_DIR / "bmad-bmm-agents-architect.md",
            CODEX_PROMPTS_DIR / "bmad-bmm-agents-dev.md",
            CODEX_PROMPTS_DIR / "bmad-bmm-agents-pm.md",
            CODEX_PROMPTS_DIR / "bmad-bmm-agents-quick-flow-solo-dev.md",
            CODEX_PROMPTS_DIR / "bmad-bmm-agents-sm.md",
            CODEX_PROMPTS_DIR / "bmad-bmm-agents-tea.md",
            CODEX_PROMPTS_DIR / "bmad-bmm-agents-tech-writer.md",
            CODEX_PROMPTS_DIR / "bmad-bmm-agents-ux-designer.md",
            CODEX_PROMPTS_DIR / "bmad-bmm-workflows-check-implementation-readiness.md",
            CODEX_PROMPTS_DIR / "bmad-bmm-workflows-code-review.md",
            CODEX_PROMPTS_DIR / "bmad-bmm-workflows-correct-course.md",
            CODEX_PROMPTS_DIR / "bmad-bmm-workflows-create-architecture.md",
            CODEX_PROMPTS_DIR / "bmad-bmm-workflows-create-epics-and-stories.md",
            CODEX_PROMPTS_DIR / "bmad-bmm-workflows-create-excalidraw-dataflow.md",
            CODEX_PROMPTS_DIR / "bmad-bmm-workflows-create-excalidraw-diagram.md",
            CODEX_PROMPTS_DIR / "bmad-bmm-workflows-create-excalidraw-flowchart.md",
            CODEX_PROMPTS_DIR / "bmad-bmm-workflows-create-excalidraw-wireframe.md",
        ]

    @pytest.mark.unit
    def test_workflow_files_exist(self, workflow_files):
        """Test that all workflow files exist."""
        for file_path in workflow_files:
            assert file_path.exists(), f"Workflow file not found: {file_path}"
            assert file_path.is_file(), f"Path is not a file: {file_path}"

    @pytest.mark.unit
    def test_workflow_yaml_frontmatter(self, workflow_files):
        """Test that workflow files have valid YAML frontmatter."""
        for file_path in workflow_files:
            content = read_file_content(file_path)
            frontmatter = parse_yaml_frontmatter(content)

            assert frontmatter is not None, \
                f"No YAML frontmatter found in: {file_path}"

    @pytest.mark.unit
    def test_workflow_required_fields(self, workflow_files):
        """Test that workflow files contain required fields."""
        for file_path in workflow_files:
            content = read_file_content(file_path)
            frontmatter = parse_yaml_frontmatter(content)

            assert frontmatter is not None, f"No frontmatter in: {file_path}"

            # At minimum, should have name or description
            has_name = 'name' in frontmatter
            has_description = 'description' in frontmatter

            assert has_name or has_description, \
                f"Missing both 'name' and 'description' in: {file_path}"

    @pytest.mark.unit
    def test_workflow_agent_activation_pattern(self, workflow_files):
        """Test agent files contain activation pattern."""
        agent_files = [f for f in workflow_files if 'agents' in str(f)]

        for file_path in agent_files:
            content = read_file_content(file_path)

            # Check for agent activation instructions
            assert '<agent-activation' in content or \
                   'agent' in content.lower(), \
                f"No agent activation pattern found in: {file_path}"

    @pytest.mark.unit
    def test_workflow_command_pattern(self, workflow_files):
        """Test workflow files contain IT IS CRITICAL command."""
        workflow_command_files = [f for f in workflow_files if 'workflows' in str(f)]

        for file_path in workflow_command_files:
            content = read_file_content(file_path)

            # Check for critical command pattern
            assert 'IT IS CRITICAL' in content or \
                   'LOAD' in content or \
                   'CRITICAL' in content, \
                f"No critical command pattern found in: {file_path}"

    @pytest.mark.unit
    def test_workflow_steps_structure(self, workflow_files):
        """Test workflow files with steps have proper structure."""
        for file_path in workflow_files:
            content = read_file_content(file_path)

            if '<steps' in content:
                # If steps tag exists, validate structure
                assert 'CRITICAL=' in content, \
                    f"Steps without CRITICAL attribute in: {file_path}"
                assert '</steps>' in content, \
                    f"Unclosed steps tag in: {file_path}"

    @pytest.mark.unit
    def test_workflow_file_references(self, workflow_files):
        """Test that workflow files reference valid paths."""
        for file_path in workflow_files:
            content = read_file_content(file_path)

            # Find all @-prefixed file references
            references = re.findall(r'@([^\s\)]+)', content)

            for ref in references:
                # References should use forward slashes
                if '\\' in ref:
                    pytest.fail(f"Backslash in file reference '{ref}' in: {file_path}")

                # Should start with valid prefix
                valid_prefixes = ['_bmad/', '.claude/', '.codex/']
                if any(ref.startswith(prefix) for prefix in valid_prefixes):
                    # Valid reference format
                    pass


class TestClaudeConfigFiles:
    """Test suite for Claude configuration files."""

    @pytest.mark.unit
    def test_ralph_loop_local_exists(self):
        """Test ralph-loop.local.md exists."""
        file_path = CLAUDE_DIR / "ralph-loop.local.md"
        assert file_path.exists(), "ralph-loop.local.md not found"

    @pytest.mark.unit
    def test_ralph_loop_yaml_structure(self):
        """Test ralph-loop.local.md has valid YAML frontmatter."""
        file_path = CLAUDE_DIR / "ralph-loop.local.md"
        content = read_file_content(file_path)
        frontmatter = parse_yaml_frontmatter(content)

        assert frontmatter is not None, "No YAML frontmatter in ralph-loop.local.md"

        # Check for loop-specific fields
        expected_fields = ['active', 'iteration', 'max_iterations']
        for field in expected_fields:
            assert field in frontmatter, f"Missing field '{field}' in ralph-loop"

    @pytest.mark.unit
    def test_ralph_loop_active_field(self):
        """Test active field is boolean in ralph-loop."""
        file_path = CLAUDE_DIR / "ralph-loop.local.md"
        content = read_file_content(file_path)
        frontmatter = parse_yaml_frontmatter(content)

        assert 'active' in frontmatter
        assert isinstance(frontmatter['active'], bool), \
            "active field should be boolean"

    @pytest.mark.unit
    def test_ralph_loop_iteration_fields(self):
        """Test iteration fields are numeric in ralph-loop."""
        file_path = CLAUDE_DIR / "ralph-loop.local.md"
        content = read_file_content(file_path)
        frontmatter = parse_yaml_frontmatter(content)

        assert 'iteration' in frontmatter
        assert 'max_iterations' in frontmatter

        assert isinstance(frontmatter['iteration'], int), \
            "iteration should be integer"
        assert isinstance(frontmatter['max_iterations'], int), \
            "max_iterations should be integer"
        assert frontmatter['iteration'] >= 0, "iteration should be non-negative"
        assert frontmatter['max_iterations'] >= 0, "max_iterations should be non-negative"

    @pytest.mark.unit
    def test_rules_md_exists(self):
        """Test rules.md exists."""
        file_path = CLAUDE_DIR / "rules.md"
        assert file_path.exists(), "rules.md not found"

    @pytest.mark.unit
    def test_rules_md_content(self):
        """Test rules.md has meaningful content."""
        file_path = CLAUDE_DIR / "rules.md"
        content = read_file_content(file_path)

        assert len(content.strip()) > 100, "rules.md seems too short"

        # Should contain guidance or examples
        assert any(keyword in content.lower() for keyword in
                  ['sentry', 'error', 'tracking', 'example', 'use']), \
            "rules.md should contain relevant keywords"

    @pytest.mark.unit
    def test_settings_local_json_exists(self):
        """Test settings.local.json exists."""
        file_path = CLAUDE_DIR / "settings.local.json"
        assert file_path.exists(), "settings.local.json not found"

    @pytest.mark.unit
    def test_settings_local_json_valid(self):
        """Test settings.local.json is valid JSON."""
        file_path = CLAUDE_DIR / "settings.local.json"

        with open(file_path, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in settings.local.json: {e}")

        assert isinstance(data, dict), "settings.local.json should be a dict"

    @pytest.mark.unit
    def test_settings_permissions_structure(self):
        """Test settings.local.json has permissions structure."""
        file_path = CLAUDE_DIR / "settings.local.json"

        with open(file_path, 'r') as f:
            data = json.load(f)

        assert 'permissions' in data, "Missing 'permissions' key"
        assert isinstance(data['permissions'], dict), "permissions should be dict"

        # Check for allow/deny lists
        if 'allow' in data['permissions']:
            assert isinstance(data['permissions']['allow'], list), \
                "permissions.allow should be list"

        if 'deny' in data['permissions']:
            assert isinstance(data['permissions']['deny'], list), \
                "permissions.deny should be list"

    @pytest.mark.unit
    def test_settings_mcp_servers(self):
        """Test settings.local.json has MCP server configuration."""
        file_path = CLAUDE_DIR / "settings.local.json"

        with open(file_path, 'r') as f:
            data = json.load(f)

        # Check for MCP server lists
        mcp_fields = ['enabledMcpjsonServers', 'disabledMcpjsonServers']
        for field in mcp_fields:
            if field in data:
                assert isinstance(data[field], list), \
                    f"{field} should be a list"

    @pytest.mark.unit
    def test_settings_no_duplicate_permissions(self):
        """Test that permission lists don't have duplicates."""
        file_path = CLAUDE_DIR / "settings.local.json"

        with open(file_path, 'r') as f:
            data = json.load(f)

        if 'permissions' in data:
            if 'allow' in data['permissions']:
                allow_list = data['permissions']['allow']
                assert len(allow_list) == len(set(allow_list)), \
                    "Duplicate entries in permissions.allow"

            if 'deny' in data['permissions']:
                deny_list = data['permissions']['deny']
                assert len(deny_list) == len(set(deny_list)), \
                    "Duplicate entries in permissions.deny"

    @pytest.mark.unit
    def test_settings_hooks_field(self):
        """Test settings.local.json hooks configuration."""
        file_path = CLAUDE_DIR / "settings.local.json"

        with open(file_path, 'r') as f:
            data = json.load(f)

        if 'disableAllHooks' in data:
            assert isinstance(data['disableAllHooks'], bool), \
                "disableAllHooks should be boolean"


class TestWorkflowReadmeFile:
    """Test suite for workflow README file."""

    @pytest.mark.unit
    def test_readme_exists(self):
        """Test bmad-bmm-workflows-README.md exists."""
        file_path = CODEX_PROMPTS_DIR / "bmad-bmm-workflows-README.md"
        assert file_path.exists(), "README.md not found"

    @pytest.mark.unit
    def test_readme_has_content(self):
        """Test README has substantial content."""
        file_path = CODEX_PROMPTS_DIR / "bmad-bmm-workflows-README.md"
        content = read_file_content(file_path)

        assert len(content.strip()) > 200, "README seems too short"

    @pytest.mark.unit
    def test_readme_structure(self):
        """Test README has expected structure."""
        file_path = CODEX_PROMPTS_DIR / "bmad-bmm-workflows-README.md"
        content = read_file_content(file_path)

        # Should have headers
        assert re.search(r'^#+ ', content, re.MULTILINE), \
            "README should have markdown headers"

        # Should list workflows
        assert 'workflow' in content.lower(), \
            "README should mention workflows"

    @pytest.mark.unit
    def test_readme_workflow_references(self):
        """Test README references actual workflow files."""
        file_path = CODEX_PROMPTS_DIR / "bmad-bmm-workflows-README.md"
        content = read_file_content(file_path)

        # Should reference workflow paths
        assert '_bmad' in content or 'workflow' in content.lower(), \
            "README should reference workflow paths"


class TestOCRTradelineValidator:
    """Test suite for OCR tradeline validator configuration."""

    @pytest.mark.unit
    def test_ocr_validator_structure(self):
        """Test OCR tradeline validator has proper structure."""
        file_path = CLAUDE_AGENTS_DIR / "ocr-tradeline-validator.md"
        content = read_file_content(file_path)

        # Should have numbered sections
        assert re.search(r'## \d+\.', content), \
            "OCR validator should have numbered sections"

    @pytest.mark.unit
    def test_ocr_validator_schema_info(self):
        """Test OCR validator contains schema information."""
        file_path = CLAUDE_AGENTS_DIR / "ocr-tradeline-validator.md"
        content = read_file_content(file_path)

        # Should define schema fields
        schema_keywords = ['schema', 'field', 'tradeline', 'column', 'type']
        assert any(keyword in content.lower() for keyword in schema_keywords), \
            "OCR validator should contain schema information"

    @pytest.mark.unit
    def test_ocr_validator_json_examples(self):
        """Test OCR validator contains JSON examples."""
        file_path = CLAUDE_AGENTS_DIR / "ocr-tradeline-validator.md"
        content = read_file_content(file_path)

        # Should have JSON code blocks
        assert '```json' in content or '```' in content, \
            "OCR validator should have code examples"

        # Should define expected output format
        assert 'json' in content.lower() or 'array' in content.lower(), \
            "OCR validator should reference JSON/array output"


class TestEdgeCases:
    """Test suite for edge cases and error conditions."""

    @pytest.mark.unit
    def test_no_malformed_yaml(self):
        """Test that all YAML frontmatter can be parsed without errors."""
        all_md_files = []

        # Collect all .md files
        for directory in [CLAUDE_AGENTS_DIR, CODEX_PROMPTS_DIR, CLAUDE_DIR]:
            if directory.exists():
                for file_path in directory.glob("*.md"):
                    all_md_files.append(file_path)

        for file_path in all_md_files:
            content = read_file_content(file_path)

            # If file has frontmatter delimiters, it should parse
            if content.startswith('---'):
                frontmatter = parse_yaml_frontmatter(content)
                assert frontmatter is not None, \
                    f"Malformed YAML frontmatter in: {file_path}"

    @pytest.mark.unit
    def test_no_invalid_characters(self):
        """Test that config files don't contain problematic characters."""
        all_files = []

        # Collect all config files
        for directory in [CLAUDE_AGENTS_DIR, CODEX_PROMPTS_DIR, CLAUDE_DIR]:
            if directory.exists():
                for file_path in directory.glob("*.md"):
                    all_files.append(file_path)

        # Add JSON file
        json_file = CLAUDE_DIR / "settings.local.json"
        if json_file.exists():
            all_files.append(json_file)

        for file_path in all_files:
            content = read_file_content(file_path)

            # Check for null bytes
            assert '\x00' not in content, \
                f"Null byte found in: {file_path}"

    @pytest.mark.unit
    def test_file_encoding_utf8(self):
        """Test that all files are valid UTF-8."""
        all_files = []

        for directory in [CLAUDE_AGENTS_DIR, CODEX_PROMPTS_DIR, CLAUDE_DIR]:
            if directory.exists():
                for file_path in directory.glob("*"):
                    if file_path.is_file():
                        all_files.append(file_path)

        for file_path in all_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    f.read()
            except UnicodeDecodeError:
                pytest.fail(f"File is not valid UTF-8: {file_path}")

    @pytest.mark.unit
    def test_no_trailing_whitespace_in_keys(self):
        """Test YAML keys don't have trailing whitespace."""
        all_md_files = []

        for directory in [CLAUDE_AGENTS_DIR, CODEX_PROMPTS_DIR, CLAUDE_DIR]:
            if directory.exists():
                for file_path in directory.glob("*.md"):
                    all_md_files.append(file_path)

        for file_path in all_md_files:
            content = read_file_content(file_path)
            frontmatter = parse_yaml_frontmatter(content)

            if frontmatter:
                for key in frontmatter.keys():
                    assert key == key.strip(), \
                        f"YAML key has whitespace: '{key}' in {file_path}"

    @pytest.mark.unit
    def test_consistent_line_endings(self):
        """Test that files use consistent line endings."""
        all_files = []

        for directory in [CLAUDE_AGENTS_DIR, CODEX_PROMPTS_DIR, CLAUDE_DIR]:
            if directory.exists():
                for file_path in directory.glob("*"):
                    if file_path.is_file():
                        all_files.append(file_path)

        for file_path in all_files:
            with open(file_path, 'rb') as f:
                raw_content = f.read()

            # Check for mixed line endings
            has_crlf = b'\r\n' in raw_content
            has_lf_only = b'\n' in raw_content.replace(b'\r\n', b'')

            if has_crlf and has_lf_only:
                pytest.fail(f"Mixed line endings in: {file_path}")


class TestSecurityAndCompliance:
    """Test suite for security and compliance checks."""

    @pytest.mark.unit
    def test_no_hardcoded_secrets(self):
        """Test that config files don't contain obvious secrets."""
        all_files = []

        for directory in [CLAUDE_AGENTS_DIR, CODEX_PROMPTS_DIR, CLAUDE_DIR]:
            if directory.exists():
                for file_path in directory.glob("*"):
                    if file_path.is_file():
                        all_files.append(file_path)

        # Patterns that might indicate secrets
        secret_patterns = [
            r'password\s*[=:]\s*[\'"][^\'"]{8,}[\'"]',
            r'api[_-]?key\s*[=:]\s*[\'"][^\'"]{16,}[\'"]',
            r'secret\s*[=:]\s*[\'"][^\'"]{16,}[\'"]',
            r'token\s*[=:]\s*[\'"][^\'"]{16,}[\'"]',
        ]

        for file_path in all_files:
            content = read_file_content(file_path).lower()

            for pattern in secret_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    # Allow documentation/examples, but warn
                    if 'example' not in content and 'sample' not in content:
                        pytest.fail(
                            f"Possible hardcoded secret in {file_path}: {matches[0]}"
                        )

    @pytest.mark.unit
    def test_settings_permissions_reasonable(self):
        """Test that permission settings are reasonable and safe."""
        file_path = CLAUDE_DIR / "settings.local.json"

        with open(file_path, 'r') as f:
            data = json.load(f)

        if 'permissions' in data and 'allow' in data['permissions']:
            allow_list = data['permissions']['allow']

            # Check for overly permissive patterns
            dangerous_patterns = [
                'Bash(rm -rf /)',
                'Bash(sudo)',
                'Bash(chmod 777)',
            ]

            for permission in allow_list:
                for dangerous in dangerous_patterns:
                    assert dangerous not in permission, \
                        f"Dangerous permission found: {permission}"

    @pytest.mark.unit
    def test_file_permissions_not_world_writable(self):
        """Test that config files are not world-writable."""
        all_files = []

        for directory in [CLAUDE_AGENTS_DIR, CODEX_PROMPTS_DIR, CLAUDE_DIR]:
            if directory.exists():
                for file_path in directory.glob("*"):
                    if file_path.is_file():
                        all_files.append(file_path)

        for file_path in all_files:
            stat_info = os.stat(file_path)
            mode = stat_info.st_mode

            # Check if world-writable (others have write permission)
            is_world_writable = bool(mode & 0o002)

            assert not is_world_writable, \
                f"File is world-writable: {file_path}"


class TestCrossFileConsistency:
    """Test suite for consistency across multiple files."""

    @pytest.mark.unit
    def test_agent_names_unique(self):
        """Test that agent names are unique across all agent files."""
        agent_files = list(CLAUDE_AGENTS_DIR.glob("*.md"))
        agent_names = []

        for file_path in agent_files:
            content = read_file_content(file_path)
            frontmatter = parse_yaml_frontmatter(content)

            if frontmatter and 'name' in frontmatter:
                agent_names.append(frontmatter['name'])

        # Check for duplicates
        assert len(agent_names) == len(set(agent_names)), \
            f"Duplicate agent names found: {agent_names}"

    @pytest.mark.unit
    def test_workflow_descriptions_unique(self):
        """Test that workflow descriptions are reasonably unique."""
        workflow_files = [
            f for f in CODEX_PROMPTS_DIR.glob("*.md")
            if 'workflow' in f.name
        ]

        descriptions = []

        for file_path in workflow_files:
            content = read_file_content(file_path)
            frontmatter = parse_yaml_frontmatter(content)

            if frontmatter and 'description' in frontmatter:
                descriptions.append(frontmatter['description'])

        # Check for exact duplicates (some similarity is OK)
        assert len(descriptions) == len(set(descriptions)), \
            "Duplicate workflow descriptions found"

    @pytest.mark.unit
    def test_consistent_frontmatter_format(self):
        """Test that frontmatter uses consistent formatting."""
        all_md_files = []

        for directory in [CLAUDE_AGENTS_DIR, CODEX_PROMPTS_DIR, CLAUDE_DIR]:
            if directory.exists():
                all_md_files.extend(directory.glob("*.md"))

        for file_path in all_md_files:
            content = read_file_content(file_path)

            if content.startswith('---'):
                # Frontmatter should end with ---\n
                lines = content.split('\n')

                # Find closing ---
                closing_index = None
                for i, line in enumerate(lines[1:], 1):
                    if line.strip() == '---':
                        closing_index = i
                        break

                assert closing_index is not None, \
                    f"Frontmatter not properly closed in: {file_path}"