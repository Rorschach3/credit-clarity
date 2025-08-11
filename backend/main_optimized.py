"""
Performance-Optimized Credit Clarity API
Combines security enhancements with performance optimizations
"""
import os
import sys
import logging
import tempfile
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager
import asyncio
import time

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import optimized modules
from core.config import get_settings, validate_required_settings
from core.security import (
    get_supabase_user, 
    get_current_user_optional,
    check_rate_limit,
    AuthenticationError
)
from middleware.security import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    ContentValidationMiddleware
)

# Import performance services
from services.optimized_processor import OptimizedCreditReportProcessor
from services.database_optimizer import db_optimizer
from services.cache_service import cache, cached
from services.background_jobs import job_processor, submit_pdf_processing_job, JobPriority
from services.monitoring import (
    metrics_collector, 
    monitor_api_call, 
    track_performance,
    track_pdf_processing_time,
    track_tradelines_extracted,
    track_user_activity,
    start_monitoring
)

# Initialize settings
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.is_development() else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress verbose logs
logging.getLogger('pdfminer').setLevel(logging.WARNING)
logging.getLogger('google.cloud').setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with performance monitoring."""
    startup_time = time.time()
    logger.info("🚀 Starting optimized Credit Clarity API...")
    
    try:
        # Validate configuration
        validate_required_settings()
        logger.info("✅ Configuration validation passed")
        
        # Initialize services
        await initialize_optimized_services()
        logger.info("✅ Optimized services initialized")
        
        # Start background services
        await job_processor.start()
        await start_monitoring()
        logger.info("✅ Background services started")
        
        startup_duration = time.time() - startup_time
        logger.info(f"🎉 Startup completed in {startup_duration:.2f}s")
        
        # Track startup time
        metrics_collector.record_business_metric(
            'app_startup_time_ms',
            startup_duration * 1000,
            'gauge'
        )
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down optimized API...")
    await job_processor.stop()
    await metrics_collector.stop_collection()
    

# Create optimized FastAPI app
app = FastAPI(
    title="Credit Clarity API - Optimized",
    description="High-performance credit report processing with security",
    version="2.1.0",
    docs_url="/docs" if settings.is_development() else None,
    redoc_url="/redoc" if settings.is_development() else None,
    lifespan=lifespan
)

# Add performance-aware middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ContentValidationMiddleware)
app.add_middleware(RateLimitMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Process-Time", "X-RateLimit-Limit"]
)

# Global services
optimized_processor = None


async def initialize_optimized_services():
    """Initialize all optimized services."""
    global optimized_processor
    
    try:
        # Initialize optimized processor
        optimized_processor = OptimizedCreditReportProcessor()
        logger.info("✅ Optimized processor initialized")
        
        # Warm up cache with common data
        await warmup_cache()
        logger.info("✅ Cache warmed up")
        
    except Exception as e:
        logger.error(f"❌ Service initialization failed: {e}")
        raise


async def warmup_cache():
    """Warm up cache with commonly accessed data."""
    try:
        # Cache common configuration
        await cache.set("app_config", {
            "version": "2.1.0",
            "features": ["pdf_processing", "background_jobs", "caching"],
            "performance_mode": True
        }, ttl=3600)
        
    except Exception as e:
        logger.warning(f"Cache warmup failed: {e}")


# Enhanced response models
class OptimizedTradelineResponse(BaseModel):
    """Optimized tradeline response model."""
    creditor_name: str = "NULL"
    account_balance: str = ""
    credit_limit: str = ""
    monthly_payment: str = ""
    account_number: str = ""
    date_opened: str = ""
    account_type: str = ""
    account_status: str = ""
    credit_bureau: str = ""
    is_negative: bool = False
    dispute_count: int = 0


class OptimizedProcessingResponse(BaseModel):
    """Enhanced processing response with performance metrics."""
    success: bool
    message: str = ""
    tradelines_found: int = 0
    tradelines: List[OptimizedTradelineResponse] = []
    processing_method: str = ""
    cost_estimate: float = 0.0
    processing_time: Dict[str, Any] = {}
    performance_metrics: Dict[str, Any] = {}
    cache_hit: bool = False


class JobStatusResponse(BaseModel):
    """Background job status response."""
    job_id: str
    status: str
    progress: int
    message: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    processing_time: Optional[float] = None


# Health check with performance metrics
@app.get("/health")
@cached(ttl=30, key_prefix="health_check")
async def health_check():
    """Enhanced health check with performance metrics."""
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.1.0",
        "environment": settings.environment,
        "features": {
            "security": True,
            "performance_optimization": True,
            "background_jobs": True,
            "caching": True,
            "monitoring": True
        },
        "services": {
            "optimized_processor": optimized_processor is not None,
            "background_jobs": job_processor.is_running,
            "cache": True,
            "database": True
        }
    }
    
    # Add performance metrics if available
    try:
        health_status = metrics_collector.get_health_status()
        health_data["system_health"] = health_status
        
        # Add cache statistics
        cache_stats = cache.stats()
        health_data["cache_stats"] = cache_stats
        
    except Exception as e:
        logger.debug(f"Failed to get performance metrics for health check: {e}")
    
    return health_data


# Fast PDF processing endpoint (synchronous for small files)
@app.post("/process-credit-report-fast", response_model=OptimizedProcessingResponse)
@monitor_api_call
async def process_credit_report_fast(
    request: Request,
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_supabase_user),
    _: None = Depends(check_rate_limit)
):
    """
    Fast credit report processing for small files (< 5MB).
    Uses optimized concurrent processing with caching.
    """
    start_time = time.time()
    user_id = current_user.get("id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found")
    
    # Track user activity
    track_user_activity("pdf_upload_fast", user_id)
    
    logger.info(f"🚀 Fast processing for user: {user_id}, file: {file.filename}")
    
    # File size check for fast processing
    file_content = await file.read()
    file_size_mb = len(file_content) / (1024 * 1024)
    
    if file_size_mb > 5:
        # Redirect to background processing for large files
        return await submit_background_processing(file, file_content, user_id)
    
    # Validate file
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    if not file_content.startswith(b'%PDF'):
        raise HTTPException(status_code=400, detail="Invalid PDF file")
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        temp_file.write(file_content)
        temp_file_path = temp_file.name
    
    try:
        # Process with optimized pipeline
        with track_performance(f"fast_pdf_processing_{user_id}"):
            result = await optimized_processor.process_credit_report_optimized(temp_file_path)
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Processing failed'))
        
        tradelines = result.get('tradelines', [])
        
        # Save to database with batch optimization
        if tradelines:
            for tradeline in tradelines:
                tradeline['user_id'] = user_id
            
            with track_performance(f"batch_save_{user_id}"):
                save_result = await db_optimizer.batch_insert_tradelines(tradelines)
            
            logger.info(f"Saved {save_result.get('inserted', 0)} tradelines to database")
        
        # Track metrics
        processing_time_ms = (time.time() - start_time) * 1000
        track_pdf_processing_time(processing_time_ms, result.get('method_used', 'optimized'))
        track_tradelines_extracted(len(tradelines), user_id)
        
        # Prepare response
        response_tradelines = [OptimizedTradelineResponse(**t) for t in tradelines]
        
        performance_metrics = {
            "file_size_mb": file_size_mb,
            "processing_time_ms": processing_time_ms,
            "method_used": result.get('method_used'),
            "cache_hit": result.get('cache_hit', False),
            "tradelines_processed": len(tradelines),
            "optimization_level": "fast"
        }
        
        return OptimizedProcessingResponse(
            success=True,
            message=f"Successfully processed {len(tradelines)} tradelines",
            tradelines_found=len(tradelines),
            tradelines=response_tradelines,
            processing_method=result.get('method_used', 'optimized'),
            cost_estimate=result.get('cost_estimate', 0.0),
            processing_time={
                "start_time": datetime.fromtimestamp(start_time).isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_ms": processing_time_ms
            },
            performance_metrics=performance_metrics,
            cache_hit=result.get('cache_hit', False)
        )
        
    finally:
        # Cleanup
        try:
            os.unlink(temp_file_path)
        except:
            pass


async def submit_background_processing(file: UploadFile, file_content: bytes, user_id: str) -> OptimizedProcessingResponse:
    """Submit large file for background processing."""
    # Save file for background processing
    file_id = f"bg_{user_id}_{int(time.time())}"
    temp_path = f"/tmp/credit_report_{file_id}.pdf"
    
    with open(temp_path, 'wb') as f:
        f.write(file_content)
    
    # Submit background job
    job_id = await submit_pdf_processing_job(
        pdf_path=temp_path,
        user_id=user_id,
        priority=JobPriority.HIGH
    )
    
    return OptimizedProcessingResponse(
        success=True,
        message=f"Large file submitted for background processing. Job ID: {job_id}",
        tradelines_found=0,
        tradelines=[],
        processing_method="background_job",
        cost_estimate=0.0,
        processing_time={},
        performance_metrics={
            "file_size_mb": len(file_content) / (1024 * 1024),
            "job_id": job_id,
            "optimization_level": "background"
        }
    )


# Background job status endpoint
@app.get("/job/{job_id}", response_model=JobStatusResponse)
@monitor_api_call
async def get_job_status(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """Get background job status."""
    job_data = await job_processor.get_job_status(job_id)
    
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Verify user access
    if job_data.get('user_id') != current_user.get('id'):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return JobStatusResponse(
        job_id=job_data['job_id'],
        status=job_data['status'],
        progress=job_data['progress'],
        message=job_data.get('progress_message', ''),
        result=job_data.get('result'),
        error=job_data.get('error'),
        created_at=job_data['created_at'],
        processing_time=job_data.get('processing_time')
    )


# User's jobs endpoint
@app.get("/my-jobs")
@monitor_api_call
async def get_user_jobs(
    current_user: Dict[str, Any] = Depends(get_supabase_user),
    limit: int = 20
):
    """Get user's recent jobs."""
    user_id = current_user.get('id')
    jobs = job_processor.job_queue.get_user_jobs(user_id, limit)
    
    return {
        "jobs": [job.to_dict() for job in jobs],
        "total": len(jobs)
    }


