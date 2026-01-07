"""
PDF text extraction service for TransUnion credit reports
Implements TDD approach with comprehensive error handling
"""
import logging
import re
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import asyncio
from dataclasses import dataclass
import shutil
import numpy as np
import cv2
from PIL import Image
import io

# Import cost tracking
from services.cost_tracker import cost_tracker, OCRMethod
from services.advanced_parsing.multi_layer_extractor import MultiLayerExtractor

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
        self.negative_keywords = [
            'charge off', 'charged off', 'collection', 'collections', 'in collection',
            'late payment', 'past due', 'delinquent', 'delinquency', 'default', 'defaulted',
            'repossession', 'foreclosure', 'settled', 'settlement', 'bankruptcy', 'write off',
            'paid charge off', 'settled for less', 'included in bankruptcy', 
            'voluntary repossession', 'seriously delinquent'
        ]
        self.multi_layer_extractor = MultiLayerExtractor()
    
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
        Multi-layer extraction with intelligent fallback strategy:
        1. Primary: MultiLayerExtractor.extract_text_multi_layer() with all methods
        2. Fallback: Single-method OCR with adaptive preprocessing if confidence is low
        3. Last resort: Document AI for very poor quality
        
        Uses confidence/quality scores to decide fallback and implements
        negative-section/page prioritization with weighted keywords.
        """
        last_error = None
        
        # 1. PRIMARY PATH: Multi-layer extraction
        try:
            logger.info(f"Starting multi-layer extraction for {path.name}")
            multi_layer_result = await self.multi_layer_extractor.extract_text_multi_layer(
                str(path), 
                use_ai=True, 
                quality_threshold=0.75
            )
            
            if multi_layer_result and multi_layer_result.text:
                quality_score = multi_layer_result.quality_score
                confidence = multi_layer_result.confidence
                
                logger.info(
                    f"✅ Multi-layer extraction completed: "
                    f"quality={quality_score:.2f}, confidence={confidence:.2f}, "
                    f"methods={', '.join(multi_layer_result.methods_used)}"
                )
                
                # Accept result if quality/confidence meet threshold
                if quality_score >= 0.70 or confidence >= 0.75:
                    logger.info(f"Multi-layer result meets quality threshold - using result")
                    return self._finalize_text(multi_layer_result.text, path, "multi_layer")
                else:
                    logger.warning(
                        f"Multi-layer result below threshold (quality={quality_score:.2f}, "
                        f"confidence={confidence:.2f}) - attempting single-method fallback"
                    )
                    last_error = "Multi-layer result quality below threshold"
                    
        except Exception as e:
            last_error = str(e)
            logger.error(f"Multi-layer extraction failed: {e}")
        
        # 2. FALLBACK: Single-method OCR with adaptive preprocessing
        logger.info(f"Attempting single-method OCR fallback with adaptive preprocessing")
        try:
            result = await self._extract_with_adaptive_ocr(path)
            if result:
                quality_score = self._calculate_quality_score(result)
                logger.info(f"✅ Adaptive OCR successful (quality={quality_score:.2f})")
                
                if quality_score >= 0.60:
                    return self._finalize_text(result, path, "adaptive_ocr")
                else:
                    logger.warning(f"Adaptive OCR quality still low ({quality_score:.2f})")
                    
        except Exception as e:
            logger.error(f"Adaptive OCR fallback failed: {e}")
            last_error = str(e)
        
        # 3. LAST RESORT: Document AI
        try:
            logger.info(f"Using Document AI as last resort for {path.name}")
            result = await self._extract_with_document_ai(path)
            if result:
                return self._finalize_text(result, path, "document_ai")
        except Exception as e:
            logger.error(f"Document AI fallback failed: {e}")
            last_error = str(e)
            
        raise Exception(f"All extraction methods failed. Last error: {last_error}")

    def _calculate_quality_score(self, text: str) -> float:
        """Calculate quality score based on text characteristics."""
        if not text.strip():
            return 0.0
        
        score = 0.0
        
        # Length factor
        length_score = min(1.0, len(text.strip()) / 1000)
        score += length_score * 0.3
        
        # Content quality (presence of credit report indicators)
        content_indicators = [
            'account', 'balance', 'credit', 'payment', 'status',
            'experian', 'equifax', 'transunion', 'tradeline',
            'bureau', 'creditor', 'limit', 'opened'
        ]
        
        text_lower = text.lower()
        indicators_found = sum(1 for indicator in content_indicators if indicator in text_lower)
        content_score = min(1.0, indicators_found / len(content_indicators))
        score += content_score * 0.4
        
        # Negative keyword density check (if present, ensures we caught them)
        negative_stats = self._score_negative_keywords(text)
        if negative_stats['hits'] > 0:
            score += 0.3
        else:
            score += 0.1
            
        return min(1.0, score)

    def _finalize_text(self, text: str, path: Path, method_name: str) -> str:
        """
        Finalize extracted text with prioritization and tracking.
        Uses weighted negative keyword scoring for intelligent section prioritization.
        """
        # Apply negative section prioritization with weighted keywords
        negative_stats = self._score_negative_keywords(text)
        if negative_stats["hits"] > 0:
            logger.info(
                f"Detected {negative_stats['hits']} negative keyword hits (density={negative_stats['density']:.5f}); "
                f"applying weighted prioritization"
            )
            text = self._prioritize_negative_sections(text)
        else:
            logger.info("No negative keywords detected - maintaining original order")
            
        # Track usage
        try:
            file_size_mb = path.stat().st_size / (1024 * 1024)
            cost_tracker.record_usage(
                user_id="unknown",
                method=OCRMethod(method_name) if method_name in [m.value for m in OCRMethod] else OCRMethod.PYMUPDF,
                file_size_mb=file_size_mb,
                processing_time_ms=0,
                success=True
            )
        except Exception as e:
            logger.debug(f"Cost tracking failed: {e}")
            
        return text
    
    def _prioritize_negative_sections(self, text: str) -> str:
        """
        Move sections with high negative keyword density to the top using weighted scoring.
        Implements the weighted keyword approach from the plan with context-aware boosting.
        """
        # Weighted scoring for prioritization (aligned with _calculate_page_negative_score)
        weights = {
            'charge off': 1.0, 'charged off': 1.0, 'paid charge off': 1.0,
            'collection': 0.9, 'collections': 0.9, 'in collection': 0.9,
            'bankruptcy': 1.0, 'foreclosure': 1.0, 'repossession': 1.0,
            'voluntary repossession': 1.0, 'included in bankruptcy': 1.0,
            'seriously delinquent': 0.9, 'delinquent': 0.8, 'delinquency': 0.8,
            'settled': 0.8, 'settlement': 0.8, 'settled for less': 0.9,
            'default': 0.9, 'defaulted': 0.9,
            'late payment': 0.7, 'past due': 0.7,
            'write off': 0.9
        }
        
        # Split text into sections (by page markers or double newlines)
        if '--- Page' in text:
            sections = re.split(r'\n(?=--- Page)', text)
        else:
            sections = text.split('\n\n')
        
        scored_sections = []
        
        for section in sections:
            if not section.strip():
                continue
                
            section_lower = section.lower()
            section_score = 0.0
            keyword_hits = []
            
            # Calculate weighted score
            for keyword, weight in weights.items():
                count = section_lower.count(keyword)
                if count > 0:
                    section_score += count * weight
                    keyword_hits.append(f"{keyword}({count})")
            
            # Context window analysis: boost score if account details are near negative keywords
            has_account_context = any(
                term in section_lower 
                for term in ['account', 'balance', 'status', 'payment', 'creditor', 'tradeline']
            )
            
            if section_score > 0 and has_account_context:
                section_score *= 1.5
                logger.debug(f"Section boosted for account context: score={section_score:.2f}")
            
            # Additional boost for sections with multiple different negative keywords
            if len(keyword_hits) >= 3:
                section_score *= 1.2
                logger.debug(f"Section boosted for multiple keywords: {', '.join(keyword_hits[:3])}")
            
            scored_sections.append({
                'text': section,
                'score': section_score,
                'keywords': keyword_hits
            })
        
        # Sort by score descending (highest priority first)
        scored_sections.sort(key=lambda item: item['score'], reverse=True)
        
        # Log prioritization results
        high_priority_count = sum(1 for s in scored_sections if s['score'] > 0.5)
        if high_priority_count > 0:
            logger.info(f"Prioritized {high_priority_count} high-priority sections to top")
            for i, section_data in enumerate(scored_sections[:3]):  # Log top 3
                if section_data['score'] > 0:
                    logger.debug(
                        f"  #{i+1}: score={section_data['score']:.2f}, "
                        f"keywords={', '.join(section_data['keywords'][:5])}"
                    )
        
        # Reconstruct text with prioritized ordering
        prioritized = "\n\n".join(s['text'] for s in scored_sections if s['text'].strip())
        
        return prioritized if prioritized.strip() else text

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
    
    def _score_negative_keywords(self, text: str) -> Dict[str, Any]:
        """Calculate negative keyword counts and density for prioritization."""
        text_lower = text.lower()
        hits = sum(text_lower.count(keyword) for keyword in self.negative_keywords)
        word_count = max(len(text_lower.split()), 1)
        density = hits / word_count
        return {"hits": hits, "density": density}
    
    def _validate_extraction_quality(self, text: str) -> bool:
        """
        Validate if extracted text is good enough for processing
        """
        return self._calculate_quality_score(text) >= 0.5
    
    def _validate_negative_tradeline_fields(self, tradeline: Dict[str, Any]) -> bool:
        """Validate that negative account has minimum required fields with correct formatting."""
        required_fields = ['creditor_name', 'account_number', 'account_status', 'credit_bureau']
        
        # Check required fields exist
        for field in required_fields:
            if not tradeline.get(field):
                return False
        
        # Validate account_number is alphanumeric only
        account_num = tradeline.get('account_number', '')
        if not re.match(r'^[A-Za-z0-9]+$', account_num):
            return False
        
        # Validate credit_bureau is one of the three
        if tradeline.get('credit_bureau') not in ['Experian', 'Equifax', 'TransUnion']:
            return False
        
        # Validate currency fields have correct format
        if tradeline.get('monthly_payment') and not re.match(r'^\$\d+\.\d{2}$', tradeline.get('monthly_payment', '')):
            return False
        
        if tradeline.get('credit_limit') and not re.match(r'^\$\d+$', tradeline.get('credit_limit', '')):
            return False
        
        if tradeline.get('account_balance') and not re.match(r'^\$\d+$', tradeline.get('account_balance', '')):
            return False
        
        # Validate date format
        if tradeline.get('date_opened') and not re.match(r'^\d{2}/\d{2}/\d{4}$', tradeline.get('date_opened', '')):
            return False
        
        return True
    
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
        Basic OCR without advanced preprocessing - use _extract_with_adaptive_ocr for better quality.
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
                    pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))
                    
                    # Basic OCR
                    try:
                        custom_config = r'--psm 6'
                        page_text = pytesseract.image_to_string(img, config=custom_config)
                        text_content += f"\n--- Page {page_num + 1} (OCR) ---\n{page_text}"
                    except Exception as e:
                        logger.warning(f"OCR failed for page {page_num + 1}: {e}")
                        continue
            finally:
                doc.close()
            
            return text_content
        
        return await loop.run_in_executor(None, _sync_extract)
    
    async def _extract_with_adaptive_ocr(self, path: Path) -> str:
        """
        Advanced OCR with adaptive preprocessing strategies.
        Implements multiple preprocessing techniques (contrast enhancement, binarization, deskewing)
        and uses Tesseract configs optimized for credit reports.
        
        Based on multi_layer_extractor.py advanced OCR techniques.
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
            page_scores = []  # Track quality scores for prioritization
            
            doc = fitz.open(str(path))
            try:
                # Process all pages but limit to 20 for performance
                for page_num in range(min(len(doc), 20)):
                    page = doc[page_num]
                    
                    # Convert to image at higher DPI
                    pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5))  # ~300 DPI
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))
                    
                    # Try multiple preprocessing strategies
                    strategies = [
                        ("original", img),
                        ("enhanced_contrast", self._enhance_contrast(img)),
                        ("binarized", self._binarize_image(img)),
                        ("deskewed", self._deskew_image(img))
                    ]
                    
                    best_result = ""
                    best_confidence = 0.0
                    best_strategy = "original"
                    
                    for strategy_name, processed_img in strategies:
                        try:
                            # Advanced Tesseract config for credit reports
                            # --oem 3: Use both legacy and LSTM engines
                            # --psm 6: Assume uniform block of text
                            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz .,()-/$%#*'
                            
                            # Get OCR data with confidence scores
                            data = pytesseract.image_to_data(
                                processed_img, 
                                config=custom_config,
                                output_type=pytesseract.Output.DICT
                            )
                            
                            # Reconstruct text from high-confidence words
                            lines = {}
                            min_confidence = 30
                            confidences = []
                            
                            for i, text in enumerate(data['text']):
                                conf = int(data['conf'][i])
                                if conf >= min_confidence and text.strip():
                                    line_num = data['line_num'][i]
                                    if line_num not in lines:
                                        lines[line_num] = []
                                    
                                    # Clean OCR artifacts
                                    clean_text = text.replace('(cid:', '').replace(')', '')
                                    lines[line_num].append(clean_text)
                                    confidences.append(conf)
                            
                            # Calculate average confidence for this strategy
                            avg_conf = sum(confidences) / len(confidences) if confidences else 0
                            
                            # Reconstruct text
                            reconstructed_lines = []
                            for line_num in sorted(lines.keys()):
                                line_text = ' '.join(lines[line_num])
                                if line_text.strip():
                                    reconstructed_lines.append(line_text)
                            
                            strategy_result = '\n'.join(reconstructed_lines)
                            
                            # Select best strategy based on confidence
                            if avg_conf > best_confidence:
                                best_confidence = avg_conf
                                best_result = strategy_result
                                best_strategy = strategy_name
                        
                        except Exception as e:
                            logger.debug(f"Strategy {strategy_name} failed for page {page_num + 1}: {e}")
                    
                    # Calculate negative keyword score for this page
                    page_negative_score = self._calculate_page_negative_score(best_result)
                    
                    page_scores.append({
                        'page_num': page_num + 1,
                        'text': best_result,
                        'confidence': best_confidence,
                        'strategy': best_strategy,
                        'negative_score': page_negative_score
                    })
                    
                    logger.debug(
                        f"Page {page_num + 1}: strategy={best_strategy}, "
                        f"confidence={best_confidence:.1f}, negative_score={page_negative_score:.2f}"
                    )
            finally:
                doc.close()
            
            # Prioritize pages with negative keywords (higher negative_score = more important)
            page_scores.sort(key=lambda x: x['negative_score'], reverse=True)
            
            # Reconstruct text with prioritized ordering
            for page_data in page_scores:
                if page_data['text'].strip():
                    priority_marker = " [HIGH PRIORITY]" if page_data['negative_score'] > 0.5 else ""
                    text_content += (
                        f"\n--- Page {page_data['page_num']} "
                        f"(OCR: {page_data['strategy']}, conf={page_data['confidence']:.0f}%)"
                        f"{priority_marker} ---\n{page_data['text']}"
                    )
            
            return text_content
        
        return await loop.run_in_executor(None, _sync_extract)
    
    def _enhance_contrast(self, image: Image.Image) -> Image.Image:
        """Enhance image contrast using CLAHE for better OCR."""
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        lab = cv2.cvtColor(cv_image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced_bgr = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        return Image.fromarray(cv2.cvtColor(enhanced_bgr, cv2.COLOR_BGR2RGB))
    
    def _binarize_image(self, image: Image.Image) -> Image.Image:
        """Apply adaptive binarization for better text separation."""
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
        
        # Apply denoising first
        denoised = cv2.fastNlMeansDenoising(cv_image, None, 10, 7, 21)
        
        # Adaptive threshold
        binary = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        return Image.fromarray(binary)
    
    def _deskew_image(self, image: Image.Image) -> Image.Image:
        """Deskew image to correct rotation using Hough line detection."""
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
        
        # Detect edges
        edges = cv2.Canny(cv_image, 50, 150, apertureSize=3)
        
        # Detect lines using Hough transform
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        if lines is not None and len(lines) > 0:
            # Calculate average angle from detected lines
            angles = []
            for rho, theta in lines[:10]:  # Use first 10 lines
                angle = theta * 180 / np.pi - 90
                angles.append(angle)
            
            if angles:
                avg_angle = np.mean(angles)
                
                # Only rotate if there's significant skew
                if abs(avg_angle) > 0.5:
                    height, width = cv_image.shape
                    center = (width // 2, height // 2)
                    M = cv2.getRotationMatrix2D(center, avg_angle, 1.0)
                    rotated = cv2.warpAffine(
                        cv_image, M, (width, height), 
                        flags=cv2.INTER_CUBIC, 
                        borderMode=cv2.BORDER_REPLICATE
                    )
                    return Image.fromarray(rotated)
        
        # Return grayscale version if no rotation needed
        return image.convert('L')
    
    def _calculate_page_negative_score(self, text: str) -> float:
        """
        Calculate weighted negative keyword score for page/section prioritization.
        Higher score = more negative content = higher priority for processing.
        """
        if not text.strip():
            return 0.0
        
        # Weighted keywords from the plan
        weights = {
            'charge off': 1.0, 'charged off': 1.0, 'paid charge off': 1.0,
            'collection': 0.9, 'collections': 0.9, 'in collection': 0.9,
            'bankruptcy': 1.0, 'foreclosure': 1.0, 'repossession': 1.0,
            'voluntary repossession': 1.0, 'included in bankruptcy': 1.0,
            'seriously delinquent': 0.9, 'delinquent': 0.8, 'delinquency': 0.8,
            'settled': 0.8, 'settlement': 0.8, 'settled for less': 0.9,
            'default': 0.9, 'defaulted': 0.9,
            'late payment': 0.7, 'past due': 0.7,
            'write off': 0.9
        }
        
        text_lower = text.lower()
        total_score = 0.0
        
        # Calculate weighted score
        for keyword, weight in weights.items():
            count = text_lower.count(keyword)
            total_score += count * weight
        
        # Context multiplier: boost if account-related terms are present
        has_account_context = any(
            term in text_lower 
            for term in ['account', 'balance', 'status', 'payment', 'creditor', 'tradeline']
        )
        
        if has_account_context and total_score > 0:
            total_score *= 1.5
        
        # Normalize by word count to get density
        word_count = max(len(text_lower.split()), 1)
        normalized_score = min(1.0, total_score / word_count * 10)  # Scale to 0-1
        
        return normalized_score
    
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
