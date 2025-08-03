"""
PDF Credit Report Processing with Document AI + Gemini fallback
Extracts tradelines and saves to Supabase
Enhanced with comprehensive debugging and error handling
"""
import os
import PyPDF2 # type: ignore
import tempfile
import logging
import re
import traceback
from typing import List, Dict, Any, Optional
import sys
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, Form, HTTPException

from fastapi.middleware.cors import CORSMiddleware # type: ignore
from pydantic import BaseModel, ValidationError # type: ignore

# Document AI imports
from google.api_core.client_options import ClientOptions # type: ignore
from google.cloud import documentai

# Gemini AI imports (with error handling)
try:
    import google.generativeai as genai # type: ignore
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False
    logger.warning("⚠️ Google Generative AI not available - install with: pip install google-generativeai")

from google.oauth2 import service_account # type: ignore

# Supabase
from supabase import create_client, Client
from datetime import datetime

# PDF Chunking
from services.pdf_chunker import PDFChunker

# Import asyncio for timeout handling
import asyncio

from dotenv import load_dotenv # type: ignore
load_dotenv()

# Add current directory to Python path for local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import utility modules
from utils.field_validator import field_validator
from utils.tradeline_normalizer import tradeline_normalizer

async def with_timeout(coro, timeout_seconds):
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.error(f"Operation timed out after {timeout_seconds} seconds")
        raise TimeoutError("Operation timed out")

# Enhanced logging setup
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
app = FastAPI(title="Credit Report Processor", debug=True)

# Environment variables with debugging
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us")
PROCESSOR_ID = os.getenv("DOCUMENT_AI_PROCESSOR_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = "https://gywohmbqohytziwsjrps.supabase.co"
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

def normalize_date_for_postgres(date_str: str) -> Optional[str]:
    """
    Ensure date_opened is in ISO format (YYYY-MM-DD) for PostgreSQL.
    Input: '04/18/2022' or other formats
    Output: '2022-04-18' or None for invalid dates
    """
    if not date_str or not date_str.strip():
        return None
    
    try:
        # If already in ISO format, validate and return
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str.strip()):
            datetime.strptime(date_str.strip(), '%Y-%m-%d')
            return date_str.strip()
        
        # Try MM/DD/YYYY format (most common)
        if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_str.strip()):
            parsed_date = datetime.strptime(date_str.strip(), '%m/%d/%Y').date()
            return parsed_date.isoformat()  # Returns YYYY-MM-DD
        
        # Try other common formats
        formats = ['%m-%d-%Y', '%Y/%m/%d', '%d/%m/%Y']
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str.strip(), fmt).date()
                return parsed_date.isoformat()
            except ValueError:
                continue
                
        logger.warning(f"⚠️ Unable to parse date format: '{date_str}'")
        return None
        
    except (ValueError, TypeError) as e:
        logger.warning(f"⚠️ Invalid date: '{date_str}' - {e}")
        return None

# Debug environment variables
logger.info(f"🔧 Environment Check:")
logger.info(f"  PROJECT_ID: {'✅ Set' if PROJECT_ID else '❌ Missing'}")
logger.info(f"  LOCATION: {LOCATION}")
logger.info(f"  PROCESSOR_ID: {'✅ Set' if PROCESSOR_ID else '❌ Missing'}")
logger.info(f"  GEMINI_API_KEY: {'✅ Set' if GEMINI_API_KEY else '❌ Missing'}")
logger.info(f"  SUPABASE_URL: {'✅ Set' if SUPABASE_URL else '❌ Missing'}")
logger.info(f"  SUPABASE_ANON_KEY: {'✅ Set' if SUPABASE_ANON_KEY else '❌ Missing'}")

# Initialize services with error handling
try:
    if SUPABASE_URL and SUPABASE_ANON_KEY:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        logger.info("✅ Supabase client initialized")
    else:
        logger.error("❌ Supabase configuration missing")
        supabase = None
except Exception as e:
    logger.error(f"❌ Supabase initialization failed: {e}")
    supabase = None

try:
    if GEMINI_API_KEY and GEMINI_AVAILABLE and genai:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("✅ Gemini model initialized")
    else:
        if not GEMINI_AVAILABLE:
            logger.warning("⚠️ Gemini not available - missing dependencies")
        elif not GEMINI_API_KEY:
            logger.error("❌ Gemini API key missing")
        gemini_model = None
except Exception as e:
    logger.error(f"❌ Gemini initialization failed: {e}")
    gemini_model = None

