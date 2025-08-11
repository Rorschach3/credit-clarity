"""
Modular Credit Clarity API - Phase 3 Architecture
Clean, modular structure with proper separation of concerns
"""
import os
import sys
import logging
import asyncio
import time
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from pydantic import ValidationError

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import modular components
from core.config import get_settings, validate_required_settings
from core.exceptions import CreditClarityException, to_http_exception, ErrorResponse, ErrorDetail
from middleware.security import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    ContentValidationMiddleware
)

# Import API router
from api.v1.router import v1_router

# Import services for initialization
from services.optimized_processor import OptimizedCreditReportProcessor
from services.database_optimizer import db_optimizer
from services.cache_service import cache
from services.background_jobs import job_processor
from services.monitoring import metrics_collector, start_monitoring

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
    """Application lifespan management with proper startup/shutdown."""
    startup_time = time.time()
    logger.info("🚀 Starting modular Credit Clarity API...")
    
    try:
        # Validate configuration
        validate_required_settings()
        logger.info("✅ Configuration validation passed")
        
        # Initialize services
        await initialize_services()
        logger.info("✅ Services initialized")
        
        # Start background services
        await start_background_services()
        logger.info("✅ Background services started")
        
        startup_duration = time.time() - startup_time
        logger.info(f"🎉 Startup completed in {startup_duration:.2f}s")
        
        # Track startup metrics
        metrics_collector.record_business_metric(
            'app_startup_time_ms',
            startup_duration * 1000,
            'gauge',
            {'version': '3.0', 'architecture': 'modular'}
        )
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Graceful shutdown
    logger.info("🔄 Shutting down modular API...")
    await shutdown_services()
    logger.info("✅ Shutdown completed")


async def initialize_services():
    """Initialize all application services."""
    try:
        # Initialize processor
        app.state.processor = OptimizedCreditReportProcessor()
        logger.info("✅ Optimized processor initialized")
        
        # Initialize database connections
        await db_optimizer.initialize()
        logger.info("✅ Database optimizer initialized")
        
        # Initialize cache
        await cache.initialize()
        logger.info("✅ Cache service initialized")
        
        # Warm up cache
        await warmup_cache()
        logger.info("✅ Cache warmed up")
        
    except Exception as e:
        logger.error(f"❌ Service initialization failed: {e}")
        raise


async def start_background_services():
    """Start background processing services."""
    try:
        # Start job processor
        await job_processor.start()
        logger.info("✅ Background job processor started")
        
        # Start monitoring
        await start_monitoring()
        logger.info("✅ Monitoring services started")
        
    except Exception as e:
        logger.error(f"❌ Background services failed to start: {e}")
        raise


async def shutdown_services():
    """Gracefully shutdown all services."""
    try:
        # Stop background services
        if job_processor:
            await job_processor.stop()
        
        if metrics_collector:
            await metrics_collector.stop_collection()
        
        # Close database connections
        await db_optimizer.close()
        
        # Clear cache connections
        await cache.close()
        
        logger.info("✅ All services shutdown gracefully")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


async def warmup_cache():
    """Warm up cache with frequently accessed data."""
    try:
        await cache.set("app_config", {
            "version": "3.0",
            "architecture": "modular",
            "features": [
                "pdf_processing", 
                "background_jobs", 
                "caching", 
                "monitoring",
                "api_versioning",
                "error_handling"
            ],
            "performance_mode": True
        }, ttl=3600)
        
    except Exception as e:
        logger.warning(f"Cache warmup failed: {e}")


# Create modular FastAPI application
app = FastAPI(
    title="Credit Clarity API - Modular Architecture",
    description="High-performance credit report processing with clean architecture",
    version="3.0.0",
    docs_url="/docs" if settings.is_development() else None,
    redoc_url="/redoc" if settings.is_development() else None,
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Health",
            "description": "System health and status endpoints"
        },
        {
            "name": "Processing", 
            "description": "Credit report processing operations"
        },
        {
            "name": "Tradelines",
            "description": "Tradeline management and CRUD operations"
        },
        {
            "name": "Admin",
            "description": "Administrative functions and monitoring"
        }
    ]
)

