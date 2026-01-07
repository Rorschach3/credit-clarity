"""
Multi-Layer PDF Text Extraction System
Combines multiple extraction methods for maximum accuracy
"""
import logging
import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import threading

# PDF processing libraries
import fitz  # PyMuPDF
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import cv2
import numpy as np

# Google Cloud Document AI
from google.cloud import documentai

from core.config import get_settings
from core.logging.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# AI/ML libraries - with optional imports (after logger is defined)
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers library not available. AI extraction features will be limited.")

logger = get_logger(__name__)
settings = get_settings()

@dataclass
class ExtractionResult:
    """Results from a single extraction method."""
    method: str
    success: bool
    text: str
    confidence: float
    processing_time: float
    metadata: Dict[str, Any]
    error: Optional[str] = None

@dataclass
class ConsolidatedResult:
    """Final consolidated extraction result."""
    text: str
    confidence: float
    methods_used: List[str]
    processing_time: float
    quality_score: float
    metadata: Dict[str, Any]

class MultiLayerExtractor:
    """
    Advanced multi-layer PDF text extraction system.
    Combines multiple extraction methods for maximum accuracy.
    """
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.document_ai_client = None
        self.ai_classifier = None
        self._models_initialized = False
        self._initialization_lock = threading.Lock()
        self.extraction_stats = {
            'total_extractions': 0,
            'method_success_rates': {},
            'avg_confidence_scores': {},
            'processing_times': {}
        }
        
        # Try to schedule async initialization if event loop is running
        # Otherwise, defer until first async call (lazy initialization)
        try:
            loop = asyncio.get_running_loop()
            # Event loop is running, schedule initialization
            asyncio.create_task(self._initialize_ai_models())
        except RuntimeError:
            # No event loop running, will initialize lazily on first async method call
            logger.debug("No event loop available at init time, deferring AI model initialization")
    
    async def _ensure_initialized(self):
        """Ensure AI models are initialized (lazy initialization if needed)."""
        if self._models_initialized:
            return
        
        # Thread-safe check
        with self._initialization_lock:
            if self._models_initialized:
                return
            await self._initialize_ai_models()
    
    async def _initialize_ai_models(self):
        """Initialize AI models for text classification and validation."""
        if self._models_initialized:
            return
            
        try:
            # Initialize Document AI client if available
            if settings.google_cloud_project_id and settings.document_ai_processor_id:
                self.document_ai_client = documentai.DocumentProcessorServiceClient()
                logger.info("Document AI client initialized")
            
            # Initialize credit report classifier (only if transformers available)
            if TRANSFORMERS_AVAILABLE:
                try:
                    model_name = "microsoft/DialoGPT-medium"  # Placeholder - would use custom model
                    self.ai_classifier = pipeline(
                        "text-classification",
                        model=model_name,
                        return_all_scores=True
                    )
                    logger.info("AI classifier initialized")
                except Exception as e:
                    logger.warning(f"AI classifier initialization failed: {e}")
                    self.ai_classifier = None
            else:
                logger.info("Transformers not available, AI classifier disabled")
                self.ai_classifier = None
            
            self._models_initialized = True
            
        except Exception as e:
            logger.warning(f"AI model initialization failed: {e}")
            self._models_initialized = False  # Allow retry on next call
    
    async def extract_text_multi_layer(
        self, 
        pdf_path: str,
        use_ai: bool = True,
        quality_threshold: float = 0.8
    ) -> ConsolidatedResult:
        """
        Extract text using multiple methods and consolidate results.
        
        Args:
            pdf_path: Path to PDF file
            use_ai: Whether to use AI enhancement
            quality_threshold: Minimum quality score required
            
        Returns:
            ConsolidatedResult with best consolidated text
        """
        # Ensure AI models are initialized (lazy initialization if needed)
        await self._ensure_initialized()
        
        start_time = time.time()
        
        logger.info(f"Starting multi-layer extraction for {pdf_path}")
        
        # Run all extraction methods in parallel
        extraction_tasks = [
            self._extract_with_pymupdf(pdf_path),
            self._extract_with_pdfplumber(pdf_path),
            self._extract_with_ocr_tesseract(pdf_path),
            self._extract_with_advanced_ocr(pdf_path),
        ]
        
        if self.document_ai_client:
            extraction_tasks.append(self._extract_with_document_ai(pdf_path))
        
        # Execute all extractions concurrently
        results = await asyncio.gather(*extraction_tasks, return_exceptions=True)
        
        # Filter successful results
        successful_results = []
        for result in results:
            if isinstance(result, ExtractionResult) and result.success:
                successful_results.append(result)
                logger.info(f"Method {result.method} succeeded with confidence {result.confidence:.2f}")
            elif isinstance(result, Exception):
                logger.error(f"Extraction method failed: {result}")
        
        if not successful_results:
            raise Exception("All extraction methods failed")
        
        # Consolidate results using intelligent merging
        consolidated = await self._consolidate_results(successful_results, use_ai)
        
        # Enhance with AI if requested and available
        if use_ai and consolidated.quality_score < quality_threshold:
            enhanced = await self._ai_enhance_text(consolidated)
            if enhanced.quality_score > consolidated.quality_score:
                consolidated = enhanced
        
        consolidated.processing_time = time.time() - start_time
        
        # Update statistics
        self._update_stats(successful_results, consolidated)
        
        logger.info(f"Multi-layer extraction completed in {consolidated.processing_time:.2f}s "
                   f"with quality score {consolidated.quality_score:.2f}")
        
        return consolidated
    
    async def _extract_with_pymupdf(self, pdf_path: str) -> ExtractionResult:
        """Extract text using PyMuPDF with enhanced formatting."""
        start_time = time.time()
        
        try:
            def extract():
                doc = fitz.open(pdf_path)
                text_parts = []
                metadata = {
                    'pages': len(doc),
                    'has_text_layer': False,
                    'font_info': {},
                    'layout_analysis': {}
                }
                
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    
                    # Check if page has text layer
                    text = page.get_text()
                    if text.strip():
                        metadata['has_text_layer'] = True
                    
                    # Extract with formatting preservation
                    blocks = page.get_text("dict")
                    page_text = self._process_pymupdf_blocks(blocks)
                    text_parts.append(page_text)
                    
                    # Analyze fonts and layout
                    font_info = page.get_fonts()
                    if font_info:
                        metadata['font_info'][f'page_{page_num}'] = len(font_info)
                
                doc.close()
                return '\n'.join(text_parts), metadata
            
            # Run in thread pool
            text, metadata = await asyncio.get_event_loop().run_in_executor(
                self.executor, extract
            )
            
            # Calculate confidence based on text layer presence and content quality
            confidence = 0.9 if metadata['has_text_layer'] else 0.6
            confidence *= min(1.0, len(text.strip()) / 1000)  # Adjust based on content length
            
            return ExtractionResult(
                method="pymupdf",
                success=True,
                text=text,
                confidence=confidence,
                processing_time=time.time() - start_time,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
            return ExtractionResult(
                method="pymupdf",
                success=False,
                text="",
                confidence=0.0,
                processing_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _process_pymupdf_blocks(self, blocks: Dict) -> str:
        """Process PyMuPDF text blocks with layout preservation."""
        text_parts = []
        
        for block in blocks.get("blocks", []):
            if block.get("type") == 0:  # Text block
                for line in block.get("lines", []):
                    line_text = ""
                    for span in line.get("spans", []):
                        line_text += span.get("text", "")
                    if line_text.strip():
                        text_parts.append(line_text)
        
        return '\n'.join(text_parts)
    
    async def _extract_with_pdfplumber(self, pdf_path: str) -> ExtractionResult:
        """Extract text using pdfplumber with table detection."""
        start_time = time.time()
        
        try:
            def extract():
                import pdfplumber
                
                text_parts = []
                metadata = {
                    'tables_found': 0,
                    'pages_processed': 0,
                    'layout_quality': 'unknown'
                }
                
                with pdfplumber.open(pdf_path) as pdf:
                    for page_num, page in enumerate(pdf.pages):
                        # Extract regular text
                        page_text = page.extract_text() or ""
                        
                        # Extract tables
                        tables = page.extract_tables()
                        if tables:
                            metadata['tables_found'] += len(tables)
                            for table in tables:
                                # Convert table to text format
                                table_text = self._format_table_text(table)
                                page_text += f"\n\n[TABLE]\n{table_text}\n[/TABLE]\n"
                        
                        text_parts.append(page_text)
                        metadata['pages_processed'] += 1
                
                return '\n'.join(text_parts), metadata
            
            text, metadata = await asyncio.get_event_loop().run_in_executor(
                self.executor, extract
            )
            
            # Higher confidence if tables were found (structured data)
            confidence = 0.8
            if metadata['tables_found'] > 0:
                confidence = 0.85
            
            confidence *= min(1.0, len(text.strip()) / 1000)
            
            return ExtractionResult(
                method="pdfplumber",
                success=True,
                text=text,
                confidence=confidence,
                processing_time=time.time() - start_time,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"PDFPlumber extraction failed: {e}")
            return ExtractionResult(
                method="pdfplumber",
                success=False,
                text="",
                confidence=0.0,
                processing_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _format_table_text(self, table: List[List[str]]) -> str:
        """Format table data as readable text."""
        if not table:
            return ""
        
        formatted_rows = []
        for row in table:
            if row:  # Skip empty rows
                clean_row = [str(cell or "").strip() for cell in row]
                if any(clean_row):  # Only include rows with content
                    formatted_rows.append(" | ".join(clean_row))
        
        return "\n".join(formatted_rows)
    
    async def _extract_with_ocr_tesseract(self, pdf_path: str) -> ExtractionResult:
        """Extract text using Tesseract OCR with image preprocessing."""
        start_time = time.time()
        
        try:
            def extract():
                # Convert PDF to images
                images = convert_from_path(pdf_path, dpi=300)
                text_parts = []
                metadata = {
                    'pages_processed': len(images),
                    'preprocessing_applied': [],
                    'ocr_confidence': []
                }
                
                for i, image in enumerate(images):
                    # Preprocess image for better OCR
                    processed_image = self._preprocess_image_for_ocr(image)
                    
                    # Run Tesseract with custom configuration
                    custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz .,()-/$%'
                    
                    # Extract text with confidence
                    data = pytesseract.image_to_data(
                        processed_image, 
                        config=custom_config,
                        output_type=pytesseract.Output.DICT
                    )
                    
                    # Filter by confidence and reconstruct text
                    page_text = self._reconstruct_text_from_ocr_data(data)
                    text_parts.append(page_text)
                    
                    # Track confidence
                    confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                    if confidences:
                        metadata['ocr_confidence'].append(sum(confidences) / len(confidences))
                
                return '\n'.join(text_parts), metadata
            
            text, metadata = await asyncio.get_event_loop().run_in_executor(
                self.executor, extract
            )
            
            # Calculate confidence based on OCR confidence scores
            avg_ocr_confidence = 0.0
            if metadata['ocr_confidence']:
                avg_ocr_confidence = sum(metadata['ocr_confidence']) / len(metadata['ocr_confidence'])
            
            confidence = (avg_ocr_confidence / 100) * 0.7  # OCR typically less reliable
            
            return ExtractionResult(
                method="tesseract_ocr",
                success=True,
                text=text,
                confidence=confidence,
                processing_time=time.time() - start_time,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Tesseract OCR extraction failed: {e}")
            return ExtractionResult(
                method="tesseract_ocr",
                success=False,
                text="",
                confidence=0.0,
                processing_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _preprocess_image_for_ocr(self, image: Image.Image) -> Image.Image:
        """Preprocess image to improve OCR accuracy."""
        # Convert to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        # Apply denoising
        denoised = cv2.medianBlur(gray, 3)
        
        # Enhance contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        # Apply threshold to get binary image
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Convert back to PIL Image
        return Image.fromarray(binary)
    
    def _reconstruct_text_from_ocr_data(self, data: Dict) -> str:
        """Reconstruct text from OCR data with confidence filtering."""
        lines = {}
        min_confidence = 30
        
        for i, text in enumerate(data['text']):
            if int(data['conf'][i]) >= min_confidence and text.strip():
                line_num = data['line_num'][i]
                if line_num not in lines:
                    lines[line_num] = []
                lines[line_num].append(text)
        
        # Reconstruct text by lines
        reconstructed_lines = []
        for line_num in sorted(lines.keys()):
            line_text = ' '.join(lines[line_num])
            if line_text.strip():
                reconstructed_lines.append(line_text)
        
        return '\n'.join(reconstructed_lines)
    
    async def _extract_with_advanced_ocr(self, pdf_path: str) -> ExtractionResult:
        """Advanced OCR with multiple preprocessing strategies."""
        start_time = time.time()
        
        try:
            def extract():
                images = convert_from_path(pdf_path, dpi=400)  # Higher DPI
                text_parts = []
                metadata = {
                    'strategies_used': [],
                    'best_confidence': 0.0,
                    'total_strategies': 0
                }
                
                for image in images:
                    # Try multiple preprocessing strategies
                    strategies = [
                        ("original", image),
                        ("enhanced_contrast", self._enhance_contrast(image)),
                        ("binarized", self._binarize_image(image)),
                        ("deskewed", self._deskew_image(image))
                    ]
                    
                    best_result = ""
                    best_confidence = 0.0
                    
                    for strategy_name, processed_image in strategies:
                        try:
                            # Custom config for credit reports
                            config = r'--oem 3 --psm 6'
                            result = pytesseract.image_to_string(processed_image, config=config)
                            
                            # Get confidence
                            data = pytesseract.image_to_data(processed_image, config=config, output_type=pytesseract.Output.DICT)
                            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                            avg_conf = sum(confidences) / len(confidences) if confidences else 0
                            
                            if avg_conf > best_confidence:
                                best_confidence = avg_conf
                                best_result = result
                                metadata['strategies_used'].append(strategy_name)
                        
                        except Exception as e:
                            logger.debug(f"Strategy {strategy_name} failed: {e}")
                    
                    text_parts.append(best_result)
                    metadata['best_confidence'] = max(metadata['best_confidence'], best_confidence)
                    metadata['total_strategies'] += len(strategies)
                
                return '\n'.join(text_parts), metadata
            
            text, metadata = await asyncio.get_event_loop().run_in_executor(
                self.executor, extract
            )
            
            confidence = (metadata['best_confidence'] / 100) * 0.75
            
            return ExtractionResult(
                method="advanced_ocr",
                success=True,
                text=text,
                confidence=confidence,
                processing_time=time.time() - start_time,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Advanced OCR extraction failed: {e}")
            return ExtractionResult(
                method="advanced_ocr",
                success=False,
                text="",
                confidence=0.0,
                processing_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _enhance_contrast(self, image: Image.Image) -> Image.Image:
        """Enhance image contrast for better OCR."""
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        lab = cv2.cvtColor(cv_image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced_bgr = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        return Image.fromarray(cv2.cvtColor(enhanced_bgr, cv2.COLOR_BGR2RGB))
    
    def _binarize_image(self, image: Image.Image) -> Image.Image:
        """Apply advanced binarization."""
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
        
        # Adaptive threshold
        binary = cv2.adaptiveThreshold(
            cv_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        return Image.fromarray(binary)
    
    def _deskew_image(self, image: Image.Image) -> Image.Image:
        """Deskew image to correct rotation."""
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
        
        # Detect edges
        edges = cv2.Canny(cv_image, 50, 150, apertureSize=3)
        
        # Detect lines
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        if lines is not None:
            # Calculate average angle
            angles = []
            for rho, theta in lines[:10]:  # Use first 10 lines
                angle = theta * 180 / np.pi - 90
                angles.append(angle)
            
            if angles:
                avg_angle = np.mean(angles)
                
                # Rotate image
                if abs(avg_angle) > 0.5:  # Only rotate if significant skew
                    height, width = cv_image.shape
                    center = (width // 2, height // 2)
                    M = cv2.getRotationMatrix2D(center, avg_angle, 1.0)
                    rotated = cv2.warpAffine(cv_image, M, (width, height), 
                                           flags=cv2.INTER_CUBIC, 
                                           borderMode=cv2.BORDER_REPLICATE)
                    return Image.fromarray(rotated)
        
        return image.convert('L')
    
    async def _extract_with_document_ai(self, pdf_path: str) -> ExtractionResult:
        """Extract text using Google Cloud Document AI."""
        start_time = time.time()
        
        try:
            if not self.document_ai_client:
                raise Exception("Document AI client not initialized")
            
            def extract():
                with open(pdf_path, 'rb') as pdf_file:
                    document_content = pdf_file.read()
                
                # Configure request
                name = f"projects/{settings.google_cloud_project_id}/locations/us/processors/{settings.document_ai_processor_id}"
                
                request = documentai.ProcessRequest(
                    name=name,
                    raw_document=documentai.RawDocument(
                        content=document_content,
                        mime_type="application/pdf"
                    )
                )
                
                # Process document
                result = self.document_ai_client.process_document(request=request)
                document = result.document
                
                # Extract structured information
                text = document.text
                metadata = {
                    'pages': len(document.pages),
                    'entities_found': len(document.entities),
                    'confidence_scores': []
                }
                
                # Collect confidence scores
                for entity in document.entities:
                    if entity.confidence:
                        metadata['confidence_scores'].append(entity.confidence)
                
                return text, metadata
            
            text, metadata = await asyncio.get_event_loop().run_in_executor(
                self.executor, extract
            )
            
            # Calculate confidence from entity confidence scores
            confidence = 0.95  # High confidence for Document AI
            if metadata['confidence_scores']:
                avg_entity_confidence = sum(metadata['confidence_scores']) / len(metadata['confidence_scores'])
                confidence = min(0.95, avg_entity_confidence)
            
            return ExtractionResult(
                method="document_ai",
                success=True,
                text=text,
                confidence=confidence,
                processing_time=time.time() - start_time,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Document AI extraction failed: {e}")
            return ExtractionResult(
                method="document_ai",
                success=False,
                text="",
                confidence=0.0,
                processing_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    async def _consolidate_results(
        self, 
        results: List[ExtractionResult],
        use_ai: bool = True
    ) -> ConsolidatedResult:
        """Consolidate multiple extraction results into best final result."""
        
        if not results:
            raise Exception("No results to consolidate")
        
        # Sort by confidence score
        sorted_results = sorted(results, key=lambda r: r.confidence, reverse=True)
        
        # Use highest confidence as base
        best_result = sorted_results[0]
        
        # If using AI and we have multiple results, try to merge intelligently
        if use_ai and len(sorted_results) > 1:
            merged_text = await self._ai_merge_texts([r.text for r in sorted_results[:3]])
            if merged_text:
                # Calculate quality score based on multiple factors
                quality_score = self._calculate_quality_score(merged_text, sorted_results)
                
                return ConsolidatedResult(
                    text=merged_text,
                    confidence=best_result.confidence * 1.1,  # Bonus for multi-method
                    methods_used=[r.method for r in sorted_results],
                    processing_time=sum(r.processing_time for r in results),
                    quality_score=quality_score,
                    metadata={
                        'consolidation_method': 'ai_merge',
                        'source_methods': len(results),
                        'best_method': best_result.method
                    }
                )
        
        # Fallback to best single result
        quality_score = self._calculate_quality_score(best_result.text, [best_result])
        
        return ConsolidatedResult(
            text=best_result.text,
            confidence=best_result.confidence,
            methods_used=[best_result.method],
            processing_time=sum(r.processing_time for r in results),
            quality_score=quality_score,
            metadata={
                'consolidation_method': 'best_single',
                'source_methods': len(results),
                'best_method': best_result.method
            }
        )
    
    async def _ai_merge_texts(self, texts: List[str]) -> Optional[str]:
        """Use AI to intelligently merge multiple text extractions."""
        try:
            # Simple implementation - would use more sophisticated AI in production
            # This is a placeholder for intelligent text merging
            
            # Find common patterns and merge
            merged = self._merge_texts_by_similarity(texts)
            return merged
            
        except Exception as e:
            logger.error(f"AI text merging failed: {e}")
            return None
    
    def _merge_texts_by_similarity(self, texts: List[str]) -> str:
        """Merge texts by finding common elements and best representations."""
        if not texts:
            return ""
        
        if len(texts) == 1:
            return texts[0]
        
        # Simple implementation: use longest text as base and enhance with others
        longest_text = max(texts, key=len)
        
        # TODO: Implement sophisticated merging algorithm
        # For now, return the longest text
        return longest_text
    
    def _calculate_quality_score(
        self, 
        text: str, 
        results: List[ExtractionResult]
    ) -> float:
        """Calculate quality score based on text characteristics and extraction metadata."""
        
        if not text.strip():
            return 0.0
        
        score = 0.0
        
        # Length factor (reasonable length indicates good extraction)
        length_score = min(1.0, len(text.strip()) / 5000)  # Normalize to 5k characters
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
        
        # Method confidence (average of all methods used)
        if results:
            avg_confidence = sum(r.confidence for r in results) / len(results)
            score += avg_confidence * 0.3
        
        return min(1.0, score)
    
    async def _ai_enhance_text(self, result: ConsolidatedResult) -> ConsolidatedResult:
        """Use AI to enhance and clean up extracted text."""
        try:
            # Placeholder for AI enhancement
            # Would use fine-tuned models for credit report cleaning
            
            enhanced_text = self._basic_text_cleanup(result.text)
            
            # Recalculate quality score
            quality_score = max(result.quality_score, 
                               self._calculate_quality_score(enhanced_text, []))
            
            return ConsolidatedResult(
                text=enhanced_text,
                confidence=result.confidence * 1.05,  # Small bonus for enhancement
                methods_used=result.methods_used + ['ai_enhancement'],
                processing_time=result.processing_time,
                quality_score=quality_score,
                metadata={
                    **result.metadata,
                    'ai_enhanced': True
                }
            )
            
        except Exception as e:
            logger.error(f"AI text enhancement failed: {e}")
            return result
    
    def _basic_text_cleanup(self, text: str) -> str:
        """Basic text cleanup and formatting."""
        import re
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common OCR errors
        replacements = {
            r'\bO\b': '0',  # Letter O -> number 0
            r'\bl\b': '1',  # Letter l -> number 1
            r'\bS\b': '5',  # Letter S -> number 5 in amounts
        }
        
        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text)
        
        # Clean up line breaks
        text = re.sub(r'\n\s*\n', '\n', text)
        
        return text.strip()
    
    def _update_stats(self, results: List[ExtractionResult], consolidated: ConsolidatedResult):
        """Update extraction statistics for monitoring."""
        self.extraction_stats['total_extractions'] += 1
        
        for result in results:
            method = result.method
            if method not in self.extraction_stats['method_success_rates']:
                self.extraction_stats['method_success_rates'][method] = {'success': 0, 'total': 0}
                self.extraction_stats['avg_confidence_scores'][method] = []
                self.extraction_stats['processing_times'][method] = []
            
            self.extraction_stats['method_success_rates'][method]['total'] += 1
            if result.success:
                self.extraction_stats['method_success_rates'][method]['success'] += 1
                self.extraction_stats['avg_confidence_scores'][method].append(result.confidence)
            
            self.extraction_stats['processing_times'][method].append(result.processing_time)
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get extraction statistics for monitoring and optimization."""
        stats = self.extraction_stats.copy()
        
        # Calculate success rates
        for method, data in stats['method_success_rates'].items():
            if data['total'] > 0:
                data['success_rate'] = data['success'] / data['total']
            else:
                data['success_rate'] = 0.0
        
        # Calculate average confidence scores
        for method, scores in stats['avg_confidence_scores'].items():
            if scores:
                stats['avg_confidence_scores'][method] = sum(scores) / len(scores)
            else:
                stats['avg_confidence_scores'][method] = 0.0
        
        # Calculate average processing times
        for method, times in stats['processing_times'].items():
            if times:
                stats['processing_times'][method] = sum(times) / len(times)
            else:
                stats['processing_times'][method] = 0.0
        
        return stats