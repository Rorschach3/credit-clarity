"""
Credit report processing endpoints
Handles PDF upload, processing, and job management
"""
import os
import time
import tempfile
import logging
from typing import Dict, Any, List

from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse

from core.security import get_supabase_user, check_rate_limit
from schemas.responses import APIResponse, ProcessingResponse, JobStatusResponse
from schemas.requests import ProcessingOptions
from services.optimized_processor import OptimizedCreditReportProcessor
from services.database_optimizer import db_optimizer
from services.background_jobs import submit_pdf_processing_job, job_processor, JobPriority
from services.monitoring import (
    monitor_api_call, 
    track_user_activity,
    track_pdf_processing_time,
    track_tradelines_extracted,
    track_performance
)
from services.ab_testing import ab_test_manager, TestVariant, track_pipeline_performance
from services.storage_service import storage_service
from services.virus_scanner import virus_scanner
from services.audit_service import audit_service

router = APIRouter(prefix="/processing", tags=["Processing"])
logger = logging.getLogger(__name__)

# Global processor instance
processor = None

async def get_processor():
    """Get or create processor instance."""
    global processor
    if processor is None:
        processor = OptimizedCreditReportProcessor()
    return processor

@router.post("/upload", response_model=APIResponse[ProcessingResponse])
@monitor_api_call
async def process_credit_report(
    request: Request,
    file: UploadFile = File(..., description="PDF credit report file"),
    options: ProcessingOptions = Depends(),
    current_user: Dict[str, Any] = Depends(get_supabase_user),
    _: None = Depends(check_rate_limit)
):
    """
    Process credit report PDF file.
    Automatically routes to sync or async processing based on file size.
    """
    start_time = time.time()
    user_id = current_user.get("id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User authentication required")
    
    # Track user activity
    track_user_activity("pdf_upload", user_id)
    
    # Validate file
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Read file content
    file_content = await file.read()
    file_size_mb = len(file_content) / (1024 * 1024)
    
    # Validate PDF format
    if not file_content.startswith(b'%PDF'):
        raise HTTPException(status_code=400, detail="Invalid PDF file format")
    
    # Check for duplicate file
    file_hash = await storage_service.calculate_file_hash(file_content)
    is_duplicate = await storage_service.check_duplicate_hash(file_hash, user_id)
    duplicate_warning = None
    if is_duplicate:
        duplicate_warning = "This file appears to be a duplicate of a previously uploaded file."
        logger.info(f"Duplicate file detected for user {user_id}: {file_hash[:16]}...")
    
    # Scan file for viruses
    scan_result = await virus_scanner.scan_file(file_content, file.filename)
    if not scan_result.clean:
        raise HTTPException(
            status_code=400, 
            detail=f"File security check failed: {scan_result.details}"
        )
    
    # A/B Testing: Assign user to test variant
    test_variant = ab_test_manager.assign_variant(user_id, file_size_mb)
    
    # Route based on file size and options
    # For very large files (>3MB) or many pages, use background processing
    if file_size_mb > 3 or options.priority == "low":
        # Large files or low priority -> background processing
        logger.info(f"Routing {file_size_mb:.2f}MB file to background processing")
        return await _process_in_background(
            file, file_content, user_id, options, file_size_mb, test_variant
        )
    else:
        # Small files -> synchronous processing
        return await _process_synchronously(
            file, file_content, user_id, options, file_size_mb, start_time, test_variant
        )