# Performance metrics endpoint (admin only)
@app.get("/admin/metrics")
@monitor_api_call
async def get_performance_metrics(
    current_user: Dict[str, Any] = Depends(get_supabase_user),
    minutes: int = 60
):
    """Get system performance metrics (admin only)."""
    # Simple admin check (you might want to implement proper role checking)
    user_email = current_user.get('email', '')
    if not user_email.endswith('@creditclarity.com'):  # Replace with your domain
        raise HTTPException(status_code=403, detail="Admin access required")
    
    system_metrics = metrics_collector.get_system_metrics_summary(minutes)
    api_metrics = metrics_collector.get_api_metrics_summary(minutes)
    business_metrics = metrics_collector.get_business_metrics_summary(minutes)
    job_stats = job_processor.get_stats()
    cache_stats = cache.stats()
    
    return {
        "system": system_metrics,
        "api": api_metrics,
        "business": business_metrics,
        "background_jobs": job_stats,
        "cache": cache_stats,
        "timestamp": datetime.now().isoformat()
    }


# Cache management endpoint (admin only)
@app.post("/admin/cache/clear")
@monitor_api_call
async def clear_cache(
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """Clear application cache (admin only)."""
    user_email = current_user.get('email', '')
    if not user_email.endswith('@creditclarity.com'):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await cache.clear()
    db_optimizer.clear_cache()
    
    return {"message": "Cache cleared successfully"}


# Optimized tradelines endpoint with caching
@app.get("/tradelines")
@monitor_api_call
async def get_user_tradelines(
    current_user: Dict[str, Any] = Depends(get_supabase_user),
    limit: int = 50,
    offset: int = 0
):
    """Get user's tradelines with optimized caching."""
    user_id = current_user.get('id')
    
    # Use optimized database queries
    result = await db_optimizer.get_user_tradelines_optimized(
        user_id=user_id,
        limit=limit,
        offset=offset
    )
    
    return result


# Error handlers with performance tracking
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Enhanced HTTP exception handler with metrics."""
    # Track error metrics
    metrics_collector.record_business_metric(
        'http_errors',
        1,
        'counter',
        {'status_code': str(exc.status_code), 'endpoint': request.url.path}
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "detail": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "request_id": request.headers.get("x-request-id")
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler with error tracking."""
    # Track unexpected errors
    metrics_collector.record_business_metric(
        'unexpected_errors',
        1,
        'counter',
        {'endpoint': request.url.path, 'error_type': type(exc).__name__}
    )
    
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    
    detail = str(exc) if settings.is_development() else "Internal server error"
    
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "status_code": 500,
            "detail": detail,
            "timestamp": datetime.now().isoformat(),
            "request_id": request.headers.get("x-request-id")
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main_optimized:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development(),
        log_level="debug" if settings.is_development() else "info",
        workers=1,  # Use 1 worker for development, scale in production
        loop="asyncio",
        access_log=True
    )