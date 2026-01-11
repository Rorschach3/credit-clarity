"""
API Router for credit report processing and tradeline extraction.
Handles PDF uploads, processing, and extraction with enhanced prompts.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Dict, Any
import logging
import uuid
import io
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["credit-reports"])


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "credit-report-processor"}


@router.post("/process-credit-report")
async def process_credit_report(file: UploadFile = File(...)):
    """
    Main endpoint for processing credit reports and extracting tradelines.

    This endpoint:
    1. Accepts PDF upload
    2. Extracts text content
    3. Uses enhanced prompts to extract ALL tradelines
    4. Returns structured tradeline data with confidence scores
    """
    try:
        logger.info(f"Received credit report upload: {file.filename}")

        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        # Read file content
        file_content = await file.read()
        file_size = len(file_content)

        logger.info(f"File size: {file_size} bytes")

        # Create job ID
        job_id = str(uuid.uuid4())

        # Extract text from PDF
        logger.info(f"Extracting text from PDF for job {job_id}")
        text_content = extract_text_from_pdf(file_content)

        # Detect credit bureau
        from enhanced_bureau_detection import EnhancedBureauDetector
        bureau_detector = EnhancedBureauDetector()
        detected_bureau, confidence, indicators = bureau_detector.detect_credit_bureau(text_content)
        logger.info(f"Detected bureau: {detected_bureau} (confidence: {confidence:.2f})")

        # Extract tradelines using enhanced extraction
        logger.info(f"Extracting tradelines with enhanced prompts for job {job_id}")
        from services.enhanced_extraction_service import EnhancedExtractionService
        enhanced_extraction = EnhancedExtractionService()

        tradelines = enhanced_extraction.extract_enhanced_tradelines(
            text=text_content,
            detected_bureau=detected_bureau
        )

        logger.info(f"Pattern-based extraction found {len(tradelines)} tradelines")

        # Format tradelines to include all 9 required fields
        formatted_tradelines = []
        for idx, tradeline in enumerate(tradelines):
            formatted_tradeline = {
                "id": idx + 1,
                "creditor_name": tradeline.get("creditor_name", "Unknown"),
                "account_number": tradeline.get("account_number", "Not found"),
                "credit_bureau": detected_bureau,
                "date_opened": tradeline.get("date_opened", "Not found"),
                "account_balance": tradeline.get("current_balance", "$0"),
                "monthly_payment": tradeline.get("monthly_payment", "$0"),
                "account_type": tradeline.get("account_type", "Unknown"),
                "account_status": tradeline.get("account_status", "Unknown"),
                "credit_limit": tradeline.get("credit_limit", "$0"),
                "confidence_score": tradeline.get("confidence_score", 0.5),
                "extraction_notes": tradeline.get("extraction_notes", "Extracted via pattern matching")
            }
            formatted_tradelines.append(formatted_tradeline)

        logger.info(f"Successfully extracted {len(formatted_tradelines)} tradelines for job {job_id}")

        return {
            "success": True,
            "job_id": job_id,
            "detected_bureau": detected_bureau,
            "tradelines_count": len(formatted_tradelines),
            "tradelines": formatted_tradelines,
            "message": f"Successfully extracted {len(formatted_tradelines)} tradelines"
        }

    except Exception as e:
        logger.error(f"Error processing credit report: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Simple file upload endpoint that returns a job_id"""
    try:
        job_id = str(uuid.uuid4())
        file_content = await file.read()

        return {
            "job_id": job_id,
            "status": "uploaded",
            "filename": file.filename,
            "size": len(file_content)
        }

    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/llm/status")
async def get_llm_status():
    """Get LLM service status"""
    try:
        from config.llm_config import get_llm_config
        llm_config = get_llm_config()
        return {
            "status": "active",
            "service": "llm-parsing",
            "openai_configured": llm_config.is_openai_configured(),
            "gemini_configured": llm_config.is_gemini_configured()
        }
    except:
        return {
            "status": "active",
            "service": "llm-parsing",
            "openai_configured": False,
            "gemini_configured": False
        }


def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF using PyPDF2"""
    try:
        from PyPDF2 import PdfReader

        pdf_file = io.BytesIO(file_content)
        reader = PdfReader(pdf_file)

        text = ""
        for page_num, page in enumerate(reader.pages):
            text += f"\n--- Page {page_num + 1} ---\n"
            page_text = page.extract_text()
            if page_text:
                text += page_text

        return text

    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF extraction failed: {str(e)}")


@router.post("/quick-test")
async def quick_test(file: UploadFile = File(...)):
    """Quick test endpoint for rapid PDF processing validation"""
    try:
        file_content = await file.read()
        text_content = extract_text_from_pdf(file_content)

        # Return first 1000 characters of extracted text
        return {
            "success": True,
            "filename": file.filename,
            "text_preview": text_content[:1000] + "..." if len(text_content) > 1000 else text_content,
            "total_length": len(text_content),
            "page_count": text_content.count("--- Page")
        }
    except Exception as e:
        logger.error(f"Quick test error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
