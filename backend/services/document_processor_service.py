import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime

from .document_ai_service import DocumentAIService
from .storage_service import StorageService
from .job_service import JobService
from models.tradeline_models import ProcessingStatus, DocumentAIResult
from .llm_parser_service import LLMParserService
from .ocr_service import OCRService
from .pdf_chunking_service import PDFChunkingService
from ..enhanced_bureau_detection import EnhancedBureauDetector

logger = logging.getLogger(__name__)

class DocumentProcessorService:
    """Main document processing orchestrator"""
    
    def __init__(self, storage_service: StorageService, job_service: JobService,
                 document_ai_service: DocumentAIService = None, llm_parser: LLMParserService = None,
                 ocr_service: OCRService = None, chunking_service: PDFChunkingService = None,
                 bureau_detector: EnhancedBureauDetector = None):
        self.storage = storage_service
        self.job_service = job_service
        self.document_ai = document_ai_service or DocumentAIService()
        self.llm_parser = llm_parser or LLMParserService(config=None) # config will be set by the caller
        self.ocr_service = ocr_service or OCRService()
        self.chunking_service = chunking_service or PDFChunkingService(max_pages_per_chunk=30)
        self.bureau_detector = bureau_detector or EnhancedBureauDetector()
    
    async def document_ai_workflow(self, job_id: str) -> bool:
        """Main workflow for Document AI processing phase with PDF chunking"""
        try:
            logger.info(f"Starting Document AI workflow with PDF chunking for job {job_id}")
            
            # Update job status
            await self.job_service.update_job_status(job_id, ProcessingStatus.PROCESSING)
            
            # Retrieve uploaded file
            file_content, file_metadata = await self.get_stored_file(job_id)
            filename = file_metadata.get('file_name', 'unknown')
            
            # Step 1: Add OCR text layer to PDF using OCRmyPDF + Tesseract
            logger.info(f"Adding OCR text layer to PDF for job {job_id}")
            ocr_file_content, ocr_success = await self.ocr_service.add_ocr_layer(file_content, filename)
            
            if ocr_success:
                logger.info(f"OCR processing successful for job {job_id}, using OCR'd PDF")
                await self.storage.store_ocr_pdf(job_id, ocr_file_content)
                processed_file_content = ocr_file_content
            else:
                logger.warning(f"OCR processing failed for job {job_id}, using original PDF")
                processed_file_content = file_content
            
            # Step 2: Split PDF into chunks (≤30 pages each)
            logger.info(f"Splitting PDF into chunks for job {job_id}")
            pdf_chunks = await self.chunking_service.split_pdf(processed_file_content, filename)
            logger.info(f"Split PDF into {len(pdf_chunks)} chunk(s) for job {job_id}")
            
            # Step 3: Process each chunk with Document AI
            chunk_results = []
            for i, chunk in enumerate(pdf_chunks):
                logger.info(f"Processing chunk {i+1}/{len(pdf_chunks)} for job {job_id} "
                           f"(pages {chunk['page_range']['start']}-{chunk['page_range']['end']})")
                
                try:
                    # Process chunk with Document AI
                    chunk_ai_result = await self.document_ai.process_document(
                        chunk['chunk_data'], 
                        f"{filename}_chunk_{i+1}"
                    )
                    chunk_ai_result.job_id = f"{job_id}_chunk_{i}"
                    
                    # Extract structured data for this chunk
                    chunk_tables = self.extract_tables(chunk_ai_result)
                    chunk_text_content = self.extract_text(chunk_ai_result)
                    
                    # Store chunk results
                    chunk_result = {
                        'job_id': job_id,
                        'chunk_id': i,
                        'chunk_info': chunk,
                        'document_type': chunk_ai_result.document_type.value if hasattr(chunk_ai_result, 'document_type') else 'unknown',
                        'processing_time': chunk_ai_result.processing_time if hasattr(chunk_ai_result, 'processing_time') else 0,
                        'confidence_score': chunk_ai_result.confidence_score if hasattr(chunk_ai_result, 'confidence_score') else 0,
                        'raw_text': chunk_text_content.get('raw_text', ''),
                        'tables': chunk_tables,
                        'text_blocks': chunk_text_content.get('text_blocks', []),
                        'total_pages': chunk['total_pages'],
                        'metadata': chunk_ai_result.metadata if hasattr(chunk_ai_result, 'metadata') else {}
                    }
                    
                    chunk_results.append(chunk_result)
                    
                    # Store individual chunk results for debugging/reference
                    await self.storage.store_chunk_ai_results(job_id, i, chunk_result)
                    
                    logger.info(f"Completed processing chunk {i+1}/{len(pdf_chunks)} for job {job_id}")
                    
                except Exception as chunk_error:
                    logger.error(f"Error processing chunk {i+1} for job {job_id}: {str(chunk_error)}")
                    # Continue with other chunks even if one fails
                    continue
            
            if not chunk_results:
                raise Exception("Failed to process any PDF chunks successfully")
            
            # Step 4: Combine results from all chunks
            logger.info(f"Combining results from {len(chunk_results)} chunks for job {job_id}")
            combined_result = await self.chunking_service.combine_chunk_results(chunk_results, filename)
            
            # Step 5: Detect credit bureau from combined text
            raw_text = combined_result.get('raw_text', '')
            detected_bureau = await self._detect_credit_bureau(raw_text, job_id)
            logger.info(f"Detected credit bureau: {detected_bureau} for job {job_id}")
            
            # Step 6: Extract and format final results with bureau info
            final_tables = combined_result.get('tables', [])
            final_text_content = {
                'raw_text': raw_text,
                'text_blocks': combined_result.get('text_blocks', []),
                'total_confidence': combined_result.get('confidence_score', 0),
                'page_count': combined_result.get('total_pages', 0),
                'detected_bureau': detected_bureau
            }
            
            # Create a mock AI result object for compatibility
            mock_ai_result = type('MockAIResult', (), {
                'job_id': job_id,
                'document_type': type('DocumentType', (), {'value': combined_result.get('document_type', 'unknown')})(),
                'processing_time': combined_result.get('processing_time', 0),
                'confidence_score': combined_result.get('confidence_score', 0),
                'total_pages': combined_result.get('total_pages', 0),
                'metadata': combined_result.get('metadata', {})
            })()
            
            # Store final combined results
            await self.store_ai_results(job_id, mock_ai_result, final_tables, final_text_content)
            
            # Update job status
            await self.job_service.update_job_status(job_id, ProcessingStatus.COMPLETED)
            
            # Trigger LLM processing
            await self.trigger_llm_processing(job_id)
            
            logger.info(f"Document AI workflow with chunking completed for job {job_id}: "
                       f"{len(final_tables)} tables, {len(final_text_content.get('text_blocks', []))} text blocks, "
                       f"{combined_result.get('total_pages', 0)} pages processed")
            return True
            
        except Exception as e:
            logger.error(f"Document AI workflow with chunking failed for job {job_id}: {str(e)}")
            await self.job_service.update_job_status(job_id, ProcessingStatus.FAILED)
            await self.job_service.update_job_error(job_id, str(e))
            return False
    
    async def get_stored_file(self, job_id: str) -> Tuple[bytes, Dict[str, Any]]:
        """Retrieve uploaded file from storage"""
        try:
            file_data = await self.storage.get_file(job_id)
            return file_data['content'], file_data['metadata']
        except Exception as e:
            logger.error(f"Failed to retrieve file for job {job_id}: {str(e)}")
            raise
    
    def extract_tables(self, ai_result: DocumentAIResult) -> List[Dict[str, Any]]:
        """Extract and format tables from AI result"""
        formatted_tables = []
        
        for table in ai_result.tables:
            formatted_table = {
                'table_id': table.table_id,
                'headers': table.headers,
                'rows': table.rows,
                'confidence': table.confidence,
                'page_number': table.page_number,
                'row_count': len(table.rows),
                'column_count': len(table.headers),
                'bounding_box': table.bounding_box
            }
            formatted_tables.append(formatted_table)
        
        logger.info(f"Extracted {len(formatted_tables)} tables")
        return formatted_tables
    
    def extract_text(self, ai_result: DocumentAIResult) -> Dict[str, Any]:
        """Extract and format text content from AI result"""
        text_data = {
            'raw_text': ai_result.raw_text,
            'text_blocks': [],
            'total_confidence': ai_result.confidence_score,
            'page_count': ai_result.total_pages
        }
        
        for block in ai_result.text_blocks:
            text_block = {
                'content': block.content,
                'page_number': block.page_number,
                'confidence': block.confidence,
                'word_count': len(block.content.split()),
                'bounding_box': block.bounding_box
            }
            text_data['text_blocks'].append(text_block)
        
        logger.info(f"Extracted text from {len(text_data['text_blocks'])} blocks")
        return text_data
    
    async def store_ai_results(self, job_id: str, ai_result: DocumentAIResult, 
                             tables: List[Dict], text_content: Dict) -> None:
        """Store intermediate AI processing results"""
        try:
            # Prepare storage data
            storage_data = {
                'job_id': job_id,
                'document_type': ai_result.document_type.value,
                'processing_time': ai_result.processing_time,
                'confidence_score': ai_result.confidence_score,
                'tables': tables,
                'text_content': text_content,
                'metadata': ai_result.metadata,
                'processed_at': datetime.now().isoformat()
            }
            
            # Store AI results
            await self.storage.store_document_ai_results(job_id, storage_data)
            
            # Store formatted data for LLM processing
            llm_input_data = {
                'tables': tables,
                'text': text_content['raw_text'],
                'text_blocks': text_content['text_blocks'],
                'document_type': ai_result.document_type.value,
                'confidence_score': ai_result.confidence_score,
                'metadata': ai_result.metadata
            }
            
            await self.storage.store_llm_input(job_id, llm_input_data)
            
            logger.info(f"Stored AI results for job {job_id}")
            
        except Exception as e:
            logger.error(f"Failed to store AI results for job {job_id}: {str(e)}")
            raise
    
    async def trigger_llm_processing(self, job_id: str) -> None:
        """Trigger the next phase - LLM processing"""
        try:
            # Start LLM processing in background
            await self.llm_parser.process_document_job(job_id)
            logger.info(f"Triggered LLM processing for job {job_id}")
            
        except Exception as e:
            logger.error(f"Failed to trigger LLM processing for job {job_id}: {str(e)}")
            raise
    
    async def get_processing_status(self, job_id: str) -> Dict[str, Any]:
        """Get current processing status for a job"""
        try:
            job_status = await self.job_service.get_job_status(job_id)
            ai_results = await self.storage.get_document_ai_results(job_id)
            
            return {
                'job_id': job_id,
                'status': job_status.get('status'),
                'progress': job_status.get('progress', 0),
                'ai_processing_complete': ai_results is not None,
                'processing_time': ai_results.get('processing_time') if ai_results else None,
                'confidence_score': ai_results.get('confidence_score') if ai_results else None,
                'tables_extracted': len(ai_results.get('tables', [])) if ai_results else 0,
                'error': job_status.get('error')
            }
            
        except Exception as e:
            logger.error(f"Failed to get processing status for job {job_id}: {str(e)}")
            raise
    
    async def _detect_credit_bureau(self, raw_text: str, job_id: str) -> str:
        """Detect credit bureau from document text"""
        try:
            logger.info(f"Detecting credit bureau for job {job_id}")
            
            # Use enhanced bureau detector
            bureau, confidence, evidence = self.bureau_detector.detect_credit_bureau(raw_text)
            
            if confidence >= 0.5:  # Minimum confidence threshold
                logger.info(f"Bureau detected: {bureau} "
                           f"(confidence: {confidence:.2f}) for job {job_id}")
                logger.debug(f"Evidence: {evidence[:3]}")  # Log first 3 pieces of evidence
                return bureau
            
            # Fallback to unknown
            logger.warning(f"Could not reliably detect bureau for job {job_id}, using 'Unknown' "
                          f"(best guess: {bureau}, confidence: {confidence:.2f})")
            return "Unknown"
            
        except Exception as e:
            logger.error(f"Error detecting bureau for job {job_id}: {str(e)}")
            return "Unknown"