async def _process_synchronously(
    file: UploadFile,
    file_content: bytes,
    user_id: str,
    options: ProcessingOptions,
    file_size_mb: float,
    start_time: float,
    test_variant: TestVariant
) -> APIResponse[ProcessingResponse]:
    """Process file synchronously for fast response."""
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        temp_file.write(file_content)
        temp_file_path = temp_file.name
    
    try:
        # Get processor and process
        proc = await get_processor()
        
        with track_performance(f"sync_processing_{user_id}"):
            result = await proc.process_credit_report_optimized(temp_file_path)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=500, 
                detail=result.get('error', 'Processing failed')
            )
        
        tradelines = result.get('tradelines', [])
        
        # Save to database if requested
        if options.save_to_database and tradelines:
            try:
                for tradeline in tradelines:
                    tradeline['user_id'] = user_id
                
                with track_performance(f"batch_save_{user_id}"):
                    save_result = await db_optimizer.batch_insert_tradelines(tradelines)
                
                # Log save results
                if save_result.get('inserted', 0) > 0:
                    logger.info(f"Successfully saved {save_result['inserted']} tradelines for user {user_id}")
                elif save_result.get('errors', 0) > 0:
                    logger.warning(f"Failed to save {save_result['errors']} tradelines for user {user_id}")
                
            except Exception as db_error:
                logger.error(f"Database save operation failed for user {user_id}: {db_error}")
                # Don't fail the entire request if database save fails
                # The processing was successful, just the save failed
                pass
        
        # Track metrics
        processing_time_ms = (time.time() - start_time) * 1000
        track_pdf_processing_time(processing_time_ms, result.get('method_used', 'sync'))
        track_tradelines_extracted(len(tradelines), user_id)
        
        # A/B Testing: Track pipeline performance
        track_pipeline_performance(
            variant=test_variant,
            user_id=user_id,
            file_size_mb=file_size_mb,
            processing_time_ms=processing_time_ms,
            tradelines_extracted=len(tradelines),
            success=result.get('success', True),
            cost_usd=result.get('cost_estimate', 0.0),
            method_used=result.get('method_used', 'optimized_sync'),
            error_message=None
        )
        
        # Prepare response
        processing_response = ProcessingResponse(
            status="completed",
            tradelines_found=len(tradelines),
            processing_method=result.get('method_used', 'optimized_sync'),
            cost_estimate=result.get('cost_estimate', 0.0),
            processing_time={
                "start_time": start_time,
                "duration_ms": processing_time_ms,
                "method": "synchronous"
            },
            performance_metrics={
                "file_size_mb": file_size_mb,
                "processing_time_ms": processing_time_ms,
                "method_used": result.get('method_used'),
                "cache_hit": result.get('cache_hit', False),
                "tradelines_processed": len(tradelines),
                "optimization_level": "sync",
                "ab_test_variant": test_variant.value,  # Include A/B test info
                "cost_breakdown": {
                    "ocr_method": "free" if result.get('cost_estimate', 0.0) == 0.0 else "paid",
                    "total_cost": result.get('cost_estimate', 0.0)
                }
            },
            cache_hit=result.get('cache_hit', False)
        )
        
        return APIResponse[ProcessingResponse](
            success=True,
            data=processing_response,
            message=f"Successfully processed {len(tradelines)} tradelines"
        )
        
    except Exception as e:
        # Track A/B testing failure metrics
        processing_time_ms = (time.time() - start_time) * 1000
        track_pipeline_performance(
            variant=test_variant,
            user_id=user_id,
            file_size_mb=file_size_mb,
            processing_time_ms=processing_time_ms,
            tradelines_extracted=0,
            success=False,
            cost_usd=0.0,
            method_used="failed_sync",
            error_message=str(e)
        )
        raise  # Re-raise the original exception
        
    finally:
        # Cleanup temp file
        try:
            os.unlink(temp_file_path)
        except:
            pass

async def _process_in_background(
    file: UploadFile,
    file_content: bytes,
    user_id: str,
    options: ProcessingOptions,
    file_size_mb: float,
    test_variant: TestVariant
) -> APIResponse[ProcessingResponse]:
    """Submit file for background processing."""
    
    # Save file for background processing
    file_id = f"bg_{user_id}_{int(time.time())}"
    temp_path = f"/tmp/credit_report_{file_id}.pdf"
    
    with open(temp_path, 'wb') as f:
        f.write(file_content)
    
    # Determine job priority
    priority_map = {
        "low": JobPriority.LOW,
        "normal": JobPriority.NORMAL,
        "high": JobPriority.HIGH
    }
    
    # Submit background job with A/B test variant info
    job_id = await submit_pdf_processing_job(
        pdf_path=temp_path,
        user_id=user_id,
        priority=priority_map.get(options.priority, JobPriority.NORMAL),
        processing_options={"ab_test_variant": test_variant.value}
    )
    
    processing_response = ProcessingResponse(
        job_id=job_id,
        status="queued",
        progress=0,
        tradelines_found=0,
        processing_method="background_job",
        cost_estimate=0.0,
        processing_time={},
        performance_metrics={
            "file_size_mb": file_size_mb,
            "job_id": job_id,
            "optimization_level": "background",
            "priority": options.priority,
            "ab_test_variant": test_variant.value  # Include A/B test info
        }
    )
    
    return APIResponse[ProcessingResponse](
        success=True,
        data=processing_response,
        message=f"File submitted for background processing. Job ID: {job_id}"
    )

