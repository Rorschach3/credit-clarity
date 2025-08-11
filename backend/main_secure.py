"""
Secure Credit Report Processing API
Enhanced with proper authentication, rate limiting, and security headers
"""
import os
import sys
import logging
import tempfile
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import our secure modules
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

# Import original processing classes
from utils.field_validator import field_validator
from utils.tradeline_normalizer import tradeline_normalizer

# Initialize settings
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.is_development() else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress verbose PDF processing logs
logging.getLogger('pdfminer').setLevel(logging.WARNING)
logging.getLogger('google.cloud').setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("🚀 Starting Credit Clarity API...")
    
    try:
        # Validate required settings
        validate_required_settings()
        logger.info("✅ Configuration validation passed")
        
        # Initialize services
        await initialize_services()
        logger.info("✅ Services initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down Credit Clarity API...")


# Create FastAPI app with security configuration
app = FastAPI(
    title="Credit Clarity API",
    description="Secure credit report processing with authentication",
    version="2.0.0",
    docs_url="/docs" if settings.is_development() else None,  # Disable docs in production
    redoc_url="/redoc" if settings.is_development() else None,
    lifespan=lifespan
)

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ContentValidationMiddleware)
app.add_middleware(RateLimitMiddleware)

# Configure CORS with security considerations
if settings.is_development():
    # Development: Allow localhost origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
else:
    # Production: Strict CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

# Global variables for services (initialized in lifespan)
supabase_client = None
gemini_model = None
document_ai_client = None
optimal_processor = None


async def initialize_services():
    """Initialize all external services with proper error handling."""
    global supabase_client, gemini_model, document_ai_client, optimal_processor
    
    # Initialize Supabase
    if settings.supabase_url and settings.supabase_anon_key:
        try:
            from supabase import create_client
            supabase_client = create_client(settings.supabase_url, settings.supabase_anon_key)
            logger.info("✅ Supabase client initialized")
        except Exception as e:
            logger.error(f"❌ Supabase initialization failed: {e}")
            if settings.is_production():
                raise
    
    # Initialize Gemini
    if settings.gemini_api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            gemini_model = genai.GenerativeModel('gemini-2.0-flash')
            logger.info("✅ Gemini model initialized")
        except Exception as e:
            logger.warning(f"⚠️ Gemini initialization failed: {e}")
    
    # Initialize Document AI
    if settings.google_cloud_project_id and settings.document_ai_processor_id:
        try:
            from google.cloud import documentai
            from google.oauth2 import service_account
            
            if settings.google_application_credentials and os.path.exists(settings.google_application_credentials):
                credentials = service_account.Credentials.from_service_account_file(
                    settings.google_application_credentials
                )
                document_ai_client = documentai.DocumentProcessorServiceClient(credentials=credentials)
                logger.info("✅ Document AI client initialized with service account")
            else:
                document_ai_client = documentai.DocumentProcessorServiceClient()
                logger.info("✅ Document AI client initialized with default credentials")
        except Exception as e:
            logger.warning(f"⚠️ Document AI initialization failed: {e}")
    
    # Initialize optimal processor
    try:
        from main import OptimalCreditReportProcessor  # Import from original main.py
        optimal_processor = OptimalCreditReportProcessor()
        logger.info("✅ Optimal processor initialized")
    except Exception as e:
        logger.warning(f"⚠️ Optimal processor initialization failed: {e}")


# Pydantic models
class TradelineResponse(BaseModel):
    """Response model for tradeline data."""
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


class ProcessingResponse(BaseModel):
    """Response model for processing results."""
    success: bool
    message: str = ""
    tradelines_found: int = 0
    tradelines: List[TradelineResponse] = []
    processing_method: str = ""
    cost_estimate: float = 0.0
    processing_time: Dict[str, Any] = {}


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    services: Dict[str, str]
    environment: str
    version: str


# Health check endpoint (no authentication required)
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with service status."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        environment=settings.environment,
        version="2.0.0",
        services={
            "supabase": "configured" if supabase_client else "not_configured",
            "gemini": "configured" if gemini_model else "not_configured",
            "document_ai": "configured" if document_ai_client else "not_configured",
            "processor": "configured" if optimal_processor else "not_configured"
        }
    )


