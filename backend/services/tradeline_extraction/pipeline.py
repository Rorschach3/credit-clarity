"""
Tradeline Extraction Pipeline
Orchestrates PDF extraction, parsing, normalization, validation, and storage.
"""
import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.tradeline_extraction.data_storage import TradelineStorageService
from services.tradeline_extraction.pdf_extractor import TransUnionPDFExtractor
from services.tradeline_extraction.tradeline_parser import RealWorldTransUnionParser, TransUnionTradelineParser, ParsedTradeline
from services.tradeline_extraction.validation_pipeline import TradelineValidationPipeline
from utils.enhanced_tradeline_normalizer import EnhancedTradelineNormalizer

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result from the full tradeline extraction pipeline."""
    success: bool = False
    pdf_processed: bool = False
    text_extracted: bool = False
    tradelines_parsed: int = 0
    tradelines_validated: int = 0
    tradelines_stored: int = 0
    processing_time_ms: float = 0.0
    validation_summary: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TradelineExtractionPipeline:
    """Orchestrates extraction, parsing, normalization, validation, and storage."""

    def __init__(self, use_real_world_parser: bool = True):
        self.pdf_extractor = TransUnionPDFExtractor()
        self.parser = RealWorldTransUnionParser() if use_real_world_parser else TransUnionTradelineParser()
        self.storage_service = TradelineStorageService()
        self.normalizer = EnhancedTradelineNormalizer()
        self.validator = TradelineValidationPipeline()

        self.max_processing_time_seconds = 300
        self.min_tradelines_expected = 1
        self.max_tradelines_expected = 50

    async def process_credit_report(
        self,
        pdf_path: str | Path,
        user_id: Optional[str] = None,
        store_results: bool = True
    ) -> PipelineResult:
        """Run the full pipeline against a PDF credit report."""
        start_time = asyncio.get_event_loop().time()
        result = PipelineResult()

        try:
            logger.info(f"Starting pipeline for {pdf_path}")
            validation = self.pdf_extractor.validate_pdf_file(Path(pdf_path))
            if not validation['valid']:
                result.error = f"PDF validation failed: {'; '.join(validation['errors'])}"
                return result

            extraction = await self.pdf_extractor.extract_text_from_pdf(pdf_path)
            if not extraction.success or not extraction.text:
                result.error = extraction.error or "PDF extraction returned no text"
                return result

            result.pdf_processed = True
            result.text_extracted = True
            logger.info(f"Extracted {len(extraction.text)} characters from {pdf_path}")

            parsed_tradelines = self.parser.parse_tradelines_from_text(extraction.text)
            result.tradelines_parsed = len(parsed_tradelines)

            if not parsed_tradelines:
                result.warnings.append("No tradelines parsed from extracted text")

            validation_summary = []
            valid_tradelines = []

            for tradeline in parsed_tradelines:
                normalized = self.normalizer.normalize_tradeline(tradeline.to_dict())
                self._apply_normalized_data(tradeline, normalized)

                validation_result = self.validator.validate_tradeline(normalized)
                validation_summary.append(validation_result)

                if validation_result.get('valid') and self._is_valid_tradeline(tradeline):
                    valid_tradelines.append(tradeline)
                else:
                    warnings = validation_result.get('errors', []) + validation_result.get('warnings', [])
                    if warnings:
                        result.warnings.append(
                            f"Tradeline skipped ({tradeline.creditor_name or 'unknown'}): {warnings}"
                        )

            result.validation_summary = validation_summary
            result.tradelines_validated = len(validation_summary)

            validation_scores = [
                entry.get('score', 0.0) for entry in validation_summary if isinstance(entry.get('score'), (int, float))
            ]
            if validation_scores:
                avg_score = sum(validation_scores) / len(validation_scores)
                result.metadata['validation_average_score'] = round(avg_score, 2)

            if not valid_tradelines:
                result.warnings.append("No valid tradelines after validation")

            if store_results and valid_tradelines:
                storage = await self.storage_service.store_tradelines(valid_tradelines, user_id)
                if storage.get('success'):
                    result.tradelines_stored = storage.get('stored_count', 0)
                else:
                    result.warnings.append("Storage reported issues: " + ", ".join(storage.get('errors', [])))
                    result.tradelines_stored = storage.get('stored_count', 0)
                result.warnings.extend(storage.get('warnings', []))

            if len(valid_tradelines) > self.max_tradelines_expected:
                result.warnings.append(f"High tradeline count: {len(valid_tradelines)}")
            elif len(valid_tradelines) < self.min_tradelines_expected:
                result.warnings.append(f"Low tradeline count: {len(valid_tradelines)}")

            end_time = asyncio.get_event_loop().time()
            result.processing_time_ms = round((end_time - start_time) * 1000, 2)
            result.success = (
                result.pdf_processed and
                result.text_extracted and
                len(valid_tradelines) > 0 and
                (not store_results or result.tradelines_stored > 0)
            )

            logger.info(
                f"Pipeline finished: parsed={result.tradelines_parsed}, "
                f"validated={result.tradelines_validated}, stored={result.tradelines_stored}, "
                f"time={result.processing_time_ms}ms"
            )

        except asyncio.TimeoutError:
            result.error = "Pipeline timeout exceeded"
            logger.error(result.error)
        except Exception as exc:
            result.error = f"Pipeline failure: {exc}"
            logger.exception("Pipeline unexpected failure")

        return result

    def _apply_normalized_data(self, tradeline: ParsedTradeline, normalized: Dict[str, Any]) -> None:
        """Copy normalized values back into the ParsedTradeline object."""
        fields_to_copy = [
            'creditor_name', 'account_number', 'account_balance', 'credit_limit',
            'monthly_payment', 'date_opened', 'account_type', 'account_status',
            'credit_bureau', 'payment_history', 'comments', 'user_id', 'is_negative'
        ]

        for field in fields_to_copy:
            if field in normalized and hasattr(tradeline, field):
                setattr(tradeline, field, normalized[field])

        if 'negative_confidence' in normalized:
            setattr(tradeline, 'negative_confidence', normalized['negative_confidence'])
        if 'negative_indicators' in normalized:
            setattr(tradeline, 'negative_indicators', normalized['negative_indicators'])

    def _is_valid_tradeline(self, tradeline: ParsedTradeline) -> bool:
        """Delegate validity check to the storage service helper."""
        return self.storage_service._is_valid_tradeline(tradeline)

    async def validate_pdf_file(self, pdf_path: str | Path) -> Dict[str, Any]:
        """Validate a PDF file without processing it."""
        return self.pdf_extractor.validate_pdf_file(pdf_path)

    async def get_pipeline_statistics(self) -> Dict[str, Any]:
        """Return current pipeline configuration for monitoring."""
        return {
            'pdf_extractor': {
                'supported_extensions': list(self.pdf_extractor.supported_extensions),
                'max_file_size_mb': self.pdf_extractor.max_file_size_mb,
                'extraction_timeout_seconds': self.pdf_extractor.extraction_timeout_seconds
            },
            'parser': {
                'parsing_method': self.parser.__class__.__name__,
            },
            'storage': {
                'table_name': self.storage_service.table_name,
                'batch_size': self.storage_service.batch_size
            },
            'pipeline': {
                'max_processing_time_seconds': self.max_processing_time_seconds,
                'min_tradelines_expected': self.min_tradelines_expected,
                'max_tradelines_expected': self.max_tradelines_expected
            }
        }

    async def health_check(self) -> Dict[str, Any]:
        """Check health of pipeline components."""
        status = {
            'overall_healthy': True,
            'components': {},
            'timestamp': asyncio.get_event_loop().time()
        }

        status['components']['pdf_extractor'] = {
            'status': 'healthy',
            'message': 'PDF extractor initialized'
        }
        status['components']['parser'] = {
            'status': 'healthy',
            'message': f"{self.parser.__class__.__name__} initialized"
        }
        status['components']['storage'] = {
            'status': 'healthy',
            'message': 'Storage service initialized'
        }

        return status
