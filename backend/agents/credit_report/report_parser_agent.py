"""
Report Parser Agent
===================

Extracts structured tradeline data from uploaded credit-report PDFs.

Wraps the existing extraction services:
    - services.optimized_processor.OptimizedCreditReportProcessor
    - services.tradeline_extraction.pipeline.TradelineExtractionPipeline
    - services.enhanced_gemini_processor.EnhancedGeminiProcessor

The agent adds retry logic, multi-bureau routing, and normalises
output into a consistent list of tradeline dicts regardless of which
internal parser was used.

Inputs (via execute()):
    pdf_path : str          – Local path to the uploaded PDF.
    user_id  : str          – Owner of the report (for storage / RLS).
    bureau   : str | None   – 'experian' | 'equifax' | 'transunion' | None (auto-detect).

Output (AgentResult.data):
    {
        "tradelines":       List[Dict],   # normalised tradeline records
        "bureau_detected":  str,          # detected bureau name
        "pages_processed":  int,
        "extraction_method": str,         # 'gemini' | 'document_ai' | 'pdfplumber'
        "raw_text_length":  int,
    }
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.base import BaseAgent


class ReportParserAgent(BaseAgent):
    """Parse a credit-report PDF into structured tradeline dicts."""

    def __init__(self) -> None:
        super().__init__()

        # Lazy-import heavy services so the module loads fast.
        # Actual instances are created in _run() on first use.
        self._pipeline = None
        self._optimized_processor = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_pipeline(self):
        """Lazy-init the TradelineExtractionPipeline."""
        if self._pipeline is None:
            from services.tradeline_extraction.pipeline import (
                TradelineExtractionPipeline,
            )
            self._pipeline = TradelineExtractionPipeline(use_real_world_parser=True)
        return self._pipeline

    def _get_optimized_processor(self):
        """Lazy-init the OptimizedCreditReportProcessor (Gemini + Doc AI)."""
        if self._optimized_processor is None:
            from services.optimized_processor import (
                OptimizedCreditReportProcessor,
            )
            self._optimized_processor = OptimizedCreditReportProcessor()
        return self._optimized_processor

    async def _detect_bureau(self, text: str) -> str:
        """Identify which bureau issued the report from raw text.

        Args:
            text: First ~2000 chars of extracted PDF text.

        Returns:
            'experian' | 'equifax' | 'transunion' | 'unknown'
        """
        # TODO: Implement keyword / regex heuristic or call LLM classifier.
        raise NotImplementedError

    async def _normalise_tradelines(
        self,
        raw: List[Dict[str, Any]],
        bureau: str,
    ) -> List[Dict[str, Any]]:
        """Map parser-specific keys to the canonical tradeline schema.

        Canonical keys:
            creditor, account_number, balance, credit_limit, payment_status,
            date_opened, date_reported, bureau, account_type, remarks, …

        Args:
            raw:    Tradeline dicts as returned by the underlying parser.
            bureau: Bureau name for tagging.

        Returns:
            List of tradeline dicts with canonical keys.
        """
        # TODO: Use EnhancedTradelineNormalizer from utils.
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Core execution
    # ------------------------------------------------------------------

    async def _run(
        self,
        *,
        pdf_path: str,
        user_id: str,
        bureau: Optional[str] = None,
        store_results: bool = False,
    ) -> Dict[str, Any]:
        """Execute the full PDF → tradelines extraction.

        Strategy:
            1. Try TradelineExtractionPipeline (pdfplumber + regex parsers).
            2. On low yield (<3 tradelines), fall back to OptimizedProcessor
               (Gemini LLM + Document AI OCR).
            3. Normalise and return merged results.

        Args:
            pdf_path:      Local filesystem path to the PDF.
            user_id:       Supabase user UUID.
            bureau:        Optional bureau hint; auto-detected if omitted.
            store_results: If True, persist tradelines to Supabase immediately.

        Returns:
            Dict with keys: tradelines, bureau_detected, pages_processed,
            extraction_method, raw_text_length.
        """
        # TODO:
        # 1. Validate pdf_path exists and file size is within limits.
        # 2. Run self._get_pipeline().process_credit_report(pdf_path, user_id).
        # 3. If result.tradelines_parsed < 3, run self._get_optimized_processor().
        # 4. Auto-detect bureau if not provided.
        # 5. Normalise tradeline dicts via _normalise_tradelines().
        # 6. Optionally persist via TradelineStorageService.
        # 7. Return structured dict.
        raise NotImplementedError
