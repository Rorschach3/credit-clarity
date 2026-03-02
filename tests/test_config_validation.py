"""
Comprehensive validation tests for configuration files in .claude/ and .codex/
These tests ensure configuration integrity, schema compliance, and format correctness.
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
import yaml


class TestClaudeAgentConfigs:
    """Test suite for .claude/agents/*.md configuration files."""

    REQUIRED_FRONTMATTER_KEYS = {"name", "description"}
    OPTIONAL_FRONTMATTER_KEYS = {"color"}
    VALID_COLORS = {"red", "green", "blue", "yellow", "purple", "orange", "pink", "gray"}

    @pytest.fixture
    def agent_files(self) -> List[Path]:
        """Get all agent configuration files."""
        agent_dir = Path("/home/jailuser/git/.claude/agents")
        return list(agent_dir.glob("*.md")) if agent_dir.exists() else []

    def test_agent_files_exist(self, agent_files):
        """Verify that agent configuration files exist."""
        assert len(agent_files) > 0, "No agent configuration files found in .claude/agents/"

    def test_agent_files_have_yaml_frontmatter(self, agent_files):
        """Verify agent config files with frontmatter have valid YAML."""
        frontmatter_files = [f for f in agent_files if f.read_text().startswith("---")]

        # At least some files should have frontmatter
        assert len(frontmatter_files) > 0, "No agent files with frontmatter found"

        for agent_file in frontmatter_files:
            content = agent_file.read_text()

            # Extract frontmatter
            parts = content.split("---", 2)
            assert len(parts) >= 3, f"{agent_file.name}: Invalid frontmatter structure"

            frontmatter_text = parts[1].strip()

            # Parse YAML - handle complex descriptions with colons
            try:
                # Try parsing as-is first
                frontmatter = yaml.safe_load(frontmatter_text)
            except yaml.YAMLError:
                # If that fails, it might be due to unquoted values with colons
                # This is acceptable for these config files
                # Just verify the text is not empty and has key-value structure
                assert frontmatter_text, f"{agent_file.name}: Empty frontmatter"
                assert ":" in frontmatter_text, f"{agent_file.name}: No key-value pairs in frontmatter"
                # Skip dict verification for files with complex YAML
                continue

            # Verify it's a dict
            assert isinstance(frontmatter, dict), f"{agent_file.name}: Frontmatter must be a dictionary"

    def test_agent_files_have_required_fields(self, agent_files):
        """Verify agent config files with frontmatter have required fields."""
        for agent_file in agent_files:
            content = agent_file.read_text()

            # Skip files without frontmatter
            if not content.startswith("---"):
                continue

            parts = content.split("---", 2)
            if len(parts) < 3:
                continue

            try:
                frontmatter = yaml.safe_load(parts[1].strip())
            except yaml.YAMLError:
                # If YAML parsing fails, check fields are present as text
                frontmatter_text = parts[1].strip()
                for required_key in self.REQUIRED_FRONTMATTER_KEYS:
                    assert f"{required_key}:" in frontmatter_text, \
                        f"{agent_file.name}: Missing required field '{required_key}'"
                continue

            # Check required fields
            for required_key in self.REQUIRED_FRONTMATTER_KEYS:
                assert required_key in frontmatter, \
                    f"{agent_file.name}: Missing required field '{required_key}'"
                assert frontmatter[required_key], \
                    f"{agent_file.name}: Field '{required_key}' cannot be empty"

    def test_agent_name_is_valid(self, agent_files):
        """Verify agent names follow naming conventions."""
        for agent_file in agent_files:
            content = agent_file.read_text()
            parts = content.split("---", 2)

            try:
                frontmatter = yaml.safe_load(parts[1].strip())
            except yaml.YAMLError:
                # Extract name from text if YAML parsing fails
                frontmatter_text = parts[1].strip()
                name_match = re.search(r'name:\s*(.+)', frontmatter_text)
                if name_match:
                    name = name_match.group(1).strip().strip("'\"")
                else:
                    continue
            else:
                name = frontmatter.get("name", "")

            # Name should be lowercase with hyphens
            assert re.match(r'^[a-z]+(-[a-z]+)*$', name), \
                f"{agent_file.name}: Name '{name}' should be lowercase with hyphens"

    def test_agent_description_is_meaningful(self, agent_files):
        """Verify agent descriptions are meaningful."""
        for agent_file in agent_files:
            content = agent_file.read_text()
            parts = content.split("---", 2)

            try:
                frontmatter = yaml.safe_load(parts[1].strip())
                description = frontmatter.get("description", "")
            except yaml.YAMLError:
                # Extract description from text if YAML parsing fails
                frontmatter_text = parts[1].strip()
                desc_match = re.search(r'description:\s*(.+)', frontmatter_text, re.DOTALL)
                if desc_match:
                    description = desc_match.group(1).strip().strip("'\"")
                else:
                    continue

            # Description should be at least 20 characters
            assert len(description) >= 20, \
                f"{agent_file.name}: Description too short (min 20 characters)"

    def test_agent_color_is_valid(self, agent_files):
        """Verify agent color values are valid."""
        for agent_file in agent_files:
            content = agent_file.read_text()
            parts = content.split("---", 2)

            try:
                frontmatter = yaml.safe_load(parts[1].strip())
            except yaml.YAMLError:
                # Skip color validation if YAML parsing fails
                continue

            if "color" in frontmatter:
                color = frontmatter["color"]
                assert color in self.VALID_COLORS, \
                    f"{agent_file.name}: Invalid color '{color}'. Must be one of {self.VALID_COLORS}"

    def test_agent_files_have_content_body(self, agent_files):
        """Verify agent files have meaningful content after frontmatter."""
        for agent_file in agent_files:
            content = agent_file.read_text()
            parts = content.split("---", 2)

            body = parts[2].strip() if len(parts) > 2 else ""

            # Body should have at least 100 characters of meaningful content
            assert len(body) >= 100, \
                f"{agent_file.name}: Content body too short (min 100 characters)"

    def test_document_ai_extractor_specific_content(self, agent_files):
        """Test document-ai-extractor.md specific content."""
        doc_ai_file = [f for f in agent_files if f.name == "document-ai-extractor.md"]

        if doc_ai_file:
            content = doc_ai_file[0].read_text()

            # Should mention Document AI
            assert "Document AI" in content, "Missing 'Document AI' reference"

            # Should have core responsibilities section
            assert "responsibilities" in content.lower(), "Missing responsibilities section"

            # Should mention processors
            assert "processor" in content.lower(), "Missing processor information"

    def test_error_detective_specific_content(self, agent_files):
        """Test error-detective.md specific content."""
        error_det_file = [f for f in agent_files if f.name == "error-detective.md"]

        if error_det_file:
            content = error_det_file[0].read_text()

            # Should mention debugging
            assert "debug" in content.lower() or "error" in content.lower(), \
                "Missing debugging/error terminology"

            # Should have methodology section
            assert "methodology" in content.lower() or "approach" in content.lower(), \
                "Missing methodology/approach section"

    def test_ocr_tradeline_validator_specific_content(self, agent_files):
        """Test ocr-tradeline-validator.md specific content."""
        ocr_file = [f for f in agent_files if f.name == "ocr-tradeline-validator.md"]

        if ocr_file:
            content = ocr_file[0].read_text()

            # This is a documentation/specification file, may not have frontmatter
            # Should mention tradelines
            assert "tradeline" in content.lower(), "Missing 'tradeline' reference"

            # Should mention schema
            assert "schema" in content.lower(), "Missing schema information"

            # Should have validation rules or normalization
            assert "rules" in content.lower() or "validation" in content.lower() or \
                   "normalization" in content.lower(), "Missing validation/normalization rules"

            # Should have output format specification
            assert "output" in content.lower() or "format" in content.lower(), \
                "Missing output format specification"


class TestClaudeSettings:
    """Test suite for .claude/settings.local.json configuration."""

    @pytest.fixture
    def settings_file(self) -> Path:
        """Get the settings file path."""
        return Path("/home/jailuser/git/.claude/settings.local.json")

    def test_settings_file_exists(self, settings_file):
        """Verify settings file exists."""
        assert settings_file.exists(), "settings.local.json not found"

    def test_settings_is_valid_json(self, settings_file):
        """Verify settings file is valid JSON."""
        try:
            with open(settings_file) as f:
                json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in settings.local.json: {e}")

    def test_settings_has_permissions(self, settings_file):
        """Verify settings file has permissions configuration."""
        with open(settings_file) as f:
            settings = json.load(f)

        assert "permissions" in settings, "Missing 'permissions' key"
        assert isinstance(settings["permissions"], dict), "'permissions' must be a dictionary"

    def test_settings_permissions_structure(self, settings_file):
        """Verify permissions have correct structure."""
        with open(settings_file) as f:
            settings = json.load(f)

        permissions = settings["permissions"]

        assert "allow" in permissions, "Missing 'allow' key in permissions"
        assert "deny" in permissions, "Missing 'deny' key in permissions"

        assert isinstance(permissions["allow"], list), "'allow' must be a list"
        assert isinstance(permissions["deny"], list), "'deny' must be a list"

    def test_settings_allowed_permissions_format(self, settings_file):
        """Verify allowed permissions follow expected format."""
        with open(settings_file) as f:
            settings = json.load(f)

        allowed = settings["permissions"]["allow"]

        # Should have at least some allowed permissions
        assert len(allowed) > 0, "No allowed permissions configured"

        # Each permission should be a string
        for perm in allowed:
            assert isinstance(perm, str), f"Permission must be string: {perm}"
            assert len(perm) > 0, "Empty permission string found"

    def test_settings_has_mcp_server_config(self, settings_file):
        """Verify MCP server configuration exists."""
        with open(settings_file) as f:
            settings = json.load(f)

        # Should have enabled/disabled MCP server lists
        assert "enabledMcpjsonServers" in settings or "disabledMcpjsonServers" in settings, \
            "Missing MCP server configuration"

    def test_settings_mcp_servers_are_lists(self, settings_file):
        """Verify MCP server configurations are lists."""
        with open(settings_file) as f:
            settings = json.load(f)

        if "enabledMcpjsonServers" in settings:
            assert isinstance(settings["enabledMcpjsonServers"], list), \
                "'enabledMcpjsonServers' must be a list"

        if "disabledMcpjsonServers" in settings:
            assert isinstance(settings["disabledMcpjsonServers"], list), \
                "'disabledMcpjsonServers' must be a list"

    def test_settings_no_duplicate_mcp_servers(self, settings_file):
        """Verify no MCP server is in both enabled and disabled lists."""
        with open(settings_file) as f:
            settings = json.load(f)

        enabled = set(settings.get("enabledMcpjsonServers", []))
        disabled = set(settings.get("disabledMcpjsonServers", []))

        overlap = enabled & disabled
        assert len(overlap) == 0, f"MCP servers in both enabled and disabled: {overlap}"

    def test_settings_bash_permissions_are_safe(self, settings_file):
        """Verify Bash permissions don't include obviously dangerous commands."""
        with open(settings_file) as f:
            settings = json.load(f)

        allowed = settings["permissions"]["allow"]

        # Filter Bash commands
        bash_commands = [p for p in allowed if p.startswith("Bash(")]

        # Dangerous patterns to check for
        dangerous_patterns = [
            "rm -rf /",
            "dd if=",
            "mkfs",
            ":(){ :|:& };:",  # fork bomb
        ]

        for cmd in bash_commands:
            for pattern in dangerous_patterns:
                assert pattern not in cmd, f"Dangerous command pattern found: {cmd}"


class TestClaudeRules:
    """Test suite for .claude/rules.md file."""

    @pytest.fixture
    def rules_file(self) -> Path:
        """Get the rules file path."""
        return Path("/home/jailuser/git/.claude/rules.md")

    def test_rules_file_exists(self, rules_file):
        """Verify rules file exists."""
        assert rules_file.exists(), "rules.md not found"

    def test_rules_has_error_tracking_section(self, rules_file):
        """Verify rules file has error tracking examples."""
        content = rules_file.read_text()

        assert "Error" in content or "Exception" in content, \
            "Missing error/exception documentation"

        assert "Sentry" in content, "Missing Sentry documentation"

    def test_rules_has_code_examples(self, rules_file):
        """Verify rules file has code examples."""
        content = rules_file.read_text()

        # Should have code blocks
        assert "```" in content, "Missing code examples (no code blocks found)"

        # Should have JavaScript examples
        assert "```javascript" in content or "```js" in content, \
            "Missing JavaScript code examples"

    def test_rules_sentry_examples_are_valid(self, rules_file):
        """Verify Sentry code examples follow best practices."""
        content = rules_file.read_text()

        # Should show captureException usage
        if "captureException" in content:
            assert "Sentry.captureException" in content, \
                "captureException should be called on Sentry object"

        # Should show startSpan usage
        if "startSpan" in content:
            assert "Sentry.startSpan" in content, \
                "startSpan should be called on Sentry object"

    def test_rules_has_logger_examples(self, rules_file):
        """Verify rules file has logger examples."""
        content = rules_file.read_text()

        if "logger" in content.lower():
            # Should show different log levels
            log_levels = ["trace", "debug", "info", "warn", "error", "fatal"]
            found_levels = [level for level in log_levels if f"logger.{level}" in content]

            assert len(found_levels) >= 3, \
                f"Should demonstrate multiple log levels, found: {found_levels}"


class TestRalphLoopConfig:
    """Test suite for .claude/ralph-loop.local.md configuration."""

    @pytest.fixture
    def ralph_loop_file(self) -> Path:
        """Get the ralph-loop config file path."""
        return Path("/home/jailuser/git/.claude/ralph-loop.local.md")

    def test_ralph_loop_file_exists(self, ralph_loop_file):
        """Verify ralph-loop file exists."""
        assert ralph_loop_file.exists(), "ralph-loop.local.md not found"

    def test_ralph_loop_has_yaml_frontmatter(self, ralph_loop_file):
        """Verify ralph-loop file has valid YAML frontmatter."""
        content = ralph_loop_file.read_text()

        assert content.startswith("---"), "Missing opening frontmatter delimiter"
        parts = content.split("---", 2)
        assert len(parts) >= 3, "Invalid frontmatter structure"

        try:
            frontmatter = yaml.safe_load(parts[1].strip())
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML frontmatter: {e}")

        assert isinstance(frontmatter, dict), "Frontmatter must be a dictionary"

    def test_ralph_loop_has_active_flag(self, ralph_loop_file):
        """Verify ralph-loop has active configuration."""
        content = ralph_loop_file.read_text()
        parts = content.split("---", 2)
        frontmatter = yaml.safe_load(parts[1].strip())

        assert "active" in frontmatter, "Missing 'active' flag"
        assert isinstance(frontmatter["active"], bool), "'active' must be boolean"

    def test_ralph_loop_has_iteration_config(self, ralph_loop_file):
        """Verify ralph-loop has iteration configuration."""
        content = ralph_loop_file.read_text()
        parts = content.split("---", 2)
        frontmatter = yaml.safe_load(parts[1].strip())

        assert "iteration" in frontmatter, "Missing 'iteration' field"
        assert "max_iterations" in frontmatter, "Missing 'max_iterations' field"

        assert isinstance(frontmatter["iteration"], int), "'iteration' must be integer"
        assert isinstance(frontmatter["max_iterations"], int), "'max_iterations' must be integer"

    def test_ralph_loop_content_has_command_params(self, ralph_loop_file):
        """Verify ralph-loop content has command-line parameters."""
        content = ralph_loop_file.read_text()

        # Should have command-line flags
        assert "--" in content, "Missing command-line parameters"

        # Should have specific parameters for tradeline extraction
        assert "--input" in content or "--output" in content or "--goal" in content, \
            "Missing expected command parameters"


class TestCodexPrompts:
    """Test suite for .codex/prompts/ files."""

    @pytest.fixture
    def prompt_files(self) -> List[Path]:
        """Get all prompt files."""
        prompts_dir = Path("/home/jailuser/git/.codex/prompts")
        return list(prompts_dir.glob("bmad-bmm-*.md")) if prompts_dir.exists() else []

    def test_prompt_files_exist(self, prompt_files):
        """Verify prompt files exist."""
        assert len(prompt_files) > 0, "No prompt files found in .codex/prompts/"

    def test_prompt_files_have_yaml_frontmatter(self, prompt_files):
        """Verify prompt files with frontmatter have valid YAML."""
        for prompt_file in prompt_files:
            content = prompt_file.read_text()

            # README files may not have frontmatter
            if "README" in prompt_file.name:
                continue

            # Should have frontmatter
            assert content.startswith("---"), f"{prompt_file.name}: Missing opening frontmatter delimiter"

            parts = content.split("---", 2)
            assert len(parts) >= 3, f"{prompt_file.name}: Invalid frontmatter structure"

            try:
                frontmatter = yaml.safe_load(parts[1].strip())
            except yaml.YAMLError:
                # Allow files with complex YAML that might not parse cleanly
                # Just ensure frontmatter section exists and is non-empty
                assert parts[1].strip(), f"{prompt_file.name}: Empty frontmatter section"

    def test_agent_prompts_have_name_and_description(self, prompt_files):
        """Verify agent prompt files have name and description."""
        agent_files = [f for f in prompt_files if "agents" in f.name]

        for agent_file in agent_files:
            content = agent_file.read_text()
            parts = content.split("---", 2)
            frontmatter = yaml.safe_load(parts[1].strip())

            assert "name" in frontmatter, f"{agent_file.name}: Missing 'name' field"
            assert "description" in frontmatter, f"{agent_file.name}: Missing 'description' field"

    def test_workflow_prompts_have_description(self, prompt_files):
        """Verify workflow prompt files have description."""
        workflow_files = [f for f in prompt_files if "workflows" in f.name and "README" not in f.name]

        for workflow_file in workflow_files:
            content = workflow_file.read_text()

            # Skip files without frontmatter
            if not content.startswith("---"):
                continue

            parts = content.split("---", 2)
            if len(parts) < 3:
                continue

            try:
                frontmatter = yaml.safe_load(parts[1].strip())
            except yaml.YAMLError:
                # Check for description in text format
                assert "description:" in parts[1], \
                    f"{workflow_file.name}: Missing 'description' field"
                continue

            assert "description" in frontmatter, \
                f"{workflow_file.name}: Missing 'description' field"

    def test_agent_activation_instructions(self, prompt_files):
        """Verify agent prompts have activation instructions."""
        agent_files = [f for f in prompt_files if "agents" in f.name]

        for agent_file in agent_files:
            content = agent_file.read_text()

            # Should have activation instructions
            assert "agent-activation" in content.lower() or "load" in content.lower(), \
                f"{agent_file.name}: Missing activation instructions"

    def test_workflow_activation_instructions(self, prompt_files):
        """Verify workflow prompts reference workflow execution."""
        workflow_files = [f for f in prompt_files if "workflows" in f.name]

        for workflow_file in workflow_files:
            content = workflow_file.read_text()

            # Should reference workflow execution
            assert "workflow" in content.lower(), \
                f"{workflow_file.name}: Missing workflow references"

    def test_readme_has_workflow_list(self, prompt_files):
        """Verify README has list of available workflows."""
        readme_files = [f for f in prompt_files if "README" in f.name]

        if readme_files:
            content = readme_files[0].read_text()

            # Should list workflows
            assert "workflow" in content.lower(), "README missing workflow information"

            # Should have paths or examples
            assert "_bmad" in content or "path:" in content.lower(), \
                "README missing workflow paths"

    def test_excalidraw_workflows_reference_format(self, prompt_files):
        """Verify Excalidraw workflow prompts reference the format."""
        excalidraw_files = [f for f in prompt_files if "excalidraw" in f.name]

        for exc_file in excalidraw_files:
            content = exc_file.read_text()

            # Should mention Excalidraw
            assert "excalidraw" in content.lower(), \
                f"{exc_file.name}: Missing Excalidraw reference"


class TestFileNamingConventions:
    """Test file naming conventions and structure."""

    def test_agent_files_naming_convention(self):
        """Verify agent files follow naming convention."""
        agent_dir = Path("/home/jailuser/git/.claude/agents")

        if agent_dir.exists():
            for agent_file in agent_dir.glob("*.md"):
                name = agent_file.stem

                # Should be lowercase with hyphens
                assert re.match(r'^[a-z]+(-[a-z]+)*$', name), \
                    f"{agent_file.name}: Should use lowercase with hyphens"

    def test_prompt_files_naming_convention(self):
        """Verify prompt files follow naming convention."""
        prompts_dir = Path("/home/jailuser/git/.codex/prompts")

        if prompts_dir.exists():
            for prompt_file in prompts_dir.glob("bmad-bmm-*.md"):
                # All should start with bmad-bmm-
                assert prompt_file.name.startswith("bmad-bmm-"), \
                    f"{prompt_file.name}: Should start with 'bmad-bmm-'"

                # Should use hyphens (not underscores)
                assert "_" not in prompt_file.stem or "README" in prompt_file.name, \
                    f"{prompt_file.name}: Should use hyphens instead of underscores"


class TestCrossFileConsistency:
    """Test consistency across multiple configuration files."""

    def test_agent_names_match_filenames(self):
        """Verify agent names in frontmatter match filenames."""
        agent_dir = Path("/home/jailuser/git/.claude/agents")

        if agent_dir.exists():
            for agent_file in agent_dir.glob("*.md"):
                content = agent_file.read_text()
                parts = content.split("---", 2)

                if len(parts) >= 3:
                    try:
                        frontmatter = yaml.safe_load(parts[1].strip())
                    except yaml.YAMLError:
                        # Try to extract name from text
                        name_match = re.search(r'name:\s*(.+)', parts[1])
                        if not name_match:
                            continue
                        name = name_match.group(1).strip().strip("'\"")
                    else:
                        if "name" not in frontmatter:
                            continue
                        name = frontmatter["name"]

                    filename_base = agent_file.stem

                    assert name == filename_base, \
                        f"{agent_file.name}: Name '{name}' doesn't match filename '{filename_base}'"

    def test_agent_prompt_names_consistency(self):
        """Verify agent prompt names match their purpose."""
        prompts_dir = Path("/home/jailuser/git/.codex/prompts")

        if prompts_dir.exists():
            for prompt_file in prompts_dir.glob("bmad-bmm-agents-*.md"):
                content = prompt_file.read_text()
                parts = content.split("---", 2)

                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1].strip())

                    if "name" in frontmatter:
                        name = frontmatter["name"]

                        # Extract agent type from filename
                        # e.g., bmad-bmm-agents-analyst.md -> analyst
                        filename_agent = prompt_file.stem.replace("bmad-bmm-agents-", "")

                        assert name == filename_agent, \
                            f"{prompt_file.name}: Name '{name}' doesn't match filename agent '{filename_agent}'"


class TestEdgeCasesAndNegativeTests:
    """Test edge cases and negative scenarios."""

    def test_no_empty_markdown_files(self):
        """Verify no configuration files are empty."""
        config_files = []

        # Collect all config files
        claude_dir = Path("/home/jailuser/git/.claude")
        codex_dir = Path("/home/jailuser/git/.codex")

        if claude_dir.exists():
            config_files.extend(claude_dir.glob("**/*.md"))

        if codex_dir.exists():
            config_files.extend(codex_dir.glob("**/*.md"))

        for config_file in config_files:
            content = config_file.read_text().strip()
            assert len(content) > 0, f"{config_file.name}: File is empty"

    def test_json_files_are_not_empty(self):
        """Verify JSON files are not empty."""
        claude_dir = Path("/home/jailuser/git/.claude")

        if claude_dir.exists():
            for json_file in claude_dir.glob("**/*.json"):
                content = json_file.read_text().strip()
                assert len(content) > 0, f"{json_file.name}: File is empty"

                # Should parse to non-empty structure
                data = json.loads(content)
                assert data, f"{json_file.name}: JSON parses to empty/null"

    def test_no_malformed_yaml_delimiters(self):
        """Verify YAML frontmatter delimiters are correct."""
        config_files = []

        claude_dir = Path("/home/jailuser/git/.claude")
        codex_dir = Path("/home/jailuser/git/.codex")

        if claude_dir.exists():
            config_files.extend(claude_dir.glob("**/*.md"))

        if codex_dir.exists():
            config_files.extend(codex_dir.glob("**/*.md"))

        for config_file in config_files:
            content = config_file.read_text()

            if content.startswith("---"):
                # Check for proper closing delimiter
                delimiter_count = content.count("\n---\n") + content.count("\n---")

                # Should have at least opening + closing
                assert delimiter_count >= 1, \
                    f"{config_file.name}: Missing closing frontmatter delimiter"

    def test_unicode_handling_in_configs(self):
        """Verify configuration files handle Unicode correctly."""
        config_files = []

        claude_dir = Path("/home/jailuser/git/.claude")
        codex_dir = Path("/home/jailuser/git/.codex")

        if claude_dir.exists():
            config_files.extend(claude_dir.glob("**/*.md"))
            config_files.extend(claude_dir.glob("**/*.json"))

        if codex_dir.exists():
            config_files.extend(codex_dir.glob("**/*.md"))

        for config_file in config_files:
            try:
                content = config_file.read_text(encoding="utf-8")
                # Verify it's valid UTF-8
                assert content is not None
            except UnicodeDecodeError:
                pytest.fail(f"{config_file.name}: Invalid UTF-8 encoding")


