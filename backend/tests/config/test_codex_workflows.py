"""Tests for .codex/prompts/bmad-bmm-workflows-*.md files validation."""
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


class TestCodexWorkflowPrompts:
    """Test suite for .codex/prompts/bmad-bmm-workflows-*.md files."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent.parent

    @pytest.fixture
    def workflow_prompt_dir(self, project_root):
        """Get workflow prompts directory."""
        return project_root / ".codex" / "prompts"

    @pytest.fixture
    def workflow_prompt_files(self, workflow_prompt_dir):
        """Get all workflow prompt files (excluding README)."""
        if not workflow_prompt_dir.exists():
            pytest.skip(f"Workflow prompts directory not found: {workflow_prompt_dir}")

        files = [f for f in workflow_prompt_dir.glob("bmad-bmm-workflows-*.md")
                 if f.name != "bmad-bmm-workflows-README.md"]

        if len(files) == 0:
            pytest.skip("No workflow prompt files found")

        return files

    @pytest.fixture
    def readme_file(self, workflow_prompt_dir):
        """Get workflow README file."""
        return workflow_prompt_dir / "bmad-bmm-workflows-README.md"

    def test_workflow_prompt_files_exist(self, workflow_prompt_files):
        """Test that workflow prompt files exist."""
        assert len(workflow_prompt_files) > 0, "No workflow prompt files found"

    def test_all_workflow_prompts_have_frontmatter(self, workflow_prompt_files):
        """Test that all workflow prompt files have YAML frontmatter."""
        for file_path in workflow_prompt_files:
            content = file_path.read_text()
            frontmatter = parse_yaml_frontmatter(content)

            assert len(frontmatter) > 0, \
                f"Workflow prompt {file_path.name} missing YAML frontmatter"

    def test_workflow_prompts_have_description(self, workflow_prompt_files):
        """Test that workflow prompts have description field."""
        for file_path in workflow_prompt_files:
            content = file_path.read_text()
            frontmatter = parse_yaml_frontmatter(content)

            assert "description" in frontmatter, \
                f"{file_path.name} missing 'description' field"

            # Description should be meaningful
            description = frontmatter["description"]
            assert len(description) > 20, \
                f"{file_path.name} description too short"

    def test_workflow_prompts_have_loading_instructions(self, workflow_prompt_files):
        """Test that workflow prompts contain loading instructions."""
        for file_path in workflow_prompt_files:
            content = file_path.read_text()
            body = get_markdown_body(content)

            # Should have loading/execution instructions
            assert any(word in body.upper() for word in ["LOAD", "READ", "FOLLOW"]), \
                f"{file_path.name} missing loading instructions"

    def test_workflow_prompts_reference_bmad_paths(self, workflow_prompt_files):
        """Test that workflow prompts reference @_bmad paths."""
        for file_path in workflow_prompt_files:
            content = file_path.read_text()
            body = get_markdown_body(content)

            # Should reference bmad workflow paths
            assert "@_bmad" in body, \
                f"{file_path.name} missing @_bmad path reference"

    def test_workflow_prompts_have_critical_markers(self, workflow_prompt_files):
        """Test that workflow prompts use CRITICAL markers."""
        for file_path in workflow_prompt_files:
            content = file_path.read_text()

            # Should have CRITICAL markers for important instructions
            assert "CRITICAL" in content, \
                f"{file_path.name} missing CRITICAL markers"

    def test_workflow_prompts_reference_workflow_files(self, workflow_prompt_files):
        """Test that workflow prompts reference specific workflow files."""
        for file_path in workflow_prompt_files:
            content = file_path.read_text()
            body = get_markdown_body(content)

            # Should reference workflow.md or workflow.yaml or workflow.xml
            assert any(ext in body for ext in ['.md', '.yaml', '.yml', '.xml']), \
                f"{file_path.name} should reference workflow files"

    def test_specific_workflows_exist(self, workflow_prompt_dir):
        """Test that expected workflow files exist."""
        expected_workflows = [
            "bmad-bmm-workflows-check-implementation-readiness.md",
            "bmad-bmm-workflows-code-review.md",
            "bmad-bmm-workflows-create-architecture.md",
            "bmad-bmm-workflows-create-epics-and-stories.md"
        ]

        for workflow_file in expected_workflows:
            file_path = workflow_prompt_dir / workflow_file
            assert file_path.exists(), f"Expected workflow file not found: {workflow_file}"

    def test_check_implementation_readiness_structure(self, workflow_prompt_dir):
        """Test check-implementation-readiness workflow structure."""
        file_path = workflow_prompt_dir / "bmad-bmm-workflows-check-implementation-readiness.md"

        if not file_path.exists():
            pytest.skip(f"Workflow not found: {file_path}")

        content = file_path.read_text()
        frontmatter = parse_yaml_frontmatter(content)

        assert "description" in frontmatter
        assert "validation" in frontmatter["description"].lower() or \
               "readiness" in frontmatter["description"].lower()

    def test_code_review_workflow_structure(self, workflow_prompt_dir):
        """Test code-review workflow structure."""
        file_path = workflow_prompt_dir / "bmad-bmm-workflows-code-review.md"

        if not file_path.exists():
            pytest.skip(f"Workflow not found: {file_path}")

        content = file_path.read_text()
        frontmatter = parse_yaml_frontmatter(content)

        assert "description" in frontmatter
        assert "code review" in frontmatter["description"].lower() or \
               "review" in frontmatter["description"].lower()

    def test_create_architecture_workflow_structure(self, workflow_prompt_dir):
        """Test create-architecture workflow structure."""
        file_path = workflow_prompt_dir / "bmad-bmm-workflows-create-architecture.md"

        if not file_path.exists():
            pytest.skip(f"Workflow not found: {file_path}")

        content = file_path.read_text()
        frontmatter = parse_yaml_frontmatter(content)

        assert "description" in frontmatter
        assert "architect" in frontmatter["description"].lower()

    def test_create_epics_and_stories_structure(self, workflow_prompt_dir):
        """Test create-epics-and-stories workflow structure."""
        file_path = workflow_prompt_dir / "bmad-bmm-workflows-create-epics-and-stories.md"

        if not file_path.exists():
            pytest.skip(f"Workflow not found: {file_path}")

        content = file_path.read_text()
        frontmatter = parse_yaml_frontmatter(content)

        assert "description" in frontmatter
        assert any(word in frontmatter["description"].lower()
                   for word in ["epic", "stories", "story"])

    def test_excalidraw_workflows_exist(self, workflow_prompt_dir):
        """Test that Excalidraw workflow files exist."""
        excalidraw_workflows = [
            "bmad-bmm-workflows-create-excalidraw-dataflow.md",
            "bmad-bmm-workflows-create-excalidraw-diagram.md",
            "bmad-bmm-workflows-create-excalidraw-flowchart.md",
            "bmad-bmm-workflows-create-excalidraw-wireframe.md"
        ]

        for workflow_file in excalidraw_workflows:
            file_path = workflow_prompt_dir / workflow_file
            assert file_path.exists(), f"Excalidraw workflow not found: {workflow_file}"

    def test_excalidraw_workflows_mention_excalidraw(self, workflow_prompt_dir):
        """Test that Excalidraw workflows reference Excalidraw."""
        excalidraw_workflows = [
            "bmad-bmm-workflows-create-excalidraw-dataflow.md",
            "bmad-bmm-workflows-create-excalidraw-diagram.md",
            "bmad-bmm-workflows-create-excalidraw-flowchart.md",
            "bmad-bmm-workflows-create-excalidraw-wireframe.md"
        ]

        for workflow_file in excalidraw_workflows:
            file_path = workflow_prompt_dir / workflow_file

            if not file_path.exists():
                continue

            content = file_path.read_text()
            assert "excalidraw" in content.lower(), \
                f"{workflow_file} should reference Excalidraw"

    def test_workflow_prompts_have_xml_structure(self, workflow_prompt_files):
        """Test that workflow prompts use XML-style tags."""
        for file_path in workflow_prompt_files:
            content = file_path.read_text()
            body = get_markdown_body(content)

            # Should have XML tags or structured content
            has_xml = bool(re.search(r'<[a-zA-Z\-]+', body))
            has_steps = "steps" in body.lower()

            assert has_xml or has_steps, \
                f"{file_path.name} missing structured instructions"

    def test_workflow_prompts_have_numbered_steps(self, workflow_prompt_files):
        """Test that workflow prompts have numbered steps."""
        for file_path in workflow_prompt_files:
            content = file_path.read_text()
            body = get_markdown_body(content)

            # Should have numbered steps (1. 2. 3. etc.)
            numbered_steps = re.findall(r'^\d+\.\s+', body, re.MULTILINE)

            assert len(numbered_steps) >= 2, \
                f"{file_path.name} should have numbered steps"

    def test_workflow_readme_exists(self, readme_file):
        """Test that workflow README exists."""
        assert readme_file.exists(), "Workflow README not found"

    def test_workflow_readme_lists_workflows(self, readme_file):
        """Test that README lists available workflows."""
        if not readme_file.exists():
            pytest.skip("README not found")

        content = readme_file.read_text()

        # Should list workflows
        assert "workflow" in content.lower()

        # Should have multiple workflow entries
        workflow_references = len(re.findall(r'workflow', content, re.IGNORECASE))
        assert workflow_references >= 5, "README should list multiple workflows"

    def test_workflow_readme_has_execution_section(self, readme_file):
        """Test that README has execution instructions."""
        if not readme_file.exists():
            pytest.skip("README not found")

        content = readme_file.read_text()

        # Should have execution section
        assert "execution" in content.lower() or "running" in content.lower(), \
            "README missing execution instructions"

    def test_workflow_readme_references_workflow_paths(self, readme_file):
        """Test that README references workflow file paths."""
        if not readme_file.exists():
            pytest.skip("README not found")

        content = readme_file.read_text()

        # Should reference workflow paths
        assert "_bmad/bmm/workflows" in content, \
            "README should reference workflow paths"

    def test_workflow_descriptions_are_unique(self, workflow_prompt_files):
        """Test that workflow descriptions are unique."""
        descriptions = []

        for file_path in workflow_prompt_files:
            content = file_path.read_text()
            frontmatter = parse_yaml_frontmatter(content)

            if "description" in frontmatter:
                descriptions.append(frontmatter["description"])

        # All descriptions should be unique
        assert len(descriptions) == len(set(descriptions)), \
            "Workflow descriptions should be unique"

    def test_workflow_prompts_consistent_format(self, workflow_prompt_files):
        """Test that workflow prompts follow consistent format."""
        structures = []

        for file_path in workflow_prompt_files:
            content = file_path.read_text()
            frontmatter = parse_yaml_frontmatter(content)
            body = get_markdown_body(content)

            structure = {
                'has_description': 'description' in frontmatter,
                'has_critical': 'CRITICAL' in content,
                'has_load_instruction': 'LOAD' in body,
                'has_bmad_reference': '@_bmad' in body
            }

            structures.append(structure)

        # Most should have same basic structure
        if len(structures) > 1:
            # Count how many have each feature
            feature_counts = {
                'has_description': sum(s['has_description'] for s in structures),
                'has_critical': sum(s['has_critical'] for s in structures),
                'has_load_instruction': sum(s['has_load_instruction'] for s in structures),
                'has_bmad_reference': sum(s['has_bmad_reference'] for s in structures)
            }

            # At least 80% should have key features
            total = len(structures)
            assert feature_counts['has_description'] >= total * 0.8, \
                "Most workflows should have descriptions"
            assert feature_counts['has_bmad_reference'] >= total * 0.8, \
                "Most workflows should reference bmad paths"

    def test_workflow_prompts_reference_correct_workflow_type(self, workflow_prompt_files):
        """Test that workflow prompts reference appropriate workflow files."""
        for file_path in workflow_prompt_files:
            content = file_path.read_text()
            body = get_markdown_body(content)

            # Extract workflow name from filename
            # Format: bmad-bmm-workflows-{name}.md
            workflow_name = file_path.stem.replace('bmad-bmm-workflows-', '')

            # Normalize name for comparison
            workflow_name_normalized = workflow_name.replace('-', '')

            # Should reference a path containing similar name
            assert any(
                workflow_name_normalized in path.replace('-', '').replace('/', '')
                for path in re.findall(r'@_bmad/bmm/workflows/[\w\-/]+', body)
            ) or len(re.findall(r'@_bmad/bmm/workflows/', body)) > 0, \
                f"{file_path.name} should reference related workflow path"