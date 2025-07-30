from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional
import logging
from datetime import datetime

from ..services.llm_parser_service import LLMParserService, ProcessingContext
from ..services.storage_service import StorageService
from ..models.llm_models import (
    LLMRequest, 
    LLMResponse, 
    NormalizationResult,
    ValidationRequest,
    ValidationResponse
)
from ..config.llm_config import get_llm_config
from ..utils.auth import get_current_user
from ..utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/llm", tags=["llm-parsing"])

# Rate limiter for LLM operations
rate_limiter = RateLimiter(max_requests=10, window_minutes=1)

@router.post("/normalize", response_model=NormalizationResult)
async def normalize_document_data(
    request: LLMRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    llm_service: LLMParserService = Depends(get_llm_service),
    storage_service: StorageService = Depends(get_storage_service)
):
    """
    Normalize document data using LLM
    
    This endpoint takes raw document data and normalizes it into
    structured tradeline and consumer information.
    """
    
    # Check rate limit
    if not rate_limiter.allow_request(current_user.get("user_id")):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )
    
    try:
        # Get processing context
        context = ProcessingContext(
            job_id=request.job_id,
            document_type=request.document_type,
            confidence_threshold=request.confidence_threshold or 0.7
        )
        
        # Get document data from storage
        document_data = await storage_service.get_document_ai_results(request.job_id)
        
        if not document_data:
            raise HTTPException(
                status_code=404,
                detail=f"Document AI results not found for job {request.job_id}"
            )
        
        # Start normalization process
        start_time = datetime.utcnow()
        
        logger.info(f"Starting LLM normalization for job {request.job_id}")
        
        # Perform normalization
        result = await llm_service.normalize_tradeline_data(
            raw_text=document_data.get("text_content", ""),
            table_data=document_data.get("tables", []),
            context=context
        )
        
        # Calculate processing duration
        processing_duration = (datetime.utcnow() - start_time).total_seconds()
        result.processing_metadata["processing_duration"] = processing_duration
        
        # Store results
        background_tasks.add_task(
            storage_service.store_llm_results,
            request.job_id,
            result
        )
        
        # Update job status
        background_tasks.add_task(
            storage_service.update_job_status,
            request.job_id,
            "llm_completed",
            {"llm_processing_duration": processing_duration}
        )
        
        logger.info(f"LLM normalization completed for job {request.job_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in LLM normalization: {str(e)}")
        
        # Update job status with error
        background_tasks.add_task(
            storage_service.update_job_status,
            request.job_id,
            "llm_failed",
            {"error": str(e)}
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"LLM normalization failed: {str(e)}"
        )

@router.post("/validate", response_model=ValidationResponse)
async def validate_normalized_data(
    request: ValidationRequest,
    current_user: dict = Depends(get_current_user),
    llm_service: LLMParserService = Depends(get_llm_service)
):
    """
    Validate normalized data using LLM
    
    This endpoint validates the consistency and accuracy of
    normalized tradeline data.
    """
    
    try:
        context = ProcessingContext(
            job_id=request.job_id,
            document_type=request.document_type,
            confidence_threshold=request.confidence_threshold or 0.7
        )
        
        # Perform validation
        validation_result = await llm_service._validate_and_score(
            tradelines=request.tradelines,
            consumer_info=request.consumer_info,
            context=context
        )
        
        return ValidationResponse(
            job_id=request.job_id,
            validation_result=validation_result,
            validated_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in data validation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Data validation failed: {str(e)}"
        )

@router.get("/jobs/{job_id}/results")
async def get_llm_results(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    storage_service: StorageService = Depends(get_storage_service)
):
    """
    Get LLM processing results for a specific job
    """
    
    try:
        results = await storage_service.get_llm_results(job_id)
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"LLM results not found for job {job_id}"
            )
        
        return results
        
    except Exception as e:
        logger.error(f"Error retrieving LLM results: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve LLM results: {str(e)}"
        )

@router.post("/jobs/{job_id}/reprocess")
async def reprocess_with_llm(
    job_id: str,
    background_tasks: BackgroundTasks,
    confidence_threshold: Optional[float] = 0.7,
    current_user: dict = Depends(get_current_user),
    llm_service: LLMParserService = Depends(get_llm_service),
    storage_service: StorageService = Depends(get_storage_service)
):
    """
    Reprocess document data with LLM using different parameters
    """
    
    try:
        # Get original document data
        document_data = await storage_service.get_document_ai_results(job_id)
        
        if not document_data:
            raise HTTPException(
                status_code=404,
                detail=f"Document AI results not found for job {job_id}"
            )
        
        # Create new processing context
        context = ProcessingContext(
            job_id=job_id,
            document_type=document_data.get("document_type", "credit_report"),
            confidence_threshold=confidence_threshold
        )
        
        # Start reprocessing in background
        background_tasks.add_task(
            _reprocess_job_background,
            job_id,
            document_data,
            context,
            llm_service,
            storage_service
        )
        
        return JSONResponse(
            content={
                "message": f"Reprocessing started for job {job_id}",
                "job_id": job_id,
                "status": "reprocessing"
            }
        )
        
    except Exception as e:
        logger.error(f"Error starting reprocessing: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start reprocessing: {str(e)}"
        )

async def _reprocess_job_background(
    job_id: str,
    document_data: dict,
    context: ProcessingContext,
    llm_service: LLMParserService,
    storage_service: StorageService
):
    """Background task for reprocessing job with LLM"""
    
    try:
        # Update status to reprocessing
        await storage_service.update_job_status(
            job_id, 
            "reprocessing", 
            {"reprocess_started_at": datetime.utcnow().isoformat()}
        )
        
        # Perform normalization
        result = await llm_service.normalize_tradeline_data(
            raw_text=document_data.get("text_content", ""),
            table_data=document_data.get("tables", []),
            context=context
        )
        
        # Store new results
        await storage_service.store_llm_results(job_id, result)
        
        # Update job status
        await storage_service.update_job_status(
            job_id,
            "reprocess_completed",
            {"reprocess_completed_at": datetime.utcnow().isoformat()}
        )
        
    except Exception as e:
        logger.error(f"Error in background reprocessing: {str(e)}")
        await storage_service.update_job_status(
            job_id,
            "reprocess_failed",
            {"error": str(e)}
        )

# Dependency functions
async def get_llm_service() -> LLMParserService:
    """Get LLM parser service instance"""
    config = get_llm_config()
    return LLMParserService(config)