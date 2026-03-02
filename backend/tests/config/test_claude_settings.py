"""Tests for .claude/settings.local.json validation."""
import json
import pytest
from pathlib import Path
from typing import Dict, Any, List


class TestClaudeSettings:
    """Test suite for Claude settings configuration file."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent.parent

    @pytest.fixture
    def settings_file(self, project_root):
        """Get settings file path."""
        return project_root / ".claude" / "settings.local.json"

    @pytest.fixture
    def settings_data(self, settings_file):
        """Load and parse settings JSON."""
        if not settings_file.exists():
            pytest.skip(f"Settings file not found: {settings_file}")

        with open(settings_file, 'r') as f:
            return json.load(f)

    def test_settings_file_exists(self, settings_file):
        """Test that settings.local.json exists."""
        assert settings_file.exists(), "settings.local.json not found"

    def test_settings_is_valid_json(self, settings_file):
        """Test that settings file is valid JSON."""
        try:
            with open(settings_file, 'r') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in settings file: {e}")

    def test_settings_has_required_top_level_keys(self, settings_data):
        """Test that settings has required top-level structure."""
        # Check for expected top-level keys
        assert isinstance(settings_data, dict), "Settings should be a JSON object"

        # At minimum, should have some configuration
        assert len(settings_data) > 0, "Settings file is empty"

    def test_permissions_structure(self, settings_data):
        """Test permissions configuration structure."""
        if "permissions" not in settings_data:
            pytest.skip("No permissions configuration")

        permissions = settings_data["permissions"]
        assert isinstance(permissions, dict), "Permissions should be an object"

        # Check for allow/deny lists if present
        if "allow" in permissions:
            assert isinstance(permissions["allow"], list), "permissions.allow should be an array"

        if "deny" in permissions:
            assert isinstance(permissions["deny"], list), "permissions.deny should be an array"

    def test_permissions_allow_list_format(self, settings_data):
        """Test that permission allow list entries are properly formatted."""
        if "permissions" not in settings_data or "allow" not in settings_data["permissions"]:
            pytest.skip("No allow list in permissions")

        allow_list = settings_data["permissions"]["allow"]

        for entry in allow_list:
            assert isinstance(entry, str), f"Permission entry should be string: {entry}"
            assert len(entry) > 0, "Empty permission entry"

            # Common permission patterns
            if entry.startswith("Bash("):
                assert entry.endswith(")"), f"Malformed Bash permission: {entry}"
                assert ":" in entry, f"Bash permission should have command pattern: {entry}"

    def test_permissions_bash_commands(self, settings_data):
        """Test Bash command permissions are valid."""
        if "permissions" not in settings_data or "allow" not in settings_data["permissions"]:
            pytest.skip("No allow list in permissions")

        allow_list = settings_data["permissions"]["allow"]
        bash_permissions = [p for p in allow_list if p.startswith("Bash(")]

        # Should have some bash permissions
        assert len(bash_permissions) > 0, "No Bash permissions defined"

        # Validate format
        for perm in bash_permissions:
            # Format: Bash(command:*)
            assert perm.startswith("Bash(") and perm.endswith(")"), \
                f"Invalid Bash permission format: {perm}"

            # Extract command
            cmd_pattern = perm[5:-1]  # Remove "Bash(" and ")"
            assert len(cmd_pattern) > 0, f"Empty Bash command pattern: {perm}"

    def test_common_bash_permissions_present(self, settings_data):
        """Test that common necessary bash permissions are present."""
        if "permissions" not in settings_data or "allow" not in settings_data["permissions"]:
            pytest.skip("No allow list in permissions")

        allow_list = settings_data["permissions"]["allow"]

        # Common useful commands that should likely be allowed
        useful_patterns = ["npm", "ls", "find", "grep"]

        for pattern in useful_patterns:
            matching = [p for p in allow_list if pattern in p.lower()]
            assert len(matching) > 0, \
                f"Common command '{pattern}' might be missing from permissions"

    def test_mcp_servers_configuration(self, settings_data):
        """Test MCP servers configuration if present."""
        enabled_key = "enabledMcpjsonServers"
        disabled_key = "disabledMcpjsonServers"

        if enabled_key in settings_data:
            assert isinstance(settings_data[enabled_key], list), \
                f"{enabled_key} should be an array"

            # Each entry should be a string
            for server in settings_data[enabled_key]:
                assert isinstance(server, str), \
                    f"MCP server name should be string: {server}"
                assert len(server) > 0, "Empty MCP server name"

        if disabled_key in settings_data:
            assert isinstance(settings_data[disabled_key], list), \
                f"{disabled_key} should be an array"

            # Each entry should be a string
            for server in settings_data[disabled_key]:
                assert isinstance(server, str), \
                    f"MCP server name should be string: {server}"

    def test_no_server_in_both_enabled_and_disabled(self, settings_data):
        """Test that no MCP server is in both enabled and disabled lists."""
        enabled_key = "enabledMcpjsonServers"
        disabled_key = "disabledMcpjsonServers"

        if enabled_key in settings_data and disabled_key in settings_data:
            enabled = set(settings_data[enabled_key])
            disabled = set(settings_data[disabled_key])

            overlap = enabled & disabled
            assert len(overlap) == 0, \
                f"Servers in both enabled and disabled lists: {overlap}"

    def test_disable_all_hooks_is_boolean(self, settings_data):
        """Test disableAllHooks is a boolean if present."""
        if "disableAllHooks" in settings_data:
            value = settings_data["disableAllHooks"]
            assert isinstance(value, bool), \
                f"disableAllHooks should be boolean, got: {type(value)}"

    def test_no_duplicate_permissions(self, settings_data):
        """Test that there are no duplicate permission entries."""
        if "permissions" not in settings_data or "allow" not in settings_data["permissions"]:
            pytest.skip("No allow list in permissions")

        allow_list = settings_data["permissions"]["allow"]

        # Check for exact duplicates
        seen = set()
        duplicates = []

        for perm in allow_list:
            if perm in seen:
                duplicates.append(perm)
            seen.add(perm)

        assert len(duplicates) == 0, \
            f"Duplicate permissions found: {duplicates}"

    def test_skill_permissions_format(self, settings_data):
        """Test Skill() permission format if present."""
        if "permissions" not in settings_data or "allow" not in settings_data["permissions"]:
            pytest.skip("No allow list in permissions")

        allow_list = settings_data["permissions"]["allow"]
        skill_permissions = [p for p in allow_list if p.startswith("Skill(")]

        for perm in skill_permissions:
            assert perm.startswith("Skill(") and perm.endswith(")"), \
                f"Invalid Skill permission format: {perm}"

            # Extract skill name
            skill_pattern = perm[6:-1]  # Remove "Skill(" and ")"
            assert len(skill_pattern) > 0, f"Empty Skill pattern: {perm}"

    def test_mcp_permissions_format(self, settings_data):
        """Test Mcp__* permission format if present."""
        if "permissions" not in settings_data or "allow" not in settings_data["permissions"]:
            pytest.skip("No allow list in permissions")

        allow_list = settings_data["permissions"]["allow"]
        mcp_permissions = [p for p in allow_list if "Mcp" in p or "mcp__" in p]

        for perm in mcp_permissions:
            # MCP permissions should contain double underscore or be simple names
            if "mcp__" in perm.lower():
                parts = perm.split("__")
                assert len(parts) >= 2, f"Invalid MCP permission format: {perm}"
            else:
                # Simple MCP server name
                assert len(perm) > 0, f"Empty MCP permission: {perm}"

    def test_permissions_are_not_overly_permissive(self, settings_data):
        """Test that permissions don't include dangerous wildcards."""
        if "permissions" not in settings_data or "allow" not in settings_data["permissions"]:
            pytest.skip("No allow list in permissions")

        allow_list = settings_data["permissions"]["allow"]

        # Dangerous patterns that should generally be avoided
        dangerous_patterns = [
            "Bash(*)",  # Allow all bash commands
            "Bash(rm -rf *)",  # Recursive force delete
            "Bash(sudo *)",  # Unrestricted sudo
        ]

        for dangerous in dangerous_patterns:
            if dangerous in allow_list:
                pytest.fail(f"Overly permissive permission detected: {dangerous}")

    def test_settings_structure_consistency(self, settings_data):
        """Test overall structure consistency."""
        # Should be a flat or shallow object
        assert isinstance(settings_data, dict)

        # All keys should be strings
        for key in settings_data.keys():
            assert isinstance(key, str), f"Non-string key found: {key}"

        # Values should be standard JSON types
        for key, value in settings_data.items():
            assert isinstance(value, (dict, list, str, int, float, bool, type(None))), \
                f"Invalid value type for key '{key}': {type(value)}"