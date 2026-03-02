#!/usr/bin/env python
"""
Standalone test runner for configuration file validation.
This script runs tests without requiring pytest dependencies.
"""
import sys
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple


class TestResult:
    """Simple test result tracker."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = []

    def record_pass(self, test_name: str):
        self.passed += 1
        print(f"  ✓ {test_name}")

    def record_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"  ✗ {test_name}: {error}")

    def record_skip(self, test_name: str, reason: str):
        self.skipped += 1
        print(f"  ⊘ {test_name}: {reason}")

    def summary(self):
        print("\n" + "=" * 70)
        print(f"Tests Passed: {self.passed}")
        print(f"Tests Failed: {self.failed}")
        print(f"Tests Skipped: {self.skipped}")
        print("=" * 70)

        if self.errors:
            print("\nFailed Tests Details:")
            for test_name, error in self.errors:
                print(f"  - {test_name}: {error}")

        return self.failed == 0


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

            # Handle quoted strings
            if (value.startswith("'") and value.endswith("'")) or \
               (value.startswith('"') and value.endswith('"')):
                value = value[1:-1]

            # Handle booleans
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif value.lower() == 'null':
                value = None
            else:
                # Try to parse as number
                try:
                    if '.' in value:
                        value = float(value)
                    else:
                        value = int(value)
                except ValueError:
                    pass

            frontmatter[key] = value

    return frontmatter


def test_claude_agents(project_root: Path, result: TestResult):
    """Test .claude/agents/*.md files."""
    print("\n[Test Suite] Claude Agent Specifications")

    agents_dir = project_root / ".claude" / "agents"
    if not agents_dir.exists():
        result.record_skip("claude_agents", "Agents directory not found")
        return

    agent_files = list(agents_dir.glob("*.md"))

    # Test: Files exist
    if len(agent_files) > 0:
        result.record_pass(f"Found {len(agent_files)} agent files")
    else:
        result.record_fail("agent_files_exist", "No agent files found")
        return

    # Test each agent file
    for agent_file in agent_files:
        content = agent_file.read_text()
        frontmatter = parse_yaml_frontmatter(content)

        # Test structure
        if frontmatter or len(content) > 200:
            result.record_pass(f"{agent_file.name}: Valid structure")
        else:
            result.record_fail(f"{agent_file.name}", "Invalid structure")

        # Test frontmatter fields if present
        if frontmatter:
            if "name" not in frontmatter:
                result.record_fail(f"{agent_file.name}_name", "Missing 'name' field")
            if "description" not in frontmatter:
                result.record_fail(f"{agent_file.name}_description", "Missing 'description' field")


def test_claude_settings(project_root: Path, result: TestResult):
    """Test .claude/settings.local.json."""
    print("\n[Test Suite] Claude Settings")

    settings_file = project_root / ".claude" / "settings.local.json"
    if not settings_file.exists():
        result.record_skip("settings_file", "Settings file not found")
        return

    # Test: Valid JSON
    try:
        with open(settings_file) as f:
            data = json.load(f)
        result.record_pass("Valid JSON")
    except json.JSONDecodeError as e:
        result.record_fail("valid_json", f"Invalid JSON: {e}")
        return

    # Test: Permissions structure
    if "permissions" in data:
        permissions = data["permissions"]
        if isinstance(permissions, dict):
            result.record_pass("Permissions is object")

            if "allow" in permissions:
                if isinstance(permissions["allow"], list):
                    result.record_pass(f"Allow list has {len(permissions['allow'])} entries")
                else:
                    result.record_fail("allow_list_type", "Allow should be array")

            if "deny" in permissions:
                if isinstance(permissions["deny"], list):
                    result.record_pass(f"Deny list has {len(permissions['deny'])} entries")
                else:
                    result.record_fail("deny_list_type", "Deny should be array")
        else:
            result.record_fail("permissions_structure", "Permissions should be object")


def test_claude_rules(project_root: Path, result: TestResult):
    """Test .claude/rules.md."""
    print("\n[Test Suite] Claude Rules")

    rules_file = project_root / ".claude" / "rules.md"
    if not rules_file.exists():
        result.record_skip("rules_file", "Rules file not found")
        return

    content = rules_file.read_text()

    # Test: Has content
    if len(content) > 100:
        result.record_pass("Rules file has content")
    else:
        result.record_fail("rules_content", "Rules file too short")

    # Test: Has Sentry examples
    if "Sentry" in content:
        result.record_pass("Contains Sentry references")
    else:
        result.record_fail("sentry_references", "Missing Sentry references")

    # Test: Has code blocks
    code_blocks = re.findall(r'```.*?\n.*?```', content, re.DOTALL)
    if len(code_blocks) > 0:
        result.record_pass(f"Has {len(code_blocks)} code blocks")
    else:
        result.record_fail("code_blocks", "No code blocks found")


def test_codex_agents(project_root: Path, result: TestResult):
    """Test .codex/prompts/bmad-bmm-agents-*.md files."""
    print("\n[Test Suite] Codex Agent Prompts")

    prompts_dir = project_root / ".codex" / "prompts"
    if not prompts_dir.exists():
        result.record_skip("codex_prompts", "Prompts directory not found")
        return

    agent_files = list(prompts_dir.glob("bmad-bmm-agents-*.md"))

    if len(agent_files) > 0:
        result.record_pass(f"Found {len(agent_files)} agent prompt files")
    else:
        result.record_fail("agent_prompts_exist", "No agent prompt files found")
        return

    # Test each agent prompt
    valid_count = 0
    for agent_file in agent_files:
        content = agent_file.read_text()
        frontmatter = parse_yaml_frontmatter(content)

        if frontmatter:
            valid_count += 1
            if "name" not in frontmatter:
                result.record_fail(f"{agent_file.name}_name", "Missing 'name' field")
            if "description" not in frontmatter:
                result.record_fail(f"{agent_file.name}_description", "Missing 'description' field")

    result.record_pass(f"{valid_count}/{len(agent_files)} have valid frontmatter")


def test_codex_workflows(project_root: Path, result: TestResult):
    """Test .codex/prompts/bmad-bmm-workflows-*.md files."""
    print("\n[Test Suite] Codex Workflow Prompts")

    prompts_dir = project_root / ".codex" / "prompts"
    if not prompts_dir.exists():
        result.record_skip("workflow_prompts", "Prompts directory not found")
        return

    workflow_files = [f for f in prompts_dir.glob("bmad-bmm-workflows-*.md")
                      if f.name != "bmad-bmm-workflows-README.md"]

    if len(workflow_files) > 0:
        result.record_pass(f"Found {len(workflow_files)} workflow prompt files")
    else:
        result.record_fail("workflow_prompts_exist", "No workflow prompt files found")
        return

    # Test each workflow prompt
    valid_count = 0
    for workflow_file in workflow_files:
        content = workflow_file.read_text()
        frontmatter = parse_yaml_frontmatter(content)

        if frontmatter and "description" in frontmatter:
            valid_count += 1

    result.record_pass(f"{valid_count}/{len(workflow_files)} have descriptions")

    # Test README
    readme_file = prompts_dir / "bmad-bmm-workflows-README.md"
    if readme_file.exists():
        content = readme_file.read_text()
        if "workflow" in content.lower():
            result.record_pass("README contains workflow references")
        else:
            result.record_fail("readme_content", "README missing workflow references")
    else:
        result.record_fail("readme_exists", "README not found")


def test_ralph_loop_config(project_root: Path, result: TestResult):
    """Test ralph-loop.local.md configuration."""
    print("\n[Test Suite] Ralph Loop Configuration")

    ralph_loop_file = project_root / ".claude" / "ralph-loop.local.md"
    if not ralph_loop_file.exists():
        result.record_skip("ralph_loop", "Ralph loop file not found")
        return

    content = ralph_loop_file.read_text()
    frontmatter = parse_yaml_frontmatter(content)

    # Test: Has frontmatter
    if frontmatter:
        result.record_pass("Has YAML frontmatter")
    else:
        result.record_fail("ralph_loop_frontmatter", "Missing frontmatter")
        return

    # Test: Expected fields
    if "active" in frontmatter:
        if isinstance(frontmatter["active"], bool):
            result.record_pass("'active' field is boolean")
        else:
            result.record_fail("active_type", "'active' should be boolean")

    if "iteration" in frontmatter:
        if isinstance(frontmatter["iteration"], (int, float)):
            result.record_pass("'iteration' field is number")
        else:
            result.record_fail("iteration_type", "'iteration' should be number")


def main():
    """Run all tests."""
    print("=" * 70)
    print("Configuration File Validation Test Suite")
    print("=" * 70)

    project_root = Path(__file__).parent.parent.parent.parent

    result = TestResult()

    # Run all test suites
    test_claude_agents(project_root, result)
    test_claude_settings(project_root, result)
    test_claude_rules(project_root, result)
    test_codex_agents(project_root, result)
    test_codex_workflows(project_root, result)
    test_ralph_loop_config(project_root, result)

    # Print summary
    success = result.summary()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())