# Test endpoint for development
@app.post("/test-pdf")
async def test_pdf_processing(
    file: UploadFile = File(...),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Test PDF processing endpoint (development only)."""
    if not settings.is_development():
        raise HTTPException(status_code=404, detail="Endpoint not available in production")
    
    logger.info(f"🧪 Test PDF processing: {file.filename}")
    
    # Basic file validation
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400, 
            detail="Only PDF files are supported"
        )
    
    # Save file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name
    
    try:
        # Test basic PDF reading
        import pdfplumber
        with pdfplumber.open(temp_file_path) as pdf:
            page_count = len(pdf.pages)
            first_page_text = pdf.pages[0].extract_text() if page_count > 0 else ""
            
            return {
                "success": True,
                "page_count": page_count,
                "first_page_preview": first_page_text[:200] if first_page_text else "No text found",
                "file_size": len(content),
                "user_authenticated": current_user is not None
            }
    
    except Exception as e:
        logger.error(f"❌ PDF test failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"PDF processing test failed: {str(e)}"
        )
    finally:
        try:
            os.unlink(temp_file_path)
        except:
            pass


# Main processing endpoint with authentication
@app.post("/process-credit-report", response_model=ProcessingResponse)
async def process_credit_report_secure(
    request: Request,
    file: UploadFile = File(...),
    user_id: str = Form(default=""),
    current_user: Dict[str, Any] = Depends(get_supabase_user),
    _: None = Depends(check_rate_limit)  # Rate limiting dependency
):
    """
    Secure credit report processing endpoint.
    Requires authentication and implements rate limiting.
    """
    start_time = datetime.now()
    
    # Use authenticated user ID, not form parameter
    authenticated_user_id = current_user.get("id")
    if not authenticated_user_id:
        raise HTTPException(
            status_code=401,
            detail="User ID not found in authentication token"
        )
    
    logger.info(f"🚀 Processing credit report for authenticated user: {authenticated_user_id}")
    logger.info(f"📁 Uploaded file: {file.filename}, Content-Type: {file.content_type}")
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Please upload a PDF file. Received: {file.filename}"
        )
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        try:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
            
            logger.info(f"📄 File saved to: {temp_file_path}, Size: {len(content)} bytes")
            
            # Basic PDF validation
            if len(content) < 100:
                raise HTTPException(
                    status_code=400,
                    detail="File too small to be a valid PDF"
                )
            
            if not content.startswith(b'%PDF'):
                raise HTTPException(
                    status_code=400,
                    detail="File does not appear to be a valid PDF"
                )
            
            # Check if optimal processor is available
            if not optimal_processor:
                raise HTTPException(
                    status_code=503,
                    detail="PDF processing service is not available"
                )
            
            # Process with optimal pipeline
            logger.info("🚀 Starting secure processing pipeline...")
            
            # Calculate timeout based on file size
            file_size_mb = len(content) / (1024 * 1024)
            timeout_minutes = max(5, min(20, int(file_size_mb * 2)))
            timeout_seconds = timeout_minutes * 60
            
            logger.info(f"⏱️ Processing timeout set to {timeout_minutes} minutes for {file_size_mb:.2f}MB file")
            
            # Process with timeout
            try:
                result = await asyncio.wait_for(
                    optimal_processor.process_credit_report_optimal(temp_file_path),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                logger.error(f"⏰ Processing timeout after {timeout_minutes} minutes")
                raise HTTPException(
                    status_code=408,
                    detail=f"Processing timed out after {timeout_minutes} minutes"
                )
            
            if not result.get('success'):
                raise HTTPException(
                    status_code=500,
                    detail=result.get('error', 'Processing failed')
                )
            
            # Prepare response
            processing_time = {
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_seconds": result.get('processing_time', 0),
                "duration_formatted": f"{result.get('processing_time', 0):.2f}s"
            }
            
            # Convert tradelines to response format
            tradelines = []
            for tradeline in result.get('tradelines', []):
                tradelines.append(TradelineResponse(**tradeline))
            
            logger.info(f"✅ Processing completed successfully: {len(tradelines)} tradelines found")
            
            return ProcessingResponse(
                success=True,
                message=f"Successfully processed {len(tradelines)} tradelines",
                tradelines_found=len(tradelines),
                tradelines=tradelines,
                processing_method=result.get('method_used', 'unknown'),
                cost_estimate=result.get('cost_estimate', 0.0),
                processing_time=processing_time
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Processing error: {str(e)}")
            logger.error(f"❌ Processing error traceback:", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Processing failed: {str(e)}"
            )
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file_path)
            except:
                pass


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail} - {request.method} {request.url}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "detail": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors."""
    logger.warning(f"Validation error: {exc} - {request.method} {request.url}")
    
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "status_code": 422,
            "detail": "Validation error",
            "errors": exc.errors(),
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(f"Unexpected error: {exc} - {request.method} {request.url}", exc_info=True)
    
    # Don't expose internal errors in production
    detail = str(exc) if settings.is_development() else "Internal server error"
    
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "status_code": 500,
            "detail": detail,
            "timestamp": datetime.now().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    # Run the secure application
    uvicorn.run(
        "main_secure:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development(),
        log_level="debug" if settings.is_development() else "info"
    )