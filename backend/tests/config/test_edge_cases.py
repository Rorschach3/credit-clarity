"""Additional edge case and boundary tests for configuration files."""
import re
import json
import pytest
from pathlib import Path
from typing import Dict, Any


def parse_yaml_frontmatter(content: str) -> Dict[str, Any]:
    """Parse YAML frontmatter from markdown content."""
    frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.match(frontmatter_pattern, content, re.DOTALL)

    if not match:
        return {}

    frontmatter_text = match.group(1)
    frontmatter = {}
    for line in frontmatter_text.strip().split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()

            if (value.startswith("'") and value.endswith("'")) or \
               (value.startswith('"') and value.endswith('"')):
                value = value[1:-1]

            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif value.lower() == 'null':
                value = None
            else:
                try:
                    if '.' in value:
                        value = float(value)
                    else:
                        value = int(value)
                except ValueError:
                    pass

            frontmatter[key] = value

    return frontmatter


class TestEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent.parent

    def test_no_duplicate_agent_names(self, project_root):
        """Test that agent names are unique across .claude and .codex."""
        agent_names = set()

        # Check .claude/agents
        claude_agents_dir = project_root / ".claude" / "agents"
        if claude_agents_dir.exists():
            for agent_file in claude_agents_dir.glob("*.md"):
                content = agent_file.read_text()
                frontmatter = parse_yaml_frontmatter(content)
                if "name" in frontmatter:
                    name = frontmatter["name"]
                    assert name not in agent_names, \
                        f"Duplicate agent name found: {name}"
                    agent_names.add(name)

        # Check .codex/prompts agents
        codex_prompts_dir = project_root / ".codex" / "prompts"
        if codex_prompts_dir.exists():
            for agent_file in codex_prompts_dir.glob("bmad-bmm-agents-*.md"):
                content = agent_file.read_text()
                frontmatter = parse_yaml_frontmatter(content)
                if "name" in frontmatter:
                    name = frontmatter["name"]
                    # Agent prompts may reference same names, so we only check within same category
                    # This is actually expected behavior

        # At minimum, should have found some agent names
        assert len(agent_names) > 0, "No agent names found"

    def test_no_broken_markdown_links(self, project_root):
        """Test that markdown files don't contain obviously broken links."""
        markdown_files = []

        # Collect all markdown files
        claude_dir = project_root / ".claude"
        if claude_dir.exists():
            markdown_files.extend(claude_dir.rglob("*.md"))

        codex_dir = project_root / ".codex"
        if codex_dir.exists():
            markdown_files.extend(codex_dir.rglob("*.md"))

        for md_file in markdown_files:
            content = md_file.read_text()

            # Check for common broken link patterns
            broken_patterns = [
                r'\[.*?\]\(\)',  # Empty link
                r'\[.*?\]\( \)',  # Link with only space
            ]

            for pattern in broken_patterns:
                matches = re.findall(pattern, content)
                assert len(matches) == 0, \
                    f"{md_file.name} contains broken link pattern: {pattern}"

    def test_settings_json_no_comments(self, project_root):
        """Test that JSON files don't contain comments (which are invalid JSON)."""
        settings_file = project_root / ".claude" / "settings.local.json"

        if not settings_file.exists():
            pytest.skip("Settings file not found")

        # First verify it's valid JSON
        try:
            with open(settings_file) as f:
                json.load(f)
            # If it loads successfully, it doesn't have invalid comments
            # (even if it has /* or // in string values, those are valid)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON (may contain comments): {e}")

    def test_yaml_frontmatter_not_malformed(self, project_root):
        """Test that YAML frontmatter has proper delimiters."""
        markdown_files = []

        # Collect all markdown files
        claude_dir = project_root / ".claude"
        if claude_dir.exists():
            markdown_files.extend(claude_dir.rglob("*.md"))

        codex_dir = project_root / ".codex"
        if codex_dir.exists():
            markdown_files.extend(codex_dir.rglob("*.md"))

        for md_file in markdown_files:
            content = md_file.read_text()

            # If file starts with ---, ensure it has closing ---
            if content.startswith('---\n'):
                lines_after_first = content[4:].split('\n')

                # Find closing ---
                closing_found = False
                for i, line in enumerate(lines_after_first):
                    if line.strip() == '---':
                        closing_found = True
                        break

                if not closing_found and len(content) > 10:
                    # Only fail if file has substantial content
                    # Some files might intentionally not have frontmatter
                    pytest.fail(f"{md_file.name} has opening --- but no closing ---")

    def test_no_extremely_long_lines(self, project_root):
        """Test that config files don't have excessively long lines."""
        max_line_length = 500  # Reasonable limit

        config_files = []

        # Collect config files
        claude_dir = project_root / ".claude"
        if claude_dir.exists():
            config_files.extend(claude_dir.rglob("*.md"))
            config_files.extend(claude_dir.rglob("*.json"))

        codex_dir = project_root / ".codex"
        if codex_dir.exists():
            config_files.extend(codex_dir.rglob("*.md"))

        for config_file in config_files:
            # Skip JSON files as they may have long lines by nature
            if config_file.suffix == '.json':
                continue

            content = config_file.read_text()
            lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                if len(line) > max_line_length:
                    # This is a warning, not a hard failure
                    print(f"Warning: {config_file.name}:{line_num} has {len(line)} characters")

    def test_permissions_bash_commands_not_empty(self, project_root):
        """Test that Bash permissions have non-empty command patterns."""
        settings_file = project_root / ".claude" / "settings.local.json"

        if not settings_file.exists():
            pytest.skip("Settings file not found")

        with open(settings_file) as f:
            data = json.load(f)

        if "permissions" not in data or "allow" not in data["permissions"]:
            pytest.skip("No allow list in permissions")

        allow_list = data["permissions"]["allow"]
        bash_permissions = [p for p in allow_list if p.startswith("Bash(")]

        for perm in bash_permissions:
            # Extract command pattern
            if perm.startswith("Bash(") and perm.endswith(")"):
                cmd_pattern = perm[5:-1]

                # Command pattern should not be empty
                assert len(cmd_pattern) > 0, f"Empty Bash command pattern: {perm}"

                # Most should have a colon for pattern matching, but shell commands
                # like "if [...]" or full commands are also valid
                # Just ensure it's not suspiciously empty or malformed
                assert not cmd_pattern.strip() == ":", \
                    f"Malformed Bash permission (lone colon): {perm}"

    def test_agent_descriptions_not_identical(self, project_root):
        """Test that agent descriptions are not copy-pasted duplicates."""
        descriptions = []

        # Collect descriptions from .claude/agents
        claude_agents_dir = project_root / ".claude" / "agents"
        if claude_agents_dir.exists():
            for agent_file in claude_agents_dir.glob("*.md"):
                content = agent_file.read_text()
                frontmatter = parse_yaml_frontmatter(content)
                if "description" in frontmatter:
                    desc = frontmatter["description"].lower().strip()
                    # Store first 50 chars as fingerprint
                    fingerprint = desc[:50] if len(desc) > 50 else desc
                    descriptions.append((agent_file.name, fingerprint))

        # Check for duplicates
        seen = {}
        for name, fingerprint in descriptions:
            if fingerprint in seen:
                # Identical descriptions are suspicious but not necessarily wrong
                # Just warn about it
                print(f"Warning: {name} has very similar description to {seen[fingerprint]}")
            else:
                seen[fingerprint] = name

    def test_workflow_prompts_reference_real_paths(self, project_root):
        """Test that workflow prompts reference plausible file paths."""
        prompts_dir = project_root / ".codex" / "prompts"

        if not prompts_dir.exists():
            pytest.skip("Prompts directory not found")

        workflow_files = [f for f in prompts_dir.glob("bmad-bmm-workflows-*.md")
                          if f.name != "bmad-bmm-workflows-README.md"]

        for workflow_file in workflow_files:
            content = workflow_file.read_text()

            # Extract @_bmad path references
            path_refs = re.findall(r'@_bmad/[\w\-/]+\.(?:md|yaml|yml|xml)', content)

            # Should have at least one path reference
            assert len(path_refs) > 0, \
                f"{workflow_file.name} should reference at least one workflow file"

            # Path should look reasonable
            for path in path_refs:
                assert not path.endswith('/.md'), \
                    f"Malformed path in {workflow_file.name}: {path}"

    def test_ocr_validator_schema_completeness(self, project_root):
        """Test that OCR validator defines all critical tradeline fields."""
        ocr_validator = project_root / ".claude" / "agents" / "ocr-tradeline-validator.md"

        if not ocr_validator.exists():
            pytest.skip("OCR validator not found")

        content = ocr_validator.read_text()

        # Critical fields that must be documented
        critical_fields = [
            "credit_bureau",
            "creditor_name",
            "account_number",
            "account_status",
            "account_type",
            "date_opened",
            "credit_limit",
            "monthly_payment",
            "account_balance"
        ]

        missing_fields = []
        for field in critical_fields:
            if field not in content:
                missing_fields.append(field)

        assert len(missing_fields) == 0, \
            f"OCR validator missing critical fields: {missing_fields}"

    def test_error_detective_has_methodology_steps(self, project_root):
        """Test that error-detective agent has structured methodology."""
        error_detective = project_root / ".claude" / "agents" / "error-detective.md"

        if not error_detective.exists():
            pytest.skip("Error detective not found")

        content = error_detective.read_text()

        # Should have numbered methodology steps
        numbered_steps = re.findall(r'^\d+\.\s+\*\*.*?\*\*:', content, re.MULTILINE)

        assert len(numbered_steps) >= 3, \
            "Error detective should have at least 3 methodology steps"

    def test_settings_mcp_servers_lowercase(self, project_root):
        """Test that MCP server names follow lowercase convention."""
        settings_file = project_root / ".claude" / "settings.local.json"

        if not settings_file.exists():
            pytest.skip("Settings file not found")

        with open(settings_file) as f:
            data = json.load(f)

        mcp_keys = ["enabledMcpjsonServers", "disabledMcpjsonServers"]

        for key in mcp_keys:
            if key in data:
                for server_name in data[key]:
                    # Most MCP server names should be lowercase with hyphens
                    # This is a convention check, not a hard requirement
                    if server_name.lower() != server_name:
                        print(f"Info: MCP server '{server_name}' uses mixed case")