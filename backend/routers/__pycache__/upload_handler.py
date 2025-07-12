import os
import base64
import uuid
import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_MIME_TYPES = {"application/pdf"}
MAX_FILE_SIZE_MB = 10

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    validate_file(file)
    
    try:
        contents = await file.read()
        base64_file = base64.b64encode(contents).decode("utf-8")
        job_id = create_processing_job(base64_file)
        return JSONResponse({"message": "File received and job created", "job_id": job_id})
    except Exception as e:
        logger.error(f"Failed to process uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Error processing file")

def validate_file(file: UploadFile):
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDFs are allowed.")
    if file.size and file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File size exceeds {MAX_FILE_SIZE_MB}MB limit.")

def create_processing_job(base64_file: str) -> str:
    job_id = str(uuid.uuid4())
    logger.info(f"Created processing job {job_id} for uploaded file")
    # This is where you would enqueue the file for processing (e.g. Redis, task queue, etc.)
    # For now, it's a no-op
    return job_id