@router.get("/job/{job_id}", response_model=APIResponse[JobStatusResponse])
@monitor_api_call
async def get_job_status(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """Get background job status and results."""
    
    job_data = await job_processor.get_job_status(job_id)
    
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Verify user access
    if job_data.get('user_id') != current_user.get('id'):
        raise HTTPException(status_code=403, detail="Access denied")
    
    job_response = JobStatusResponse(
        job_id=job_data['job_id'],
        status=job_data['status'],
        progress=job_data['progress'],
        message=job_data.get('progress_message', ''),
        result=job_data.get('result'),
        error=job_data.get('error'),
        created_at=job_data['created_at'],
        updated_at=job_data.get('updated_at'),
        processing_time=job_data.get('processing_time')
    )
    
    return APIResponse[JobStatusResponse](
        success=True,
        data=job_response,
        message="Job status retrieved"
    )

@router.get("/jobs", response_model=APIResponse[List[JobStatusResponse]])
@monitor_api_call
async def get_user_jobs(
    current_user: Dict[str, Any] = Depends(get_supabase_user),
    limit: int = 20,
    status_filter: str = None
):
    """Get user's processing jobs with optional filtering."""
    
    user_id = current_user.get('id')
    jobs = job_processor.job_queue.get_user_jobs(user_id, limit)
    
    # Filter by status if requested
    if status_filter:
        jobs = [job for job in jobs if job.status == status_filter]
    
    job_responses = [
        JobStatusResponse(
            job_id=job.job_id,
            status=job.status,
            progress=job.progress,
            message=job.progress_message or '',
            result=job.result,
            error=job.error,
            created_at=job.created_at,
            updated_at=job.updated_at,
            processing_time=job.processing_time
        ) for job in jobs
    ]
    
    return APIResponse[List[JobStatusResponse]](
        success=True,
        data=job_responses,
        message=f"Retrieved {len(job_responses)} jobs"
    )

@router.delete("/job/{job_id}", response_model=APIResponse[Dict[str, str]])
@monitor_api_call
async def cancel_job(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """Cancel a background processing job."""
    
    job_data = await job_processor.get_job_status(job_id)
    
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Verify user access
    if job_data.get('user_id') != current_user.get('id'):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Cancel job
    cancelled = await job_processor.cancel_job(job_id)
    
    if not cancelled:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled")
    
    return APIResponse[Dict[str, str]](
        success=True,
        data={"job_id": job_id, "status": "cancelled"},
        message="Job cancelled successfully"
    )


# A/B Testing Management Endpoints
@router.get("/ab-test/results", response_model=APIResponse[Dict[str, Any]])
@monitor_api_call
async def get_ab_test_results(
    current_user: Dict[str, Any] = Depends(get_supabase_user),
    days: int = 7,
    test_name: str = "pipeline_v2"
):
    """Get A/B test results for analysis (Admin only)."""
    if not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        results = ab_test_manager.get_test_results(test_name, days)
        return APIResponse[Dict[str, Any]](
            success=True,
            data=results,
            message=f"A/B test results retrieved for {test_name} (last {days} days)"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get A/B test results: {str(e)}")


@router.post("/ab-test/config", response_model=APIResponse[Dict[str, str]])
@monitor_api_call
async def update_ab_test_config(
    current_user: Dict[str, Any] = Depends(get_supabase_user),
    test_name: str = "pipeline_v2",
    treatment_percentage: float = None,
    enabled: bool = None,
    file_size_threshold_mb: float = None
):
    """Update A/B test configuration (Admin only)."""
    if not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        updates = {}
        if treatment_percentage is not None:
            updates['treatment_percentage'] = treatment_percentage
        if enabled is not None:
            updates['enabled'] = enabled
        if file_size_threshold_mb is not None:
            updates['file_size_threshold_mb'] = file_size_threshold_mb
        
        ab_test_manager.update_config(test_name, **updates)
        
        return APIResponse[Dict[str, str]](
            success=True,
            data={"test_name": test_name, "updates": str(updates)},
            message=f"A/B test configuration updated for {test_name}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update A/B test config: {str(e)}")


@router.get("/ab-test/status", response_model=APIResponse[Dict[str, Any]])
@monitor_api_call
async def get_ab_test_status(
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """Get current A/B test status and active tests."""
    try:
        active_tests = ab_test_manager.get_active_tests()
        
        # Get basic stats for each active test
        test_status = {}
        for test_name in active_tests:
            config = ab_test_manager.configs.get(test_name)
            test_status[test_name] = {
                "enabled": config.enabled if config else False,
                "treatment_percentage": config.treatment_percentage if config else 0,
                "active": config.is_active() if config else False,
                "start_date": config.start_date.isoformat() if config and config.start_date else None,
                "end_date": config.end_date.isoformat() if config and config.end_date else None
            }
        
        return APIResponse[Dict[str, Any]](
            success=True,
            data={
                "active_tests": active_tests,
                "test_details": test_status,
                "total_metrics_recorded": len(ab_test_manager.metrics_storage)
            },
            message="A/B test status retrieved"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get A/B test status: {str(e)}")

