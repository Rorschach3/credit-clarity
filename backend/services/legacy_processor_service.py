"""
Legacy Credit Report Processor Service
Processes credit reports using the most cost-effective method
Combines free extraction methods with structured parsing
"""
import os
import re
import asyncio
import logging
import tempfile
from typing import Dict, List, Any, Optional, Tuple

# Document AI imports
from google.api_core.client_options import ClientOptions
from google.cloud import documentai

# PDF processing imports
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    pdfplumber = None
    PDFPLUMBER_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    fitz = None
    PYMUPDF_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    import shutil
    TESSERACT_AVAILABLE = True
except ImportError:
    pytesseract = None
    Image = None
    shutil = None
    TESSERACT_AVAILABLE = False

from services.pdf_chunker import PDFChunker
from services.llm_parser_service import GeminiProcessor
from utils.date_utils import normalize_date_for_postgres
from utils.credit_bureau_detector import detect_credit_bureau

logger = logging.getLogger(__name__)


class LegacyCreditReportProcessor:
    """
    Processes credit reports using the most cost-effective method
    """
    
    def __init__(self, project_id: str = None, processor_id: str = None, location: str = "us"):
        self.logger = logging.getLogger(__name__)
        self.project_id = project_id
        self.processor_id = processor_id
        self.location = location
        
        self.processing_stats = {
            'pdfplumber_success': 0,
            'pymupdf_success': 0, 
            'ocr_success': 0,
            'document_ai_fallback': 0,
            'total_processed': 0
        }
        
        # Initialize Document AI client for fallback
        self.document_ai_client = None
        if project_id and processor_id:
            try:
                opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
                self.document_ai_client = documentai.DocumentProcessorServiceClient(
                    client_options=opts
                )
                logger.info(f"✅ Document AI fallback configured for {location}")
            except Exception as e:
                logger.warning(f"⚠️ Document AI fallback not available: {e}")
        
        # Setup cost logging
        self._setup_cost_logging()
    
    def _setup_cost_logging(self):
        """Setup cost tracking log file"""
        from datetime import datetime
        
        cost_dir = "/tmp/cost"
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
    
    async def process_credit_report_optimal(self, pdf_path: str) -> Dict[str, Any]:
        """
        Optimal processing pipeline with cost tracking
        """
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
            
            # Phase 2: Structured parsing
            tradelines = await self._parse_with_structured_parser(
                extraction_result['text'], 
                extraction_result['tables']
            )
            
            if tradelines:
                processing_time = asyncio.get_event_loop().time() - start_time
                
                # Log cost savings
                self.cost_logger.info(f"FREE_METHOD_SUCCESS: {extraction_result['method']}, "
                                    f"tradelines={len(tradelines)}, time={processing_time:.2f}s, "
                                    f"cost=0.00, savings=~$0.05")
                
                return {
                    'tradelines': tradelines,
                    'method_used': extraction_result['method'],
                    'processing_time': processing_time,
                    'cost_estimate': 0.0,  # Free methods
                    'success': True
                }
        
        # Phase 3: Expensive fallback (only if free methods failed)
        self.logger.warning("Free methods failed, using Document AI fallback")
        return await self._expensive_fallback(pdf_path, start_time)

    async def _try_free_extraction_methods(self, pdf_path: str) -> Dict[str, Any]:
        """Try all free extraction methods in parallel with timeout"""
        # For large files, reduce OCR processing to save time
        file_size = os.path.getsize(pdf_path) / (1024 * 1024)  # MB
        
        tasks = []
        method_names = []
        
        if PDFPLUMBER_AVAILABLE:
            tasks.append(self._extract_with_pdfplumber(pdf_path))
            method_names.append('pdfplumber')
        
        if PYMUPDF_AVAILABLE:
            tasks.append(self._extract_with_pymupdf(pdf_path))
            method_names.append('pymupdf')
        
        # Only add OCR for smaller files
        if file_size <= 5 and TESSERACT_AVAILABLE:
            tasks.append(self._extract_with_ocr(pdf_path))
            method_names.append('ocr')
        
        if not tasks:
            self.logger.error("No extraction methods available")
            return {'success': False, 'text': '', 'tables': [], 'method': 'no_methods'}
        
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

    async def _extract_with_pdfplumber(self, pdf_path: str) -> Dict[str, Any]:
        """Async wrapper for pdfplumber extraction with dependency checking"""
        if not PDFPLUMBER_AVAILABLE:
            return {'success': False}
        
        def _sync_extract():
            try:
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
                
            except Exception as e:
                self.logger.debug(f"pdfplumber failed: {e}")
            
            return {'success': False}
        
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _sync_extract)

    async def _extract_with_pymupdf(self, pdf_path: str) -> Dict[str, Any]:
        """Async wrapper for PyMuPDF extraction with dependency checking"""
        if not PYMUPDF_AVAILABLE:
            return {'success': False}
        
        def _sync_extract():
            try:
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
                
            except Exception as e:
                self.logger.debug(f"PyMuPDF failed: {e}")
            
            return {'success': False}
        
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _sync_extract)

    async def _extract_with_ocr(self, pdf_path: str) -> Dict[str, Any]:
        """Async wrapper for OCR extraction"""
        if not TESSERACT_AVAILABLE or not PYMUPDF_AVAILABLE:
            return {'success': False}
        
        def _sync_extract():
            try:
                # Check if tesseract is available first
                if not shutil.which('tesseract'):
                    self.logger.debug("Tesseract not available, skipping OCR")
                    return {'success': False}
                
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

    async def _parse_with_structured_parser(self, text: str, tables: List[Dict]) -> List[Dict]:
        """Parse extracted text and tables into tradelines with enhanced data extraction"""
        tradelines = []
        
        # Detect credit bureau from text
        credit_bureau = detect_credit_bureau(text)
        
        # Try table parsing first if tables are available
        if tables:
            self.logger.info(f"📊 Processing {len(tables)} tables for tradeline extraction")
            for table in tables:
                table_tradelines = self._extract_tradelines_from_table(table)
                # Enhance each tradeline with credit bureau
                for tradeline in table_tradelines:
                    tradeline["credit_bureau"] = credit_bureau
                tradelines.extend(table_tradelines)
        
        # Use Gemini for text processing
        if text.strip():
            gemini_processor = GeminiProcessor()
            gemini_tradelines = await gemini_processor.extract_tradelines(text)
            
            # Enhance Gemini results
            for tradeline in gemini_tradelines:
                if isinstance(tradeline, dict):
                    tradeline["credit_bureau"] = credit_bureau
            
            tradelines.extend(gemini_tradelines)
        
        # Smart deduplication
        unique_tradelines = self._smart_deduplicate_tradelines(tradelines)
        
        self.logger.info(f"📊 Final result: {len(unique_tradelines)} unique tradelines")
        return unique_tradelines
    
    def _smart_deduplicate_tradelines(self, tradelines: List[Dict]) -> List[Dict]:
        """Enhanced deduplication using creditor + clean account number + date + credit bureau"""
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
                self.logger.debug(f"✅ Added unique tradeline: {creditor_name} {raw_account_number}")
            else:
                self.logger.debug(f"🔄 Duplicate found, skipping: {creditor_name} {raw_account_number}")
        
        # Log deduplication statistics
        total_removed = len(valid_tradelines) - len(unique_tradelines)
        self.logger.info(f"🧹 Smart deduplication complete:")
        self.logger.info(f"   📊 Started with {len(tradelines)} tradelines")
        self.logger.info(f"   🚫 Filtered {invalid_count} without account numbers")  
        self.logger.info(f"   🔄 Removed {total_removed} duplicates")
        self.logger.info(f"   ✅ Final count: {len(unique_tradelines)} unique tradelines")
        
        return unique_tradelines

    def _extract_tradelines_from_table(self, table: Dict[str, Any]) -> List[Dict[str, Any]]:
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
            
            logger.debug(f"Extracted {len(tradelines)} tradelines from table with {len(rows)} rows")
            return tradelines
            
        except Exception as e:
            self.logger.error(f"Failed to extract tradelines from table: {str(e)}")
            return []

    async def _expensive_fallback(self, pdf_path: str, start_time: float) -> Dict[str, Any]:
        """Expensive Document AI fallback when free methods fail"""
        self.processing_stats['document_ai_fallback'] += 1
        
        if not self.document_ai_client:
            self.cost_logger.error("FALLBACK_FAILED: Document AI not configured")
            return {'success': False, 'error': 'No fallback available'}
        
        try:
            # Use Document AI for processing
            with open(pdf_path, "rb") as pdf_file:
                pdf_content = pdf_file.read()
            
            text, tables = await self._process_single_document(pdf_content)
            tradelines = await self._parse_with_structured_parser(text, tables)
            
            processing_time = asyncio.get_event_loop().time() - start_time
            estimated_cost = 0.05  # Rough estimate
            
            self.cost_logger.info(f"DOCUMENT_AI_FALLBACK: "
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

    async def _process_single_document(self, pdf_content: bytes) -> Tuple[str, List[Dict]]:
        """Process single PDF document with Document AI"""
        def _sync_process():
            raw_document = documentai.RawDocument(
                content=pdf_content,
                mime_type="application/pdf"
            )
            
            name = self.document_ai_client.processor_path(
                self.project_id, self.location, self.processor_id
            )
            request = documentai.ProcessRequest(name=name, raw_document=raw_document)
            
            result = self.document_ai_client.process_document(request=request)
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
    
    def _extract_table_data(self, table, full_text: str) -> Dict[str, Any]:
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

    # Legacy compatibility methods
    def extract_text_and_tables(self, pdf_path: str) -> Tuple[str, List[Dict]]:
        """Legacy method - simplified synchronous version"""
        try:
            if not PDFPLUMBER_AVAILABLE:
                return "", []
            
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
            
            return text_content, tables
            
        except Exception as e:
            self.logger.error(f"Legacy extraction failed: {str(e)}")
            return '', []

    def extract_text(self, pdf_path: str) -> str:
        """Extract text only - legacy compatibility method"""
        text, _ = self.extract_text_and_tables(pdf_path)
        return text

    async def extract_structured_tradelines(self, pdf_path: str) -> List[Dict]:
        """Extract tradelines - simplified synchronous version"""
        try:
            # Extract text synchronously
            text, tables = self.extract_text_and_tables(pdf_path)
            
            # Use Gemini processor for tradeline extraction
            if text:
                gemini_processor = GeminiProcessor()
                tradelines = await gemini_processor.extract_tradelines(text)
                return tradelines
            
            return []
            
        except Exception as e:
            self.logger.error(f"Legacy tradeline extraction failed: {str(e)}")
            return []