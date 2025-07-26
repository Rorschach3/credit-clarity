import logging
import subprocess
import tempfile
import os
from typing import Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class OCRService:
    """Service for adding OCR text layer to PDFs using OCRmyPDF and Tesseract"""
    
    def __init__(self):
        self.tesseract_languages = ["eng"]  # Default to English, can be expanded
        
    async def add_ocr_layer(self, pdf_content: bytes, filename: str = "document.pdf") -> Tuple[bytes, bool]:
        """
        Add OCR text layer to PDF using OCRmyPDF with Tesseract
        
        Args:
            pdf_content: Original PDF file bytes
            filename: Original filename for logging
            
        Returns:
            Tuple of (processed_pdf_bytes, success_flag)
        """
        temp_input = None
        temp_output = None
        
        try:
            logger.info(f"Starting OCR processing for {filename}")
            
            # Create temporary files
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_input:
                temp_input.write(pdf_content)
                temp_input_path = temp_input.name
                
            with tempfile.NamedTemporaryFile(suffix="_ocr.pdf", delete=False) as temp_output:
                temp_output_path = temp_output.name
            
            # Check if OCRmyPDF is available
            if not self._check_ocrmypdf_available():
                logger.warning("OCRmyPDF not available, returning original PDF")
                return pdf_content, False
                
            # Run OCRmyPDF
            success = await self._run_ocrmypdf(temp_input_path, temp_output_path)
            
            if success:
                # Read the OCR'd PDF
                with open(temp_output_path, 'rb') as f:
                    ocr_pdf_content = f.read()
                    
                logger.info(f"OCR processing completed successfully for {filename}")
                return ocr_pdf_content, True
            else:
                logger.warning(f"OCR processing failed for {filename}, returning original")
                return pdf_content, False
                
        except Exception as e:
            logger.error(f"OCR processing error for {filename}: {str(e)}")
            return pdf_content, False
            
        finally:
            # Clean up temporary files
            self._cleanup_temp_files([temp_input_path, temp_output_path])
    
    def _check_ocrmypdf_available(self) -> bool:
        """Check if OCRmyPDF is installed and available"""
        try:
            import sys
            # Try using Python module approach first
            result = subprocess.run(
                [sys.executable, "-m", "ocrmypdf", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                return True
                
            # Fallback to binary approach
            result = subprocess.run(
                ["ocrmypdf", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def _run_ocrmypdf(self, input_path: str, output_path: str) -> bool:
        """
        Run OCRmyPDF command with optimized settings for credit reports
        
        Args:
            input_path: Path to input PDF
            output_path: Path to output OCR'd PDF
            
        Returns:
            Success flag
        """
        try:
            import sys
            # OCRmyPDF command with optimized settings for financial documents
            cmd = [
                sys.executable, "-m", "ocrmypdf",
                "--language", "+".join(self.tesseract_languages),
                "--deskew",  # Correct document skew
                "--clean",   # Clean up image artifacts
                "--force-ocr",  # OCR even if text is already present
                "--optimize", "1",  # Light optimization
                "--jpeg-quality", "85",  # Good quality for images
                "--png-quality", "85",   # Good quality for images
                "--timeout", "300",  # 5 minute timeout
                "--skip-text",  # Skip if text already exists (faster)
                input_path,
                output_path
            ]
            
            logger.info(f"Running OCRmyPDF: {' '.join(cmd)}")
            
            # Run the command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                logger.info("OCRmyPDF completed successfully")
                return True
            else:
                logger.warning(f"OCRmyPDF failed with return code {result.returncode}")
                logger.warning(f"STDERR: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("OCRmyPDF timed out after 5 minutes")
            return False
        except Exception as e:
            logger.error(f"OCRmyPDF execution error: {str(e)}")
            return False
    
    def _cleanup_temp_files(self, file_paths: list) -> None:
        """Clean up temporary files"""
        for file_path in file_paths:
            if file_path and os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                    logger.debug(f"Cleaned up temp file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temp file {file_path}: {str(e)}")
    
    def set_languages(self, languages: list) -> None:
        """
        Set OCR languages for Tesseract
        
        Args:
            languages: List of language codes (e.g., ['eng', 'spa'])
        """
        self.tesseract_languages = languages
        logger.info(f"OCR languages set to: {languages}")
        
    async def get_ocr_capabilities(self) -> dict:
        """Get information about OCR capabilities and available languages"""
        try:
            import sys
            # Check OCRmyPDF version using Python module
            ocrmypdf_result = subprocess.run(
                [sys.executable, "-m", "ocrmypdf", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            # For Tesseract, we'll try multiple approaches
            tesseract_result = None
            langs_result = None
            
            # Try direct tesseract command first
            try:
                tesseract_result = subprocess.run(
                    ["tesseract", "--version"], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                langs_result = subprocess.run(
                    ["tesseract", "--list-langs"], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
            except FileNotFoundError:
                # If direct command fails, tesseract might be bundled with OCRmyPDF
                pass
            
            available_languages = []
            if langs_result and langs_result.returncode == 0:
                lines = langs_result.stdout.strip().split('\n')
                # Skip header line and get language codes
                available_languages = [line.strip() for line in lines[1:] if line.strip()]
            
            # If we can't get Tesseract info directly, but OCRmyPDF works, assume basic functionality
            tesseract_available = bool(tesseract_result and tesseract_result.returncode == 0)
            if not tesseract_available and ocrmypdf_result.returncode == 0:
                # OCRmyPDF is available, so it likely has Tesseract bundled
                tesseract_available = True
                available_languages = ["eng"]  # Default to English
            
            return {
                "ocrmypdf_available": ocrmypdf_result.returncode == 0,
                "ocrmypdf_version": ocrmypdf_result.stdout.strip() if ocrmypdf_result.returncode == 0 else None,
                "tesseract_available": tesseract_available,
                "tesseract_version": tesseract_result.stderr.strip() if tesseract_result and tesseract_result.returncode == 0 else "bundled with OCRmyPDF",
                "available_languages": available_languages,
                "current_languages": self.tesseract_languages
            }
            
        except Exception as e:
            logger.error(f"Error getting OCR capabilities: {str(e)}")
            return {
                "ocrmypdf_available": False,
                "tesseract_available": False,
                "error": str(e)
            }