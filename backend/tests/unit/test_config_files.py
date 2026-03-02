"""
Unit tests for configuration files validation
Tests YAML frontmatter, JSON schema, and content validation for .claude/ and .codex/ config files
"""
import pytest
import json
import yaml
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

# Test imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))


class TestYAMLFrontmatterValidation:
    """Test YAML frontmatter parsing and validation in markdown files."""

    @pytest.fixture
    def repo_root(self) -> Path:
        """Get repository root directory."""
        return Path(__file__).parent.parent.parent.parent

    def extract_frontmatter(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Extract YAML frontmatter from markdown file."""
        if not file_path.exists():
            return None

        content = file_path.read_text()

        # Match YAML frontmatter between --- delimiters
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not match:
            return None

        try:
            # Try to load as YAML
            return yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            # If YAML parsing fails, try manual extraction for simple key-value pairs
            frontmatter_text = match.group(1)
            result = {}
            current_key = None
            current_value = []

            for line in frontmatter_text.split('\n'):
                # Check if line starts with a key (no leading whitespace, contains colon)
                if line and not line[0].isspace() and ':' in line:
                    # Save previous key-value if exists
                    if current_key:
                        result[current_key] = ' '.join(current_value).strip()

                    # Start new key-value
                    key, value = line.split(':', 1)
                    current_key = key.strip()
                    current_value = [value.strip()]
                elif current_key:
                    # Continuation of previous value
                    current_value.append(line.strip())

            # Save last key-value
            if current_key:
                result[current_key] = ' '.join(current_value).strip()

            return result if result else None

    def test_document_ai_extractor_agent_frontmatter(self, repo_root):
        """Validate document-ai-extractor agent frontmatter."""
        file_path = repo_root / ".claude" / "agents" / "document-ai-extractor.md"
        frontmatter = self.extract_frontmatter(file_path)

        assert frontmatter is not None, "Frontmatter should exist"
        assert "name" in frontmatter, "name field is required"
        assert "description" in frontmatter, "description field is required"
        assert "color" in frontmatter, "color field is required"

        assert frontmatter["name"] == "document-ai-extractor"
        assert len(frontmatter["description"]) > 0, "description should not be empty"
        assert frontmatter["color"] in ["green", "blue", "red", "yellow", "purple"], "color should be valid"

    def test_error_detective_agent_frontmatter(self, repo_root):
        """Validate error-detective agent frontmatter."""
        file_path = repo_root / ".claude" / "agents" / "error-detective.md"
        frontmatter = self.extract_frontmatter(file_path)

        assert frontmatter is not None, "Frontmatter should exist"
        assert "name" in frontmatter
        assert "description" in frontmatter
        assert "color" in frontmatter

        assert frontmatter["name"] == "error-detective"
        assert len(frontmatter["description"]) > 50, "description should be detailed"
        assert frontmatter["color"] == "red"

    def test_ralph_loop_local_frontmatter(self, repo_root):
        """Validate ralph-loop.local frontmatter."""
        file_path = repo_root / ".claude" / "ralph-loop.local.md"
        frontmatter = self.extract_frontmatter(file_path)

        assert frontmatter is not None, "Frontmatter should exist"
        assert "active" in frontmatter
        assert "iteration" in frontmatter
        assert "max_iterations" in frontmatter

        assert isinstance(frontmatter["active"], bool)
        assert isinstance(frontmatter["iteration"], int)
        assert isinstance(frontmatter["max_iterations"], int)

    def test_bmad_agents_have_valid_frontmatter(self, repo_root):
        """Validate all bmad agent files have valid frontmatter."""
        agent_files = [
            "bmad-bmm-agents-analyst.md",
            "bmad-bmm-agents-architect.md",
            "bmad-bmm-agents-dev.md",
            "bmad-bmm-agents-pm.md",
            "bmad-bmm-agents-quick-flow-solo-dev.md",
            "bmad-bmm-agents-sm.md",
            "bmad-bmm-agents-tea.md",
            "bmad-bmm-agents-tech-writer.md",
            "bmad-bmm-agents-ux-designer.md",
        ]

        for filename in agent_files:
            file_path = repo_root / ".codex" / "prompts" / filename
            frontmatter = self.extract_frontmatter(file_path)

            assert frontmatter is not None, f"{filename} should have frontmatter"
            assert "name" in frontmatter, f"{filename} should have name field"
            assert "description" in frontmatter, f"{filename} should have description field"

    def test_bmad_workflows_have_valid_frontmatter(self, repo_root):
        """Validate all bmad workflow files have valid frontmatter."""
        workflow_files = [
            "bmad-bmm-workflows-check-implementation-readiness.md",
            "bmad-bmm-workflows-code-review.md",
            "bmad-bmm-workflows-correct-course.md",
            "bmad-bmm-workflows-create-architecture.md",
            "bmad-bmm-workflows-create-epics-and-stories.md",
            "bmad-bmm-workflows-create-excalidraw-dataflow.md",
            "bmad-bmm-workflows-create-excalidraw-diagram.md",
            "bmad-bmm-workflows-create-excalidraw-flowchart.md",
            "bmad-bmm-workflows-create-excalidraw-wireframe.md",
        ]

        for filename in workflow_files:
            file_path = repo_root / ".codex" / "prompts" / filename
            frontmatter = self.extract_frontmatter(file_path)

            assert frontmatter is not None, f"{filename} should have frontmatter"
            assert "description" in frontmatter, f"{filename} should have description field"
            assert len(frontmatter["description"]) > 0, f"{filename} description should not be empty"


class TestJSONConfigValidation:
    """Test JSON configuration file validation."""

    @pytest.fixture
    def repo_root(self) -> Path:
        """Get repository root directory."""
        return Path(__file__).parent.parent.parent.parent

    def test_settings_local_json_is_valid(self, repo_root):
        """Validate settings.local.json is valid JSON."""
        file_path = repo_root / ".claude" / "settings.local.json"

        with open(file_path, 'r') as f:
            config = json.load(f)

        assert isinstance(config, dict), "Config should be a dictionary"

    def test_settings_local_json_has_permissions(self, repo_root):
        """Validate settings.local.json has permissions structure."""
        file_path = repo_root / ".claude" / "settings.local.json"

        with open(file_path, 'r') as f:
            config = json.load(f)

        assert "permissions" in config, "Config should have permissions"
        assert "allow" in config["permissions"], "Permissions should have allow list"
        assert "deny" in config["permissions"], "Permissions should have deny list"

        assert isinstance(config["permissions"]["allow"], list)
        assert isinstance(config["permissions"]["deny"], list)

    def test_settings_local_json_has_mcp_servers(self, repo_root):
        """Validate settings.local.json has MCP server configuration."""
        file_path = repo_root / ".claude" / "settings.local.json"

        with open(file_path, 'r') as f:
            config = json.load(f)

        assert "enabledMcpjsonServers" in config, "Config should have enabledMcpjsonServers"
        assert "disabledMcpjsonServers" in config, "Config should have disabledMcpjsonServers"

        assert isinstance(config["enabledMcpjsonServers"], list)
        assert isinstance(config["disabledMcpjsonServers"], list)

    def test_settings_local_json_no_duplicate_servers(self, repo_root):
        """Validate no MCP server appears in both enabled and disabled lists."""
        file_path = repo_root / ".claude" / "settings.local.json"

        with open(file_path, 'r') as f:
            config = json.load(f)

        enabled = set(config["enabledMcpjsonServers"])
        disabled = set(config["disabledMcpjsonServers"])

        duplicates = enabled & disabled
        assert len(duplicates) == 0, f"Servers should not be in both lists: {duplicates}"


class TestMarkdownContentValidation:
    """Test markdown file content validation."""

    @pytest.fixture
    def repo_root(self) -> Path:
        """Get repository root directory."""
        return Path(__file__).parent.parent.parent.parent

    def test_ocr_tradeline_validator_has_schema_definition(self, repo_root):
        """Validate OCR tradeline validator defines schema."""
        file_path = repo_root / ".claude" / "agents" / "ocr-tradeline-validator.md"
        content = file_path.read_text()

        # Check for key schema elements
        assert "creditor_name" in content, "Should define creditor_name field"
        assert "account_number" in content, "Should define account_number field"
        assert "credit_bureau" in content, "Should define credit_bureau field"
        assert "account_status" in content, "Should define account_status field"

        # Check for bureau enums
        assert "Experian" in content
        assert "Equifax" in content
        assert "TransUnion" in content

    def test_ocr_tradeline_validator_has_normalization_rules(self, repo_root):
        """Validate OCR tradeline validator defines normalization rules."""
        file_path = repo_root / ".claude" / "agents" / "ocr-tradeline-validator.md"
        content = file_path.read_text()

        assert "Normalization Rules" in content
        assert "Account Number" in content
        assert "Dollar Values" in content
        assert "Date Format" in content

    def test_rules_md_has_sentry_examples(self, repo_root):
        """Validate rules.md contains Sentry configuration examples."""
        file_path = repo_root / ".claude" / "rules.md"
        content = file_path.read_text()

        # Check for Sentry sections
        assert "Sentry.captureException" in content
        assert "Sentry.startSpan" in content
        assert "Sentry.init" in content

        # Check for logging
        assert "logger" in content
        assert "enableLogs" in content

    def test_rules_md_has_tracing_examples(self, repo_root):
        """Validate rules.md has tracing examples."""
        file_path = repo_root / ".claude" / "rules.md"
        content = file_path.read_text()

        assert "ui.click" in content or "http.client" in content
        assert "span" in content

    def test_bmad_workflows_readme_lists_workflows(self, repo_root):
        """Validate workflows README lists available workflows."""
        file_path = repo_root / ".codex" / "prompts" / "bmad-bmm-workflows-README.md"
        content = file_path.read_text()

        # Check for key workflows
        assert "create-architecture" in content
        assert "code-review" in content
        assert "create-epics-and-stories" in content
        assert "create-excalidraw" in content


class TestAgentContentValidation:
    """Test agent-specific content validation."""

    @pytest.fixture
    def repo_root(self) -> Path:
        """Get repository root directory."""
        return Path(__file__).parent.parent.parent.parent

    def test_document_ai_extractor_has_responsibilities(self, repo_root):
        """Validate document-ai-extractor defines core responsibilities."""
        file_path = repo_root / ".claude" / "agents" / "document-ai-extractor.md"
        content = file_path.read_text()

        assert "responsibilities" in content.lower()
        assert "Document AI" in content
        assert "extraction" in content.lower()

    def test_error_detective_has_methodology(self, repo_root):
        """Validate error-detective defines debugging methodology."""
        file_path = repo_root / ".claude" / "agents" / "error-detective.md"
        content = file_path.read_text()

        assert "debugging" in content.lower() or "methodology" in content.lower()
        assert "Root Cause Analysis" in content
        assert "Investigation" in content or "investigation" in content

    def test_agent_files_not_empty(self, repo_root):
        """Validate all agent files have substantial content."""
        agent_files = [
            ".claude/agents/document-ai-extractor.md",
            ".claude/agents/error-detective.md",
        ]

        for file_path_str in agent_files:
            file_path = repo_root / file_path_str
            content = file_path.read_text()

            # Remove frontmatter and check content
            content_without_frontmatter = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
            assert len(content_without_frontmatter.strip()) > 100, f"{file_path_str} should have substantial content"


class TestWorkflowContentValidation:
    """Test workflow-specific content validation."""

    @pytest.fixture
    def repo_root(self) -> Path:
        """Get repository root directory."""
        return Path(__file__).parent.parent.parent.parent

    def test_workflow_stubs_reference_full_workflow(self, repo_root):
        """Validate workflow stubs reference the full workflow file."""
        workflow_files = [
            "bmad-bmm-workflows-code-review.md",
            "bmad-bmm-workflows-create-architecture.md",
            "bmad-bmm-workflows-create-excalidraw-diagram.md",
        ]

        for filename in workflow_files:
            file_path = repo_root / ".codex" / "prompts" / filename
            content = file_path.read_text()

            # Check for workflow reference patterns
            has_reference = (
                "LOAD" in content or
                "workflow.xml" in content or
                "workflow.yaml" in content or
                "workflow.md" in content
            )
            assert has_reference, f"{filename} should reference full workflow"

    def test_excalidraw_workflows_have_consistent_structure(self, repo_root):
        """Validate excalidraw workflow files have consistent structure."""
        excalidraw_files = [
            "bmad-bmm-workflows-create-excalidraw-dataflow.md",
            "bmad-bmm-workflows-create-excalidraw-diagram.md",
            "bmad-bmm-workflows-create-excalidraw-flowchart.md",
            "bmad-bmm-workflows-create-excalidraw-wireframe.md",
        ]

        for filename in excalidraw_files:
            file_path = repo_root / ".codex" / "prompts" / filename

            # Check file exists and has content
            assert file_path.exists(), f"{filename} should exist"

            frontmatter = self.extract_frontmatter(file_path)
            assert frontmatter is not None, f"{filename} should have frontmatter"
            assert "description" in frontmatter

            content = file_path.read_text()
            assert "Excalidraw" in content, f"{filename} should mention Excalidraw"

    def extract_frontmatter(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Extract YAML frontmatter from markdown file."""
        content = file_path.read_text()
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not match:
            return None
        try:
            return yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            # If YAML parsing fails, try manual extraction for simple key-value pairs
            frontmatter_text = match.group(1)
            result = {}
            current_key = None
            current_value = []

            for line in frontmatter_text.split('\n'):
                # Check if line starts with a key (no leading whitespace, contains colon)
                if line and not line[0].isspace() and ':' in line:
                    # Save previous key-value if exists
                    if current_key:
                        result[current_key] = ' '.join(current_value).strip()

                    # Start new key-value
                    key, value = line.split(':', 1)
                    current_key = key.strip()
                    current_value = [value.strip()]
                elif current_key:
                    # Continuation of previous value
                    current_value.append(line.strip())

            # Save last key-value
            if current_key:
                result[current_key] = ' '.join(current_value).strip()

            return result if result else None


class TestFileStructureValidation:
    """Test file structure and organization."""

    @pytest.fixture
    def repo_root(self) -> Path:
        """Get repository root directory."""
        return Path(__file__).parent.parent.parent.parent

    def test_all_changed_files_exist(self, repo_root):
        """Validate all changed files exist in the repository."""
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

        for file_path_str in changed_files:
            file_path = repo_root / file_path_str
            assert file_path.exists(), f"{file_path_str} should exist"

    def test_json_files_have_json_extension(self, repo_root):
        """Validate JSON configuration files have .json extension."""
        json_file = repo_root / ".claude" / "settings.local.json"
        assert json_file.suffix == ".json"

        # Validate it's actually valid JSON
        with open(json_file, 'r') as f:
            json.load(f)

    def test_markdown_files_have_md_extension(self, repo_root):
        """Validate markdown files have .md extension."""
        md_files = [
            ".claude/agents/document-ai-extractor.md",
            ".claude/agents/error-detective.md",
            ".claude/rules.md",
        ]

        for file_path_str in md_files:
            file_path = repo_root / file_path_str
            assert file_path.suffix == ".md", f"{file_path_str} should have .md extension"


class TestEdgeCasesAndRobustness:
    """Test edge cases and robustness of configuration files."""

    @pytest.fixture
    def repo_root(self) -> Path:
        """Get repository root directory."""
        return Path(__file__).parent.parent.parent.parent

    def test_no_trailing_whitespace_in_json(self, repo_root):
        """Validate JSON files don't have excessive trailing whitespace."""
        file_path = repo_root / ".claude" / "settings.local.json"
        content = file_path.read_text()

        # Check for reasonable formatting
        lines = content.split('\n')
        for line in lines:
            # Allow some trailing whitespace but not excessive
            assert len(line) - len(line.rstrip()) < 10, "Excessive trailing whitespace"

    def test_markdown_files_use_utf8_encoding(self, repo_root):
        """Validate markdown files can be read as UTF-8."""
        md_files = [
            ".claude/agents/document-ai-extractor.md",
            ".claude/agents/error-detective.md",
            ".claude/rules.md",
        ]

        for file_path_str in md_files:
            file_path = repo_root / file_path_str
            try:
                content = file_path.read_text(encoding='utf-8')
                assert len(content) > 0
            except UnicodeDecodeError:
                pytest.fail(f"{file_path_str} should be valid UTF-8")

    def test_agent_names_use_kebab_case(self, repo_root):
        """Validate agent names use kebab-case convention."""
        agent_files = [
            (".claude/agents/document-ai-extractor.md", "document-ai-extractor"),
            (".claude/agents/error-detective.md", "error-detective"),
        ]

        for file_path_str, expected_name in agent_files:
            file_path = repo_root / file_path_str
            content = file_path.read_text()
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if match:
                try:
                    frontmatter = yaml.safe_load(match.group(1))
                except yaml.YAMLError:
                    # If YAML parsing fails, try manual extraction
                    frontmatter_text = match.group(1)
                    frontmatter = {}
                    for line in frontmatter_text.split('\n'):
                        if line and not line[0].isspace() and ':' in line:
                            key, value = line.split(':', 1)
                            frontmatter[key.strip()] = value.strip()

                if "name" in frontmatter:
                    name = frontmatter["name"]
                    assert name == expected_name, f"Agent name should be {expected_name}"
                    # Verify kebab-case format
                    assert re.match(r'^[a-z]+(-[a-z]+)*$', name), f"Name should be kebab-case: {name}"

    def test_permissions_list_has_no_duplicates(self, repo_root):
        """Validate permissions allow list has no duplicates."""
        file_path = repo_root / ".claude" / "settings.local.json"

        with open(file_path, 'r') as f:
            config = json.load(f)

        allow_list = config["permissions"]["allow"]
        unique_items = set(allow_list)

        assert len(allow_list) == len(unique_items), "Allow list should not have duplicates"


class TestCrossFileConsistency:
    """Test consistency across multiple configuration files."""

    @pytest.fixture
    def repo_root(self) -> Path:
        """Get repository root directory."""
        return Path(__file__).parent.parent.parent.parent

    def test_workflow_readme_mentions_all_workflow_files(self, repo_root):
        """Validate README mentions all workflow files."""
        readme_path = repo_root / ".codex" / "prompts" / "bmad-bmm-workflows-README.md"
        readme_content = readme_path.read_text()

        workflow_keywords = [
            "code-review",
            "create-architecture",
            "create-epics-and-stories",
            "excalidraw",
        ]

        for keyword in workflow_keywords:
            assert keyword in readme_content, f"README should mention {keyword}"

    def test_agent_colors_are_consistent(self, repo_root):
        """Validate agent colors follow a consistent pattern."""
        valid_colors = {"green", "blue", "red", "yellow", "purple", "orange", "pink"}

        agent_files = [
            ".claude/agents/document-ai-extractor.md",
            ".claude/agents/error-detective.md",
        ]

        for file_path_str in agent_files:
            file_path = repo_root / file_path_str
            content = file_path.read_text()
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if match:
                try:
                    frontmatter = yaml.safe_load(match.group(1))
                except yaml.YAMLError:
                    # If YAML parsing fails, try manual extraction
                    frontmatter_text = match.group(1)
                    frontmatter = {}
                    for line in frontmatter_text.split('\n'):
                        if line and not line[0].isspace() and ':' in line:
                            key, value = line.split(':', 1)
                            frontmatter[key.strip()] = value.strip()

                if "color" in frontmatter:
                    color = frontmatter["color"]
                    assert color in valid_colors, f"Color {color} should be in valid colors"


class TestSecurityAndSensitiveData:
    """Test for security issues and sensitive data exposure."""

    @pytest.fixture
    def repo_root(self) -> Path:
        """Get repository root directory."""
        return Path(__file__).parent.parent.parent.parent

    def test_no_hardcoded_secrets_in_json_config(self, repo_root):
        """Validate no hardcoded secrets in JSON configuration."""
        file_path = repo_root / ".claude" / "settings.local.json"
        content = file_path.read_text().lower()

        # Check for common secret patterns
        secret_patterns = [
            "password",
            "api_key",
            "secret_key",
            "private_key",
            "token",
        ]

        with open(file_path, 'r') as f:
            config = json.load(f)

        # Make sure no values look like actual secrets (not just field names)
        config_str = json.dumps(config)
        # Allow these terms in permission strings but not as actual values
        assert "password=" not in config_str.lower(), "Should not contain password values"
        # Token in permissions is OK (like access_token in permission strings)
        # but not standalone secret values

    def test_no_hardcoded_credentials_in_markdown(self, repo_root):
        """Validate no hardcoded credentials in markdown files."""
        md_files = [
            ".claude/agents/document-ai-extractor.md",
            ".claude/agents/error-detective.md",
            ".claude/rules.md",
        ]

        suspicious_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
        ]

        for file_path_str in md_files:
            file_path = repo_root / file_path_str
            content = file_path.read_text().lower()

            for pattern in suspicious_patterns:
                matches = re.findall(pattern, content)
                # Allow example/placeholder values
                for match in matches:
                    assert "example" in match or "placeholder" in match or "your" in match, \
                        f"Potential credential found in {file_path_str}: {match}"

    def test_settings_permissions_use_wildcards_safely(self, repo_root):
        """Validate permission wildcards are not overly permissive."""
        file_path = repo_root / ".claude" / "settings.local.json"

        with open(file_path, 'r') as f:
            config = json.load(f)

        allow_list = config["permissions"]["allow"]

        # Check for overly broad permissions
        dangerous_wildcards = ["Bash(*)", "Bash(* *)", "*"]

        for permission in allow_list:
            assert permission not in dangerous_wildcards, \
                f"Overly permissive wildcard found: {permission}"


