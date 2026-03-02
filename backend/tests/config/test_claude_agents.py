"""Tests for .claude/agents/*.md files validation."""
import os
import re
import pytest
from pathlib import Path
from typing import Dict, Any, Optional


def parse_yaml_frontmatter(content: str) -> Optional[Dict[str, Any]]:
    """Parse YAML frontmatter from markdown content."""
    frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.match(frontmatter_pattern, content, re.DOTALL)

    if not match:
        return None

    frontmatter_text = match.group(1)
    # Simple YAML parser for our needs
    frontmatter = {}
    for line in frontmatter_text.strip().split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            frontmatter[key.strip()] = value.strip()

    return frontmatter


def get_markdown_body(content: str) -> str:
    """Extract markdown body content after frontmatter."""
    frontmatter_pattern = r'^---\s*\n.*?\n---\s*\n'
    return re.sub(frontmatter_pattern, '', content, count=1, flags=re.DOTALL).strip()


class TestClaudeAgentSpecs:
    """Test suite for Claude agent specification files."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent.parent

    @pytest.fixture
    def agent_files(self, project_root):
        """Get all agent specification files."""
        agents_dir = project_root / ".claude" / "agents"
        if not agents_dir.exists():
            pytest.skip(f"Agents directory not found: {agents_dir}")

        return list(agents_dir.glob("*.md"))

    def test_agent_files_exist(self, agent_files):
        """Test that agent specification files exist."""
        assert len(agent_files) > 0, "No agent specification files found"

    def test_document_ai_extractor_structure(self, project_root):
        """Test document-ai-extractor.md has valid structure."""
        file_path = project_root / ".claude" / "agents" / "document-ai-extractor.md"

        if not file_path.exists():
            pytest.skip(f"File not found: {file_path}")

        content = file_path.read_text()

        # Validate frontmatter exists
        frontmatter = parse_yaml_frontmatter(content)
        assert frontmatter is not None, "Missing YAML frontmatter"

        # Validate required fields
        assert "name" in frontmatter, "Missing 'name' field in frontmatter"
        assert "description" in frontmatter, "Missing 'description' field in frontmatter"
        assert "color" in frontmatter, "Missing 'color' field in frontmatter"

        # Validate field values
        assert frontmatter["name"] == "document-ai-extractor"
        assert len(frontmatter["description"]) > 50, "Description too short"
        assert frontmatter["color"] == "green"

        # Validate body content
        body = get_markdown_body(content)
        assert len(body) > 100, "Agent specification body too short"
        assert "Document AI" in body, "Missing expected content about Document AI"

    def test_document_ai_extractor_content(self, project_root):
        """Test document-ai-extractor.md has required content sections."""
        file_path = project_root / ".claude" / "agents" / "document-ai-extractor.md"

        if not file_path.exists():
            pytest.skip(f"File not found: {file_path}")

        content = file_path.read_text()
        body = get_markdown_body(content)

        # Check for key sections
        assert "core responsibilities" in body.lower(), "Missing core responsibilities section"
        assert "approach" in body.lower(), "Missing approach section"
        assert "always" in body.lower(), "Missing always section"

        # Check for key technical terms
        assert "Document AI" in body
        assert "extraction" in body.lower()
        assert "PDF" in body or "document" in body.lower()

    def test_error_detective_structure(self, project_root):
        """Test error-detective.md has valid structure."""
        file_path = project_root / ".claude" / "agents" / "error-detective.md"

        if not file_path.exists():
            pytest.skip(f"File not found: {file_path}")

        content = file_path.read_text()

        # Validate frontmatter
        frontmatter = parse_yaml_frontmatter(content)
        assert frontmatter is not None, "Missing YAML frontmatter"

        # Validate required fields
        assert "name" in frontmatter
        assert "description" in frontmatter
        assert "color" in frontmatter

        # Validate field values
        assert frontmatter["name"] == "error-detective"
        assert len(frontmatter["description"]) > 50
        assert frontmatter["color"] == "red"

        # Validate body has debugging methodology
        body = get_markdown_body(content)
        assert "debugging" in body.lower() or "debug" in body.lower()

    def test_error_detective_methodology(self, project_root):
        """Test error-detective.md contains debugging methodology."""
        file_path = project_root / ".claude" / "agents" / "error-detective.md"

        if not file_path.exists():
            pytest.skip(f"File not found: {file_path}")

        content = file_path.read_text()
        body = get_markdown_body(content)

        # Check for methodology sections
        required_sections = [
            "initial assessment",
            "systematic investigation",
            "root cause",
            "solution"
        ]

        for section in required_sections:
            assert section in body.lower(), f"Missing section: {section}"

    def test_ocr_tradeline_validator_structure(self, project_root):
        """Test ocr-tradeline-validator.md has valid structure."""
        file_path = project_root / ".claude" / "agents" / "ocr-tradeline-validator.md"

        if not file_path.exists():
            pytest.skip(f"File not found: {file_path}")

        content = file_path.read_text()

        # This file doesn't have standard frontmatter, check content structure
        assert len(content) > 100, "File too short"
        assert "tradeline" in content.lower()
        assert "OCR" in content or "ocr" in content.lower()

    def test_ocr_tradeline_validator_schema(self, project_root):
        """Test ocr-tradeline-validator.md defines required schema."""
        file_path = project_root / ".claude" / "agents" / "ocr-tradeline-validator.md"

        if not file_path.exists():
            pytest.skip(f"File not found: {file_path}")

        content = file_path.read_text()

        # Check for schema definition
        required_fields = [
            "credit_bureau",
            "creditor_name",
            "account_number",
            "account_status",
            "account_type",
            "date_opened"
        ]

        for field in required_fields:
            assert field in content, f"Missing required field in schema: {field}"

        # Check for validation rules
        assert "normalization" in content.lower() or "normalize" in content.lower()
        assert "validation" in content.lower() or "validate" in content.lower()

    def test_ocr_tradeline_validator_enums(self, project_root):
        """Test ocr-tradeline-validator.md defines required enum values."""
        file_path = project_root / ".claude" / "agents" / "ocr-tradeline-validator.md"

        if not file_path.exists():
            pytest.skip(f"File not found: {file_path}")

        content = file_path.read_text()

        # Check for credit bureau enums
        assert "Experian" in content
        assert "Equifax" in content
        assert "TransUnion" in content

        # Check for extraction method enums
        assert "AWS Textract" in content or "Google Document AI" in content

        # Check for account type examples
        assert "Revolving" in content or "Installment" in content

    def test_all_agents_have_frontmatter_or_content(self, agent_files):
        """Test that all agent files have either YAML frontmatter or substantial content."""
        for file_path in agent_files:
            content = file_path.read_text()

            frontmatter = parse_yaml_frontmatter(content)

            # Either has frontmatter or substantial content
            assert frontmatter is not None or len(content) > 200, \
                f"Agent file {file_path.name} lacks proper structure"

    def test_agent_names_match_filenames(self, agent_files):
        """Test that agent names in frontmatter match their filenames."""
        for file_path in agent_files:
            content = file_path.read_text()
            frontmatter = parse_yaml_frontmatter(content)

            if frontmatter and "name" in frontmatter:
                expected_name = file_path.stem  # filename without extension
                actual_name = frontmatter["name"]

                assert actual_name == expected_name, \
                    f"Agent name '{actual_name}' doesn't match filename '{expected_name}'"

    def test_agent_descriptions_are_meaningful(self, agent_files):
        """Test that agent descriptions are meaningful and not empty."""
        for file_path in agent_files:
            content = file_path.read_text()
            frontmatter = parse_yaml_frontmatter(content)

            if frontmatter and "description" in frontmatter:
                description = frontmatter["description"]

                # Description should be substantial
                assert len(description) > 20, \
                    f"Agent {file_path.name} has too short description"

                # Should contain meaningful words
                assert any(word in description.lower() for word in [
                    "use", "when", "agent", "help", "assist", "analyze", "process", "extract"
                ]), f"Agent {file_path.name} description lacks action words"

    def test_agent_colors_are_valid(self, agent_files):
        """Test that agent colors (if specified) are valid values."""
        valid_colors = {"red", "green", "blue", "yellow", "purple", "orange", "pink", "gray", "black", "white"}

        for file_path in agent_files:
            content = file_path.read_text()
            frontmatter = parse_yaml_frontmatter(content)

            if frontmatter and "color" in frontmatter:
                color = frontmatter["color"].lower()
                assert color in valid_colors, \
                    f"Agent {file_path.name} has invalid color: {color}"