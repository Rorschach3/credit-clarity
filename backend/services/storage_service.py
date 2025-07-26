import os
import json
import uuid
import hashlib
import aiofiles
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

try:
    from ..models.tradeline_models import ProcessingStatus
except ImportError:
    from models.tradeline_models import ProcessingStatus

logger = logging.getLogger(__name__)

class StorageService:
    """Service for handling file and data storage operations"""
    
    def __init__(self, storage_path: str = "storage"):
        self.storage_path = storage_path
        self.base_path = Path(storage_path)
        self.ensure_storage_directories()
    
    def ensure_storage_directories(self):
        """Create necessary storage directories"""
        directories = [
            self.base_path / "uploads",
            self.base_path / "ocr_pdfs",
            self.base_path / "ai_results",
            self.base_path / "chunk_results",
            self.base_path / "llm_input",
            self.base_path / "processed",
            self.base_path / "jobs"
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    async def store_uploaded_file(self, job_id: str, file_content: bytes, metadata: Dict[str, Any]) -> str:
        """Store uploaded file with metadata"""
        try:
            file_path = self.base_path / "uploads" / f"{job_id}.bin"
            metadata_path = self.base_path / "uploads" / f"{job_id}.json"

            # Write file content
            with open(file_path, 'wb') as f:
                f.write(file_content)

            storage_metadata = {
                "job_id": job_id,
                "file_size": len(file_content),
                "file_hash": hashlib.sha256(file_content).hexdigest(),
                "stored_at": datetime.now().isoformat(),
                **metadata
            }

            with open(metadata_path, 'w') as f:
                json.dump(storage_metadata, f, indent=2)

            logger.info(f"Stored file for job {job_id}")
            return str(file_path)

        except Exception as e:
            logger.error(f"Failed to store file for job {job_id}: {str(e)}")
            raise

    async def get_file(self, job_id: str) -> Dict[str, Any]:
        """Retrieve uploaded file and metadata"""
        try:
            file_path = self.base_path / "uploads" / f"{job_id}.bin"
            metadata_path = self.base_path / "uploads" / f"{job_id}.json"

            with open(file_path, 'rb') as f:
                content = f.read()

            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            return {
                "content": content,
                "metadata": metadata
            }

        except FileNotFoundError:
            logger.error(f"File not found for job {job_id}")
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve file for job {job_id}: {str(e)}")
            raise

    async def store_document_ai_results(self, job_id: str, ai_results: Dict[str, Any]) -> None:
        """Store Document AI processing results"""
        try:
            results_path = self.base_path / "ai_results" / f"{job_id}.json"
            with open(results_path, 'w') as f:
                json.dump(ai_results, f, indent=2)
            logger.info(f"Stored AI results for job {job_id}")
        except Exception as e:
            logger.error(f"Failed to store AI results for job {job_id}: {str(e)}")
            raise

    async def get_document_ai_results(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve Document AI processing results"""
        try:
            results_path = self.base_path / "ai_results" / f"{job_id}.json"
            if not results_path.exists():
                return None
            with open(results_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to retrieve AI results for job {job_id}: {str(e)}")
            return None
    
    async def store_ocr_pdf(self, job_id: str, ocr_pdf_content: bytes) -> str:
        """Store OCR-processed PDF file"""
        try:
            ocr_path = self.base_path / "ocr_pdfs" / f"{job_id}_ocr.pdf"
            metadata_path = self.base_path / "ocr_pdfs" / f"{job_id}_ocr.json"
            
            # Write OCR'd PDF content
            with open(ocr_path, 'wb') as f:
                f.write(ocr_pdf_content)
            
            # Store metadata
            ocr_metadata = {
                "job_id": job_id,
                "file_size": len(ocr_pdf_content),
                "file_hash": hashlib.sha256(ocr_pdf_content).hexdigest(),
                "ocr_processed_at": datetime.now().isoformat(),
                "ocr_type": "ocrmypdf_tesseract"
            }
            
            with open(metadata_path, 'w') as f:
                json.dump(ocr_metadata, f, indent=2)
            
            logger.info(f"Stored OCR PDF for job {job_id}")
            return str(ocr_path)
            
        except Exception as e:
            logger.error(f"Failed to store OCR PDF for job {job_id}: {str(e)}")
            raise
    
    async def get_ocr_pdf(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve OCR-processed PDF and metadata"""
        try:
            ocr_path = self.base_path / "ocr_pdfs" / f"{job_id}_ocr.pdf"
            metadata_path = self.base_path / "ocr_pdfs" / f"{job_id}_ocr.json"
            
            if not ocr_path.exists():
                return None
                
            with open(ocr_path, 'rb') as f:
                content = f.read()
                
            metadata = {}
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            
            return {
                "content": content,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to retrieve OCR PDF for job {job_id}: {str(e)}")
            return None
    
    async def store_chunk_ai_results(self, job_id: str, chunk_id: int, chunk_result: Dict[str, Any]) -> None:
        """Store AI processing results for a specific chunk"""
        try:
            chunk_results_path = self.base_path / "chunk_results" / f"{job_id}_chunk_{chunk_id}.json"
            
            # Add timestamp
            chunk_result_with_meta = {
                **chunk_result,
                'stored_at': datetime.now().isoformat(),
                'chunk_id': chunk_id,
                'job_id': job_id
            }
            
            with open(chunk_results_path, 'w') as f:
                json.dump(chunk_result_with_meta, f, indent=2)
                
            logger.info(f"Stored chunk {chunk_id} AI results for job {job_id}")
            
        except Exception as e:
            logger.error(f"Failed to store chunk {chunk_id} AI results for job {job_id}: {str(e)}")
            raise
    
    async def get_chunk_ai_results(self, job_id: str, chunk_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve AI processing results for a specific chunk"""
        try:
            chunk_results_path = self.base_path / "chunk_results" / f"{job_id}_chunk_{chunk_id}.json"
            
            if not chunk_results_path.exists():
                return None
                
            with open(chunk_results_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Failed to retrieve chunk {chunk_id} AI results for job {job_id}: {str(e)}")
            return None
    
    async def get_all_chunk_results(self, job_id: str) -> list[Dict[str, Any]]:
        """Retrieve all chunk results for a job"""
        try:
            chunk_results = []
            chunk_results_dir = self.base_path / "chunk_results"
            
            if not chunk_results_dir.exists():
                return chunk_results
                
            # Find all chunk result files for this job
            chunk_files = list(chunk_results_dir.glob(f"{job_id}_chunk_*.json"))
            
            # Sort by chunk ID
            chunk_files.sort(key=lambda x: int(x.stem.split('_chunk_')[1]))
            
            for chunk_file in chunk_files:
                with open(chunk_file, 'r') as f:
                    chunk_result = json.load(f)
                    chunk_results.append(chunk_result)
            
            logger.info(f"Retrieved {len(chunk_results)} chunk results for job {job_id}")
            return chunk_results
            
        except Exception as e:
            logger.error(f"Failed to retrieve all chunk results for job {job_id}: {str(e)}")
            return []

    async def store_job_data(self, job_id: str, job_data: Dict[Any, Any]) -> None:
        """Store job processing data"""
        try:
            job_path = self.base_path / "jobs" / f"{job_id}.json"
            serializable_data = self._make_serializable(job_data)
            async with aiofiles.open(job_path, 'w') as f:
                await f.write(json.dumps(serializable_data, indent=2))
            logger.info(f"Stored job data for {job_id}")
        except Exception as e:
            logger.error(f"Failed to store job data for {job_id}: {e}")
            raise

    async def get_job_data(self, job_id: str) -> Optional[Dict[Any, Any]]:
        """Retrieve job processing data"""
        try:
            job_path = self.base_path / "jobs" / f"{job_id}.json"
            if not job_path.exists():
                return None
            async with aiofiles.open(job_path, 'r') as f:
                content = await f.read()
                return json.loads(content)
        except Exception as e:
            logger.error(f"Failed to retrieve job data for {job_id}: {e}")
            return None

    async def update_job_status(self, job_id: str, status: ProcessingStatus, error_message: Optional[str] = None) -> None:
        """Update job status"""
        try:
            job_data = await self.get_job_data(job_id)
            if not job_data:
                logger.warning(f"Job {job_id} not found for status update")
                return

            job_data["status"] = status.value
            if error_message:
                job_data["error_message"] = error_message
            if status == ProcessingStatus.COMPLETED:
                job_data["completed_at"] = datetime.now().isoformat()

            await self.store_job_data(job_id, job_data)

        except Exception as e:
            logger.error(f"Failed to update job status for {job_id}: {e}")
            raise

    async def store_llm_input(self, job_id: str, llm_input: Dict[str, Any]) -> None:
        """Store prepared input data for LLM processing"""
        try:
            input_path = self.base_path / "llm_input" / f"{job_id}.json"
            llm_input["prepared_at"] = datetime.now().isoformat()
            with open(input_path, 'w') as f:
                json.dump(llm_input, f, indent=2)
            logger.info(f"Stored LLM input for job {job_id}")
        except Exception as e:
            logger.error(f"Failed to store LLM input for job {job_id}: {str(e)}")
            raise

    async def cleanup_old_files(self, retention_days: int = 7) -> None:
        """Clean up old files and job data"""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)

            # Cleanup uploads
            upload_dir = self.base_path / "uploads"
            for file_path in upload_dir.iterdir():
                if file_path.stat().st_mtime < cutoff_date.timestamp():
                    file_path.unlink()
                    logger.info(f"Cleaned up old file: {file_path}")

            # Cleanup job data
            jobs_dir = self.base_path / "jobs"
            for file_path in jobs_dir.iterdir():
                if file_path.stat().st_mtime < cutoff_date.timestamp():
                    file_path.unlink()
                    logger.info(f"Cleaned up old job data: {file_path}")

        except Exception as e:
            logger.error(f"Failed to cleanup old files: {e}")

    def _make_serializable(self, obj):
        """Convert non-serializable objects to serializable format"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        elif hasattr(obj, '__dict__'):
            return self._make_serializable(obj.__dict__)
        else:
            return obj
