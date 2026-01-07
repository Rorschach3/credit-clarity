"""Code execution server tool for the agent framework."""

from dataclasses import dataclass
from typing import Any


@dataclass
class CodeExecutionServerTool:
    """Code execution server tool that uses Anthropic's server tool format."""

    name: str = "code_execution"
    type: str = "code_execution_20250825"
    beta_header: str = "code-execution-2025-08-25"

    def to_dict(self) -> dict[str, Any]:
        """Convert to Anthropic server tool format."""
        return {
            "type": self.type,
            "name": self.name,
        }

    def get_headers(self) -> dict[str, str]:
        """Return required Anthropic beta headers."""
        return {"anthropic-beta": self.beta_header}
