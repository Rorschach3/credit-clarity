"""
Credit report processing endpoints V2 (Parallel A/B Testing)
Uses the new cost-optimized tradeline extraction pipeline
Maintains existing API structure for compatibility
"""
import os
import time
import tempfile
from typing import Dict, Any, List, Optional
from enum import Enum

from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, BackgroundTasks, Request, Query
from fastapi.responses import JSONResponse

from core.security import get_supabase_user, check_rate_limit
from schemas.responses import APIResponse, ProcessingResponse, JobStatusResponse
from schemas.requests import ProcessingOptions
from services.tradeline_extraction.pipeline import TradelineExtractionPipeline
from services.background_jobs import submit_pdf_processing_job, job_processor, JobPriority
from services.monitoring import (
    monitor_api_call, 
    track_user_activity,
    track_pdf_processing_time,
    track_tradelines_extracted,
    track_performance
)

router = APIRouter(prefix="/processing/v2", tags=["Processing V2"])

# Pipeline versions for A/B testing
class PipelineVersion(str, Enum):
    V1 = "v1"  # Original pipeline
    V2 = "v2"  # New tradeline extraction pipeline
    AUTO = "auto"  # Automatic selection based on user/file characteristics

# Global pipeline instance
pipeline = None

async def get_pipeline():
    """Get or create pipeline instance."""
    global pipeline
    if pipeline is None:
        pipeline = TradelineExtractionPipeline()
    return pipeline


def select_pipeline_version(
    user_id: str, 
    file_size_mb: float, 
    requested_version: PipelineVersion = PipelineVersion.AUTO
) -> PipelineVersion:
    """
    A/B testing logic to select pipeline version
    """
    if requested_version != PipelineVersion.AUTO:
        return requested_version
    
    # A/B testing logic
    # For now, route based on simple criteria
    # In production, you'd use more sophisticated A/B testing
    
    user_hash = abs(hash(user_id)) % 100
    
    # Route 50% of users to V2 for testing
    if user_hash < 50:
        return PipelineVersion.V2
    else:
        return PipelineVersion.V1


@router.post("/upload", response_model=APIResponse[ProcessingResponse])
@monitor_api_call
async def process_credit_report_v2(
    request: Request,
    file: UploadFile = File(..., description="PDF credit report file"),
    options: ProcessingOptions = Depends(),
    pipeline_version: PipelineVersion = Query(PipelineVersion.AUTO, description="Pipeline version for A/B testing"),
    current_user: Dict[str, Any] = Depends(get_supabase_user),
    _: None = Depends(check_rate_limit)
):
    """
    Process credit report PDF file using V2 pipeline with A/B testing.
    Maintains compatibility with existing API structure.
    """
    start_time = time.time()
    user_id = current_user.get("id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User authentication required")
    
    # Track user activity
    track_user_activity("pdf_upload_v2", user_id)
    
    # Validate file
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Read file content
    file_content = await file.read()
    file_size_mb = len(file_content) / (1024 * 1024)
    
    # Validate PDF format
    if not file_content.startswith(b'%PDF'):
        raise HTTPException(status_code=400, detail="Invalid PDF file format")
    
    # Select pipeline version for A/B testing
    selected_version = select_pipeline_version(user_id, file_size_mb, pipeline_version)
    
    # Route based on file size and options (same as V1)
    if file_size_mb > 5 or options.priority == "low":
        # Large files or low priority -> background processing
        return await _process_in_background_v2(
            file, file_content, user_id, options, file_size_mb, selected_version
        )
    else:
        # Small files -> synchronous processing
        return await _process_synchronously_v2(
            file, file_content, user_id, options, file_size_mb, start_time, selected_version
        )


