"""
Dispute Strategy Agent
======================

Analyses a user's negative tradelines and recommends the optimal
dispute approach per tradeline per bureau.

Strategy considerations:
    - FCRA violation likelihood (missing data, mixed-file indicators)
    - Bureau-specific success patterns
    - Statute of limitations for the debt type and state
    - Impact on estimated credit tier (dispute items near tier boundary first)
    - Previous dispute history (avoid re-disputing recently resolved items)

Integrations:
    - Reads dispute history from Supabase ``disputes`` table.
    - Uses CreditScoreClassifier output to rank by score impact.
    - Optionally calls LLM (Gemini) for nuanced strategy reasoning.

Inputs (via execute()):
    tradelines          : List[Dict]  – Enriched tradelines (post-classification).
    user_id             : str         – For fetching dispute history.
    credit_tier         : str         – From CreditScoreClassifier.
    dispute_priority    : float       – 0-100 urgency score.

Output (AgentResult.data):
    {
        "strategies": [
            {
                "tradeline_id":    str,
                "creditor":        str,
                "bureau":          str,
                "dispute_reason":  str,     # one of 12 FCRA reasons
                "confidence":      float,   # 0.0-1.0 estimated success
                "priority_rank":   int,     # 1 = dispute first
                "rationale":       str,     # human-readable explanation
                "statute_expired": bool,    # True if past SOL
            },
            ...
        ],
        "recommended_batch_size":  int,   # how many to dispute at once
        "estimated_tier_after":    str,   # projected tier if disputes succeed
    }
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agents.base import BaseAgent


# The 12 FCRA dispute reasons (mirrors DisputeReasonsStep.tsx)
FCRA_DISPUTE_REASONS = [
    "not_my_account",
    "paid_in_full",
    "incorrect_balance",
    "past_statute",
    "incorrect_payment_history",
    "incorrect_status",
    "duplicate",
    "identity_theft",
    "incorrect_ownership",
    "incorrect_limit",
    "bankruptcy_included",
    "incorrect_dol",
]


class DisputeStrategyAgent(BaseAgent):
    """Recommend dispute actions for each negative tradeline."""

    def __init__(self) -> None:
        super().__init__()

    async def _fetch_dispute_history(
        self,
        user_id: str,
    ) -> List[Dict[str, Any]]:
        """Load past disputes from Supabase to avoid re-disputing.

        Args:
            user_id: Supabase user UUID.

        Returns:
            List of dispute records with tradeline_id, bureau, status, created_at.
        """
        # TODO:
        # 1. Query disputes table via database_optimizer.
        # 2. Filter to user_id.
        # 3. Return list of dicts.
        raise NotImplementedError

    async def _select_dispute_reason(
        self,
        tradeline: Dict[str, Any],
    ) -> str:
        """Pick the best FCRA dispute reason for a tradeline.

        Uses the tradeline's _indicators list, status, and balance
        to select from FCRA_DISPUTE_REASONS.

        Args:
            tradeline: Enriched tradeline dict.

        Returns:
            One of the FCRA_DISPUTE_REASONS strings.
        """
        # TODO:
        # 1. Check _indicators for identity theft markers → 'identity_theft'.
        # 2. Check if balance == 0 → 'paid_in_full'.
        # 3. Check if account is past SOL → 'past_statute'.
        # 4. Fallback: 'incorrect_status'.
        raise NotImplementedError

    async def _estimate_success_probability(
        self,
        tradeline: Dict[str, Any],
        bureau: str,
        reason: str,
    ) -> float:
        """Estimate probability of successful dispute (0.0 – 1.0).

        Args:
            tradeline: Enriched tradeline dict.
            bureau:    Target bureau name.
            reason:    Selected dispute reason.

        Returns:
            Float confidence score.
        """
        # TODO:
        # 1. Missing-data tradelines have higher success rates.
        # 2. Older accounts have higher success rates.
        # 3. Certain bureaus respond more favourably to certain reasons.
        raise NotImplementedError

    async def _rank_strategies(
        self,
        strategies: List[Dict[str, Any]],
        credit_tier: str,
    ) -> List[Dict[str, Any]]:
        """Sort strategies by expected credit-score impact.

        Args:
            strategies: List of strategy dicts with confidence scores.
            credit_tier: Current estimated tier.

        Returns:
            Same list sorted by priority_rank (1 = highest priority).
        """
        # TODO:
        # 1. Weight by confidence * balance (high-balance high-confidence first).
        # 2. Boost items whose removal would push user to next tier.
        # 3. Assign priority_rank 1..N.
        raise NotImplementedError

    async def _run(
        self,
        *,
        tradelines: List[Dict[str, Any]],
        user_id: str,
        credit_tier: str = "fair",
        dispute_priority: float = 50.0,
    ) -> Dict[str, Any]:
        """Generate dispute strategies for all negative tradelines.

        Args:
            tradelines:       Enriched tradeline list (only negatives).
            user_id:          For fetching dispute history.
            credit_tier:      From CreditScoreClassifier.
            dispute_priority: 0-100 urgency score.

        Returns:
            Dict with strategies list, recommended_batch_size,
            estimated_tier_after.
        """
        # TODO:
        # 1. Filter to _is_negative == True only.
        # 2. Fetch dispute history, exclude recently-disputed items.
        # 3. For each negative tradeline × bureau, build strategy dict.
        # 4. Rank and assign priority.
        # 5. Determine recommended_batch_size (typically 3-5 per bureau).
        # 6. Project estimated_tier_after if top items are removed.
        raise NotImplementedError