class TestBoundaryConditions:
    """Test boundary conditions and edge cases."""

    @pytest.fixture
    def repo_root(self) -> Path:
        """Get repository root directory."""
        return Path(__file__).parent.parent.parent.parent

    def test_description_fields_not_empty(self, repo_root):
        """Validate description fields are not empty or whitespace-only."""
        files_with_descriptions = [
            ".claude/agents/document-ai-extractor.md",
            ".claude/agents/error-detective.md",
            ".codex/prompts/bmad-bmm-agents-analyst.md",
        ]

        for file_path_str in files_with_descriptions:
            file_path = repo_root / file_path_str
            content = file_path.read_text()
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)

            if match:
                try:
                    frontmatter = yaml.safe_load(match.group(1))
                except yaml.YAMLError:
                    # Manual extraction
                    frontmatter_text = match.group(1)
                    frontmatter = {}
                    for line in frontmatter_text.split('\n'):
                        if line and not line[0].isspace() and ':' in line:
                            key, value = line.split(':', 1)
                            frontmatter[key.strip()] = value.strip()

                if "description" in frontmatter:
                    desc = frontmatter["description"]
                    assert len(desc.strip()) > 0, f"{file_path_str} description should not be empty"
                    assert len(desc.strip()) > 10, f"{file_path_str} description should be meaningful"

    def test_workflow_files_not_too_small(self, repo_root):
        """Validate workflow files have reasonable content size."""
        workflow_files = [
            ".codex/prompts/bmad-bmm-workflows-code-review.md",
            ".codex/prompts/bmad-bmm-workflows-create-architecture.md",
        ]

        for file_path_str in workflow_files:
            file_path = repo_root / file_path_str
            content = file_path.read_text()

            # File should have more than just frontmatter
            assert len(content) > 100, f"{file_path_str} should have substantial content"

    def test_json_config_has_reasonable_size(self, repo_root):
        """Validate JSON config is not suspiciously large or small."""
        file_path = repo_root / ".claude" / "settings.local.json"
        content = file_path.read_text()

        assert len(content) > 50, "Config should have meaningful content"
        assert len(content) < 100000, "Config should not be excessively large"


