"""
Optimized Credit Report Processor
Integrates enhanced Gemini processing with improved tradeline normalization
"""
import os
import PyPDF2  # type: ignore
import tempfile
import logging
import re
import traceback
from typing import List, Dict, Any, Optional
import sys
from datetime import datetime
import asyncio

from google.api_core.client_options import ClientOptions  # type: ignore
from google.cloud import documentai

# PDF Chunking
from services.pdf_chunker import PDFChunker

# Import enhanced components
from services.enhanced_gemini_processor import EnhancedGeminiProcessor
from services.advanced_parsing.negative_tradeline_classifier import NegativeTradelineClassifier
from utils.improved_tradeline_normalizer import ImprovedTradelineNormalizer

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# Environment variables with debugging
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us")
PROCESSOR_ID = os.getenv("DOCUMENT_AI_PROCESSOR_ID")

# Initialize Document AI client for fallback
document_ai_client = None
if PROJECT_ID and PROCESSOR_ID:
    try:
        opts = ClientOptions(api_endpoint=f"{LOCATION}-documentai.googleapis.com")
        document_ai_client = documentai.DocumentProcessorServiceClient(
            client_options=opts
        )
        logger.info(f"✅ Document AI fallback configured for {LOCATION}")
    except Exception as e:
        logger.warning(f"⚠️ Document AI fallback not available: {e}")


