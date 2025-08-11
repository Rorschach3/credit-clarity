"""
API routes for tradeline extraction pipeline
Integrates with frontend file upload workflow
"""
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import tempfile
import os
from pathlib import Path
import asyncio

from services.tradeline_extraction.pipeline import TradelineExtractionPipeline, PipelineResult
from core.logging.logger import get_logger

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/tradeline-extraction", tags=["tradeline-extraction"])

# Initialize pipeline
pipeline = TradelineExtractionPipeline()


@router.post("/upload-and-extract", response_model=Dict[str, Any])
async def upload_and_extract_tradelines(
    file: UploadFile = File(...),
    user_id: Optional[str] = None,
    store_results: bool = True
) -> Dict[str, Any]:
    """
    Upload PDF file and extract tradelines
    Compatible with frontend file upload workflow
    """
    temp_file_path = None
    
    try:
        # Validate file type
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file_path = temp_file.name
            
            # Read and write file content
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()
        
        logger.info(f"Processing uploaded file: {file.filename} (size: {len(content)} bytes)")
        
        # Process through pipeline
        result = await pipeline.process_credit_report(
            pdf_path=temp_file_path,
            user_id=user_id,
            store_results=store_results
        )
        
        # Format response for frontend
        response = {
            "success": result.success,
            "data": {
                "pdf_processed": result.pdf_processed,
                "text_extracted": result.text_extracted,
                "tradelines_parsed": result.tradelines_parsed,
                "tradelines_stored": result.tradelines_stored,
                "processing_time_ms": result.processing_time_ms,
                "file_name": file.filename,
                "file_size_bytes": len(content)
            },
            "warnings": result.warnings,
            "error": result.error,
            "timestamp": asyncio.get_event_loop().time(),
            "version": "1.0.0"
        }
        
        logger.info(f"Pipeline completed: {result.tradelines_parsed} tradelines extracted")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to process uploaded file: {file.filename if file else 'unknown'}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except OSError:
                logger.warning(f"Failed to delete temporary file: {temp_file_path}")


@router.get("/health", response_model=Dict[str, Any])
async def get_pipeline_health() -> Dict[str, Any]:
    """
    Get health status of tradeline extraction pipeline
    """
    try:
        health_status = await pipeline.health_check()
        return {
            "success": True,
            "data": health_status,
            "timestamp": asyncio.get_event_loop().time(),
            "version": "1.0.0"
        }
    except Exception as e:
        logger.exception("Health check failed")
        return {
            "success": False,
            "error": f"Health check failed: {str(e)}",
            "timestamp": asyncio.get_event_loop().time(),
            "version": "1.0.0"
        }


@router.get("/statistics", response_model=Dict[str, Any])
async def get_pipeline_statistics() -> Dict[str, Any]:
    """
    Get pipeline configuration and statistics
    """
    try:
        stats = await pipeline.get_pipeline_statistics()
        return {
            "success": True,
            "data": stats,
            "timestamp": asyncio.get_event_loop().time(),
            "version": "1.0.0"
        }
    except Exception as e:
        logger.exception("Failed to get pipeline statistics")
        return {
            "success": False,
            "error": f"Failed to get statistics: {str(e)}",
            "timestamp": asyncio.get_event_loop().time(),
            "version": "1.0.0"
        }


@router.post("/validate-pdf", response_model=Dict[str, Any])
async def validate_pdf_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Validate PDF file before processing
    Useful for frontend pre-validation
    """
    temp_file_path = None
    
    try:
        # Create temporary file for validation
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file_path = temp_file.name
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()
        
        # Validate through pipeline
        validation_result = await pipeline.validate_pdf_file(temp_file_path)
        
        return {
            "success": True,
            "data": {
                "valid": validation_result['valid'],
                "errors": validation_result.get('errors', []),
                "warnings": validation_result.get('warnings', []),
                "file_info": validation_result.get('file_info', {}),
                "file_name": file.filename,
                "file_size_bytes": len(content)
            },
            "timestamp": asyncio.get_event_loop().time(),
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.exception("PDF validation failed")
        return {
            "success": False,
            "error": f"Validation failed: {str(e)}",
            "timestamp": asyncio.get_event_loop().time(),
            "version": "1.0.0"
        }
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass


@router.get("/supported-formats", response_model=Dict[str, Any])
async def get_supported_formats() -> Dict[str, Any]:
    """
    Get list of supported file formats
    """
    return {
        "success": True,
        "data": {
            "supported_extensions": [".pdf"],
            "max_file_size_mb": 50,
            "supported_bureaus": ["TransUnion"],
            "features": [
                "PDF text extraction",
                "Tradeline parsing",
                "Field validation",
                "Database storage",
                "Error handling"
            ]
        },
        "timestamp": asyncio.get_event_loop().time(),
        "version": "1.0.0"
    }


# Error handlers
@router.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with consistent response format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "timestamp": asyncio.get_event_loop().time(),
            "version": "1.0.0"
        }
    )