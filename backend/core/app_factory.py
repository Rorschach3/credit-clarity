"""
FastAPI Application Factory
Creates and configures the Credit Clarity FastAPI application
"""
import os
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Services
from services.background_jobs import job_processor

# API routes
from api.v1.router import api_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    # Startup
    try:
        await job_processor.start()
        logger.info("🚀 Background job processor started")
    except Exception as e:
        logger.error(f"❌ Failed to start background job processor: {e}")
    
    yield
    
    # Shutdown
    try:
        await job_processor.stop()
        logger.info("🛑 Background job processor stopped")
    except Exception as e:
        logger.error(f"❌ Failed to stop background job processor: {e}")


def create_app(
    title: str = "Credit Report Processor",
    debug: bool = None,
    environment: str = None
) -> FastAPI:
    """
    Create and configure FastAPI application
    
    Args:
        title: Application title
        debug: Debug mode (auto-detected from environment if None)
        environment: Environment name (auto-detected if None)
    
    Returns:
        Configured FastAPI application
    """
    # Auto-detect debug mode from environment
    if debug is None:
        debug = os.getenv("DEBUG", "false").lower() == "true"
    
    # Auto-detect environment
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development")
    
    # Create FastAPI app
    app = FastAPI(
        title=title,
        debug=debug,
        lifespan=lifespan,
        docs_url="/docs" if debug else None,
        redoc_url="/redoc" if debug else None
    )
    
    # Configure CORS
    _setup_cors(app, environment)
    
    # Include API routes
    app.include_router(api_router, prefix="/api")
    
    # Add health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "service": "credit-clarity-backend",
            "environment": environment,
            "debug": debug
        }
    
    # Add root endpoint
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "service": "Credit Clarity API",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs" if debug else "disabled"
        }
    
    logger.info(f"✅ FastAPI application created (environment: {environment}, debug: {debug})")
    return app


def _setup_cors(app: FastAPI, environment: str):
    """Setup CORS middleware based on environment"""
    if environment == "production":
        # Restrictive CORS for production
        allowed_origins = [
            "https://creditclarity.app",
            "https://www.creditclarity.app",
            # Add your production domains here
        ]
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
        )
        logger.info(f"🔒 Production CORS configured with origins: {allowed_origins}")
        
    elif environment == "staging":
        # Moderate CORS for staging
        allowed_origins = [
            "https://staging.creditclarity.app",
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:4173",
        ]
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["*"],
        )
        logger.info(f"🔧 Staging CORS configured with origins: {allowed_origins}")
        
    else:
        # Permissive CORS for development - comprehensive configuration
        origins = [
            "http://localhost:3000",    # React default
            "http://localhost:8080",    # Your frontend port
            "http://127.0.0.1:8080",
            "http://localhost:8081",    # Alternative frontend port
            "http://127.0.0.1:8081",
            "http://localhost:5173",    # Vite default
            "http://127.0.0.1:5173",
        ]
        
        # Add environment-specific origins
        if os.getenv("FRONTEND_URL"):
            origins.append(os.getenv("FRONTEND_URL"))
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            allow_headers=[
                "Accept",
                "Accept-Language",
                "Content-Language",
                "Content-Type",
                "Authorization",
                "X-Requested-With",
                "Origin",
                "Cache-Control",
                "Pragma",
            ],
            expose_headers=["*"],
            max_age=3600,
        )
        logger.info(f"🔓 Development CORS configured with origins: {origins}")


def setup_logging():
    """Setup application logging"""
    # Enhanced logging setup
    logging.basicConfig(
        level=logging.DEBUG if os.getenv("DEBUG", "false").lower() == "true" else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Suppress noisy third-party logs
    noisy_loggers = [
        'pdfminer', 'pdfminer.psparser', 'pdfminer.pdfinterp', 
        'pdfminer.converter', 'pdfminer.pdfdocument', 'pdfminer.pdfpage',
        'PIL.PngImagePlugin', 'urllib3.connectionpool'
    ]
    
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    logger.info("📋 Logging configured")


def validate_environment():
    """Validate required environment variables"""
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY"
    ]
    
    optional_vars = [
        "GOOGLE_CLOUD_PROJECT_ID",
        "DOCUMENT_AI_PROCESSOR_ID", 
        "GEMINI_API_KEY"
    ]
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
    
    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)
    
    if missing_required:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_required)}")
        raise ValueError(f"Missing required environment variables: {', '.join(missing_required)}")
    
    if missing_optional:
        logger.warning(f"⚠️ Missing optional environment variables (some features may be disabled): {', '.join(missing_optional)}")
    
    logger.info("✅ Environment validation passed")


def create_production_app() -> FastAPI:
    """Create production-ready application with all validations"""
    setup_logging()
    validate_environment()
    
    return create_app(
        title="Credit Clarity API",
        debug=False,
        environment="production"
    )


def create_development_app() -> FastAPI:
    """Create development application with debug features"""
    setup_logging()
    
    # Don't validate environment in development
    return create_app(
        title="Credit Clarity API (Development)",
        debug=True,
        environment="development"
    )