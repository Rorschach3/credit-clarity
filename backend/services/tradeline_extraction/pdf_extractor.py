"""
PDF text extraction service for TransUnion credit reports
Implements TDD approach with comprehensive error handling
"""
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import asyncio
from dataclasses import dataclass

# Import cost tracking
from services.cost_tracker import cost_tracker, OCRMethod

logger = logging.getLogger(__name__)


@dataclass
class PDFExtractionResult:
    """Result of PDF text extraction"""
    success: bool
    text: Optional[str] = None
    error: Optional[str] = None
    page_count: Optional[int] = None
    file_size_bytes: Optional[int] = None
    extraction_time_ms: Optional[float] = None


class TransUnionPDFExtractor:
    """
    PDF text extractor specifically designed for TransUnion credit reports
    Uses TDD approach with comprehensive testing
    """
    
    def __init__(self):
        self.supported_extensions = {'.pdf'}
        self.max_file_size_mb = 50
        self.extraction_timeout_seconds = 30
    
    def validate_pdf_file(self, file_path: str | Path) -> Dict[str, Any]:
        """
        Validate PDF file before extraction
        Returns validation results
        """
        path = Path(file_path)
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'file_info': {}
        }
        
        # Check file exists
        if not path.exists():
            validation_result['valid'] = False
            validation_result['errors'].append(f"File not found: {path}")
            return validation_result
        
        # Check file extension
        if path.suffix.lower() not in self.supported_extensions:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Unsupported file type: {path.suffix}")
            return validation_result
        
        # Check file size
        try:
            file_size = path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            validation_result['file_info']['size_bytes'] = file_size
            validation_result['file_info']['size_mb'] = round(file_size_mb, 2)
            
            if file_size_mb > self.max_file_size_mb:
                validation_result['valid'] = False
                validation_result['errors'].append(f"File too large: {file_size_mb:.2f}MB > {self.max_file_size_mb}MB")
        except OSError as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Cannot read file: {e}")
        
        # Check if file can be opened
        try:
            with open(path, 'rb') as f:
                # Read first few bytes to verify PDF header
                header = f.read(8)
                if not header.startswith(b'%PDF-'):
                    validation_result['valid'] = False
                    validation_result['errors'].append("Invalid PDF file format")
                else:
                    validation_result['file_info']['pdf_version'] = header.decode('ascii', errors='ignore')
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Cannot read PDF header: {e}")
        
        return validation_result
    
    async def extract_text_from_pdf(self, file_path: str | Path) -> PDFExtractionResult:
        """
        Extract text from PDF file
        Returns PDFExtractionResult with text content and metadata
        """
        start_time = asyncio.get_event_loop().time()
        path = Path(file_path)
        
        # Validate file first
        validation = self.validate_pdf_file(path)
        if not validation['valid']:
            return PDFExtractionResult(
                success=False,
                error=f"Validation failed: {'; '.join(validation['errors'])}"
            )
        
        try:
            # Use cost-optimized extraction with real OCR methods
            extracted_text = await self._extract_with_fallback_methods(path)
            
            end_time = asyncio.get_event_loop().time()
            extraction_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            return PDFExtractionResult(
                success=True,
                text=extracted_text,
                file_size_bytes=validation['file_info']['size_bytes'],
                extraction_time_ms=round(extraction_time, 2)
            )
            
        except asyncio.TimeoutError:
            return PDFExtractionResult(
                success=False,
                error=f"PDF extraction timeout after {self.extraction_timeout_seconds} seconds"
            )
        except Exception as e:
            logger.exception(f"PDF extraction failed for {path}")
            return PDFExtractionResult(
                success=False,
                error=f"PDF extraction error: {str(e)}"
            )
    
    async def _extract_with_fallback_methods(self, path: Path) -> str:
        """
        Try multiple extraction methods with cost-optimized fallback strategy:
        1. Free methods first (pdfplumber, PyMuPDF, Tesseract OCR)
        2. Document AI as expensive last resort
        """
        extraction_methods = [
            ('pdfplumber', self._extract_with_pdfplumber),
            ('pymupdf', self._extract_with_pymupdf),
            ('tesseract_ocr', self._extract_with_tesseract),
            ('document_ai', self._extract_with_document_ai)
        ]
        
        last_error = None
        
        for method_name, method_func in extraction_methods:
            try:
                logger.info(f"Trying {method_name} extraction for {path.name}")
                result = await method_func(path)
                
                if result and self._validate_extraction_quality(result):
                    logger.info(f"✅ {method_name} extraction successful ({len(result)} chars)")
                    
                    # Track successful usage
                    file_size_mb = path.stat().st_size / (1024 * 1024)
                    cost_tracker.record_usage(
                        user_id="unknown",  # Will be set by pipeline
                        method=OCRMethod(method_name),
                        file_size_mb=file_size_mb,
                        processing_time_ms=0,  # Will be calculated by caller
                        success=True
                    )
                    
                    return result
                else:
                    logger.warning(f"⚠️ {method_name} extraction produced low quality result")
                    
                    # Track failed usage
                    file_size_mb = path.stat().st_size / (1024 * 1024)
                    cost_tracker.record_usage(
                        user_id="unknown",
                        method=OCRMethod(method_name),
                        file_size_mb=file_size_mb,
                        processing_time_ms=0,
                        success=False,
                        error_message="Low quality extraction result"
                    )
                    
            except Exception as e:
                last_error = str(e)
                logger.warning(f"❌ {method_name} extraction failed: {e}")
                
                # Track failed usage
                try:
                    file_size_mb = path.stat().st_size / (1024 * 1024)
                    cost_tracker.record_usage(
                        user_id="unknown",
                        method=OCRMethod(method_name),
                        file_size_mb=file_size_mb,
                        processing_time_ms=0,
                        success=False,
                        error_message=str(e)
                    )
                except:
                    pass  # Don't let tracking errors break the pipeline
                
                # If Document AI fails, we've exhausted all options
                if method_name == 'document_ai':
                    break
                    
                # Continue to next method
                continue
        
        # If all methods fail, raise the last error
        raise Exception(f"All extraction methods failed. Last error: {last_error}")
    
    async def _get_sample_transunion_text(self) -> str:
        """
        DEPRECATED: This method is only for testing with the specific test PDF
        Real extraction now uses the cost-optimized pipeline above
        """
        logger.warning("Using sample text for testing purposes only")
        return """
        TransUnion Credit Report
        
        TRADELINE INFORMATION:
        
        LENTEGRITY LLC
        Account Number: 2212311376****
        Account Type: Installment
        Account Status: Closed
        Date Opened: 12/29/2022
        Monthly Payment: $0
        Balance: $0
        
        [... rest of sample data ...]
        """
    
    def _validate_extraction_quality(self, text: str) -> bool:
        """
        Validate if extracted text is good enough for processing
        """
        if not text or len(text.strip()) < 100:
            return False
        
        # Check for credit report indicators
        text_lower = text.lower()
        credit_indicators = [
            'credit', 'account', 'balance', 'payment', 'tradeline',
            'experian', 'equifax', 'transunion', 'creditor', 'limit',
            'monthly payment', 'date opened', 'account status'
        ]
        
        found_indicators = sum(1 for indicator in credit_indicators if indicator in text_lower)
        return found_indicators >= 3
    
    async def _extract_with_pdfplumber(self, path: Path) -> str:
        """
        Extract text using pdfplumber (free, fast)
        """
        try:
            import pdfplumber
        except ImportError:
            raise Exception("pdfplumber not installed. Install with: pip install pdfplumber")
        
        loop = asyncio.get_running_loop()
        
        def _sync_extract():
            text_content = ""
            
            with pdfplumber.open(str(path)) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    text_content += f"\n--- Page {page_num + 1} ---\n{page_text}"
                    
                    # Limit processing for very large documents
                    if page_num > 50:  # Max 50 pages
                        break
            
            return text_content
        
        return await loop.run_in_executor(None, _sync_extract)
    
    async def _extract_with_pymupdf(self, path: Path) -> str:
        """
        Extract text using PyMuPDF/fitz (free, handles complex layouts)
        """
        try:
            import fitz
        except ImportError:
            raise Exception("PyMuPDF not installed. Install with: pip install PyMuPDF")
        
        loop = asyncio.get_running_loop()
        
        def _sync_extract():
            text_content = ""
            
            doc = fitz.open(str(path))
            try:
                for page_num in range(min(len(doc), 50)):  # Max 50 pages
                    page = doc[page_num]
                    page_text = page.get_text()
                    text_content += f"\n--- Page {page_num + 1} ---\n{page_text}"
            finally:
                doc.close()
            
            return text_content
        
        return await loop.run_in_executor(None, _sync_extract)
    
    async def _extract_with_tesseract(self, path: Path) -> str:
        """
        Extract text using Tesseract OCR (free, good for scanned PDFs)
        """
        try:
            import fitz
            import pytesseract
            from PIL import Image
            import io
            import shutil
        except ImportError as e:
            raise Exception(f"OCR dependencies not installed: {e}")
        
        # Check if tesseract is available
        if not shutil.which('tesseract'):
            raise Exception("Tesseract not found. Install tesseract-ocr package")
        
        loop = asyncio.get_running_loop()
        
        def _sync_extract():
            text_content = ""
            
            doc = fitz.open(str(path))
            try:
                # Limit OCR to first 5 pages for performance
                for page_num in range(min(len(doc), 5)):
                    page = doc[page_num]
                    
                    # Convert to image
                    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))
                    
                    # OCR with timeout
                    try:
                        page_text = pytesseract.image_to_string(
                            img,
                            config='--psm 6 --oem 3',
                            timeout=30  # 30 second timeout per page
                        )
                        text_content += f"\n--- Page {page_num + 1} (OCR) ---\n{page_text}"
                    except Exception as e:
                        logger.warning(f"OCR failed for page {page_num + 1}: {e}")
                        continue
            finally:
                doc.close()
            
            return text_content
        
        return await loop.run_in_executor(None, _sync_extract)
    
    async def _extract_with_document_ai(self, path: Path) -> str:
        """
        Extract text using Google Document AI (expensive, high accuracy)
        This is the fallback method when free methods fail
        """
        logger.warning(f"Using expensive Document AI for {path.name}")
        
        try:
            # Read file as bytes
            with open(path, 'rb') as f:
                file_content = f.read()
            
            # Call Supabase function for Document AI processing
            import httpx
            
            # This would call your Supabase function
            # You'd need to configure the URL and auth
            supabase_function_url = "https://gywohmbqohytziwsjrps.supabase.co/functions/v1/docai-ocr"
            
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    supabase_function_url,
                    json={
                        "file": list(file_content),  # Convert bytes to array for JSON
                        "mimeType": "application/pdf"
                    },
                    headers={
                        "Authorization": f"Bearer {self._get_supabase_anon_key()}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get('text', '')
                else:
                    raise Exception(f"Document AI request failed: {response.status_code} - {response.text}")
                    
        except Exception as e:
            logger.error(f"Document AI extraction failed: {e}")
            raise
    
    def _get_supabase_anon_key(self) -> str:
        """
        Get Supabase anonymous key from environment or config
        """
        import os
        return os.getenv('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd5d29obWJxb2h5dHppd3NqcnBzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU4NjYzNDQsImV4cCI6MjA2MTQ0MjM0NH0.F1Y8K6wmkqTInHvI1j9Pbog782i3VSVpIbgYqakyPwo')
    
    def is_transunion_report(self, text: str) -> bool:
        """
        Check if the extracted text is from a TransUnion credit report
        """
        transunion_indicators = [
            "transunion",
            "credit report", 
            "account information",
            "tradeline",
            "credit file"
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in transunion_indicators)