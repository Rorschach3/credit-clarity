import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime

from backend.services.document_ai_service import DocumentAIService
from backend.services.storage_service import StorageService
from backend.services.job_service import JobService
from backend.models.tradeline_models import ProcessingStatus, DocumentAIResult
from backend.services.llm_parser_service import LLMParserService

logger = logging.getLogger(__name__)

class DocumentProcessorService:
    """Main document processing orchestrator"""
    
    def __init__(self, storage_service: StorageService, job_service: JobService,
                 document_ai_service: DocumentAIService = None, llm_parser: LLMParserService = None):
        self.storage = storage_service
        self.job_service = job_service
        self.document_ai = document_ai_service or DocumentAIService()
        self.llm_parser = llm_parser or LLMParserService(config=None) # config will be set by the caller
    
    async def document_ai_workflow(self, job_id: str) -> bool:
        """Main workflow for Document AI processing phase"""
        try:
            logger.info(f"Starting Document AI workflow for job {job_id}")
            
            # Update job status
            await self.job_service.update_job_status(job_id, ProcessingStatus.PROCESSING)
            
            # Retrieve uploaded file
            file_content, file_metadata = await self.get_stored_file(job_id)
            
            # Process with Document AI
            ai_result = await self.document_ai.process_document(
                file_content, 
                file_metadata.get('file_name', 'unknown')
            )
            ai_result.job_id = job_id
            
            # Extract structured data
            tables = self.extract_tables(ai_result)
            text_content = self.extract_text(ai_result)
            
            # Store intermediate results
            await self.store_ai_results(job_id, ai_result, tables, text_content)
            
            # Update job status
            await self.job_service.update_job_status(job_id, ProcessingStatus.COMPLETED)
            
            # Trigger LLM processing
            await self.trigger_llm_processing(job_id)
            
            logger.info(f"Document AI workflow completed for job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Document AI workflow failed for job {job_id}: {str(e)}")
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