# Initialize Document AI client
try:
    if os.path.exists('./service-account.json'):
        credentials = service_account.Credentials.from_service_account_file('./service-account.json')
        client = documentai.DocumentProcessorServiceClient(credentials=credentials)
        logger.info("✅ Document AI client initialized with service account")
    else:
        logger.warning("⚠️ Service account file not found, using default credentials")
        client = documentai.DocumentProcessorServiceClient()
        logger.info("✅ Document AI client initialized with default credentials")
except Exception as e:
    logger.error(f"❌ Document AI initialization failed: {e}")
    client = None

# Pydantic validation schema
class TradelineSchema(BaseModel):
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

# Enhanced CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, be more specific
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

def detect_credit_bureau(text_content: str) -> str:
    """
    Detect credit bureau from PDF text content.
    Searches for: Equifax, Experian, TransUnion
    Returns the first bureau found, or "Unknown" if none detected.
    """
    if not text_content:
        return "Unknown"
    
    # Convert to lowercase for case-insensitive matching
    text_lower = text_content.lower()
    
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

class SupabaseService:
    def __init__(self):
        self.client = supabase
    
    # Insert data
    def insert_user_profile(self, user_data):
        """Insert a new user profile"""
        try:
            result = self.client.table("user_profiles").insert(user_data).execute()
            return result.data
        except Exception as e:
            print(f"Error inserting user profile: {e}")
            return None
    
    # Select data
    def get_user_profile(self, user_id):
        """Get user profile by ID"""
        try:
            result = self.client.table("user_profiles").select("*").eq("id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return None
    
    # Update data
    def update_user_profile(self, user_id, updates):
        """Update user profile"""
        try:
            result = self.client.table("user_profiles").update(updates).eq("id", user_id).execute()
            return result.data
        except Exception as e:
            print(f"Error updating user profile: {e}")
            return None
    
    # Delete data
    def delete_user_profile(self, user_id):
        """Delete user profile"""
        try:
            result = self.client.table("user_profiles").delete().eq("id", user_id).execute()
            return result.data
        except Exception as e:
            print(f"Error deleting user profile: {e}")
            return None

class OptimalCreditReportProcessor:
    """
    Processes credit reports using the most cost-effective method
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
        
        # Initialize Document AI client for fallback
        self.document_ai_client = None
        if PROJECT_ID and PROCESSOR_ID:
            try:
                opts = ClientOptions(api_endpoint=f"{LOCATION}-documentai.googleapis.com")
                self.document_ai_client = documentai.DocumentProcessorServiceClient(
                    client_options=opts, 
                    credentials=credentials if 'credentials' in globals() else None
                )
                logger.info(f"✅ Document AI fallback configured for {LOCATION}")
            except Exception as e:
                logger.warning(f"⚠️ Document AI fallback not available: {e}")
        
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
    
    async def process_credit_report_optimal(self, pdf_path: str) -> dict:
        """
        Optimal processing pipeline with cost tracking
        """
        import asyncio
        start_time = asyncio.get_event_loop().time()
        self.processing_stats['total_processed'] += 1
        
        # Phase 1: Free/Fast extraction (try all free methods)
        extraction_result = await self._try_free_extraction_methods(pdf_path)
        
        if extraction_result['success']:
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

    async def _try_free_extraction_methods(self, pdf_path: str) -> dict:
        """Try all free extraction methods in parallel"""
        import asyncio
        
        tasks = [
            self._extract_with_pdfplumber(pdf_path),
            self._extract_with_pymupdf(pdf_path),
            self._extract_with_ocr(pdf_path)
        ]
        
        # Run extraction methods concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Return the best result
        for i, result in enumerate(results):
            if isinstance(result, dict) and result.get('success'):
                method_names = ['pdfplumber', 'pymupdf', 'ocr']
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
        
        return await asyncio.get_event_loop().run_in_executor(None, _sync_extract)

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
        
        return await asyncio.get_event_loop().run_in_executor(None, _sync_extract)

    async def _extract_with_ocr(self, pdf_path: str) -> dict:
        """Async wrapper for OCR extraction"""
        import asyncio
        
        def _sync_extract():
            try:
                import fitz  # PyMuPDF for PDF to image conversion
                import pytesseract
                from PIL import Image
                import io
                
                text_content = ""
                
                doc = fitz.open(pdf_path)
                for page_num in range(min(len(doc), 10)):  # Limit OCR to first 10 pages for speed
                    page = doc[page_num]
                    
                    # Convert page to image
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x scale for better OCR
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))
                    
                    # OCR the image
                    page_text = pytesseract.image_to_string(img, config='--psm 6')
                    text_content += f"\n--- Page {page_num + 1} (OCR) ---\n{page_text}"
                
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
        
        return await asyncio.get_event_loop().run_in_executor(None, _sync_extract)

    def _validate_extraction_quality(self, text: str) -> bool:
        """Validate if extracted text is good enough for credit report processing"""
        if not text or len(text.strip()) < 100:
            return False
        
        # Check for credit report indicators
        text_lower = text.lower()
        credit_indicators = [
            'credit', 'account', 'balance', 'payment', 'tradeline',
            'experian', 'equifax', 'transunion', 'creditor', 'limit'
        ]
        
        found_indicators = sum(1 for indicator in credit_indicators if indicator in text_lower)
        return found_indicators >= 3  # Must have at least 3 credit-related terms

    async def _parse_with_structured_parser(self, text: str, tables: list) -> list:
        """Parse extracted text and tables into tradelines with enhanced data extraction"""
        import asyncio
        
        tradelines = []
        
        # Detect credit bureau from text
        credit_bureau = detect_credit_bureau(text)
        
        # Try table parsing first if tables are available
        if tables:
            for table in tables:
                table_tradelines = self._extract_tradelines_from_table(table)
                # Enhance each tradeline with credit bureau and missing data
                for tradeline in table_tradelines:
                    tradeline["credit_bureau"] = credit_bureau
                    # Try to extract missing date_opened from text
                    if not tradeline.get("date_opened"):
                        tradeline["date_opened"] = self._extract_date_from_text(text, tradeline.get("creditor_name", ""))
                tradelines.extend(table_tradelines)
        
        # Use Gemini for text processing if no table results or as enhancement
        if not tradelines and text.strip():
            gemini_processor = GeminiProcessor()
            gemini_tradelines = gemini_processor.extract_tradelines(text)
            # Enhance Gemini results
            for tradeline in gemini_tradelines:
                if isinstance(tradeline, dict):
                    tradeline["credit_bureau"] = credit_bureau
                    if not tradeline.get("date_opened"):
                        tradeline["date_opened"] = self._extract_date_from_text(text, tradeline.get("creditor_name", ""))
            tradelines.extend(gemini_tradelines)
        
        return tradelines
    
    def _extract_date_from_text(self, text: str, creditor_name: str) -> str:
        """Extract date_opened from text context around creditor name"""
        import re
        
        if not creditor_name or not text:
            return ""
        
        try:
            # Look for text sections containing the creditor name
            lines = text.split('\n')
            creditor_lines = []
            
            for i, line in enumerate(lines):
                if creditor_name.upper() in line.upper():
                    # Get context around the creditor mention
                    start_idx = max(0, i - 3)
                    end_idx = min(len(lines), i + 10)
                    creditor_lines.extend(lines[start_idx:end_idx])
            
            # Look for date patterns in the context
            date_patterns = [
                r'Date Opened[:\s]*(\d{2}/\d{4})',  # "Date Opened: 01/2014"
                r'Date Opened[:\s]*(\d{2}/\d{2}/\d{4})',  # "Date Opened: 01/12/2014"
                r'(\d{2}/\d{4})',  # Just "01/2014"
                r'(\d{2}/\d{2}/\d{4})',  # Just "01/12/2014"
            ]
            
            context_text = ' '.join(creditor_lines)
            
            for pattern in date_patterns:
                matches = re.findall(pattern, context_text, re.IGNORECASE)
                if matches:
                    date_str = matches[0]
                    # Normalize the date format
                    normalized_date = normalize_date_for_postgres(date_str)
                    if normalized_date:
                        return normalized_date
            
            return ""
            
        except Exception as e:
            self.logger.debug(f"Date extraction failed for {creditor_name}: {e}")
            return ""

    async def _expensive_fallback(self, pdf_path: str, start_time: float) -> dict:
        """Expensive Document AI fallback when free methods fail"""
        import asyncio
        
        self.processing_stats['document_ai_fallback'] += 1
        
        if not self.document_ai_client:
            self.cost_logger.error("FALLBACK_FAILED: Document AI not configured")
            return {'success': False, 'error': 'No fallback available'}
        
        try:
            # Use original Document AI chunking logic
            with open(pdf_path, "rb") as pdf_file:
                pdf_content = pdf_file.read()
            
            chunker = PDFChunker(chunk_size=30)
            page_count = chunker.get_pdf_page_count(pdf_content)
            
            if chunker.needs_chunking(pdf_content):
                text, tables = await self._process_with_chunking(pdf_content, chunker)
            else:
                text, tables = await self._process_single_document(pdf_content)
            
            tradelines = await self._parse_with_structured_parser(text, tables)
            
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
            
            name = self.document_ai_client.processor_path(PROJECT_ID, LOCATION, PROCESSOR_ID)
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
        
        return await asyncio.get_event_loop().run_in_executor(None, _sync_process)

    # Keep existing methods for compatibility
    def extract_text_and_tables(self, pdf_path: str) -> tuple[str, list]:
        """Legacy method - now redirects to optimal processing"""
        import asyncio
        
        # Run the async optimal processing in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self.process_credit_report_optimal(pdf_path))
            if result['success']:
                return result.get('text', ''), result.get('tables', [])
            else:
                return '', []
        finally:
            loop.close()

    def extract_text(self, pdf_path: str) -> str:
        """Extract text only - legacy compatibility method"""
        text, _ = self.extract_text_and_tables(pdf_path)
        return text

    def extract_structured_tradelines(self, pdf_path: str) -> list:
        """Extract tradelines - now uses optimal processing"""
        import asyncio
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self.process_credit_report_optimal(pdf_path))
            return result.get('tradelines', []) if result['success'] else []
        finally:
            loop.close()

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
                header_lower = header.lower().strip()
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
                        if header in tradeline and cell_value.strip():
                            tradeline[header] = cell_value.strip()
                
                # Only add if we have essential fields
                if tradeline["creditor_name"] and tradeline["account_number"]:
                    tradelines.append(tradeline)
            
            return tradelines
            
        except Exception as e:
            self.logger.error(f"Failed to extract tradelines from table: {str(e)}")
            return []


class GeminiProcessor:
    """Enhanced Gemini processor with comprehensive error handling"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.gemini_available = GEMINI_AVAILABLE and gemini_model is not None
        
        if not self.gemini_available:
            self.logger.warning("⚠️ GeminiProcessor initialized but Gemini AI not available")
    
    def extract_tradelines(self, text: str) -> list:
        """Extract tradelines using Gemini AI with comprehensive error handling"""
        try:
            self.logger.info(f"🧠 Starting Gemini tradeline extraction from {len(text)} characters")
            
            # Check if Gemini is available
            if not self.gemini_available:
                self.logger.warning("⚠️ Gemini not available - using fallback basic parsing")
                return self._fallback_basic_parsing(text)
            
            if not gemini_model:
                self.logger.error("❌ Gemini model not initialized")
                return self._fallback_basic_parsing(text)
            
            # Check if genai module is available
            if not GEMINI_AVAILABLE or not genai:
                self.logger.error("❌ Google Generative AI module not available")
                return self._fallback_basic_parsing(text)
            
            # If text is too long, process in chunks
            if len(text) > 15000:
                return self._extract_tradelines_chunked(text)
            else:
                return self._extract_tradelines_single(text)
                
        except ImportError as e:
            self.logger.error(f"❌ Import error in Gemini processing: {str(e)}")
            return self._fallback_basic_parsing(text)
        except Exception as e:
            self.logger.error(f"❌ Gemini processing failed: {str(e)}")
            return self._fallback_basic_parsing(text)
    
    def _extract_tradelines_single(self, text: str) -> list:
        """Extract tradelines from a single text chunk with enhanced error handling"""
        try:
            self.logger.info("🧠 GEMINI EXTRACTION - INPUT DATA:")
            self.logger.info(f"  Text length: {len(text)} characters")
            
            # Double-check Gemini availability
            if not self.gemini_available or not gemini_model:
                self.logger.warning("⚠️ Gemini not available during single extraction")
                return self._fallback_basic_parsing(text)
            
            prompt = f"""
            You are analyzing a credit report. Extract credit tradeline information carefully.
            
            Extract each tradeline as a JSON object with these exact fields:
            {{
                "creditor_name": "Bank/Company name (e.g., CHASE CARD, SCHOOLSFIRST FEDERAL CREDIT UNION)",
                "account_number": "Account number with masking (e.g., ****1234, 755678....)",
                "account_balance": "Current balance amount (e.g., $1,975, $808)",
                "credit_limit": "Credit limit or high credit amount (e.g., $2,000, $500)", 
                "monthly_payment": "Monthly payment amount (e.g., $40, $174)",
                "date_opened": "REQUIRED: Date account was opened (find MM/YYYY or MM/DD/YYYY format like 01/2014, 05/2014, 12/2013)",
                "account_type": "Credit Card, Auto Loan, Mortgage, Installment, Unsecured, Secured Card",
                "account_status": "Open, Closed, Account charged off, Paid Closed, Redeemed repossession, etc.",
                "is_negative": true if account status indicates problems like charged off or past due
            }}
            
            IMPORTANT EXTRACTION RULES:
            - Look for "Date Opened:" followed by dates (MM/YYYY or MM/DD/YYYY)
            - Extract account numbers that may be partially masked (****1234, 755678....)
            - Include dollar signs in amounts ($1,975 not 1975)
            - Identify negative accounts (charged off, past due, collection, etc.)
            - Map account types consistently (Credit Card, Auto Loan, Mortgage, etc.)
            - SCAN ALL TEXT: Tradelines may appear in multiple sections (account summaries, payment history, potentially negative items, accounts in good standing, etc.)
            - LOOK FOR AUTO LOANS: Pay special attention to auto loans, installment loans, and closed/paid accounts
            - EXTRACT ALL ACCOUNT TYPES: Credit cards, auto loans, mortgages, installment loans, secured cards, unsecured loans
            - DON'T SKIP: Process ALL creditor mentions even if formatting is different or status is complex (like "redeemed repossession")
            - MULTIPLE SECTIONS: Same creditor may have multiple different account types
            
            Return as JSON array. If no tradelines found, return empty array [].
            
            TEXT TO ANALYZE:
            {text}
            """
            
            # Generate response using Gemini with error handling
            try:
                response = gemini_model.generate_content(prompt)
            except Exception as api_error:
                self.logger.error(f"❌ Gemini API call failed: {str(api_error)}")
                return self._fallback_basic_parsing(text)
            
            if not response or not response.text:
                self.logger.error("Empty response from Gemini")
                return self._fallback_basic_parsing(text)
            
            response_text = response.text.strip()
            self.logger.info(f"🧠 Gemini raw response: {response_text[:500]}...")
            
            # Parse JSON response
            import json
            import re
            
            # Clean up response text and extract JSON
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)
                try:
                    tradelines = json.loads(json_text)
                    self.logger.info(f"✅ Parsed {len(tradelines)} tradelines from Gemini")
                    return tradelines
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON parsing failed: {e}")
                    return self._fallback_basic_parsing(text)
            else:
                self.logger.error("No JSON array found in Gemini response")
                return self._fallback_basic_parsing(text)
                
        except ImportError as e:
            self.logger.error(f"❌ Import error during Gemini processing: {str(e)}")
            return self._fallback_basic_parsing(text)
        except Exception as e:
            self.logger.error(f"❌ Failed to process Gemini response: {str(e)}")
            return self._fallback_basic_parsing(text)

    def _extract_tradelines_chunked(self, text: str) -> list:
        """Extract tradelines from large text by chunking with overlap"""
        try:
            chunks = []
            chunk_size = 10000
            overlap_size = 2000  # 20% overlap to prevent missing tradelines at boundaries
            
            # Create overlapping chunks
            for i in range(0, len(text), chunk_size - overlap_size):
                end_pos = min(i + chunk_size, len(text))
                chunk = text[i:end_pos]
                
                # Only add chunk if it has substantial content
                if len(chunk.strip()) > 500:
                    chunks.append(chunk)
                
                # Stop if we've reached the end
                if end_pos >= len(text):
                    break
            
            self.logger.info(f"🧠 Processing {len(chunks)} overlapping chunks for large document")
            
            all_tradelines = []
            seen_tradelines = set()  # Track unique tradelines to avoid duplicates from overlap
            
            for i, chunk in enumerate(chunks):
                try:
                    chunk_tradelines = self._extract_tradelines_single(chunk)
                    
                    # Deduplicate based on creditor_name + account_number
                    unique_tradelines = []
                    for tradeline in chunk_tradelines:
                        # Create unique identifier
                        identifier = f"{tradeline.get('creditor_name', '')}-{tradeline.get('account_number', '')}"
                        if identifier not in seen_tradelines:
                            seen_tradelines.add(identifier)
                            unique_tradelines.append(tradeline)
                    
                    all_tradelines.extend(unique_tradelines)
                    self.logger.info(f"✅ Chunk {i+1}/{len(chunks)}: {len(unique_tradelines)} unique tradelines")
                except Exception as e:
                    self.logger.error(f"❌ Failed processing chunk {i+1}: {str(e)}")
                    continue
            
            return all_tradelines
            
        except Exception as e:
            self.logger.error(f"❌ Chunked processing failed: {str(e)}")
            return self._fallback_basic_parsing(text)
    
    def _fallback_basic_parsing(self, text: str) -> list:
        """Fallback basic parsing when Gemini is not available"""
        try:
            self.logger.info("🔧 Using basic parsing fallback (Gemini unavailable)")
            
            # Basic pattern matching for common credit report patterns
            tradelines = []
            lines = text.split('\n')
            
            current_tradeline = {}
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for creditor names (basic heuristic)
                if any(keyword in line.lower() for keyword in ['bank', 'credit', 'card', 'loan', 'mortgage']):
                    if 'account' in line.lower() or 'acct' in line.lower():
                        # Try to extract basic info
                        words = line.split()
                        if len(words) >= 2:
                            current_tradeline = {
                                "creditor_name": ' '.join(words[:2]),
                                "account_number": "Unknown",
                                "account_balance": "",
                                "credit_limit": "",
                                "monthly_payment": "",
                                "date_opened": "",
                                "account_type": "Unknown",
                                "account_status": "Unknown",
                                "is_negative": False
                            }
                            tradelines.append(current_tradeline)
            
            self.logger.info(f"🔧 Basic parsing found {len(tradelines)} potential tradelines")
            return tradelines[:10]  # Limit to 10 to avoid noise
            
        except Exception as e:
            self.logger.error(f"❌ Basic parsing fallback failed: {str(e)}")
            return []