class OptimizedCreditReportProcessor:
    """
    Optimized processor integrating enhanced Gemini and improved normalization
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.processing_stats = {
            'pdfplumber_success': 0,
            'pymupdf_success': 0,
            'ocr_success': 0,
            'document_ai_fallback': 0,
            'total_processed': 0
        }

        # Initialize enhanced components
        self.gemini_processor = EnhancedGeminiProcessor()
        self.normalizer = ImprovedTradelineNormalizer()
        self.negative_classifier = NegativeTradelineClassifier()
        # AI validation and error correction
        from services.advanced_parsing.ai_tradeline_validator import AITradelineValidator
        from services.advanced_parsing.error_correction_system import ErrorCorrectionSystem
        self.validator = AITradelineValidator()
        self.error_correction_system = ErrorCorrectionSystem()

        # Setup cost logging
        self._setup_cost_logging()

    def _setup_cost_logging(self):
        """Setup cost tracking log file"""
        import os
        from datetime import datetime

        cost_dir = "/mnt/c/projects/credit-clarity/backend/cost"
        os.makedirs(cost_dir, exist_ok=True)

        log_file = os.path.join(cost_dir, f"processing_costs_{datetime.now().strftime('%Y_%m')}.log")

        # Setup file handler for cost logging
        cost_handler = logging.FileHandler(log_file)
        cost_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - COST - %(message)s')
        cost_handler.setFormatter(formatter)

        # Create separate logger for cost tracking
        self.cost_logger = logging.getLogger('cost_tracker')
        self.cost_logger.setLevel(logging.INFO)
        if not self.cost_logger.handlers:
            self.cost_logger.addHandler(cost_handler)

    async def process_credit_report_optimized(self, pdf_path: str) -> dict:
        """
        Optimized processing pipeline with enhanced Gemini and normalization
        """
        import asyncio
        start_time = asyncio.get_event_loop().time()
        self.processing_stats['total_processed'] += 1

        # Phase 1: Free/Fast extraction (try all free methods)
        extraction_result = await self._try_free_extraction_methods(pdf_path)

        if extraction_result['success']:
            # Quick check if this looks like a credit report
            if not self._is_likely_credit_report(extraction_result['text']):
                self.logger.warning("⚠️ Document doesn't appear to be a credit report, returning early")
                return {
                    'tradelines': [],
                    'method_used': f"{extraction_result['method']}_non_credit",
                    'processing_time': asyncio.get_event_loop().time() - start_time,
                    'cost_estimate': 0.0,
                    'success': True,
                    'warning': 'Document does not appear to be a credit report'
                }

            # Phase 2: Enhanced structured parsing with improved normalization
            tradelines = await self._parse_with_enhanced_parser(
                extraction_result['text'],
                extraction_result['tables']
            )

            if tradelines:
                processing_time = asyncio.get_event_loop().time() - start_time

                # Log cost savings
                self.cost_logger.info(f"OPTIMIZED_FREE_METHOD_SUCCESS: {extraction_result['method']}, "
                                    f"tradelines={len(tradelines)}, time={processing_time:.2f}s, "
                                    f"cost=0.00, savings=~$0.05")

                return {
                    'tradelines': tradelines,
                    'method_used': extraction_result['method'],
                    'processing_time': processing_time,
                    'cost_estimate': 0.0,  # Free methods
                    'success': True,
                    'validation_metadata': getattr(self, '_validation_metadata', {}),
                    'flagged_for_review': self._validation_metadata.get('flagged_for_review', []) if hasattr(self, '_validation_metadata') else [],
                    'average_confidence': self._validation_metadata.get('average_confidence', None) if hasattr(self, '_validation_metadata') else None,
                    'negative_accounts_count': self._validation_metadata.get('negative_accounts_count', None) if hasattr(self, '_validation_metadata') else None,
                    'corrections_made': self._validation_metadata.get('corrections_made', None) if hasattr(self, '_validation_metadata') else None,
                    'validation_applied': self._validation_metadata.get('validation_applied', False) if hasattr(self, '_validation_metadata') else False
                }

        # Phase 3: Expensive fallback (only if free methods failed)
        self.logger.warning("Free methods failed, using Document AI fallback")
        return await self._expensive_fallback(pdf_path, start_time)

    async def _try_free_extraction_methods(self, pdf_path: str) -> dict:
        """Try all free extraction methods in parallel with timeout"""
        import asyncio

        # For large files, reduce OCR processing to save time
        file_size = os.path.getsize(pdf_path) / (1024 * 1024)  # MB

        if file_size > 5:  # Skip OCR for files larger than 5MB to save time
            tasks = [
                self._extract_with_pdfplumber(pdf_path),
                self._extract_with_pymupdf(pdf_path)
            ]
            method_names = ['pdfplumber', 'pymupdf']
        else:
            tasks = [
                self._extract_with_pdfplumber(pdf_path),
                self._extract_with_pymupdf(pdf_path),
                self._extract_with_ocr(pdf_path)
            ]
            method_names = ['pdfplumber', 'pymupdf', 'ocr']

        # Add timeout for free extraction methods (2 minutes max)
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=120  # 2 minutes timeout
            )
        except asyncio.TimeoutError:
            self.logger.warning("Free extraction methods timed out, proceeding to fallback")
            return {'success': False, 'text': '', 'tables': [], 'method': 'timeout'}

        # Return the best result
        for i, result in enumerate(results):
            if isinstance(result, dict) and result.get('success'):
                self.processing_stats[f'{method_names[i]}_success'] += 1
                return result

        return {'success': False, 'text': '', 'tables': [], 'method': 'none'}

    async def _extract_with_pdfplumber(self, pdf_path: str) -> dict:
        """Async wrapper for pdfplumber extraction with dependency checking"""
        import asyncio

        def _sync_extract():
            try:
                import pdfplumber

                text_content = ""
                tables = []

                with pdfplumber.open(pdf_path) as pdf:
                    for page_num, page in enumerate(pdf.pages):
                        page_text = page.extract_text() or ""
                        text_content += f"\n--- Page {page_num + 1} ---\n{page_text}"

                        page_tables = page.extract_tables()
                        for table in page_tables or []:
                            if table and len(table) > 0:
                                tables.append({
                                    'headers': table[0] if table else [],
                                    'rows': table[1:] if len(table) > 1 else []
                                })

                if self._validate_extraction_quality(text_content):
                    return {
                        'success': True,
                        'text': text_content,
                        'tables': tables,
                        'method': 'pdfplumber'
                    }

            except ImportError:
                self.logger.debug("pdfplumber not available - install with: pip install pdfplumber")
            except Exception as e:
                self.logger.debug(f"pdfplumber failed: {e}")

            return {'success': False}

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _sync_extract)

    async def _extract_with_pymupdf(self, pdf_path: str) -> dict:
        """Async wrapper for PyMuPDF extraction with dependency checking"""
        import asyncio

        def _sync_extract():
            try:
                import fitz  # PyMuPDF

                text_content = ""
                tables = []

                doc = fitz.open(pdf_path)
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    page_text = page.get_text()
                    text_content += f"\n--- Page {page_num + 1} ---\n{page_text}"

                    # Extract tables if available
                    try:
                        page_tables = page.find_tables()
                        for table in page_tables:
                            table_data = table.extract()
                            if table_data and len(table_data) > 0:
                                tables.append({
                                    'headers': table_data[0] if table_data else [],
                                    'rows': table_data[1:] if len(table_data) > 1 else []
                                })
                    except:
                        pass  # Table extraction is optional

                doc.close()

                if self._validate_extraction_quality(text_content):
                    return {
                        'success': True,
                        'text': text_content,
                        'tables': tables,
                        'method': 'pymupdf'
                    }

            except ImportError:
                self.logger.debug("PyMuPDF not available - install with: pip install PyMuPDF")
            except Exception as e:
                self.logger.debug(f"PyMuPDF failed: {e}")

            return {'success': False}

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _sync_extract)

    async def _extract_with_ocr(self, pdf_path: str) -> dict:
        """Async wrapper for OCR extraction"""
        import asyncio
        import shutil

        def _sync_extract():
            try:
                # Check if tesseract is available first
                if not shutil.which('tesseract'):
                    self.logger.debug("Tesseract not available, skipping OCR")
                    return {'success': False}

                import fitz  # PyMuPDF for PDF to image conversion
                import pytesseract
                from PIL import Image
                import io

                text_content = ""

                doc = fitz.open(pdf_path)
                for page_num in range(min(len(doc), 5)):  # Limit OCR to first 5 pages for speed
                    page = doc[page_num]

                    # Convert page to image
                    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))  # Reduced scale for speed
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))

                    # OCR the image with timeout protection
                    try:
                        page_text = pytesseract.image_to_string(img, config='--psm 6', timeout=10)
                        text_content += f"\n--- Page {page_num + 1} (OCR) ---\n{page_text}"
                    except Exception as ocr_err:
                        self.logger.debug(f"OCR failed for page {page_num + 1}: {ocr_err}")
                        continue

                doc.close()

                if self._validate_extraction_quality(text_content):
                    return {
                        'success': True,
                        'text': text_content,
                        'tables': [],  # OCR doesn't extract structured tables
                        'method': 'ocr'
                    }

            except Exception as e:
                self.logger.debug(f"OCR failed: {e}")

            return {'success': False}

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _sync_extract)

    def _validate_extraction_quality(self, text: str) -> bool:
        """Validate if extracted text is good enough for credit report processing"""
        if not text or len(text.strip()) < 100:
            return False

        # Check for credit report indicators
        text_lower = text.lower()
        credit_indicators = [
            'credit', 'account', 'balance', 'payment', 'tradeline',
            'experian', 'equifax', 'transunion', 'creditor', 'limit',
            'score', 'report', 'bureau', 'fico'
        ]

        found_indicators = sum(1 for indicator in credit_indicators if indicator in text_lower)
        return found_indicators >= 3  # Must have at least 3 credit-related terms

    def _is_likely_credit_report(self, text: str) -> bool:
        """Quick check if text looks like a credit report"""
        if not text or len(text.strip()) < 100:
            return False

        text_lower = text.lower()
        strong_indicators = [
            'credit report', 'credit score', 'experian', 'equifax', 'transunion',
            'fico score', 'tradeline', 'credit bureau', 'account history'
        ]

        # Look for strong credit report indicators
        found_strong = sum(1 for indicator in strong_indicators if indicator in text_lower)

        # Also check for account patterns typical in credit reports
        account_patterns = ['account #', 'acct #', 'balance:', 'limit:', 'payment:']
        found_patterns = sum(1 for pattern in account_patterns if pattern in text_lower)

        return found_strong >= 1 or found_patterns >= 2

    async def _parse_with_enhanced_parser(self, text: str, tables: list) -> list:
        """Parse extracted text and tables into tradelines with enhanced processing"""
        import asyncio

        tradelines = []

        # Detect credit bureau from text
        credit_bureau = self._detect_credit_bureau(text)

        # Section-aware processing: Detect different credit report sections
        sections = self._detect_credit_report_sections(text)
        self.logger.info(f"📋 Detected {len(sections)} credit report sections: {list(sections.keys())}")

        # Try table parsing first if tables are available
        if tables:
            self.logger.info(f"📊 Processing {len(tables)} tables for tradeline extraction")
            for table in tables:
                table_tradelines = self._extract_tradelines_from_table(table)
                # Enhance each tradeline with credit bureau and improved normalization
                for tradeline in table_tradelines:
                    tradeline["credit_bureau"] = credit_bureau
                    # Apply improved normalization
                    tradeline = self.normalizer.normalize_tradeline(tradeline)
                    # Try to extract missing date_opened from text
                    if not tradeline.get("date_opened"):
                        tradeline["date_opened"] = self._extract_date_from_text(text, tradeline.get("creditor_name", ""))
                tradelines.extend(table_tradelines)

        # Use enhanced Gemini for text processing - process each section for comprehensive extraction
        if sections:
            # Process each section separately to ensure comprehensive coverage
            for section_name, section_text in sections.items():
                if len(section_text.strip()) > 200:  # Only process substantial sections
                    self.logger.info(f"🔍 Processing section: {section_name} ({len(section_text)} chars)")
                    section_tradelines = self.gemini_processor.extract_tradelines(section_text)

                    # Enhance section results with improved normalization
                    for tradeline in section_tradelines:
                        if isinstance(tradeline, dict):
                            tradeline["credit_bureau"] = credit_bureau
                            tradeline["source_section"] = section_name  # Track which section it came from
                            # Apply improved normalization
                            tradeline = self.normalizer.normalize_tradeline(tradeline)
                            if not tradeline.get("date_opened"):
                                tradeline["date_opened"] = self._extract_date_from_text(section_text, tradeline.get("creditor_name", ""))

                    tradelines.extend(section_tradelines)
                    self.logger.info(f"✅ Section {section_name}: extracted {len(section_tradelines)} tradelines")

        # Fallback: process entire text if no sections detected or no tradelines found
        if not tradelines and text.strip():
            self.logger.info("🔄 No sections detected or no tradelines found, processing entire text")
            gemini_tradelines = self.gemini_processor.extract_tradelines(text)
            # Enhance Gemini results with improved normalization
            for tradeline in gemini_tradelines:
                if isinstance(tradeline, dict):
                    tradeline["credit_bureau"] = credit_bureau
                    # Apply improved normalization
                    tradeline = self.normalizer.normalize_tradeline(tradeline)
                    if not tradeline.get("date_opened"):
                        tradeline["date_opened"] = self._extract_date_from_text(text, tradeline.get("creditor_name", ""))
            tradelines.extend(gemini_tradelines)

        # Universal date recovery for missing dates (do this BEFORE deduplication)
        tradelines = await self._recover_missing_dates(tradelines, text)

        # --- AI Validation Layer ---
        validation_results = await self.validator.batch_validate_tradelines(tradelines, text)
        validated_tradelines = []
        corrections_made = 0
        confidence_sum = 0.0
        flagged_for_review = []
        negative_accounts_count = 0
        for idx, (tradeline, result) in enumerate(zip(tradelines, validation_results)):
            # Update tradeline with corrected data and confidence
            if hasattr(result, 'corrected_data') and result.corrected_data:
                tradeline.update(result.corrected_data if isinstance(result.corrected_data, dict) else vars(result.corrected_data))
            tradeline['validation_confidence'] = getattr(result, 'confidence', 0.0)
            tradeline['is_valid'] = getattr(result, 'is_valid', True)
            tradeline['corrections_applied'] = getattr(result, 'corrections_made', [])
            tradeline['validation_notes'] = getattr(result, 'validation_notes', [])
            tradeline['ai_score'] = getattr(result, 'ai_score', 0.0)
            confidence_sum += tradeline['validation_confidence']
            if not tradeline['is_valid'] or tradeline['validation_confidence'] < 0.5:
                flagged_for_review.append(idx)
            if tradeline.get('is_negative'):
                negative_accounts_count += 1
            if tradeline['corrections_applied']:
                corrections_made += len(tradeline['corrections_applied'])
            validated_tradelines.append(tradeline)

        # Error Correction Layer for low-confidence tradelines
        corrected_tradelines = []
        error_corrections = 0
        for idx, tradeline in enumerate(validated_tradelines):
            if tradeline.get('validation_confidence', 1.0) < 0.7 or not tradeline.get('is_valid', True):
                # Wrap as ParsingResult for error correction system
                from services.advanced_parsing.bureau_specific_parser import ParsingResult, TradelineData

                # Filter keys for TradelineData
                tradeline_data_keys = TradelineData.__annotations__.keys()
                filtered_tradeline = {k: v for k, v in tradeline.items() if k in tradeline_data_keys}

                parsing_result = ParsingResult(
                    bureau=tradeline.get('credit_bureau', 'Unknown'),
                    success=True,
                    tradelines=[TradelineData(**filtered_tradeline)],
                    confidence=tradeline.get('validation_confidence', 0.0),
                    parsing_method=tradeline.get('parsing_method', 'unknown'),
                    errors=[],
                    metadata={}
                )

                corrected_result, correction_results = await self.error_correction_system.detect_and_correct_errors(parsing_result, text, pdf_path=None)

                if corrected_result and corrected_result.tradelines:
                    # Pull corrected tradeline
                    corrected_tradeline = corrected_result.tradelines[0]
                    tradeline.update(vars(corrected_tradeline))

                    # Merge corrections applied
                    for cr in correction_results:
                        if cr.corrections_applied:
                            tradeline['corrections_applied'] = tradeline.get('corrections_applied', []) + cr.corrections_applied
                            error_corrections += 1
            corrected_tradelines.append(tradeline)

        self.logger.info(f"Error Correction: {error_corrections} low-confidence tradelines corrected.")

        # Filter out low-confidence or invalid tradelines after correction
        filtered_tradelines = [t for t in corrected_tradelines if t.get('is_valid', True) and t.get('validation_confidence', 1.0) >= 0.5]

        self.logger.info(f"AI Validation: {len(filtered_tradelines)}/{len(tradelines)} tradelines passed validation. Corrections made: {corrections_made}. Negative accounts: {negative_accounts_count}.")
        self.logger.info(f"Flagged for review: {flagged_for_review}")

        # Smart deduplication with enhanced criteria
        unique_tradelines = self._smart_deduplicate_tradelines(filtered_tradelines)

        self.logger.info(f"📊 Final result: {len(unique_tradelines)} unique tradelines (removed {len(filtered_tradelines) - len(unique_tradelines)} duplicates)")
        # Post-processing validation for negative accounts
        final_tradelines, negative_validation_stats = self._validate_negative_accounts(unique_tradelines)
        self.logger.info(f"Negative account validation: {negative_validation_stats}")
        # Store validation metadata for response
        self._validation_metadata = {
            'validation_applied': True,
            'corrections_made': corrections_made + error_corrections,
            'negative_accounts_count': negative_accounts_count,
            'average_confidence': confidence_sum / max(1, len(validated_tradelines)),
            'flagged_for_review': flagged_for_review,
            'negative_validation': negative_validation_stats
        }
        final_tradelines = self._apply_negative_classification(final_tradelines)
        return final_tradelines

    def _validate_negative_accounts(self, tradelines: list) -> tuple:
        """Final checks for negative accounts: required fields, format, and review flags."""
        flagged = []
        pass_count = 0
        total_neg = 0
        for idx, t in enumerate(tradelines):
            if t.get('is_negative'):
                total_neg += 1
                missing = []
                # Required fields
                for field in ['creditor_name', 'account_status', 'account_balance', 'credit_bureau']:
                    if not t.get(field):
                        missing.append(field)
                # Date format
                date = t.get('date_opened')
                if date and not re.match(r'^\d{2}/\d{2}/\d{4}$', str(date)):
                    missing.append('date_opened_format')
                # Amount formats
                monthly_payment_val = str(t['monthly_payment']).replace('$', '').replace(',', '') if t.get('monthly_payment') else None
                if monthly_payment_val and not re.match(r'^\d+\.\d{2}$', monthly_payment_val):
                    missing.append('monthly_payment_format')
                
                credit_limit_val = str(t['credit_limit']).replace('$', '').replace(',', '') if t.get('credit_limit') else None
                if credit_limit_val and not re.match(r'^\d+$', credit_limit_val):
                    missing.append('credit_limit_format')
                
                account_balance_val = str(t['account_balance']).replace('$', '').replace(',', '') if t.get('account_balance') else None
                if account_balance_val and not re.match(r'^\d+$', account_balance_val):
                    missing.append('account_balance_format')
                # Account number
                if t.get('account_number') and not re.match(r'^[A-Za-z0-9]+$', str(t['account_number'])):
                    missing.append('account_number_format')
                if missing:
                    flagged.append({'index': idx, 'fields': missing})
                else:
                    pass_count += 1
        stats = {
            'negative_accounts': total_neg,
            'validation_passed': pass_count,
            'flagged_for_review': flagged
        }
        return tradelines, stats

    def _apply_negative_classification(self, tradelines: list) -> list:
        """Apply rule-based classifier after validation to backfill `is_negative` flags."""
        if not tradelines:
            return tradelines

        for tradeline in tradelines:
            if not isinstance(tradeline, dict):
                continue

            existing_flag = tradeline.get("is_negative")
            if existing_flag is True:
                continue

            classification = self.negative_classifier.classify(tradeline)

            if classification.is_negative and classification.confidence >= 0.7:
                tradeline["is_negative"] = True
            elif existing_flag is None:
                tradeline["is_negative"] = classification.is_negative

        return tradelines

    def _detect_credit_bureau(self, text: str) -> str:
        """Detect credit bureau from text content"""
        if not text:
            return "Unknown"

        # Convert to lowercase for case-insensitive matching
        text_lower = text.lower()

        # Credit bureau names to search for (in order of priority)
        bureaus = [
            ("equifax", "Equifax"),
            ("experian", "Experian"),
            ("transunion", "TransUnion"),
            ("trans union", "TransUnion")  # Handle space variation
        ]

        # Search for each bureau name
        for search_term, bureau_name in bureaus:
            if search_term in text_lower:
                logger.info(f"🔍 Credit bureau detected: {bureau_name}")
                return bureau_name

        logger.info("🔍 No credit bureau detected, using 'Unknown'")
        return "Unknown"

    def _detect_credit_report_sections(self, text: str) -> dict:
        """Detect different sections in credit report for comprehensive processing"""
        import re

        sections = {}
        lines = text.split('\n')
        current_section = "header"
        current_content = []

        # Section markers for different credit bureaus
        section_markers = [
            # Negative/Derogatory sections
            (r'(?i)(potentially negative|negative|derogatory|adverse|collections?|charge.?offs?)', 'negative_items'),
            (r'(?i)(public records?|bankruptc|tax lien|judgment)', 'public_records'),

            # Positive sections
            (r'(?i)(accounts? in good standing|satisfactory|current accounts?|positive)', 'positive_accounts'),
            (r'(?i)(revolving accounts?|credit cards?)', 'revolving_accounts'),
            (r'(?i)(installment accounts?|installment loans?|mortgages?|auto loans?)', 'installment_accounts'),
            (r'(?i)(closed accounts?|paid accounts?)', 'closed_accounts'),

            # General account sections
            (r'(?i)(credit accounts?|trade lines?|tradelines?|account history)', 'all_accounts'),
            (r'(?i)(account information|credit information)', 'account_info'),

            # Payment history
            (r'(?i)(payment history|payment information)', 'payment_history'),

            # Credit inquiries
            (r'(?i)(inquiries|credit inquiries)', 'inquiries'),

            # Summary sections
            (r'(?i)(credit summary|account summary)', 'summary'),
        ]

        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # Check if this line marks a new section
            section_found = False
            for pattern, section_name in section_markers:
                if re.search(pattern, line_stripped):
                    # Save previous section if it has content
                    if current_content and current_section:
                        sections[current_section] = '\n'.join(current_content)

                    current_section = section_name
                    current_content = [line_stripped]
                    section_found = True
                    break

            if not section_found:
                current_content.append(line_stripped)

        # Save the last section
        if current_content and current_section:
            sections[current_section] = '\n'.join(current_content)

        # If no specific sections found, create logical sections based on content analysis
        if len(sections) <= 1:
            return self._create_content_based_sections(text)

        return sections

    def _create_content_based_sections(self, text: str) -> dict:
        """Create sections based on content analysis when explicit markers aren't found"""
        sections = {}

        # Split text into chunks and analyze content
        chunk_size = 5000
        overlap_size = 500
        text_chunks = []

        for i in range(0, len(text), chunk_size - overlap_size):
            end_pos = min(i + chunk_size, len(text))
            chunk = text[i:end_pos]
            text_chunks.append(chunk)

            if end_pos >= len(text):
                break

        for i, chunk in enumerate(text_chunks):
            chunk_lower = chunk.lower()

            # Classify chunk based on content
            if any(term in chunk_lower for term in ['charge off', 'collection', 'late', 'delinquent', 'past due']):
                section_name = f'negative_section_{i+1}'
            elif any(term in chunk_lower for term in ['good standing', 'current', 'paid as agreed', 'satisfactory']):
                section_name = f'positive_section_{i+1}'
            elif any(term in chunk_lower for term in ['auto loan', 'mortgage', 'installment']):
                section_name = f'installment_section_{i+1}'
            elif any(term in chunk_lower for term in ['credit card', 'revolving', 'line of credit']):
                section_name = f'revolving_section_{i+1}'
            else:
                section_name = f'general_section_{i+1}'

            sections[section_name] = chunk

        return sections

    def _extract_date_from_text(self, text: str, creditor_name: str) -> str:
        """Extract date_opened from text context around creditor name"""
        import re

        if not creditor_name or not text:
            return ""

        try:
            # Multiple strategies for date extraction

            # Strategy 1: Look for text sections containing the creditor name
            lines = text.split('\n')
            creditor_lines = []

            for i, line in enumerate(lines):
                if creditor_name.upper() in line.upper():
                    # Get broader context around the creditor mention
                    start_idx = max(0, i - 5)
                    end_idx = min(len(lines), i + 15)
                    creditor_lines.extend(lines[start_idx:end_idx])

            # Enhanced date patterns with more variations
            date_patterns = [
                # Explicit date opened patterns
                r'Date Opened[:\s]*(\d{1,2}/\d{1,2}/\d{4})',  # "Date Opened: 01/12/2014"
                r'Date Opened[:\s]*(\d{1,2}/\d{4})',          # "Date Opened: 01/2014"
                r'Date Opened[:\s]*(\d{1,2}-\d{1,2}-\d{4})',  # "Date Opened: 01-12-2014"
                r'Date Opened[:\s]*(\d{4}-\d{1,2}-\d{1,2})',  # "Date Opened: 2014-01-12"
                r'Opened[:\s]*(\d{1,2}/\d{1,2}/\d{4})',       # "Opened: 01/12/2014"
                r'Opened[:\s]*(\d{1,2}/\d{4})',               # "Opened: 01/2014"
                r'Since[:\s]*(\d{1,2}/\d{1,2}/\d{4})',        # "Since: 01/12/2014"
                r'Since[:\s]*(\d{1,2}/\d{4})',                # "Since: 01/2014"

                # Standalone date patterns (more permissive)
                r'(\d{1,2}/\d{1,2}/\d{4})',                   # "01/12/2014"
                r'(\d{1,2}/\d{4})',                           # "01/2014"
                r'(\d{1,2}-\d{1,2}-\d{4})',                   # "01-12-2014"
                r'(\d{4}-\d{1,2}-\d{1,2})',                   # "2014-01-12"
            ]

            # Search in creditor context first
            if creditor_lines:
                context_text = ' '.join(creditor_lines)
                self.logger.debug(f"Searching for dates in creditor context for {creditor_name}")

                for pattern in date_patterns:
                    matches = re.findall(pattern, context_text, re.IGNORECASE)
                    if matches:
                        # Take the first valid date
                        for match in matches:
                            date_str = match if isinstance(match, str) else match[0]
                            normalized_date = self.normalizer._normalize_date(date_str)
                            if normalized_date:
                                self.logger.debug(f"Found date {normalized_date} for {creditor_name}")
                                return normalized_date

            # Strategy 2: Global search if creditor-specific search failed
            self.logger.debug(f"Creditor-specific search failed, trying global search for {creditor_name}")

            # Look for dates anywhere in the text near creditor mentions
            # Split text into smaller sections and search each
            text_sections = [text[i:i+2000] for i in range(0, len(text), 1500)]

            for section in text_sections:
                if creditor_name.upper() in section.upper():
                    for pattern in date_patterns[:4]:  # Use only the most specific patterns for global search
                        matches = re.findall(pattern, section, re.IGNORECASE)
                        if matches:
                            for match in matches:
                                date_str = match if isinstance(match, str) else match[0]
                                normalized_date = self.normalizer._normalize_date(date_str)
                                if normalized_date:
                                    self.logger.debug(f"Found date {normalized_date} in global search for {creditor_name}")
                                    return normalized_date

            self.logger.debug(f"No date found for {creditor_name}")
            return ""

        except Exception as e:
            self.logger.warning(f"Date extraction failed for {creditor_name}: {e}")
            return ""

    async def _recover_missing_dates(self, tradelines: list, full_text: str) -> list:
        """Universal date recovery system for any creditor with missing date_opened"""
        import re
        import asyncio

        missing_date_tradelines = []
        complete_tradelines = []

        # Separate tradelines with and without dates
        for tradeline in tradelines:
            if not tradeline.get('date_opened') and tradeline.get('creditor_name'):
                missing_date_tradelines.append(tradeline)
            else:
                complete_tradelines.append(tradeline)

        if not missing_date_tradelines:
            self.logger.info("📅 All tradelines already have date_opened - no recovery needed")
            return tradelines

        self.logger.info(f"📅 Starting universal date recovery for {len(missing_date_tradelines)} tradelines")

        for tradeline in missing_date_tradelines:
            creditor_name = tradeline.get('creditor_name', '')
            account_number = tradeline.get('account_number', '')

            # Try to recover date using global search
            recovered_date = await self._global_date_search(full_text, creditor_name, account_number)

            if recovered_date:
                tradeline['date_opened'] = recovered_date
                self.logger.info(f"✅ Recovered date {recovered_date} for {creditor_name} {account_number}")
                complete_tradelines.append(tradeline)
            else:
                self.logger.warning(f"⚠️ Could not recover date for {creditor_name} {account_number}")
                # Still include the tradeline, but without date
                complete_tradelines.append(tradeline)

        recovery_success = sum(1 for t in missing_date_tradelines if t.get('date_opened'))
        self.logger.info(f"📅 Date recovery complete: {recovery_success}/{len(missing_date_tradelines)} dates recovered "
                        f"({recovery_success/max(len(missing_date_tradelines), 1)*100:.1f}% success rate)")

        return complete_tradelines

    async def _global_date_search(self, full_text: str, creditor_name: str, account_number: str) -> str:
        """Search entire credit report for dates near specific creditor/account"""
        import re
        import asyncio

        if not creditor_name:
            return ""

        try:
            # More restrictive date patterns to avoid matching invalid data
            date_patterns = [
                # MM/YYYY formats (restrict months 1-12)
                r'((?:0[1-9]|1[0-2])/\d{4})',                # 01/2015, 12/2020
                r'((?:0[1-9]|1[0-2])-\d{4})',                # 01-2015, 12-2020
                r'([1-9]/\d{4})',                            # 1/2015, 9/2020

                # MM/DD/YYYY formats (restrict months 1-12, days 1-31)
                r'((?:0[1-9]|1[0-2])/(?:0[1-9]|[12][0-9]|3[01])/\d{4})',  # 01/15/2015, 12/25/2020
                r'((?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])-\d{4})',  # 01-15-2015, 12-25-2020
                r'([1-9]/(?:0[1-9]|[12][0-9]|3[01])/\d{4})',              # 1/15/2015, 9/25/2020
                r'((?:0[1-9]|1[0-2])/[1-9]/\d{4})',                       # 01/5/2015, 12/9/2020
                r'([1-9]/[1-9]/\d{4})',                                    # 1/5/2015, 9/9/2020

                # YYYY-MM-DD formats (ISO format with validation)
                r'(\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01]))', # 2015-01-15

                # Month name formats
                r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',  # Jan 2015, January 2015
                r'((?:0[1-9]|[12][0-9]|3[01])\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',  # 15 Jan 2015

                # Short year formats with month validation
                r'((?:0[1-9]|1[0-2])/\d{2})',                # 01/15, 12/20 (assuming 20xx)
                r'([1-9]/\d{2})',                            # 1/15, 9/20 (assuming 20xx)
            ]

            # Split text into manageable chunks for searching
            chunk_size = 2000
            overlap_size = 500
            text_chunks = []

            for i in range(0, len(full_text), chunk_size - overlap_size):
                end_pos = min(i + chunk_size, len(full_text))
                chunk = full_text[i:end_pos]
                text_chunks.append(chunk)

                if end_pos >= len(full_text):
                    break

            found_dates = []

            # Search each chunk for creditor mentions and nearby dates
            for chunk_idx, chunk in enumerate(text_chunks):
                # Look for creditor name (case insensitive)
                creditor_positions = []

                # Try different variations of the creditor name
                creditor_variations = [
                    creditor_name,
                    creditor_name.upper(),
                    creditor_name.lower(),
                    creditor_name.replace(' ', ''),  # Remove spaces
                    creditor_name.split()[0] if ' ' in creditor_name else creditor_name,  # First word only
                ]

                for variation in creditor_variations:
                    for match in re.finditer(re.escape(variation), chunk, re.IGNORECASE):
                        creditor_positions.append(match.start())

                # For each creditor mention, search for dates in surrounding context
                for pos in creditor_positions:
                    # Define search window around creditor mention
                    context_start = max(0, pos - 1000)  # Look 1000 chars before
                    context_end = min(len(chunk), pos + 1000)  # Look 1000 chars after
                    context = chunk[context_start:context_end]

                    # Search for dates in this context
                    for pattern in date_patterns:
                        matches = re.findall(pattern, context, re.IGNORECASE)
                        for match in matches:
                            # Clean up the match
                            date_str = match if isinstance(match, str) else match[0]

                            # Try to normalize and validate the date
                            normalized_date = self.normalizer._normalize_date(date_str)
                            if normalized_date:
                                # Calculate distance from creditor mention
                                date_match = re.search(re.escape(date_str), context)
                                if date_match:
                                    distance = abs(date_match.start() - (pos - context_start))
                                    found_dates.append({
                                        'date': normalized_date,
                                        'distance': distance,
                                        'raw_date': date_str,
                                        'context': context[max(0, date_match.start()-50):date_match.end()+50]
                                    })

            # If we have dates, return the closest one to creditor mention
            if found_dates:
                # Sort by distance and take the closest
                found_dates.sort(key=lambda x: x['distance'])
                best_date = found_dates[0]

                self.logger.debug(f"Found date {best_date['date']} for {creditor_name} "
                                f"(distance: {best_date['distance']}, context: '{best_date['context']}')")

                return best_date['date']

            return ""

        except Exception as e:
            self.logger.warning(f"Global date search failed for {creditor_name}: {e}")
            return ""

    def _smart_deduplicate_tradelines(self, tradelines: list) -> list:
        """Enhanced deduplication using creditor + clean account number + date + credit bureau"""
        import re

        if not tradelines:
            return []

        # Step 1: Filter out tradelines without account numbers (not valid tradelines)
        valid_tradelines = []
        invalid_count = 0

        for tradeline in tradelines:
            account_number_raw = tradeline.get('account_number', '') or ''
            account_number = str(account_number_raw).strip() if account_number_raw is not None else ''
            if account_number and account_number not in ['', 'N/A', 'Unknown', 'No account']:
                valid_tradelines.append(tradeline)
            else:
                invalid_count += 1
                self.logger.debug(f"Filtered out tradeline without account number: {tradeline.get('creditor_name', 'Unknown')}")

        if invalid_count > 0:
            self.logger.info(f"🚫 Filtered out {invalid_count} tradelines without valid account numbers")

        # Step 2: Smart deduplication
        unique_tradelines = []
        seen_identifiers = set()

        for tradeline in valid_tradelines:
            # Extract and clean components for unique identifier
            creditor_name_raw = tradeline.get('creditor_name', '') or ''
            creditor_name = str(creditor_name_raw).strip().upper() if creditor_name_raw is not None else ''

            raw_account_number_val = tradeline.get('account_number', '') or ''
            raw_account_number = str(raw_account_number_val).strip() if raw_account_number_val is not None else ''

            date_opened_raw = tradeline.get('date_opened', '') or ''
            date_opened = str(date_opened_raw).strip() if date_opened_raw is not None else ''

            credit_bureau_raw = tradeline.get('credit_bureau', '') or ''
            credit_bureau = str(credit_bureau_raw).strip().upper() if credit_bureau_raw is not None else ''

            # Clean account number by removing special characters
            clean_account_number = re.sub(r'[*.\-\s]', '', raw_account_number).upper()

            # Create unique identifier: creditor + clean_account + date + bureau
            unique_identifier = f"{creditor_name}|{clean_account_number}|{date_opened}|{credit_bureau}"

            if unique_identifier not in seen_identifiers:
                seen_identifiers.add(unique_identifier)
                unique_tradelines.append(tradeline)
                self.logger.debug(f"✅ Added unique tradeline: {creditor_name} {raw_account_number} {date_opened} ({credit_bureau})")
            else:
                self.logger.debug(f"🔄 Duplicate found, skipping: {creditor_name} {raw_account_number} {date_opened} ({credit_bureau})")

        # Log deduplication statistics
        total_removed = len(valid_tradelines) - len(unique_tradelines)
        self.logger.info(f"🧹 Smart deduplication complete:")
        self.logger.info(f"   📊 Started with {len(tradelines)} tradelines")
        self.logger.info(f"   🚫 Filtered {invalid_count} without account numbers")
        self.logger.info(f"   🔄 Removed {total_removed} duplicates")
        self.logger.info(f"   ✅ Final count: {len(unique_tradelines)} unique tradelines")

        # Log examples of the unique identifiers for debugging
        if unique_tradelines:
            self.logger.debug("Sample unique identifiers:")
            for i, tradeline in enumerate(unique_tradelines[:3]):
                creditor_name_raw = tradeline.get('creditor_name', '') or ''
                creditor_name = str(creditor_name_raw).strip().upper() if creditor_name_raw is not None else ''

                raw_account_number_val = tradeline.get('account_number', '') or ''
                raw_account_number = str(raw_account_number_val).strip() if raw_account_number_val is not None else ''

                date_opened_raw = tradeline.get('date_opened', '') or ''
                date_opened = str(date_opened_raw).strip() if date_opened_raw is not None else ''

                credit_bureau_raw = tradeline.get('credit_bureau', '') or ''
                credit_bureau = str(credit_bureau_raw).strip().upper() if credit_bureau_raw is not None else ''

                identifier = f"{creditor_name}|{clean_account_number}|{date_opened}|{credit_bureau}"
                self.logger.debug(f"   {i+1}. {identifier}")

        return unique_tradelines

    async def _expensive_fallback(self, pdf_path: str, start_time: float) -> dict:
        """Expensive Document AI fallback when free methods fail"""
        import asyncio

        self.processing_stats['document_ai_fallback'] += 1

        if not document_ai_client:
            self.cost_logger.error("FALLBACK_FAILED: Document AI not configured")
            return {'success': False, 'error': 'No fallback available'}

        try:
            # Use original Document AI chunking logic
            with open(pdf_path, "rb") as pdf_file:
                pdf_content = pdf_file.read()

            # Calculate file size for optimizations
            file_size_mb = len(pdf_content) / (1024 * 1024)

            # Adjust chunk size based on file size for better performance
            chunker = PDFChunker(chunk_size=20 if file_size_mb > 3 else 30)
            page_count = chunker.get_pdf_page_count(pdf_content)

            if chunker.needs_chunking(pdf_content):
                text, tables = await self._process_with_chunking(pdf_content, chunker)
            else:
                text, tables = await self._process_single_document(pdf_content)

            tradelines = await self._parse_with_enhanced_parser(text, tables)

            processing_time = asyncio.get_event_loop().time() - start_time
            estimated_cost = 0.05 * (page_count // 30 + 1)  # Rough estimate

            self.cost_logger.info(f"DOCUMENT_AI_FALLBACK: pages={page_count}, "
                                f"tradelines={len(tradelines)}, time={processing_time:.2f}s, "
                                f"cost=${estimated_cost:.2f}")

            return {
                'tradelines': tradelines,
                'method_used': 'document_ai_fallback',
                'processing_time': processing_time,
                'cost_estimate': estimated_cost,
                'success': True
            }

        except Exception as e:
            self.cost_logger.error(f"DOCUMENT_AI_FALLBACK_FAILED: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def _process_with_chunking(self, pdf_content: bytes, chunker) -> tuple[str, list]:
        """Process large PDF with chunking"""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            chunk_paths = chunker.chunk_pdf(pdf_content, temp_dir, "credit_report")

            all_text = ""
            all_tables = []

            for chunk_path in chunk_paths:
                with open(chunk_path, "rb") as chunk_file:
                    chunk_content = chunk_file.read()

                chunk_text, chunk_tables = await self._process_single_document(chunk_content)
                all_text += chunk_text + "\n"
                all_tables.extend(chunk_tables)

            return all_text, all_tables

    async def _process_single_document(self, pdf_content: bytes) -> tuple[str, list]:
        """Process single PDF document with Document AI"""
        import asyncio

        def _sync_process():
            raw_document = documentai.RawDocument(
                content=pdf_content,
                mime_type="application/pdf"
            )

            name = document_ai_client.processor_path(PROJECT_ID, LOCATION, PROCESSOR_ID)
            request = documentai.ProcessRequest(name=name, raw_document=raw_document)

            result = document_ai_client.process_document(request=request)
            document = result.document
            extracted_text = document.text

            # Extract tables
            tables = []
            for page in document.pages:
                if hasattr(page, 'tables'):
                    for table in page.tables:
                        table_data = self._extract_table_data(table, extracted_text)
                        if table_data:
                            tables.append(table_data)

            return extracted_text, tables

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _sync_process)

    def _extract_table_data(self, table, full_text: str) -> dict:
        """Extract structured data from a Document AI table"""
        try:
            table_data = {
                "headers": [],
                "rows": []
            }

            # Extract header row (first row)
            if table.header_rows:
                header_row = table.header_rows[0]
                for cell in header_row.cells:
                    cell_text = self._get_text(cell.layout, full_text).strip()
                    table_data["headers"].append(cell_text)

            # Extract data rows
            for row in table.body_rows:
                row_data = []
                for cell in row.cells:
                    cell_text = self._get_text(cell.layout, full_text).strip()
                    row_data.append(cell_text)
                table_data["rows"].append(row_data)

            return table_data

        except Exception as e:
            self.logger.error(f"Failed to extract table data: {str(e)}")
            return {}

    def _get_text(self, layout, full_text: str) -> str:
        """Extract text from Document AI layout object"""
        if not layout:
            return ""

        if hasattr(layout, 'text_anchor') and layout.text_anchor:
            text_anchor = layout.text_anchor
            if hasattr(text_anchor, 'text_segments') and text_anchor.text_segments:
                text_segments = []
                for segment in text_anchor.text_segments:
                    start_index = int(segment.start_index) if segment.start_index else 0
                    end_index = int(segment.end_index) if segment.end_index else len(full_text)
                    text_segments.append(full_text[start_index:end_index])
                return "".join(text_segments)

        return ""

    def _extract_tradelines_from_table(self, table: dict) -> list:
        """Extract tradelines from a structured table"""
        try:
            headers = table.get("headers", [])
            rows = table.get("rows", [])

            if not headers or not rows:
                return []

            tradelines = []

            # Map common header variations to standard fields
            header_mapping = {
                "creditor": "creditor_name",
                "creditor_name": "creditor_name",
                "lender": "creditor_name",
                "company": "creditor_name",
                "account": "account_number",
                "account_number": "account_number",
                "acct": "account_number",
                "balance": "account_balance",
                "current_balance": "account_balance",
                "amount_owed": "account_balance",
                "limit": "credit_limit",
                "credit_limit": "credit_limit",
                "high_credit": "credit_limit",
                "payment": "monthly_payment",
                "monthly_payment": "monthly_payment",
                "min_payment": "monthly_payment",
                "date_opened": "date_opened",
                "opened": "date_opened",
                "status": "account_status",
                "account_status": "account_status",
                "type": "account_type",
                "account_type": "account_type"
            }

            # Normalize headers
            normalized_headers = []
            for header in headers:
                if not header:  # Skip None or empty headers
                    normalized_headers.append("")
                    continue

                header_lower = str(header).lower().strip()
                mapped_header = None
                for key, value in header_mapping.items():
                    if key in header_lower:
                        mapped_header = value
                        break
                normalized_headers.append(mapped_header or header_lower)

            # Process each row as a potential tradeline
            for row_idx, row in enumerate(rows):
                if len(row) != len(normalized_headers):
                    continue

                tradeline = {
                    "creditor_name": "",
                    "account_number": "",
                    "account_balance": "",
                    "credit_limit": "",
                    "monthly_payment": "",
                    "date_opened": "",
                    "account_type": "Credit Card",
                    "account_status": "Open",
                    "credit_bureau": "",
                    "is_negative": False,
                    "dispute_count": 0
                }

                # Map row data to tradeline fields
                for i, cell_value in enumerate(row):
                    if i < len(normalized_headers):
                        header = normalized_headers[i]
                        if header in tradeline and cell_value is not None:
                            cell_str = str(cell_value).strip()
                            if cell_str:  # Only add non-empty values
                                tradeline[header] = cell_str

                # Only add if we have essential fields
                if tradeline["creditor_name"] and tradeline["account_number"]:
                    tradelines.append(tradeline)

            return tradelines

        except Exception as e:
            self.logger.error(f"Failed to extract tradelines from table: {str(e)}")
            return []