async def _process_synchronously_v2(
    file: UploadFile,
    file_content: bytes,
    user_id: str,
    options: ProcessingOptions,
    file_size_mb: float,
    start_time: float,
    pipeline_version: PipelineVersion
) -> APIResponse[ProcessingResponse]:
    """Process file synchronously using V2 pipeline."""
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        temp_file.write(file_content)
        temp_file_path = temp_file.name
    
    try:
        if pipeline_version == PipelineVersion.V2:
            # Use new tradeline extraction pipeline
            proc = await get_pipeline()
            
            with track_performance(f"v2_sync_processing_{user_id}"):
                result = await proc.process_credit_report(
                    pdf_path=temp_file_path,
                    user_id=user_id,
                    store_results=options.save_to_database
                )
            
            if not result.success:
                raise HTTPException(
                    status_code=500, 
                    detail=result.error or 'V2 processing failed'
                )
            
            # Convert V2 result to V1 format for API compatibility
            tradelines_count = result.tradelines_parsed
            processing_method = "v2_optimized_sync"
            cost_estimate = 0.0  # Free methods used first
            cache_hit = False  # V2 doesn't use cache yet
            
        else:
            # Fallback to V1 pipeline
            from services.optimized_processor import OptimizedCreditReportProcessor
            proc_v1 = OptimizedCreditReportProcessor()
            
            with track_performance(f"v1_sync_processing_{user_id}"):
                result_v1 = await proc_v1.process_credit_report_optimized(temp_file_path)
            
            if not result_v1.get('success'):
                raise HTTPException(
                    status_code=500, 
                    detail=result_v1.get('error', 'V1 processing failed')
                )
            
            tradelines_count = len(result_v1.get('tradelines', []))
            processing_method = result_v1.get('method_used', 'v1_optimized_sync')
            cost_estimate = result_v1.get('cost_estimate', 0.0)
            cache_hit = result_v1.get('cache_hit', False)
        
        # Track metrics (same as V1)
        processing_time_ms = (time.time() - start_time) * 1000
        track_pdf_processing_time(processing_time_ms, processing_method)
        track_tradelines_extracted(tradelines_count, user_id)
        
        # Prepare response (same format as V1)
        processing_response = ProcessingResponse(
            status="completed",
            tradelines_found=tradelines_count,
            processing_method=processing_method,
            cost_estimate=cost_estimate,
            processing_time={
                "start_time": start_time,
                "duration_ms": processing_time_ms,
                "method": "synchronous"
            },
            performance_metrics={
                "file_size_mb": file_size_mb,
                "processing_time_ms": processing_time_ms,
                "method_used": processing_method,
                "cache_hit": cache_hit,
                "tradelines_processed": tradelines_count,
                "optimization_level": "sync",
                "pipeline_version": pipeline_version.value,  # A/B testing metadata
                "cost_breakdown": {
                    "ocr_method": "free" if cost_estimate == 0.0 else "paid",
                    "total_cost": cost_estimate
                }
            },
            cache_hit=cache_hit
        )
        
        return APIResponse[ProcessingResponse](
            success=True,
            data=processing_response,
            message=f"Successfully processed {tradelines_count} tradelines using {pipeline_version.value} pipeline"
        )
        
    finally:
        # Cleanup temp file
        try:
            os.unlink(temp_file_path)
        except:
            pass


async def _process_in_background_v2(
    file: UploadFile,
    file_content: bytes,
    user_id: str,
    options: ProcessingOptions,
    file_size_mb: float,
    pipeline_version: PipelineVersion
) -> APIResponse[ProcessingResponse]:
    """Submit file for background processing with V2 pipeline."""
    
    # Save file for background processing
    file_id = f"bg_v2_{user_id}_{int(time.time())}"
    temp_path = f"/tmp/credit_report_{file_id}.pdf"
    
    with open(temp_path, 'wb') as f:
        f.write(file_content)
    
    # Determine job priority
    priority_map = {
        "low": JobPriority.LOW,
        "normal": JobPriority.NORMAL,
        "high": JobPriority.HIGH
    }
    
    # Submit background job with pipeline version info
    job_id = await submit_pdf_processing_job(
        pdf_path=temp_path,
        user_id=user_id,
        priority=priority_map.get(options.priority, JobPriority.NORMAL),
        processing_options={"pipeline_version": pipeline_version.value}  # Pass version to background job
    )
    
    processing_response = ProcessingResponse(
        job_id=job_id,
        status="queued",
        progress=0,
        tradelines_found=0,
        processing_method=f"{pipeline_version.value}_background_job",
        cost_estimate=0.0,
        processing_time={},
        performance_metrics={
            "file_size_mb": file_size_mb,
            "job_id": job_id,
            "optimization_level": "background",
            "priority": options.priority,
            "pipeline_version": pipeline_version.value
        }
    )
    
    return APIResponse[ProcessingResponse](
        success=True,
        data=processing_response,
        message=f"File submitted for background processing with {pipeline_version.value} pipeline. Job ID: {job_id}"
    )


