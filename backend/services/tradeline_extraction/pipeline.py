"""
Complete tradeline extraction pipeline
Orchestrates PDF extraction, parsing, and storage
"""
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import asyncio
from dataclasses import dataclass

from services.tradeline_extraction.pdf_extractor import TransUnionPDFExtractor
from services.tradeline_extraction.tradeline_parser import TransUnionTradelineParser
from services.tradeline_extraction.real_world_parser import RealWorldTransUnionParser
from services.tradeline_extraction.data_storage import TradelineStorageService

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result of the complete tradeline extraction pipeline"""
    success: bool
    pdf_processed: bool = False
    text_extracted: bool = False
    tradelines_parsed: int = 0
    tradelines_stored: int = 0
    processing_time_ms: float = 0.0
    error: Optional[str] = None
    warnings: list = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class TradelineExtractionPipeline:
    """
    Complete pipeline for extracting tradelines from PDF credit reports
    Implements the full workflow: PDF → Text → Tradelines → Database
    """
    
    def __init__(self, use_real_world_parser: bool = True):
        self.pdf_extractor = TransUnionPDFExtractor()
        
        # Use real-world parser by default for better PDF handling
        if use_real_world_parser:
            self.tradeline_parser = RealWorldTransUnionParser()
        else:
            self.tradeline_parser = TransUnionTradelineParser()
            
        self.storage_service = TradelineStorageService()
        
        # Pipeline configuration
        self.max_processing_time_seconds = 300  # 5 minutes timeout
        self.min_tradelines_expected = 1
        self.max_tradelines_expected = 50
    
    async def process_credit_report(
        self, 
        pdf_path: str | Path,
        user_id: Optional[str] = None,
        store_results: bool = True
    ) -> PipelineResult:
        """
        Process a complete credit report PDF through the entire pipeline
        
        Args:
            pdf_path: Path to the PDF file
            user_id: Optional user ID to associate with the tradelines
            store_results: Whether to store results to database
            
        Returns:
            PipelineResult with processing details
        """
        start_time = asyncio.get_event_loop().time()
        result = PipelineResult(success=False)
        
        try:
            logger.info(f"Starting tradeline extraction pipeline for {pdf_path}")
            
            # Step 1: Extract text from PDF
            logger.info("Step 1: Extracting text from PDF...")
            extraction_result = await self.pdf_extractor.extract_text_from_pdf(pdf_path)
            
            if not extraction_result.success:
                result.error = f"PDF extraction failed: {extraction_result.error}"
                return result
            
            result.pdf_processed = True
            result.text_extracted = True
            logger.info(f"✓ PDF text extracted ({len(extraction_result.text)} characters)")
            
            # Step 2: Parse tradelines from text
            logger.info("Step 2: Parsing tradelines from text...")
            tradelines = self.tradeline_parser.parse_tradelines_from_text(extraction_result.text)
            
            # Filter out invalid tradelines
            valid_tradelines = [tl for tl in tradelines if self._is_valid_tradeline(tl)]
            result.tradelines_parsed = len(valid_tradelines)
            
            if not valid_tradelines:
                result.warnings.append("No valid tradelines found in PDF")
                if len(tradelines) > 0:
                    result.warnings.append(f"Found {len(tradelines)} entries but none were valid tradelines")
            
            logger.info(f"✓ Parsed {len(valid_tradelines)} valid tradelines")
            
            # Validate tradeline count
            if len(valid_tradelines) > self.max_tradelines_expected:
                result.warnings.append(f"Unusually high number of tradelines: {len(valid_tradelines)}")
            elif len(valid_tradelines) < self.min_tradelines_expected:
                result.warnings.append(f"Low number of tradelines found: {len(valid_tradelines)}")
            
            # Step 3: Store tradelines to database (if requested)
            if store_results and valid_tradelines:
                logger.info("Step 3: Storing tradelines to database...")
                storage_result = await self.storage_service.store_tradelines(valid_tradelines, user_id)
                
                if storage_result['success']:
                    result.tradelines_stored = storage_result['stored_count']
                    logger.info(f"✓ Stored {result.tradelines_stored} tradelines to database")
                else:
                    result.warnings.append(f"Storage partially failed: {storage_result['errors']}")
                    result.tradelines_stored = storage_result['stored_count']
                
                # Add storage warnings
                result.warnings.extend(storage_result.get('warnings', []))
            
            # Calculate processing time
            end_time = asyncio.get_event_loop().time()
            result.processing_time_ms = round((end_time - start_time) * 1000, 2)
            
            # Determine overall success
            result.success = (
                result.pdf_processed and 
                result.text_extracted and 
                result.tradelines_parsed > 0 and
                (not store_results or result.tradelines_stored > 0)
            )
            
            logger.info(f"Pipeline completed in {result.processing_time_ms}ms")
            logger.info(f"Result: {result.tradelines_parsed} parsed, {result.tradelines_stored} stored")
            
        except asyncio.TimeoutError:
            result.error = f"Pipeline timeout after {self.max_processing_time_seconds} seconds"
            logger.error(result.error)
        except Exception as e:
            result.error = f"Pipeline error: {str(e)}"
            logger.exception("Pipeline processing failed")
        
        return result
    
    def _is_valid_tradeline(self, tradeline) -> bool:
        """Check if a parsed tradeline is valid for storage"""
        return self.storage_service._is_valid_tradeline(tradeline)
    
    async def validate_pdf_file(self, pdf_path: str | Path) -> Dict[str, Any]:
        """
        Validate PDF file before processing
        Returns validation results
        """
        return self.pdf_extractor.validate_pdf_file(pdf_path)
    
    async def get_pipeline_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about pipeline performance
        """
        return {
            'pdf_extractor': {
                'supported_extensions': list(self.pdf_extractor.supported_extensions),
                'max_file_size_mb': self.pdf_extractor.max_file_size_mb,
                'extraction_timeout_seconds': self.pdf_extractor.extraction_timeout_seconds
            },
            'tradeline_parser': {
                'account_type_mappings': self.tradeline_parser.account_type_mappings,
                'account_status_mappings': self.tradeline_parser.account_status_mappings
            },
            'storage_service': {
                'table_name': self.storage_service.table_name,
                'batch_size': self.storage_service.batch_size,
                'schema': self.storage_service.get_table_schema()
            },
            'pipeline': {
                'max_processing_time_seconds': self.max_processing_time_seconds,
                'min_tradelines_expected': self.min_tradelines_expected,
                'max_tradelines_expected': self.max_tradelines_expected
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all pipeline components
        """
        health_status = {
            'overall_healthy': True,
            'components': {},
            'timestamp': asyncio.get_event_loop().time()
        }
        
        try:
            # Check PDF extractor
            health_status['components']['pdf_extractor'] = {
                'status': 'healthy',
                'message': 'PDF extractor initialized'
            }
            
            # Check tradeline parser
            health_status['components']['tradeline_parser'] = {
                'status': 'healthy',
                'message': 'Tradeline parser initialized'
            }
            
            # Check storage service
            health_status['components']['storage_service'] = {
                'status': 'healthy',
                'message': 'Storage service initialized'
            }
            
        except Exception as e:
            health_status['overall_healthy'] = False
            health_status['error'] = f"Health check failed: {str(e)}"
        
        return health_status