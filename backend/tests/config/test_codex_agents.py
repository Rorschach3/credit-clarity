"""Tests for .codex/prompts/bmad-bmm-agents-*.md files validation."""
import re
import pytest
from pathlib import Path
from typing import Dict, Any, List


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
            if value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            elif value.startswith('"') and value.endswith('"'):
                value = value[1:-1]

            frontmatter[key] = value

    return frontmatter


def get_markdown_body(content: str) -> str:
    """Extract markdown body content after frontmatter."""
    frontmatter_pattern = r'^---\s*\n.*?\n---\s*\n'
    return re.sub(frontmatter_pattern, '', content, count=1, flags=re.DOTALL).strip()


class TestCodexAgentPrompts:
    """Test suite for .codex/prompts/bmad-bmm-agents-*.md files."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent.parent

    @pytest.fixture
    def agent_prompt_dir(self, project_root):
        """Get agent prompts directory."""
        return project_root / ".codex" / "prompts"

    @pytest.fixture
    def agent_prompt_files(self, agent_prompt_dir):
        """Get all agent prompt files."""
        if not agent_prompt_dir.exists():
            pytest.skip(f"Agent prompts directory not found: {agent_prompt_dir}")

        files = list(agent_prompt_dir.glob("bmad-bmm-agents-*.md"))
        if len(files) == 0:
            pytest.skip("No agent prompt files found")

        return files

    def test_agent_prompt_files_exist(self, agent_prompt_files):
        """Test that agent prompt files exist."""
        assert len(agent_prompt_files) > 0, "No agent prompt files found"

    def test_all_agent_prompts_have_frontmatter(self, agent_prompt_files):
        """Test that all agent prompt files have YAML frontmatter."""
        for file_path in agent_prompt_files:
            content = file_path.read_text()
            frontmatter = parse_yaml_frontmatter(content)

            assert len(frontmatter) > 0, \
                f"Agent prompt {file_path.name} missing YAML frontmatter"

    def test_agent_prompts_have_required_fields(self, agent_prompt_files):
        """Test that agent prompts have required frontmatter fields."""
        for file_path in agent_prompt_files:
            content = file_path.read_text()
            frontmatter = parse_yaml_frontmatter(content)

            # Required fields
            assert "name" in frontmatter, \
                f"{file_path.name} missing 'name' field"
            assert "description" in frontmatter, \
                f"{file_path.name} missing 'description' field"

    def test_agent_prompt_names_are_descriptive(self, agent_prompt_files):
        """Test that agent prompt names are descriptive."""
        for file_path in agent_prompt_files:
            content = file_path.read_text()
            frontmatter = parse_yaml_frontmatter(content)

            if "name" in frontmatter:
                name = frontmatter["name"]

                # Name should not be empty
                assert len(name) > 0, f"{file_path.name} has empty name"

                # Name should be lowercase with hyphens or underscores
                assert re.match(r'^[a-z0-9\-_]+$', name), \
                    f"{file_path.name} name should be lowercase with hyphens/underscores: {name}"

    def test_agent_prompt_descriptions_are_meaningful(self, agent_prompt_files):
        """Test that agent prompt descriptions are meaningful."""
        for file_path in agent_prompt_files:
            content = file_path.read_text()
            frontmatter = parse_yaml_frontmatter(content)

            if "description" in frontmatter:
                description = frontmatter["description"]

                # Description should not be empty
                assert len(description) > 0, \
                    f"{file_path.name} has empty description"

                # Description should contain meaningful words
                assert any(word in description.lower() for word in [
                    "agent", "use", "when", "help", "assist", "perform"
                ]), f"{file_path.name} description should describe the agent's purpose"

    def test_agent_prompts_have_activation_instructions(self, agent_prompt_files):
        """Test that agent prompts contain activation instructions."""
        for file_path in agent_prompt_files:
            content = file_path.read_text()
            body = get_markdown_body(content)

            # Should have activation-related content
            assert "agent" in body.lower(), \
                f"{file_path.name} missing agent reference in body"

            # Should have instructions or directives
            assert any(word in body.lower() for word in [
                "load", "read", "follow", "execute", "activate"
            ]), f"{file_path.name} missing activation instructions"

    def test_agent_prompts_have_xml_tags(self, agent_prompt_files):
        """Test that agent prompts use XML-style tags for structure."""
        for file_path in agent_prompt_files:
            content = file_path.read_text()
            body = get_markdown_body(content)

            # Should have XML tags for structured instructions
            xml_tags = re.findall(r'<([a-zA-Z\-]+)', body)

            assert len(xml_tags) > 0, \
                f"{file_path.name} missing XML structure tags"

    def test_agent_prompts_reference_bmad_paths(self, agent_prompt_files):
        """Test that agent prompts reference @_bmad paths."""
        for file_path in agent_prompt_files:
            content = file_path.read_text()
            body = get_markdown_body(content)

            # Should reference bmad paths
            assert "@_bmad" in body, \
                f"{file_path.name} missing @_bmad path reference"

    def test_specific_agents_exist(self, agent_prompt_dir):
        """Test that expected agent files exist."""
        expected_agents = [
            "bmad-bmm-agents-analyst.md",
            "bmad-bmm-agents-architect.md",
            "bmad-bmm-agents-dev.md",
            "bmad-bmm-agents-pm.md"
        ]

        for agent_file in expected_agents:
            file_path = agent_prompt_dir / agent_file
            assert file_path.exists(), f"Expected agent file not found: {agent_file}"

    def test_analyst_agent_structure(self, agent_prompt_dir):
        """Test analyst agent has proper structure."""
        file_path = agent_prompt_dir / "bmad-bmm-agents-analyst.md"

        if not file_path.exists():
            pytest.skip(f"Analyst agent not found: {file_path}")

        content = file_path.read_text()
        frontmatter = parse_yaml_frontmatter(content)

        assert frontmatter["name"] == "analyst"
        assert "analyst" in frontmatter["description"].lower()

        body = get_markdown_body(content)
        assert "agent-activation" in body.lower()

    def test_architect_agent_structure(self, agent_prompt_dir):
        """Test architect agent has proper structure."""
        file_path = agent_prompt_dir / "bmad-bmm-agents-architect.md"

        if not file_path.exists():
            pytest.skip(f"Architect agent not found: {file_path}")

        content = file_path.read_text()
        frontmatter = parse_yaml_frontmatter(content)

        assert frontmatter["name"] == "architect"
        assert "architect" in frontmatter["description"].lower()

    def test_dev_agent_structure(self, agent_prompt_dir):
        """Test dev agent has proper structure."""
        file_path = agent_prompt_dir / "bmad-bmm-agents-dev.md"

        if not file_path.exists():
            pytest.skip(f"Dev agent not found: {file_path}")

        content = file_path.read_text()
        frontmatter = parse_yaml_frontmatter(content)

        assert frontmatter["name"] == "dev"
        assert "dev" in frontmatter["description"].lower()

    def test_pm_agent_structure(self, agent_prompt_dir):
        """Test PM agent has proper structure."""
        file_path = agent_prompt_dir / "bmad-bmm-agents-pm.md"

        if not file_path.exists():
            pytest.skip(f"PM agent not found: {file_path}")

        content = file_path.read_text()
        frontmatter = parse_yaml_frontmatter(content)

        assert frontmatter["name"] == "pm"
        assert "pm" in frontmatter["description"].lower()

    def test_agent_prompts_have_critical_tag(self, agent_prompt_files):
        """Test that agent prompts use CRITICAL attribute for important sections."""
        for file_path in agent_prompt_files:
            content = file_path.read_text()
            body = get_markdown_body(content)

            # Should have CRITICAL markers
            assert 'CRITICAL' in body, \
                f"{file_path.name} missing CRITICAL markers for important instructions"

    def test_agent_prompts_have_load_instruction(self, agent_prompt_files):
        """Test that agent prompts include LOAD instruction."""
        for file_path in agent_prompt_files:
            content = file_path.read_text()
            body = get_markdown_body(content)

            # Should instruct to LOAD the full agent file
            assert "LOAD" in body, \
                f"{file_path.name} missing LOAD instruction"

    def test_agent_prompts_have_read_instruction(self, agent_prompt_files):
        """Test that agent prompts include READ instruction."""
        for file_path in agent_prompt_files:
            content = file_path.read_text()
            body = get_markdown_body(content)

            # Should instruct to READ the contents
            assert "READ" in body, \
                f"{file_path.name} missing READ instruction"

    def test_agent_prompts_numbered_steps(self, agent_prompt_files):
        """Test that agent prompts have numbered activation steps."""
        for file_path in agent_prompt_files:
            content = file_path.read_text()
            body = get_markdown_body(content)

            # Should have numbered steps (1. 2. 3. etc.)
            numbered_steps = re.findall(r'^\d+\.\s+', body, re.MULTILINE)

            assert len(numbered_steps) >= 3, \
                f"{file_path.name} should have at least 3 numbered steps"

    def test_agent_prompts_character_maintenance(self, agent_prompt_files):
        """Test that agent prompts emphasize staying in character."""
        for file_path in agent_prompt_files:
            content = file_path.read_text()

            # Should mention staying in character or following persona
            assert any(phrase in content.lower() for phrase in [
                "stay in character",
                "character throughout",
                "follow the agent",
                "never break character"
            ]), f"{file_path.name} should emphasize character maintenance"

    def test_agent_prompts_reference_agent_file(self, agent_prompt_files):
        """Test that agent prompts reference specific agent files."""
        for file_path in agent_prompt_files:
            content = file_path.read_text()
            body = get_markdown_body(content)

            # Should reference an agent.md file
            assert re.search(r'@_bmad/bmm/agents/\w+\.md', body), \
                f"{file_path.name} should reference specific agent file path"

    def test_agent_prompts_consistent_format(self, agent_prompt_files):
        """Test that all agent prompts follow consistent format."""
        structures = []

        for file_path in agent_prompt_files:
            content = file_path.read_text()
            frontmatter = parse_yaml_frontmatter(content)
            body = get_markdown_body(content)

            structure = {
                'has_name': 'name' in frontmatter,
                'has_description': 'description' in frontmatter,
                'has_xml_tags': '<' in body and '>' in body,
                'has_critical': 'CRITICAL' in body,
                'has_numbered_steps': bool(re.search(r'^\d+\.', body, re.MULTILINE))
            }

            structures.append(structure)

        # All should have same structure
        if len(structures) > 1:
            first = structures[0]
            for struct in structures[1:]:
                assert struct == first, "Agent prompts should have consistent structure"