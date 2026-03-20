"""
Base Agent
==========

Abstract base class for all Credit Clarity agents. Provides shared
infrastructure: structured logging, execution timing, error handling,
and a uniform interface that FastAPI routes and Celery workers both call.

Every agent implements:
    async execute(**kwargs) -> AgentResult

AgentResult is a standardized envelope so the orchestrator can inspect
success/failure, timing, and payload without knowing agent internals.
"""

import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentStatus(str, Enum):
    """Execution outcome reported by every agent."""
    SUCCESS = "success"
    PARTIAL = "partial"       # some sub-steps failed but usable data returned
    FAILED = "failed"
    SKIPPED = "skipped"       # precondition not met, agent chose not to run


@dataclass
class AgentResult:
    """Standardized return value from any agent's execute() method.

    Attributes:
        agent_name:  Class name of the agent that produced this result.
        status:      Overall execution status.
        data:        Agent-specific payload (tradelines, letters, scores, …).
        errors:      List of error messages encountered during execution.
        warnings:    Non-fatal issues the caller should be aware of.
        metadata:    Timing, counts, version info, debug context.
        execution_id: UUID for correlating logs across agents.
        started_at:  ISO-8601 timestamp when execute() was called.
        duration_ms: Wall-clock milliseconds spent in execute().
    """
    agent_name: str = ""
    status: AgentStatus = AgentStatus.SUCCESS
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: str = ""
    duration_ms: float = 0.0

    @property
    def ok(self) -> bool:
        """True when the agent finished with usable output."""
        return self.status in (AgentStatus.SUCCESS, AgentStatus.PARTIAL)


class BaseAgent(ABC):
    """Abstract base that every Credit Clarity agent inherits from.

    Subclasses implement ``_run()`` with their domain logic.
    ``execute()`` wraps it with timing, logging, and error capture.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"agents.{self.__class__.__name__}")

    # ------------------------------------------------------------------
    # Public API – called by FastAPI routes, Celery tasks, orchestrator
    # ------------------------------------------------------------------

    async def execute(self, **kwargs: Any) -> AgentResult:
        """Run the agent and return a structured result.

        This method should NOT be overridden. Put domain logic in ``_run()``.

        Args:
            **kwargs: Agent-specific inputs (user_id, pdf_path, tradelines, …).

        Returns:
            AgentResult with status, data, and diagnostics.
        """
        result = AgentResult(
            agent_name=self.__class__.__name__,
            started_at=datetime.utcnow().isoformat(),
        )
        start = time.perf_counter()

        try:
            self.logger.info(
                "Starting %s (execution_id=%s)",
                self.__class__.__name__,
                result.execution_id,
            )
            data = await self._run(**kwargs)
            result.data = data if isinstance(data, dict) else {"result": data}
            result.status = AgentStatus.SUCCESS

        except Exception as exc:
            self.logger.exception(
                "%s failed (execution_id=%s): %s",
                self.__class__.__name__,
                result.execution_id,
                exc,
            )
            result.status = AgentStatus.FAILED
            result.errors.append(str(exc))

        finally:
            result.duration_ms = round((time.perf_counter() - start) * 1000, 2)
            self.logger.info(
                "%s finished in %.1fms  status=%s  errors=%d",
                self.__class__.__name__,
                result.duration_ms,
                result.status.value,
                len(result.errors),
            )

        return result

    # ------------------------------------------------------------------
    # Override point
    # ------------------------------------------------------------------

    @abstractmethod
    async def _run(self, **kwargs: Any) -> Dict[str, Any]:
        """Domain logic implemented by each concrete agent.

        Args:
            **kwargs: Same keyword arguments passed to execute().

        Returns:
            Dict that becomes AgentResult.data.

        Raises:
            Any exception – BaseAgent.execute() catches it and sets FAILED.
        """
        ...
