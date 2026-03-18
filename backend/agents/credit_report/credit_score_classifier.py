"""
Credit Score Classifier Agent
=============================

Estimates a user's credit-risk tier from their tradeline profile.
This is NOT a FICO score — it is a simplified risk classification
used to guide dispute prioritisation and product recommendations.

Tiers:
    excellent   700+   – Few or no negative items.
    good        650-699 – Minor derogs, mostly paid on time.
    fair        550-649 – Multiple lates or a single collection.
    poor        450-549 – Charge-offs, multiple collections.
    very_poor   <450    – Bankruptcy, foreclosure, heavy derogs.

Inputs (via execute()):
    tradelines     : List[Dict]  – Enriched tradeline list (post-NegativeTradelineAgent).
    reported_score : int | None  – Self-reported score from user profile (optional).

Output (AgentResult.data):
    {
        "estimated_tier":       str,    # 'excellent' | 'good' | 'fair' | 'poor' | 'very_poor'
        "estimated_range":      str,    # '550-649'
        "confidence":           float,  # 0.0-1.0 based on data completeness
        "risk_factors":         List[str],   # top 3-5 factors hurting score
        "positive_factors":     List[str],   # top 3-5 factors helping score
        "recommendation_tier":  str,    # 'aggressive' | 'moderate' | 'conservative'
        "dispute_priority_score": float, # 0-100, higher = more urgent to dispute
    }
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agents.base import BaseAgent


class CreditScoreClassifier(BaseAgent):
    """Estimate credit-risk tier from tradeline data."""

    # Score-range boundaries for tier assignment
    TIERS = {
        "excellent":  (700, 850),
        "good":       (650, 699),
        "fair":       (550, 649),
        "poor":       (450, 549),
        "very_poor":  (300, 449),
    }

    def __init__(self) -> None:
        super().__init__()

    async def _compute_heuristic_score(
        self,
        tradelines: List[Dict[str, Any]],
    ) -> int:
        """Derive a rough numeric score from tradeline health indicators.

        Factors considered:
            - Ratio of negative to total tradelines
            - Severity distribution (critical items penalised more)
            - Average account age
            - Total outstanding negative balance
            - Number of inquiries (if available)

        Args:
            tradelines: Enriched tradeline list with _is_negative, _severity.

        Returns:
            Estimated integer score in the 300-850 range.
        """
        # TODO:
        # 1. Count negatives vs positives.
        # 2. Weight by severity (_severity field).
        # 3. Factor in account age and utilisation.
        # 4. Clamp to 300-850 range.
        raise NotImplementedError

    async def _identify_risk_factors(
        self,
        tradelines: List[Dict[str, Any]],
    ) -> List[str]:
        """Return top risk factors dragging the score down.

        Args:
            tradelines: Enriched tradeline list.

        Returns:
            List of 3-5 human-readable risk factor strings, ordered by impact.
        """
        # TODO: Analyse _indicators on negative tradelines, group, and rank.
        raise NotImplementedError

    async def _identify_positive_factors(
        self,
        tradelines: List[Dict[str, Any]],
    ) -> List[str]:
        """Return top positive factors supporting the score.

        Args:
            tradelines: Enriched tradeline list.

        Returns:
            List of 3-5 human-readable positive factor strings.
        """
        # TODO: Identify long-standing accounts, zero-balance revolving, etc.
        raise NotImplementedError

    async def _determine_dispute_priority(
        self,
        tradelines: List[Dict[str, Any]],
        tier: str,
    ) -> float:
        """Calculate a 0-100 dispute urgency score.

        Higher score = user would benefit more from disputing now.

        Args:
            tradelines: Enriched list.
            tier:       Current estimated tier string.

        Returns:
            Float 0-100.
        """
        # TODO:
        # 1. Users near a tier boundary get higher priority.
        # 2. Recent negative items are more impactful to dispute.
        # 3. High-balance negatives get extra weight.
        raise NotImplementedError

    async def _run(
        self,
        *,
        tradelines: List[Dict[str, Any]],
        reported_score: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Classify credit risk and generate dispute-priority score.

        Args:
            tradelines:     Enriched tradeline list (post-NegativeTradelineAgent).
            reported_score: Optional user-provided score (used to calibrate).

        Returns:
            Dict with estimated_tier, estimated_range, confidence,
            risk_factors, positive_factors, recommendation_tier,
            dispute_priority_score.
        """
        # TODO:
        # 1. Compute heuristic score (blend with reported_score if available).
        # 2. Map score to tier via TIERS boundaries.
        # 3. Compute confidence based on data completeness.
        # 4. Identify risk and positive factors.
        # 5. Compute dispute priority score.
        # 6. Determine recommendation_tier:
        #      aggressive  = poor/very_poor (dispute everything possible)
        #      moderate    = fair (dispute high-impact items)
        #      conservative = good/excellent (dispute only clear errors)
        raise NotImplementedError
