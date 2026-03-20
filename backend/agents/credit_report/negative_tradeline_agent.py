"""
Negative Tradeline Agent
========================

Classifies each tradeline as negative/positive and enriches the record
with severity scores and human-readable indicators.

Wraps:
    - services.advanced_parsing.negative_tradeline_classifier.NegativeTradelineClassifier

This agent is typically called *after* ReportParserAgent has produced
a list of canonical tradeline dicts.

Inputs (via execute()):
    tradelines : List[Dict]  – Normalised tradeline records from ReportParserAgent.
    user_id    : str         – Used for audit logging.

Output (AgentResult.data):
    {
        "tradelines":         List[Dict],  # same records, enriched with classification
        "negative_count":     int,
        "positive_count":     int,
        "severity_breakdown": {
            "critical": int,    # charge-offs, bankruptcies
            "high":     int,    # 90+ days late, collections
            "medium":   int,    # 30-60 days late
            "low":      int,    # minor derog remarks
        },
        "total_negative_balance": int,    # sum of balances on negative items
    }

Each tradeline dict is enriched with:
    _is_negative    : bool
    _confidence     : float   (0.0 – 1.0)
    _severity       : str     ('critical' | 'high' | 'medium' | 'low')
    _indicators     : List[str]  (human-readable reasons)
"""

from __future__ import annotations

from typing import Any, Dict, List

from agents.base import BaseAgent


class NegativeTradelineAgent(BaseAgent):
    """Classify tradelines as negative/positive with severity scoring."""

    def __init__(self) -> None:
        super().__init__()
        self._classifier = None

    def _get_classifier(self):
        """Lazy-init the NegativeTradelineClassifier."""
        if self._classifier is None:
            from services.advanced_parsing.negative_tradeline_classifier import (
                NegativeTradelineClassifier,
            )
            self._classifier = NegativeTradelineClassifier()
        return self._classifier

    async def _classify_tradeline(
        self,
        tradeline: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run multi-factor classification on a single tradeline.

        Enriches the dict in-place with _is_negative, _confidence,
        _severity, and _indicators keys.

        Args:
            tradeline: Canonical tradeline dict from ReportParserAgent.

        Returns:
            The same dict with classification fields added.
        """
        # TODO:
        # 1. Call self._get_classifier().classify(tradeline).
        # 2. Map ClassificationResult fields onto tradeline dict.
        # 3. Assign _severity based on confidence + indicator keywords.
        raise NotImplementedError

    async def _run(
        self,
        *,
        tradelines: List[Dict[str, Any]],
        user_id: str = "",
    ) -> Dict[str, Any]:
        """Classify all tradelines and return enriched list with summary.

        Args:
            tradelines: List of canonical tradeline dicts.
            user_id:    Owner UUID (for audit logging).

        Returns:
            Dict with keys: tradelines (enriched), negative_count,
            positive_count, severity_breakdown, total_negative_balance.
        """
        # TODO:
        # 1. Iterate tradelines, call _classify_tradeline() on each.
        # 2. Compute aggregate counts and severity_breakdown.
        # 3. Sum balances on negative items.
        # 4. Return structured dict.
        raise NotImplementedError