# Processing functions for credit reports

def parse_tradelines_basic(text: str) -> list:
    """Parse tradelines using basic text pattern matching"""
    try:
        logger.info("🔧 BASIC PARSING - INPUT DATA:")
        logger.info(f"  Text length: {len(text)} characters")
        
        # Basic pattern matching logic here
        tradelines = []
        # TODO: Implement basic parsing logic
        
        return tradelines
        
    except Exception as e:
        logger.error(f"❌ Basic parsing failed: {str(e)}")
        return []


# Credit bureau detection function
def detect_credit_bureau(text: str) -> str:
    """Detect credit bureau from extracted text"""
    text_lower = text.lower()
    
    if 'experian' in text_lower or 'experion' in text_lower:
        return 'Experian'
    elif 'equifax' in text_lower or 'equifx' in text_lower:
        return 'Equifax'
    elif 'transunion' in text_lower or 'trans union' in text_lower:
        return 'TransUnion'
    else:
        return 'Unknown'


# Main processing endpoint
@app.post("/process-credit-report")
async def process_credit_report(
    file: UploadFile = File(...),
    user_id: str = Form(default="default-user")
):
    """Process uploaded credit report PDF using optimal hybrid strategy"""
    start_time = datetime.now()
    
    try:
        logger.info(f"🚀 Starting optimal credit report processing for user: {user_id}")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Initialize optimal processor
            processor = OptimalCreditReportProcessor()
            
            # Use optimal processing pipeline
            result = await processor.process_credit_report_optimal(temp_file_path)
            
            if result['success']:
                logger.info(f"✅ Processing completed using {result['method_used']}")
                
                return {
                    "success": True,
                    "message": f"Successfully processed {len(result['tradelines'])} tradelines",
                    "tradelines_found": len(result['tradelines']),
                    "tradelines": result['tradelines'],
                    "processing_method": result['method_used'],
                    "cost_estimate": result['cost_estimate'],
                    "processing_time": {
                        "start_time": start_time.isoformat(),
                        "end_time": datetime.now().isoformat(),
                        "duration_seconds": result['processing_time'],
                        "duration_formatted": f"{result['processing_time']:.2f}s"
                    }
                }
            else:
                return {"success": False, "error": result.get('error', 'Processing failed')}
                
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
    except Exception as e:
        logger.error(f"❌ Processing failed: {str(e)}")
        return {"success": False, "error": str(e)}


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "document_ai": "configured" if PROJECT_ID and PROCESSOR_ID else "not_configured",
            "gemini": "configured" if gemini_model else "not_configured",
            "supabase": "configured" if supabase else "not_configured"
        }
    }
