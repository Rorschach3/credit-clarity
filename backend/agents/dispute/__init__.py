"""
Dispute Agents
==============

Agents that handle the dispute lifecycle:
    1. DisputeStrategyAgent   – Recommend which items to dispute and how.
    2. LetterGeneratorAgent   – Produce FCRA-compliant dispute letters.
    3. BureauResponseAgent    – Track responses and update dispute status.

These agents consume the enriched tradeline list produced by the
credit_report agents and interface with the existing Supabase edge
functions and Lob mailing service.
"""

from agents.dispute.dispute_strategy_agent import DisputeStrategyAgent
from agents.dispute.letter_generator_agent import LetterGeneratorAgent
from agents.dispute.bureau_response_agent import BureauResponseAgent

__all__ = [
    "DisputeStrategyAgent",
    "LetterGeneratorAgent",
    "BureauResponseAgent",
]