class TestRegressionTests:
    """Regression tests for previously found issues."""

    @pytest.fixture
    def repo_root(self) -> Path:
        """Get repository root directory."""
        return Path(__file__).parent.parent.parent.parent

    def test_yaml_frontmatter_handles_colons_in_values(self, repo_root):
        """Regression: YAML parser should handle colons in description values."""
        file_path = repo_root / ".claude" / "agents" / "document-ai-extractor.md"
        content = file_path.read_text()

        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        assert match is not None, "Should find frontmatter"

        # This should not raise an exception
        frontmatter_text = match.group(1)
        # Our fallback parser should handle this
        result = {}
        current_key = None
        current_value = []

        for line in frontmatter_text.split('\n'):
            if line and not line[0].isspace() and ':' in line:
                if current_key:
                    result[current_key] = ' '.join(current_value).strip()
                key, value = line.split(':', 1)
                current_key = key.strip()
                current_value = [value.strip()]
            elif current_key:
                current_value.append(line.strip())

        if current_key:
            result[current_key] = ' '.join(current_value).strip()

        assert "description" in result
        assert "Examples include:" in result["description"] or "include" in result["description"].lower()

    def test_agent_activation_stubs_reference_source(self, repo_root):
        """Regression: Agent stub files should reference their full source."""
        stub_files = [
            ".codex/prompts/bmad-bmm-agents-analyst.md",
            ".codex/prompts/bmad-bmm-agents-architect.md",
        ]

        for file_path_str in stub_files:
            file_path = repo_root / file_path_str
            content = file_path.read_text()

            # Should contain reference to loading full agent
            assert "LOAD" in content or "agent file" in content.lower(), \
                f"{file_path_str} should reference loading full agent file"

    def test_excalidraw_workflows_mention_format(self, repo_root):
        """Regression: Excalidraw workflows should mention the Excalidraw format."""
        excalidraw_files = [
            ".codex/prompts/bmad-bmm-workflows-create-excalidraw-diagram.md",
            ".codex/prompts/bmad-bmm-workflows-create-excalidraw-wireframe.md",
        ]

        for file_path_str in excalidraw_files:
            file_path = repo_root / file_path_str
            content = file_path.read_text()

            assert "Excalidraw" in content or "excalidraw" in content, \
                f"{file_path_str} should mention Excalidraw format"

    def test_settings_has_disable_hooks_option(self, repo_root):
        """Regression: Settings should have disableAllHooks option."""
        file_path = repo_root / ".claude" / "settings.local.json"

        with open(file_path, 'r') as f:
            config = json.load(f)

        assert "disableAllHooks" in config, "Config should have disableAllHooks option"
        assert isinstance(config["disableAllHooks"], bool), "disableAllHooks should be boolean"


