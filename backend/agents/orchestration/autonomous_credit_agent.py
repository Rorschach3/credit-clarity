"""
Autonomous Credit Agent
=======================

Top-level orchestrator that chains all sub-agents into a single
end-to-end credit report analysis and dispute pipeline.

Pipeline stages:
    1. ReportParserAgent      – Extract tradelines from uploaded PDF.
    2. NegativeTradelineAgent – Classify and enrich negative items.
    3. CreditScoreClassifier  – Estimate risk tier and dispute priority.
    4. DisputeStrategyAgent   – Recommend dispute actions per tradeline.
    5. LetterGeneratorAgent   – Generate FCRA-compliant dispute letters.

Each stage feeds its output to the next. If any stage fails, the
pipeline halts and returns a partial result with the error context.

Integrations:
    - All sub-agents in agents.credit_report and agents.dispute.
    - Supabase (via sub-agents) for persistence.
    - Celery (optional) for async execution via BackgroundJobProcessor.

Inputs (via execute()):
    pdf_path       : str              – Path to uploaded credit report PDF.
    user_id        : str              – Supabase user UUID.
    user_info      : Dict             – Name, address for letter header.
    bureau         : str | None       – Force bureau detection (or auto-detect).
    preview_only   : bool             – If True, generate HTML preview only.
    skip_letters   : bool             – If True, stop after strategy stage.

Output (AgentResult.data):
    {
        "stages_completed":  List[str],     # names of stages that ran
        "report":            Dict,          # ReportParserAgent output
        "negatives":         Dict,          # NegativeTradelineAgent output
        "credit_score":      Dict,          # CreditScoreClassifier output
        "strategy":          Dict | None,   # DisputeStrategyAgent output
        "letters":           Dict | None,   # LetterGeneratorAgent output
        "pipeline_status":   str,           # 'complete' | 'partial' | 'failed'
        "stage_timings":     Dict[str, float],  # stage name → ms
    }
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agents.base import AgentResult, AgentStatus, BaseAgent


class AutonomousCreditAgent(BaseAgent):
    """End-to-end orchestrator chaining all credit and dispute agents."""

    # Ordered pipeline stage definitions
    STAGES = [
        "report_parser",
        "negative_tradeline",
        "credit_score",
        "dispute_strategy",
        "letter_generator",
    ]

    def __init__(self) -> None:
        super().__init__()
        # Lazy-init sub-agents on first run to avoid circular imports
        self._agents: Dict[str, BaseAgent] = {}

    def _init_agents(self) -> None:
        """Lazily instantiate all sub-agents.

        Uses local imports to avoid circular dependency issues with
        heavy service modules.
        """
        if self._agents:
            return

        from agents.credit_report import (
            CreditScoreClassifier,
            NegativeTradelineAgent,
            ReportParserAgent,
        )
        from agents.dispute import (
            DisputeStrategyAgent,
            LetterGeneratorAgent,
        )

        self._agents = {
            "report_parser": ReportParserAgent(),
            "negative_tradeline": NegativeTradelineAgent(),
            "credit_score": CreditScoreClassifier(),
            "dispute_strategy": DisputeStrategyAgent(),
            "letter_generator": LetterGeneratorAgent(),
        }

    async def _run_stage(
        self,
        stage_name: str,
        **kwargs: Any,
    ) -> AgentResult:
        """Execute a single pipeline stage.

        Args:
            stage_name: Key into self._agents.
            **kwargs:   Arguments forwarded to the sub-agent's execute().

        Returns:
            AgentResult from the sub-agent.
        """
        agent = self._agents[stage_name]
        self.logger.info("Running stage: %s", stage_name)
        return await agent.execute(**kwargs)

    async def _run(
        self,
        *,
        pdf_path: str,
        user_id: str,
        user_info: Optional[Dict[str, Any]] = None,
        bureau: Optional[str] = None,
        preview_only: bool = False,
        skip_letters: bool = False,
    ) -> Dict[str, Any]:
        """Run the full credit analysis and dispute pipeline.

        Args:
            pdf_path:     Path to uploaded credit report PDF.
            user_id:      Supabase user UUID.
            user_info:    Name/address dict for letter header (required if
                          skip_letters is False).
            bureau:       Force bureau detection (or None for auto-detect).
            preview_only: If True, letters are HTML preview only.
            skip_letters: If True, pipeline stops after strategy stage.

        Returns:
            Dict with stages_completed, per-stage outputs, pipeline_status,
            and stage_timings.
        """
        self._init_agents()

        stages_completed: List[str] = []
        stage_timings: Dict[str, float] = {}
        result_data: Dict[str, Any] = {
            "stages_completed": stages_completed,
            "report": {},
            "negatives": {},
            "credit_score": {},
            "strategy": None,
            "letters": None,
            "pipeline_status": "failed",
            "stage_timings": stage_timings,
        }

        # --- Stage 1: Parse credit report ---
        report_result = await self._run_stage(
            "report_parser",
            pdf_path=pdf_path,
            user_id=user_id,
            bureau=bureau,
        )
        stage_timings["report_parser"] = report_result.duration_ms
        if not report_result.ok:
            result_data["report"] = {"errors": report_result.errors}
            return result_data
        result_data["report"] = report_result.data
        stages_completed.append("report_parser")

        tradelines = report_result.data.get("tradelines", [])

        # --- Stage 2: Classify negative tradelines ---
        neg_result = await self._run_stage(
            "negative_tradeline",
            tradelines=tradelines,
        )
        stage_timings["negative_tradeline"] = neg_result.duration_ms
        if not neg_result.ok:
            result_data["negatives"] = {"errors": neg_result.errors}
            result_data["pipeline_status"] = "partial"
            return result_data
        result_data["negatives"] = neg_result.data
        stages_completed.append("negative_tradeline")

        enriched = neg_result.data.get("tradelines", tradelines)

        # --- Stage 3: Credit score classification ---
        score_result = await self._run_stage(
            "credit_score",
            tradelines=enriched,
        )
        stage_timings["credit_score"] = score_result.duration_ms
        if not score_result.ok:
            result_data["credit_score"] = {"errors": score_result.errors}
            result_data["pipeline_status"] = "partial"
            return result_data
        result_data["credit_score"] = score_result.data
        stages_completed.append("credit_score")

        credit_tier = score_result.data.get("estimated_tier", "fair")
        dispute_priority = score_result.data.get("dispute_priority_score", 50.0)

        # --- Stage 4: Dispute strategy ---
        negatives_only = [t for t in enriched if t.get("_is_negative")]
        strategy_result = await self._run_stage(
            "dispute_strategy",
            tradelines=negatives_only,
            user_id=user_id,
            credit_tier=credit_tier,
            dispute_priority=dispute_priority,
        )
        stage_timings["dispute_strategy"] = strategy_result.duration_ms
        if not strategy_result.ok:
            result_data["strategy"] = {"errors": strategy_result.errors}
            result_data["pipeline_status"] = "partial"
            return result_data
        result_data["strategy"] = strategy_result.data
        stages_completed.append("dispute_strategy")

        if skip_letters:
            result_data["pipeline_status"] = "complete"
            return result_data

        # --- Stage 5: Letter generation ---
        if not user_info:
            result_data["pipeline_status"] = "partial"
            result_data["letters"] = {"errors": ["user_info required for letter generation"]}
            return result_data

        strategies = strategy_result.data.get("strategies", [])
        letter_result = await self._run_stage(
            "letter_generator",
            strategies=strategies,
            user_id=user_id,
            user_info=user_info,
            preview_only=preview_only,
        )
        stage_timings["letter_generator"] = letter_result.duration_ms
        if not letter_result.ok:
            result_data["letters"] = {"errors": letter_result.errors}
            result_data["pipeline_status"] = "partial"
            return result_data
        result_data["letters"] = letter_result.data
        stages_completed.append("letter_generator")

        result_data["pipeline_status"] = "complete"
        return result_data
