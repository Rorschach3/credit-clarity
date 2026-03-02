"""Tests for .claude/rules.md and ralph-loop.local.md validation."""
import re
import pytest
from pathlib import Path
from typing import List, Dict, Any


def parse_yaml_frontmatter(content: str) -> Dict[str, Any]:
    """Parse YAML frontmatter from markdown content."""
    frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.match(frontmatter_pattern, content, re.DOTALL)

    if not match:
        return {}

    frontmatter_text = match.group(1)
    # Simple YAML parser for our needs
    frontmatter = {}
    for line in frontmatter_text.strip().split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()

            # Handle quoted strings
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]

            # Try to parse as number
            try:
                if '.' in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                # Handle booleans
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                elif value.lower() == 'null':
                    value = None

            frontmatter[key] = value

    return frontmatter


def extract_code_blocks(content: str) -> List[tuple]:
    """Extract code blocks from markdown with language tags."""
    code_block_pattern = r'```(\w+)?\n(.*?)```'
    matches = re.findall(code_block_pattern, content, re.DOTALL)
    return matches


class TestClaudeRules:
    """Test suite for Claude rules.md file."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent.parent

    @pytest.fixture
    def rules_file(self, project_root):
        """Get rules file path."""
        return project_root / ".claude" / "rules.md"

    @pytest.fixture
    def rules_content(self, rules_file):
        """Load rules file content."""
        if not rules_file.exists():
            pytest.skip(f"Rules file not found: {rules_file}")
        return rules_file.read_text()

    def test_rules_file_exists(self, rules_file):
        """Test that rules.md exists."""
        assert rules_file.exists(), "rules.md not found"

    def test_rules_has_content(self, rules_content):
        """Test that rules file has substantial content."""
        assert len(rules_content) > 100, "Rules file is too short"

    def test_rules_has_sentry_examples(self, rules_content):
        """Test that rules contain Sentry usage examples."""
        assert "Sentry" in rules_content, "Missing Sentry references"
        assert "import" in rules_content.lower(), "Missing import examples"

    def test_rules_code_blocks_are_valid(self, rules_content):
        """Test that code blocks in rules are properly formatted."""
        code_blocks = extract_code_blocks(rules_content)

        # Should have some code examples
        assert len(code_blocks) > 0, "No code examples found in rules"

        for lang, code in code_blocks:
            # Code block should not be empty
            assert len(code.strip()) > 0, "Empty code block found"

            # If language specified, should be reasonable
            if lang:
                valid_languages = {'javascript', 'typescript', 'python', 'js', 'ts', 'jsx', 'tsx', 'json', 'yaml'}
                assert lang.lower() in valid_languages, f"Unusual language tag: {lang}"

    def test_rules_has_error_tracking_section(self, rules_content):
        """Test that rules include error/exception tracking guidance."""
        content_lower = rules_content.lower()

        assert any(term in content_lower for term in ['error', 'exception', 'tracking']), \
            "Missing error tracking section"

        # Should mention captureException
        assert "captureException" in rules_content or "capture" in content_lower, \
            "Missing exception capture examples"

    def test_rules_has_tracing_examples(self, rules_content):
        """Test that rules include tracing examples."""
        content_lower = rules_content.lower()

        assert "tracing" in content_lower or "span" in content_lower, \
            "Missing tracing section"

        # Should have span-related content
        assert "span" in content_lower, "Missing span examples"

    def test_rules_has_logging_examples(self, rules_content):
        """Test that rules include logging examples."""
        content_lower = rules_content.lower()

        # Should discuss logs
        assert "log" in content_lower, "Missing logging section"

        # Should have logger examples
        assert "logger" in content_lower, "Missing logger examples"

    def test_rules_sentry_init_configuration(self, rules_content):
        """Test that rules show Sentry initialization."""
        assert "Sentry.init" in rules_content, "Missing Sentry.init example"
        assert "dsn" in rules_content.lower(), "Missing DSN configuration"

    def test_rules_has_proper_sections(self, rules_content):
        """Test that rules file has proper section headers."""
        # Look for markdown headers
        headers = re.findall(r'^#+\s+(.+)$', rules_content, re.MULTILINE)

        assert len(headers) > 0, "No section headers found"

        # Should have distinct sections
        assert len(set(headers)) > 1, "Not enough variety in sections"

    def test_rules_javascript_syntax_valid(self, rules_content):
        """Test that JavaScript examples have basic syntax validity."""
        code_blocks = extract_code_blocks(rules_content)
        js_blocks = [code for lang, code in code_blocks
                     if lang and lang.lower() in {'javascript', 'js', 'jsx', 'typescript', 'ts', 'tsx'}]

        for code in js_blocks:
            # Basic syntax checks
            # Balanced braces
            open_braces = code.count('{')
            close_braces = code.count('}')
            assert open_braces == close_braces, f"Unbalanced braces in code block"

            # Balanced parentheses
            open_parens = code.count('(')
            close_parens = code.count(')')
            assert open_parens == close_parens, f"Unbalanced parentheses in code block"


class TestRalphLoopConfig:
    """Test suite for ralph-loop.local.md configuration."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent.parent

    @pytest.fixture
    def ralph_loop_file(self, project_root):
        """Get ralph-loop file path."""
        return project_root / ".claude" / "ralph-loop.local.md"

    @pytest.fixture
    def ralph_loop_content(self, ralph_loop_file):
        """Load ralph-loop file content."""
        if not ralph_loop_file.exists():
            pytest.skip(f"Ralph loop file not found: {ralph_loop_file}")
        return ralph_loop_file.read_text()

    def test_ralph_loop_file_exists(self, ralph_loop_file):
        """Test that ralph-loop.local.md exists."""
        assert ralph_loop_file.exists(), "ralph-loop.local.md not found"

    def test_ralph_loop_has_frontmatter(self, ralph_loop_content):
        """Test that ralph-loop has YAML frontmatter."""
        frontmatter = parse_yaml_frontmatter(ralph_loop_content)
        assert len(frontmatter) > 0, "Missing or empty YAML frontmatter"

    def test_ralph_loop_frontmatter_fields(self, ralph_loop_content):
        """Test that ralph-loop frontmatter has expected fields."""
        frontmatter = parse_yaml_frontmatter(ralph_loop_content)

        # Expected fields based on the file
        expected_fields = ['active', 'iteration']

        for field in expected_fields:
            assert field in frontmatter, f"Missing required field: {field}"

    def test_ralph_loop_active_is_boolean(self, ralph_loop_content):
        """Test that 'active' field is boolean."""
        frontmatter = parse_yaml_frontmatter(ralph_loop_content)

        if 'active' in frontmatter:
            assert isinstance(frontmatter['active'], bool), \
                f"'active' should be boolean, got: {type(frontmatter['active'])}"

    def test_ralph_loop_iteration_is_number(self, ralph_loop_content):
        """Test that 'iteration' field is a number."""
        frontmatter = parse_yaml_frontmatter(ralph_loop_content)

        if 'iteration' in frontmatter:
            assert isinstance(frontmatter['iteration'], (int, float)), \
                f"'iteration' should be number, got: {type(frontmatter['iteration'])}"
            assert frontmatter['iteration'] >= 0, \
                "'iteration' should be non-negative"

    def test_ralph_loop_has_command_content(self, ralph_loop_content):
        """Test that ralph-loop contains command-like content."""
        # After frontmatter, should have command parameters
        body_pattern = r'^---\s*\n.*?\n---\s*\n(.+)$'
        match = re.search(body_pattern, ralph_loop_content, re.DOTALL)

        if match:
            body = match.group(1).strip()
            assert len(body) > 50, "Command content too short"

            # Should contain typical command flags
            assert '--' in body, "Missing command flags"

    def test_ralph_loop_command_structure(self, ralph_loop_content):
        """Test that ralph-loop command has proper structure."""
        # Check for common command patterns
        assert '--input' in ralph_loop_content or '--output' in ralph_loop_content, \
            "Missing input/output parameters"

    def test_ralph_loop_has_goal_or_constraints(self, ralph_loop_content):
        """Test that ralph-loop specifies goals or constraints."""
        assert '--goal' in ralph_loop_content or '--constraint' in ralph_loop_content, \
            "Missing goal or constraint specification"

    def test_ralph_loop_max_iterations_valid(self, ralph_loop_content):
        """Test that max_iterations if present is valid."""
        frontmatter = parse_yaml_frontmatter(ralph_loop_content)

        if 'max_iterations' in frontmatter:
            max_iter = frontmatter['max_iterations']
            assert isinstance(max_iter, (int, float)), \
                f"max_iterations should be number, got: {type(max_iter)}"
            assert max_iter >= 0, "max_iterations should be non-negative"

    def test_ralph_loop_pipeline_specification(self, ralph_loop_content):
        """Test that ralph-loop specifies a pipeline."""
        # Should mention pipeline or steps
        assert '--pipeline' in ralph_loop_content or 'pipeline' in ralph_loop_content.lower(), \
            "Missing pipeline specification"

    def test_ralph_loop_has_ocr_or_extraction_config(self, ralph_loop_content):
        """Test that ralph-loop contains OCR or extraction configuration."""
        content_lower = ralph_loop_content.lower()

        # Should reference OCR, extraction, or processing
        assert any(term in content_lower for term in ['ocr', 'extract', 'process', 'parse']), \
            "Missing OCR/extraction references"

    def test_ralph_loop_tradeline_schema(self, ralph_loop_content):
        """Test that ralph-loop references tradeline schema."""
        content_lower = ralph_loop_content.lower()

        # Should mention tradelines since it's about credit report processing
        assert 'tradeline' in content_lower, "Missing tradeline references"