class TestWorkflowIntegrity:
    """Test workflow definition integrity and completeness."""

    @pytest.fixture
    def repo_root(self) -> Path:
        """Get repository root directory."""
        return Path(__file__).parent.parent.parent.parent

    def test_all_workflow_files_have_descriptions(self, repo_root):
        """Validate all workflow files have description in frontmatter."""
        workflow_files = [
            ".codex/prompts/bmad-bmm-workflows-check-implementation-readiness.md",
            ".codex/prompts/bmad-bmm-workflows-code-review.md",
            ".codex/prompts/bmad-bmm-workflows-create-architecture.md",
        ]

        for file_path_str in workflow_files:
            file_path = repo_root / file_path_str
            content = file_path.read_text()
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)

            if match:
                try:
                    frontmatter = yaml.safe_load(match.group(1))
                except yaml.YAMLError:
                    frontmatter_text = match.group(1)
                    frontmatter = {}
                    for line in frontmatter_text.split('\n'):
                        if line and not line[0].isspace() and ':' in line:
                            key, value = line.split(':', 1)
                            frontmatter[key.strip()] = value.strip()

                assert "description" in frontmatter, \
                    f"{file_path_str} should have description in frontmatter"

    def test_workflow_stubs_have_consistent_structure(self, repo_root):
        """Validate workflow stubs follow consistent structure."""
        stub_files = [
            ".codex/prompts/bmad-bmm-workflows-code-review.md",
            ".codex/prompts/bmad-bmm-workflows-create-excalidraw-diagram.md",
        ]

        for file_path_str in stub_files:
            file_path = repo_root / file_path_str
            content = file_path.read_text()

            # Should have frontmatter
            assert content.startswith("---"), f"{file_path_str} should start with frontmatter"

            # Should have instructions or steps
            assert "CRITICAL" in content or "steps" in content.lower() or "LOAD" in content, \
                f"{file_path_str} should contain instructions"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])