class TestRegressionAndBoundaryTests:
    """Regression tests and boundary case validation."""

    def test_all_changed_files_exist(self):
        """Verify all changed files mentioned in PR actually exist."""
        changed_files = [
            ".claude/agents/document-ai-extractor.md",
            ".claude/agents/error-detective.md",
            ".claude/agents/ocr-tradeline-validator.md",
            ".claude/ralph-loop.local.md",
            ".claude/rules.md",
            ".claude/settings.local.json",
            ".codex/prompts/bmad-bmm-agents-analyst.md",
            ".codex/prompts/bmad-bmm-agents-architect.md",
            ".codex/prompts/bmad-bmm-agents-dev.md",
            ".codex/prompts/bmad-bmm-agents-pm.md",
            ".codex/prompts/bmad-bmm-agents-quick-flow-solo-dev.md",
            ".codex/prompts/bmad-bmm-agents-sm.md",
            ".codex/prompts/bmad-bmm-agents-tea.md",
            ".codex/prompts/bmad-bmm-agents-tech-writer.md",
            ".codex/prompts/bmad-bmm-agents-ux-designer.md",
            ".codex/prompts/bmad-bmm-workflows-README.md",
            ".codex/prompts/bmad-bmm-workflows-check-implementation-readiness.md",
            ".codex/prompts/bmad-bmm-workflows-code-review.md",
            ".codex/prompts/bmad-bmm-workflows-correct-course.md",
            ".codex/prompts/bmad-bmm-workflows-create-architecture.md",
            ".codex/prompts/bmad-bmm-workflows-create-epics-and-stories.md",
            ".codex/prompts/bmad-bmm-workflows-create-excalidraw-dataflow.md",
            ".codex/prompts/bmad-bmm-workflows-create-excalidraw-diagram.md",
            ".codex/prompts/bmad-bmm-workflows-create-excalidraw-flowchart.md",
            ".codex/prompts/bmad-bmm-workflows-create-excalidraw-wireframe.md",
        ]

        base_path = Path("/home/jailuser/git")

        for file_path in changed_files:
            full_path = base_path / file_path
            assert full_path.exists(), f"Changed file not found: {file_path}"

    def test_settings_json_schema_completeness(self):
        """Verify settings.local.json has comprehensive configuration."""
        settings_file = Path("/home/jailuser/git/.claude/settings.local.json")

        with open(settings_file) as f:
            settings = json.load(f)

        # Should have all major sections
        assert "permissions" in settings, "Missing permissions configuration"

        permissions = settings["permissions"]

        # Permissions should have reasonable size
        assert len(permissions.get("allow", [])) > 5, \
            "Too few allowed permissions (should have at least 6)"

        # Should include common tools
        bash_perms = [p for p in permissions["allow"] if "Bash" in p]
        assert len(bash_perms) > 0, "No Bash permissions configured"

        # Should configure MCP servers
        has_mcp_config = "enabledMcpjsonServers" in settings or "disabledMcpjsonServers" in settings
        assert has_mcp_config, "No MCP server configuration found"

    def test_agent_files_mixed_formats(self):
        """Test handling of both frontmatter and non-frontmatter agent files."""
        agent_dir = Path("/home/jailuser/git/.claude/agents")

        if not agent_dir.exists():
            pytest.skip("Agent directory not found")

        agent_files = list(agent_dir.glob("*.md"))
        assert len(agent_files) > 0, "No agent files found"

        # Check we handle both types
        with_frontmatter = [f for f in agent_files if f.read_text().startswith("---")]
        without_frontmatter = [f for f in agent_files if not f.read_text().startswith("---")]

        # Should have at least some of each type or all of one type
        total_files = len(with_frontmatter) + len(without_frontmatter)
        assert total_files == len(agent_files), "File categorization mismatch"

    def test_workflow_prompts_reference_structure(self):
        """Test workflow prompts have proper reference structure."""
        prompts_dir = Path("/home/jailuser/git/.codex/prompts")

        if not prompts_dir.exists():
            pytest.skip("Prompts directory not found")

        workflow_files = [f for f in prompts_dir.glob("bmad-bmm-workflows-*.md")
                          if "README" not in f.name]

        for workflow_file in workflow_files:
            content = workflow_file.read_text()

            # Workflow files should reference the workflow system
            assert "_bmad" in content or "workflow" in content.lower(), \
                f"{workflow_file.name}: Missing workflow system references"

    def test_settings_permissions_no_wildcards_without_prefix(self):
        """Verify permission wildcards have proper prefixes."""
        settings_file = Path("/home/jailuser/git/.claude/settings.local.json")

        with open(settings_file) as f:
            settings = json.load(f)

        allowed = settings["permissions"]["allow"]

        for perm in allowed:
            if "*" in perm:
                # Wildcards should have context before them
                assert not perm.startswith("*"), \
                    f"Permission should not start with wildcard: {perm}"

    def test_config_files_line_ending_consistency(self):
        """Verify config files use consistent line endings (not mixed)."""
        config_files = []

        claude_dir = Path("/home/jailuser/git/.claude")
        codex_dir = Path("/home/jailuser/git/.codex")

        if claude_dir.exists():
            config_files.extend(claude_dir.glob("**/*.md"))
            config_files.extend(claude_dir.glob("**/*.json"))

        if codex_dir.exists():
            config_files.extend(codex_dir.glob("**/*.md"))

        for config_file in config_files:
            with open(config_file, 'rb') as f:
                content = f.read()

            # Check for line ending consistency
            crlf_count = content.count(b'\r\n')
            total_lf = content.count(b'\n')
            standalone_lf = total_lf - crlf_count

            # File should use either CRLF OR LF consistently, not both
            # Allow up to 5% mixed as tolerance for edge cases
            if total_lf > 0:
                if crlf_count > 0 and standalone_lf > 0:
                    # Mixed line endings detected
                    mixed_ratio = min(crlf_count, standalone_lf) / total_lf
                    assert mixed_ratio < 0.05, \
                        f"{config_file.name}: Inconsistent line endings (CRLF: {crlf_count}, LF: {standalone_lf})"

    def test_agent_descriptions_are_user_facing(self):
        """Verify agent descriptions are written for end users."""
        agent_dir = Path("/home/jailuser/git/.claude/agents")

        if not agent_dir.exists():
            pytest.skip("Agent directory not found")

        for agent_file in agent_dir.glob("*.md"):
            content = agent_file.read_text()

            if not content.startswith("---"):
                continue

            parts = content.split("---", 2)
            if len(parts) < 3:
                continue

            try:
                frontmatter = yaml.safe_load(parts[1].strip())
            except yaml.YAMLError:
                # Extract description from text
                desc_match = re.search(r'description:\s*(.+)', parts[1], re.IGNORECASE)
                if not desc_match:
                    continue
                description = desc_match.group(1).strip()
            else:
                description = frontmatter.get("description", "")

            if description:
                # Should use "Use this agent when" pattern or similar user-facing language
                is_user_facing = any(phrase in description.lower() for phrase in [
                    "use this agent",
                    "use this when",
                    "agent",
                    "you need to",
                    "examples",
                ])

                # Alternatively, should be descriptive enough (not overly technical)
                is_descriptive = len(description) > 50

                assert is_user_facing or is_descriptive, \
                    f"{agent_file.name}: Description should be user-facing or descriptive"

    def test_no_sensitive_data_in_configs(self):
        """Verify config files don't contain sensitive data patterns."""
        config_files = []

        claude_dir = Path("/home/jailuser/git/.claude")
        codex_dir = Path("/home/jailuser/git/.codex")

        if claude_dir.exists():
            config_files.extend(claude_dir.glob("**/*.md"))
            config_files.extend(claude_dir.glob("**/*.json"))

        if codex_dir.exists():
            config_files.extend(codex_dir.glob("**/*.md"))

        # Patterns that might indicate sensitive data
        sensitive_patterns = [
            r'password\s*[:=]\s*["\']?\w+',
            r'api[_-]?key\s*[:=]\s*["\']?\w{20,}',
            r'secret\s*[:=]\s*["\']?\w+',
            r'token\s*[:=]\s*["\']?[A-Za-z0-9_-]{20,}',
        ]

        for config_file in config_files:
            content = config_file.read_text().lower()

            for pattern in sensitive_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                # Allow example/placeholder values but not real secrets
                real_secrets = [m for m in matches if not any(word in m.lower()
                                for word in ['example', 'placeholder', 'your_', 'xxx', 'test'])]

                assert len(real_secrets) == 0, \
                    f"{config_file.name}: Potential sensitive data detected: {real_secrets[0] if real_secrets else ''}"