# Add security middleware
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
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Process-Time", "X-RateLimit-Limit", "X-API-Version"]
)

# Include API routers
app.include_router(v1_router, prefix="/api")

# Add request middleware for tracking
@app.middleware("http")
async def add_request_tracking(request: Request, call_next):
    """Add request tracking and timing."""
    start_time = time.time()
    request.state.start_time = start_time
    
    # Generate request ID
    import uuid
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    
    response = await call_next(request)
    
    # Add headers
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-API-Architecture"] = "modular"
    
    return response

# Custom exception handlers
@app.exception_handler(CreditClarityException)
async def custom_exception_handler(request: Request, exc: CreditClarityException):
    """Handle custom application exceptions."""
    request_id = getattr(request.state, 'request_id', None)
    
    # Log the error
    logger.error(f"Application error [{request_id}]: {exc.message}", exc_info=True)
    
    # Track error metrics
    metrics_collector.record_business_metric(
        'application_errors',
        1,
        'counter',
        {
            'error_code': exc.error_code,
            'endpoint': request.url.path,
            'status_code': str(exc.status_code)
        }
    )
    
    # Convert to HTTP exception
    http_exc = to_http_exception(exc, request_id)
    return JSONResponse(
        status_code=http_exc.status_code,
        content=http_exc.detail
    )

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors."""
    request_id = getattr(request.state, 'request_id', None)
    
    # Extract validation details
    error_details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        error_details.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    error_response = ErrorResponse(
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details={"validation_errors": error_details}
        ),
        timestamp=datetime.now().isoformat(),
        request_id=request_id
    )
    
    logger.warning(f"Validation error [{request_id}]: {error_details}")
    
    return JSONResponse(
        status_code=422,
        content=error_response.dict()
    )

@app.exception_handler(HTTPException)
async def enhanced_http_exception_handler(request: Request, exc: HTTPException):
    """Enhanced HTTP exception handler with better error format."""
    request_id = getattr(request.state, 'request_id', None)
    
    # If detail is already in our format, use it
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )
    
    # Otherwise, format it properly
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=f"HTTP_{exc.status_code}",
            message=str(exc.detail)
        ),
        timestamp=datetime.now().isoformat(),
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    request_id = getattr(request.state, 'request_id', None)
    
    # Log the error
    logger.error(f"Unexpected error [{request_id}]: {str(exc)}", exc_info=True)
    
    # Track unexpected errors
    metrics_collector.record_business_metric(
        'unexpected_errors',
        1,
        'counter',
        {
            'endpoint': request.url.path,
            'error_type': type(exc).__name__
        }
    )
    
    # Return generic error in production, detailed in development
    if settings.is_development():
        message = f"Internal server error: {str(exc)}"
    else:
        message = "An unexpected error occurred"
    
    error_response = ErrorResponse(
        error=ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message=message
        ),
        timestamp=datetime.now().isoformat(),
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.dict()
    )

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint with basic information."""
    return {
        "name": "Credit Clarity API",
        "version": "3.0.0",
        "architecture": "modular",
        "status": "operational",
        "api_docs": "/docs" if settings.is_development() else None,
        "health_check": "/api/v1/health"
    }

# Health check endpoint (simplified version)
@app.get("/health")
async def simple_health_check():
    """Simple health check for load balancers."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    
    # Run with optimal settings
    uvicorn.run(
        "main_modular:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development(),
        log_level="debug" if settings.is_development() else "info",
        workers=1,  # Use 1 worker for development, scale in production
        loop="asyncio",
        access_log=True,
        server_header=False,  # Don't expose server info
        date_header=True
    )