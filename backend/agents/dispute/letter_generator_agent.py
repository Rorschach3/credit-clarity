"""
Letter Generator Agent
======================

Generates FCRA-compliant dispute letters for selected tradelines.

Wraps the existing Supabase edge function ``generate-dispute-letter``
and adds:
    - Multi-tradeline batch generation (one letter per bureau, many items).
    - Letter preview (HTML) before PDF commit.
    - Rate-limit awareness (checks usage before generation).
    - Audit logging via notification_log.

Integrations:
    - supabase/functions/generate-dispute-letter/index.ts  (edge function)
    - services.rate_limit_service.RateLimitService          (usage check)
    - services.email_service.EmailService                   (notification)

Inputs (via execute()):
    strategies  : List[Dict]  – Output of DisputeStrategyAgent (selected items).
    user_id     : str         – Owner.
    user_info   : Dict        – Name, address fields for letter header.
    preview_only: bool        – If True, return HTML preview without creating PDF.

Output (AgentResult.data):
    {
        "letters": [
            {
                "bureau":         str,
                "tradeline_ids":  List[str],
                "dispute_reason": str,
                "html_preview":   str,       # rendered letter text
                "pdf_url":        str | None, # Supabase storage URL (None if preview)
                "letter_id":      str,        # dispute record ID
            },
            ...
        ],
        "total_generated":   int,
        "rate_limit_remaining": int,
    }
"""

from __future__ import annotations

from typing import Any, Dict, List

from agents.base import BaseAgent


# Bureau mailing addresses (matches mailing.py BUREAU_ADDRESSES)
BUREAU_ADDRESSES = {
    "experian": {
        "name": "Experian",
        "address_line1": "PO Box 4500",
        "city": "Allen",
        "state": "TX",
        "zip": "75013",
    },
    "equifax": {
        "name": "Equifax",
        "address_line1": "PO Box 740256",
        "city": "Atlanta",
        "state": "GA",
        "zip": "30374",
    },
    "transunion": {
        "name": "TransUnion",
        "address_line1": "PO Box 2000",
        "city": "Chester",
        "state": "PA",
        "zip": "19016",
    },
}


class LetterGeneratorAgent(BaseAgent):
    """Generate FCRA dispute letters grouped by bureau."""

    def __init__(self) -> None:
        super().__init__()

    async def _check_rate_limit(self, user_id: str) -> Dict[str, Any]:
        """Check if the user has remaining letter-generation credits.

        Args:
            user_id: Supabase user UUID.

        Returns:
            Dict with 'allowed' (bool), 'remaining' (int), 'reset_at' (str|None).
        """
        # TODO:
        # 1. Call rate_limit_service.check_letter_limit(user_id).
        # 2. Return result dict.
        raise NotImplementedError

    async def _group_by_bureau(
        self,
        strategies: List[Dict[str, Any]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group dispute strategies by target bureau.

        One letter per bureau, containing all tradelines for that bureau.

        Args:
            strategies: List of strategy dicts from DisputeStrategyAgent.

        Returns:
            Dict mapping bureau name to list of strategy dicts.
        """
        # TODO: Group strategies by 'bureau' key.
        raise NotImplementedError

    async def _render_letter_html(
        self,
        bureau: str,
        items: List[Dict[str, Any]],
        user_info: Dict[str, Any],
    ) -> str:
        """Render a dispute letter as HTML for preview.

        Args:
            bureau:    Target bureau name.
            items:     Tradeline strategy dicts for this bureau.
            user_info: Name, address for letter header.

        Returns:
            HTML string of the rendered letter.
        """
        # TODO:
        # 1. Build letter template with user's return address.
        # 2. Include bureau address from BUREAU_ADDRESSES.
        # 3. List each disputed tradeline with reason.
        # 4. Include FCRA citation and signature block.
        raise NotImplementedError

    async def _generate_pdf(
        self,
        html: str,
        user_id: str,
        bureau: str,
    ) -> str:
        """Call generate-dispute-letter edge function to produce PDF.

        Args:
            html:    Rendered letter HTML.
            user_id: Owner UUID.
            bureau:  Bureau name (for filename).

        Returns:
            Supabase storage URL of the generated PDF.
        """
        # TODO:
        # 1. Call Supabase edge function generate-dispute-letter.
        # 2. Upload PDF to storage.
        # 3. Return public URL.
        raise NotImplementedError

    async def _log_generation(
        self,
        user_id: str,
        letter_id: str,
        bureau: str,
        tradeline_ids: List[str],
    ) -> None:
        """Write notification_log entry for the generated letter.

        Args:
            user_id:       Owner UUID.
            letter_id:     Dispute record ID.
            bureau:        Target bureau.
            tradeline_ids: IDs of disputed tradelines.
        """
        # TODO:
        # 1. Call database_optimizer.upsert_notification_log() with
        #    notification_type='letter_sent'.
        # 2. Enqueue email notification via email_worker.send_notification_email.delay().
        raise NotImplementedError

    async def _run(
        self,
        *,
        strategies: List[Dict[str, Any]],
        user_id: str,
        user_info: Dict[str, Any],
        preview_only: bool = False,
    ) -> Dict[str, Any]:
        """Generate dispute letters for all selected strategies.

        Args:
            strategies:   Dispute strategy dicts from DisputeStrategyAgent.
            user_id:      Supabase user UUID.
            user_info:    Dict with name, address_line1, city, state, zip.
            preview_only: If True, return HTML preview without creating PDF.

        Returns:
            Dict with letters list, total_generated, rate_limit_remaining.
        """
        # TODO:
        # 1. Check rate limit; abort early if exceeded.
        # 2. Group strategies by bureau.
        # 3. For each bureau group:
        #    a. Render HTML preview.
        #    b. If not preview_only, generate PDF and store URL.
        #    c. Create dispute record in Supabase.
        #    d. Log generation.
        # 4. Return structured result.
        raise NotImplementedError