@router.get("/pipeline-health", response_model=APIResponse[Dict[str, Any]])
@monitor_api_call
async def get_pipeline_health():
    """Get health status of V2 pipeline components."""
    try:
        proc = await get_pipeline()
        health_data = await proc.health_check()
        
        return APIResponse[Dict[str, Any]](
            success=True,
            data=health_data,
            message="V2 pipeline health check completed"
        )
    except Exception as e:
        return APIResponse[Dict[str, Any]](
            success=False,
            data={"error": str(e)},
            message="V2 pipeline health check failed"
        )


@router.get("/pipeline-stats", response_model=APIResponse[Dict[str, Any]])
@monitor_api_call
async def get_pipeline_statistics():
    """Get V2 pipeline configuration and performance statistics."""
    try:
        proc = await get_pipeline()
        stats_data = await proc.get_pipeline_statistics()
        
        return APIResponse[Dict[str, Any]](
            success=True,
            data=stats_data,
            message="V2 pipeline statistics retrieved"
        )
    except Exception as e:
        return APIResponse[Dict[str, Any]](
            success=False,
            data={"error": str(e)},
            message="Failed to get V2 pipeline statistics"
        )


@router.post("/validate-pdf", response_model=APIResponse[Dict[str, Any]])
@monitor_api_call
async def validate_pdf_v2(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """Validate PDF file before processing with V2 pipeline."""
    temp_file_path = None
    
    try:
        # Create temporary file for validation
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file_path = temp_file.name
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()
        
        # Validate through V2 pipeline
        proc = await get_pipeline()
        validation_result = await proc.validate_pdf_file(temp_file_path)
        
        return APIResponse[Dict[str, Any]](
            success=True,
            data={
                "valid": validation_result['valid'],
                "errors": validation_result.get('errors', []),
                "warnings": validation_result.get('warnings', []),
                "file_info": validation_result.get('file_info', {}),
                "file_name": file.filename,
                "file_size_bytes": len(content),
                "validator": "v2_pipeline"
            },
            message="PDF validation completed"
        )
        
    except Exception as e:
        return APIResponse[Dict[str, Any]](
            success=False,
            data={"error": str(e)},
            message="PDF validation failed"
        )
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass


@router.get("/compare-pipelines/{user_id}", response_model=APIResponse[Dict[str, Any]])
@monitor_api_call
async def compare_pipeline_performance(
    user_id: str,
    days: int = Query(7, description="Number of days to look back"),
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """
    Compare performance between V1 and V2 pipelines for A/B testing analysis.
    (Admin or self-access only)
    """
    # Check access permissions
    if current_user.get('id') != user_id and not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # This would query your monitoring/analytics system
    # For now, return a mock comparison
    comparison_data = {
        "period": f"last_{days}_days",
        "user_id": user_id,
        "pipelines": {
            "v1": {
                "total_files": 0,
                "avg_processing_time_ms": 0,
                "avg_tradelines_extracted": 0,
                "success_rate": 0,
                "avg_cost": 0
            },
            "v2": {
                "total_files": 0,
                "avg_processing_time_ms": 0,
                "avg_tradelines_extracted": 0,
                "success_rate": 0,
                "avg_cost": 0
            }
        },
        "recommendation": "continue_ab_testing"
    }
    
    return APIResponse[Dict[str, Any]](
        success=True,
        data=comparison_data,
        message="Pipeline performance comparison completed"
    )


# Maintain compatibility with existing V1 endpoints by importing them
# This allows gradual migration
@router.get("/job/{job_id}", response_model=APIResponse[JobStatusResponse])
@monitor_api_call  
async def get_job_status_v2(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """Get background job status (compatible with V1)."""
    # Import V1 function to maintain compatibility
    from api.v1.routes.processing import get_job_status
    return await get_job_status(job_id, current_user)


@router.get("/jobs", response_model=APIResponse[List[JobStatusResponse]])  
@monitor_api_call
async def get_user_jobs_v2(
    current_user: Dict[str, Any] = Depends(get_supabase_user),
    limit: int = 20,
    status_filter: str = None
):
    """Get user's processing jobs (compatible with V1)."""
    # Import V1 function to maintain compatibility
    from api.v1.routes.processing import get_user_jobs
    return await get_user_jobs(current_user, limit, status_filter)


@router.delete("/job/{job_id}", response_model=APIResponse[Dict[str, str]])
@monitor_api_call
async def cancel_job_v2(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """Cancel a background processing job (compatible with V1)."""
    # Import V1 function to maintain compatibility  
    from api.v1.routes.processing import cancel_job
    return await cancel_job(job_id, current_user)