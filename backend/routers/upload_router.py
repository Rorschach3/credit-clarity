from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks # type: ignore
from typing import Optional
import uuid
import logging

from backend.services.validation_service import ValidationService
from backend.models.tradeline_models import DocumentAIResult, ProcessingStatus
from backend.services.document_processor_service import DocumentProcessorService
from backend.services.storage_service import StorageService
from backend.services.job_service import JobService
from backend.utils.auth import get_current_user_id

from pydantic import BaseModel # type: ignore

class UploadResponse(BaseModel):
    job_id: str
    status: str
    message: str
    estimated_processing_time: int

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/upload", tags=["upload"])

# Construct the services
storage_service = StorageService()
job_service = JobService(storage_service)
validation_service = ValidationService()
processor_service = DocumentProcessorService(storage_service, job_service)


async def start_processing_pipeline(job_id: str):
    try:
        logger.info(f"🚀 Starting full pipeline for job {job_id}")
        success = await processor_service.document_ai_workflow(job_id)
        if success:
            logger.info(f"✅ Pipeline completed successfully for job {job_id}")
        else:
            logger.warning(f"⚠️ Pipeline failed during document AI step for job {job_id}")
    except Exception as e:
        logger.exception(f"❌ Pipeline crashed for job {job_id}")
        await job_service.update_job_status(
            job_id,
            ProcessingStatus.FAILED,
            error_message=str(e)
        )

@router.post("/", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: Optional[uuid.UUID] = Depends(get_current_user_id)
):
    """
    Upload a PDF document for processing
    """
    try:
        # Read file content
        file_content = await file.read()

        # Validate filename
        is_valid, error_msg = validation_service.validate_filename(file.filename)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid filename: {error_msg}")

        # Validate PDF content
        is_valid, error_msg = validation_service.validate_pdf(
            file_content, file.filename, file.content_type
        )
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid PDF: {error_msg}")

        # Create processing job
        job_id = await job_service.create_processing_job(
            user_id=user_id,
            filename=file.filename,
            file_size=len(file_content)
        )

        # Store uploaded file with metadata
        await storage_service.store_uploaded_file(
            job_id=job_id,
            file_content=file_content,
            metadata={"file_name": file.filename}
        )

        # Launch background processing
        background_tasks.add_task(start_processing_pipeline, job_id)

        return UploadResponse(
            job_id=job_id,
            status=ProcessingStatus.PENDING,
            message="Document uploaded successfully and processing started",
            estimated_processing_time=120  # seconds
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Upload failed")
        raise HTTPException(status_code=500, detail="Upload failed")
