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
    # Note: logger not yet configured at this point

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

# Suppress pdfminer debug logs
logging.getLogger('pdfminer').setLevel(logging.WARNING)
logging.getLogger('pdfminer.psparser').setLevel(logging.WARNING)
logging.getLogger('pdfminer.pdfinterp').setLevel(logging.WARNING)
logging.getLogger('pdfminer.converter').setLevel(logging.WARNING)
logging.getLogger('pdfminer.pdfdocument').setLevel(logging.WARNING)
logging.getLogger('pdfminer.pdfpage').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
app = FastAPI(title="Credit Report Processor", debug=True)

# Initialize background job processor
from services.background_jobs import job_processor

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await job_processor.start()
    logger.info("🚀 Background job processor started")

@app.on_event("shutdown")  
async def shutdown_event():
    """Cleanup on shutdown"""
    await job_processor.stop()
    logger.info("🛑 Background job processor stopped")

# Note: CORS is configured later in the file with more permissive settings for development

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
    if not date_str:
        return None
    
    # Convert to string and strip safely
    date_str = str(date_str).strip()
    if not date_str:
        return None
    
    # Pre-validation: Skip obviously invalid date strings
    # Skip strings with invalid patterns that look like reference numbers
    if re.match(r'^\d{2,}-\d+(-\d+)?$', date_str):
        parts = date_str.split('-')
        if len(parts) >= 2:
            try:
                first_part = int(parts[0])
                second_part = int(parts[1])
                # If first part > 12 (invalid month) or second part > 59 (likely reference), skip
                if first_part > 12 or second_part > 59:
                    return None
                # Additional check for 4+ digit numbers in first position (likely years in wrong position)
                if first_part > 31:
                    return None
            except ValueError:
                return None
    
    try:
        # If already in ISO format, validate and return
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            datetime.strptime(date_str, '%Y-%m-%d')
            return date_str
        
        # Try MM/DD/YYYY format (most common)
        if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_str):
            parsed_date = datetime.strptime(date_str, '%m/%d/%Y').date()
            return parsed_date.isoformat()  # Returns YYYY-MM-DD
        
        # Try MM/YYYY format (common in credit reports)
        if re.match(r'^\d{1,2}/\d{4}$', date_str):
            parsed_date = datetime.strptime(f"{date_str}/01", '%m/%Y/%d').date()  # Default to 1st of month
            return parsed_date.isoformat()  # Returns YYYY-MM-DD
        
        # Try other common formats
        formats = ['%m-%d-%Y', '%Y/%m/%d', '%d/%m/%Y']
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt).date()
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
        gemini_model = genai.GenerativeModel('gemini-2.5-flash')
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

# CORS configuration for development - allows frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",    # React default
        "http://127.0.0.1:3000", 
        "http://localhost:5173",    # Vite default
        "http://127.0.0.1:5173",
        "http://localhost:8080",    # Other common ports
        "http://127.0.0.1:8080",
        "http://localhost:4173",    # Vite preview
        "http://127.0.0.1:4173"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
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

class LegacyCreditReportProcessor:
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
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        
        for i, chunk in enumerate(chunks):
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

    async def _parse_with_structured_parser(self, text: str, tables: list) -> list:
        """Parse extracted text and tables into tradelines with enhanced data extraction"""
        import asyncio
        
        tradelines = []
        
        # Detect credit bureau from text
        credit_bureau = detect_credit_bureau(text)
        
        # Section-aware processing: Detect different credit report sections
        sections = self._detect_credit_report_sections(text)
        self.logger.info(f"📋 Detected {len(sections)} credit report sections: {list(sections.keys())}")
        
        # Try table parsing first if tables are available
        if tables:
            self.logger.info(f"📊 Processing {len(tables)} tables for tradeline extraction")
            for table in tables:
                table_tradelines = self._extract_tradelines_from_table(table)
                # Enhance each tradeline with credit bureau and missing data
                for tradeline in table_tradelines:
                    tradeline["credit_bureau"] = credit_bureau
                    # Try to extract missing date_opened from text
                    if not tradeline.get("date_opened"):
                        tradeline["date_opened"] = self._extract_date_from_text(text, tradeline.get("creditor_name", ""))
                tradelines.extend(table_tradelines)
        
        # Use Gemini for text processing - process each section for comprehensive extraction
        gemini_processor = GeminiProcessor()
        
        if sections:
            # Process each section separately to ensure comprehensive coverage
            for section_name, section_text in sections.items():
                if len(section_text.strip()) > 200:  # Only process substantial sections
                    self.logger.info(f"🔍 Processing section: {section_name} ({len(section_text)} chars)")
                    section_tradelines = gemini_processor.extract_tradelines(section_text)
                    
                    # Enhance section results
                    for tradeline in section_tradelines:
                        if isinstance(tradeline, dict):
                            tradeline["credit_bureau"] = credit_bureau
                            tradeline["source_section"] = section_name  # Track which section it came from
                            if not tradeline.get("date_opened"):
                                tradeline["date_opened"] = self._extract_date_from_text(section_text, tradeline.get("creditor_name", ""))
                    
                    tradelines.extend(section_tradelines)
                    self.logger.info(f"✅ Section {section_name}: extracted {len(section_tradelines)} tradelines")
        
        # Fallback: process entire text if no sections detected or no tradelines found
        if not tradelines and text.strip():
            self.logger.info("🔄 No sections detected or no tradelines found, processing entire text")
            gemini_tradelines = gemini_processor.extract_tradelines(text)
            # Enhance Gemini results
            for tradeline in gemini_tradelines:
                if isinstance(tradeline, dict):
                    tradeline["credit_bureau"] = credit_bureau
                    if not tradeline.get("date_opened"):
                        tradeline["date_opened"] = self._extract_date_from_text(text, tradeline.get("creditor_name", ""))
            tradelines.extend(gemini_tradelines)
        
        # Universal date recovery for missing dates (do this BEFORE deduplication)
        tradelines = await self._recover_missing_dates(tradelines, text)
        
        # Smart deduplication with enhanced criteria
        unique_tradelines = self._smart_deduplicate_tradelines(tradelines)
        
        self.logger.info(f"📊 Final result: {len(unique_tradelines)} unique tradelines (removed {len(tradelines) - len(unique_tradelines)} duplicates)")
        return unique_tradelines
    
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
                            normalized_date = normalize_date_for_postgres(date_str)
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
                                normalized_date = normalize_date_for_postgres(date_str)
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
                            normalized_date = normalize_date_for_postgres(date_str)
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
                clean_account_number = re.sub(r'[*.\-\s]', '', raw_account_number).upper()
                
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
        
        if not self.document_ai_client:
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
        
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _sync_process)

    # Keep existing methods for compatibility
    def extract_text_and_tables(self, pdf_path: str) -> tuple[str, list]:
        """Legacy method - simplified synchronous version"""
        try:
            # Use synchronous extraction to avoid async issues
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
            
            return text_content, tables
            
        except Exception as e:
            self.logger.error(f"Legacy extraction failed: {str(e)}")
            return '', []

    def extract_text(self, pdf_path: str) -> str:
        """Extract text only - legacy compatibility method"""
        text, _ = self.extract_text_and_tables(pdf_path)
        return text

    def extract_structured_tradelines(self, pdf_path: str) -> list:
        """Extract tradelines - simplified synchronous version"""
        try:
            # Extract text synchronously
            text, tables = self.extract_text_and_tables(pdf_path)
            
            # Use Gemini processor for tradeline extraction
            if text:
                gemini_processor = GeminiProcessor()
                tradelines = gemini_processor.extract_tradelines(text)
                return tradelines
            
            return []
            
        except Exception as e:
            self.logger.error(f"Legacy tradeline extraction failed: {str(e)}")
            return []

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
            
            # If text is too long, process in chunks (but limit total processing time)
            if len(text) > 20000:  # Increased threshold
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
            You are analyzing a credit report section. Your job is to extract ALL tradeline information comprehensively.
            
            CRITICAL: Extract EVERY account mentioned, including both positive and negative accounts.
            
            Extract each tradeline as a JSON object with these exact fields:
            {{
                "creditor_name": "Bank/Company name (e.g., CHASE CARD, SCHOOLSFIRST FEDERAL CREDIT UNION, CAPITAL ONE)",
                "account_number": "Account number with masking (e.g., ****1234, 755678...., XXXX-XXXX-XXXX-1234)",
                "account_balance": "Current balance amount (e.g., $1,975, $808, $0 for paid accounts)",
                "credit_limit": "Credit limit or high credit amount (e.g., $2,000, $500)", 
                "monthly_payment": "Monthly payment amount (e.g., $40, $174, $0 for paid accounts)",
                "date_opened": "CRITICAL: Date account was opened - search for patterns like 'Date Opened: 01/2014', 'Opened: 12/2013', 'Since: 05/2015', or standalone dates near creditor names",
                "account_type": "Credit Card, Auto Loan, Mortgage, Installment, Personal Loan, Student Loan, Secured Card, Store Card",
                "account_status": "Current, Open, Closed, Paid Closed, Account charged off, Collection, Late, Satisfactory, etc.",
                "is_negative": true if account has problems (charged off, collection, late payments, past due), false for current/good accounts
            }}
            
            COMPREHENSIVE EXTRACTION RULES:
            
            🔍 DATE EXTRACTION (MOST IMPORTANT):
            - Search for "Date Opened:", "Opened:", "Since:", "Date Open:", patterns
            - Look for dates in MM/YYYY format (01/2014, 12/2013) or MM/DD/YYYY format
            - Check text immediately before and after each creditor name
            - Don't skip if date format is unusual - extract any reasonable date pattern
            
            📊 ACCOUNT TYPES TO FIND:
            - Credit Cards: Chase, Capital One, Discover, Amex, store cards
            - Auto Loans: Ford Credit, GM Financial, Toyota Financial, etc.
            - Mortgages: Wells Fargo, Bank of America, Quicken Loans
            - Personal/Installment Loans: OneMain, Avant, LendingClub
            - Student Loans: Great Lakes, Navient, Federal loans
            - Secured Cards: Capital One Secured, Discover Secured
            
            ✅ POSITIVE ACCOUNTS (Don't Skip These!):
            - Accounts marked "Current", "Paid as Agreed", "Satisfactory"  
            - Accounts "In Good Standing", "Open", "Never Late"
            - Closed accounts that were "Paid in Full", "Paid Closed"
            - Zero balance accounts that are current
            
            ❌ NEGATIVE ACCOUNTS:
            - "Charge Off", "Collection", "Past Due", "Late Payment"
            - "Delinquent", "Default", "Repossession" 
            
            🎯 SECTION-SPECIFIC GUIDANCE:
            - Positive sections: Focus on current, good standing accounts
            - Negative sections: Include all derogatory accounts
            - Mixed sections: Extract both positive and negative
            - Account summaries: Often contain the most complete information
            - MULTIPLE ACCOUNTS PER CREDITOR: When you see the same creditor multiple times (e.g., SCHOOLSFIRST appears 4 times), extract EACH occurrence as a separate account
            
            🔧 TECHNICAL RULES:
            - Extract partial account numbers: ****1234, XXXX-XXXX-XXXX-5678
            - Include $0 balances for paid accounts
            - Map store cards as "Credit Card" type
            - Mark closed good accounts as NOT negative (is_negative: false)
            
            EXAMPLES OF WHAT TO EXTRACT:
            ✅ "CHASE CARD ****1234 - Current, $500 balance, $2000 limit, Opened 01/2015"
            ✅ "AUTO LOAN - Ford Credit, Paid Closed, $0 balance, Opened 03/2018" 
            ✅ "DISCOVER CARD - Good Standing, $0 balance, Opened 12/2020"
            ✅ "STUDENT LOAN - Great Lakes, Current, $15000 balance, Since 09/2016"
            
            🚨 CRITICAL: If you see the SAME CREDITOR multiple times with DIFFERENT account numbers or account types, they are SEPARATE ACCOUNTS:
            ✅ "SCHOOLSFIRST - Checking Account 420973****" = Account 1
            ✅ "SCHOOLSFIRST - Savings Account 755678****" = Account 2  
            ✅ "SCHOOLSFIRST - Auto Loan 755678...." = Account 3
            ✅ "SCHOOLSFIRST - Credit Card 755678...." = Account 4
            ALL FOUR are different accounts - extract each one!
            
            Return as JSON array. Extract EVERYTHING - count every single account mention, even from the same creditor.
            
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
                    
                    # Log detailed statistics about extracted tradelines
                    positive_count = sum(1 for t in tradelines if not t.get('is_negative', False))
                    negative_count = sum(1 for t in tradelines if t.get('is_negative', False))
                    dates_count = sum(1 for t in tradelines if t.get('date_opened'))
                    
                    self.logger.info(f"✅ Parsed {len(tradelines)} tradelines from Gemini:")
                    self.logger.info(f"   📈 {positive_count} positive accounts, {negative_count} negative accounts")
                    self.logger.info(f"   📅 {dates_count} accounts with date_opened ({dates_count/max(len(tradelines), 1)*100:.1f}%)")
                    
                    # Log sample tradelines for debugging
                    for i, tradeline in enumerate(tradelines[:3]):  # Log first 3 as examples
                        creditor = tradeline.get('creditor_name', 'Unknown')
                        account = tradeline.get('account_number', 'No account')
                        date_opened = tradeline.get('date_opened', 'No date')
                        status = "NEGATIVE" if tradeline.get('is_negative') else "POSITIVE"
                        self.logger.info(f"   📋 Sample {i+1}: {creditor} | {account} | {date_opened} | {status}")
                    
                    return tradelines
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON parsing failed: {e}")
                    self.logger.error(f"Problematic JSON: {json_text[:200]}...")
                    return self._fallback_basic_parsing(text)
            else:
                self.logger.error("No JSON array found in Gemini response")
                self.logger.error(f"Full response: {response_text[:1000]}...")
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
            chunk_size = 20000  # Increased chunk size for better context
            overlap_size = 3000  # Larger overlap to prevent missing tradelines
            max_chunks = 15  # Increased limit to process more comprehensive reports
            
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
            
            # Only limit chunks if we have an excessive number (>15)
            if len(chunks) > max_chunks:
                self.logger.warning(f"⚠️ Large document with {len(chunks)} chunks, processing first {max_chunks} for performance")
                chunks = chunks[:max_chunks]
            
            self.logger.info(f"🧠 Processing {len(chunks)} overlapping chunks for comprehensive extraction")
            
            all_tradelines = []
            seen_tradelines = set()  # Track unique tradelines to avoid duplicates from overlap
            positive_count = 0
            negative_count = 0
            dates_found = 0
            
            for i, chunk in enumerate(chunks):
                try:
                    self.logger.info(f"🔍 Processing chunk {i+1}/{len(chunks)} ({len(chunk)} chars)")
                    chunk_tradelines = self._extract_tradelines_single(chunk)
                    
                    # Deduplicate based on creditor_name + account_number
                    unique_tradelines = []
                    chunk_positive = 0
                    chunk_negative = 0
                    chunk_dates = 0
                    
                    for tradeline in chunk_tradelines:
                        # Create unique identifier
                        identifier = f"{tradeline.get('creditor_name', '')}-{tradeline.get('account_number', '')}"
                        if identifier not in seen_tradelines:
                            seen_tradelines.add(identifier)
                            unique_tradelines.append(tradeline)
                            
                            # Track statistics
                            if tradeline.get('is_negative'):
                                chunk_negative += 1
                                negative_count += 1
                            else:
                                chunk_positive += 1
                                positive_count += 1
                            
                            if tradeline.get('date_opened'):
                                chunk_dates += 1
                                dates_found += 1
                    
                    all_tradelines.extend(unique_tradelines)
                    self.logger.info(f"✅ Chunk {i+1}/{len(chunks)}: {len(unique_tradelines)} unique tradelines "
                                   f"({chunk_positive} positive, {chunk_negative} negative, {chunk_dates} with dates)")
                except Exception as e:
                    self.logger.error(f"❌ Failed processing chunk {i+1}: {str(e)}")
                    continue
            
            # Log final statistics
            self.logger.info(f"📊 Chunked extraction complete: {len(all_tradelines)} total tradelines")
            self.logger.info(f"📈 Statistics: {positive_count} positive, {negative_count} negative")
            self.logger.info(f"📅 Date extraction: {dates_found}/{len(all_tradelines)} tradelines have dates "
                           f"({dates_found/max(len(all_tradelines), 1)*100:.1f}%)")
            
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


# Test endpoint for debugging
@app.post("/test-pdf")
async def test_pdf_processing(file: UploadFile = File(...)):
    """Simple test endpoint to debug PDF processing"""
    try:
        logger.info(f"🧪 Testing PDF processing: {file.filename}")
        
        # Basic file validation
        if not file.filename.lower().endswith('.pdf'):
            return {"success": False, "error": "Not a PDF file"}
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Test basic PDF reading
            import pdfplumber
            with pdfplumber.open(temp_file_path) as pdf:
                page_count = len(pdf.pages)
                if page_count > 0:
                    first_page_text = pdf.pages[0].extract_text()
                    return {
                        "success": True,
                        "page_count": page_count,
                        "first_page_preview": first_page_text[:200] if first_page_text else "No text found"
                    }
                else:
                    return {"success": False, "error": "No pages found in PDF"}
        
        except Exception as e:
            logger.error(f"❌ PDF processing test failed: {str(e)}")
            return {"success": False, "error": f"PDF processing failed: {str(e)}"}
        
        finally:
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
    except Exception as e:
        logger.error(f"❌ Test endpoint failed: {str(e)}")
        return {"success": False, "error": str(e)}

# Main processing endpoint (legacy path)
@app.post("/process-credit-report")
async def process_credit_report(
    file: UploadFile = File(...),
    user_id: str = Form(default="default-user"),
    use_background: bool = Form(default=False)
):
    """Process uploaded credit report PDF using optimal hybrid strategy"""
    return await _process_credit_report_core(file, user_id, use_background)

# Frontend API endpoint with /api prefix
@app.post("/api/process-credit-report")  
async def api_process_credit_report(
    file: UploadFile = File(...),
    user_id: str = Form(default="default-user"),
    use_background: bool = Form(default=True)  # Default to background processing for frontend
):
    """API endpoint for frontend - routes to background processing by default"""
    return await _process_credit_report_core(file, user_id, use_background)

async def _process_credit_report_core(
    file: UploadFile,
    user_id: str,
    use_background: bool = False
):
    """Process uploaded credit report PDF using optimal hybrid strategy"""
    start_time = datetime.now()
    
    try:
        logger.info(f"🚀 Starting optimal credit report processing for user: {user_id}")
        logger.info(f"📁 Uploaded file: {file.filename}, Content-Type: {file.content_type}")
        
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            logger.error(f"❌ Invalid file type: {file.filename}")
            return {
                "success": False, 
                "error": f"Invalid file type. Please upload a PDF file. Received: {file.filename}"
            }
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
            
        logger.info(f"📄 File saved to: {temp_file_path}, Size: {len(content)} bytes")
        
        # Basic PDF validation
        if len(content) < 100:
            logger.error("❌ File too small to be a valid PDF")
            return {
                "success": False, 
                "error": "File too small to be a valid PDF. Please check your file."
            }
            
        # Check PDF magic bytes
        if not content.startswith(b'%PDF'):
            logger.error("❌ File does not appear to be a valid PDF")
            return {
                "success": False, 
                "error": "File does not appear to be a valid PDF. Please check your file format."
            }
        
        # Calculate file size for routing decision
        file_size_mb = len(content) / (1024 * 1024)
        
        # Route to background processing if requested or file is large
        if use_background or file_size_mb > 2.0:
            logger.info(f"🔄 Routing {file_size_mb:.2f}MB file to background processing")
            
            try:
                from services.background_jobs import submit_pdf_processing_job, JobPriority
                
                # Submit background job
                job_id = await submit_pdf_processing_job(
                    pdf_path=temp_file_path,
                    user_id=user_id,
                    priority=JobPriority.NORMAL
                )
                
                logger.info(f"✅ Background job submitted: {job_id}")
                
                return {
                    "success": True,
                    "job_id": job_id,
                    "status": "queued",
                    "message": f"File submitted for background processing. Job ID: {job_id}",
                    "processing_method": "background_job",
                    "file_size_mb": file_size_mb,
                    "estimated_time": f"{max(2, int(file_size_mb * 2))} minutes"
                }
                
            except Exception as bg_error:
                logger.error(f"❌ Background job submission failed: {bg_error}")
                # Fall through to synchronous processing
                logger.info("🔄 Falling back to synchronous processing")
        
        try:
            # Use new optimized processor with chunking support
            logger.info("🔧 Initializing OptimizedCreditReportProcessor with chunking...")
            from services.optimized_processor import OptimizedCreditReportProcessor
            processor = OptimizedCreditReportProcessor()
            logger.info("✅ OptimizedCreditReportProcessor with chunking initialized successfully")
            
            # Calculate file size for routing decision
            file_size_mb = len(content) / (1024 * 1024)
            
            logger.info(f"📦 Processing {file_size_mb:.2f}MB file with chunking support")
            
            # Use optimized processing pipeline with chunking (extended timeout)
            logger.info("🚀 Starting optimized processing pipeline with chunking...")
            result = await processor.process_credit_report_optimized(temp_file_path)
            logger.info(f"📊 Processing result: success={result.get('success', False)}")
            
            if result['success']:
                logger.info(f"✅ Processing completed using {result['method_used']}")
                
                # Save tradelines to database if available
                tradelines = result.get('tradelines', [])
                if tradelines and supabase:
                    logger.info(f"💾 Saving {len(tradelines)} tradelines to database...")
                    try:
                        # Add user_id to each tradeline
                        for tradeline in tradelines:
                            tradeline['user_id'] = user_id
                        
                        # Insert tradelines into database
                        from utils.tradeline_normalizer import tradeline_normalizer
                        normalized_tradelines = []
                        for tradeline in tradelines:
                            try:
                                # Validate and normalize each tradeline
                                normalized = tradeline_normalizer.normalize(tradeline)
                                if normalized:
                                    normalized_tradelines.append(normalized)
                            except Exception as norm_error:
                                logger.warning(f"Failed to normalize tradeline: {norm_error}")
                                continue
                        
                        if normalized_tradelines:
                            # Batch insert
                            insert_result = supabase.table("tradelines").insert(normalized_tradelines).execute()
                            if insert_result.data:
                                logger.info(f"✅ Successfully saved {len(insert_result.data)} tradelines to database")
                            else:
                                logger.warning("⚠️ Database insert returned no data")
                        
                    except Exception as db_error:
                        logger.error(f"❌ Failed to save tradelines to database: {db_error}")
                        # Continue without failing the entire request
                
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
                    },
                    "chunking_enabled": True,
                    "performance_metrics": result.get('stats', {})
                }
            else:
                return {"success": False, "error": result.get('error', 'Processing failed')}
                
        except TimeoutError as e:
            logger.error(f"⏰ Processing timeout: {str(e)}")
            return {
                "success": False, 
                "error": f"Processing timed out after {timeout_minutes} minutes. The file may be too complex or the server may be overloaded. Please try again or contact support."
            }
        except Exception as processing_error:
            logger.error(f"❌ Processing error: {str(processing_error)}")
            logger.error(f"❌ Processing error traceback:", exc_info=True)
            return {
                "success": False, 
                "error": f"Processing failed: {str(processing_error)}"
            }
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
    except Exception as e:
        logger.error(f"❌ Processing failed: {str(e)}")
        return {"success": False, "error": str(e)}


# Job status endpoints
@app.get("/api/job/{job_id}")
async def get_job_status(job_id: str):
    """Get background job status and results"""
    try:
        from services.background_jobs import job_processor
        
        job_data = await job_processor.get_job_status(job_id)
        
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {
            "success": True,
            "job_id": job_data['job_id'],
            "status": job_data['status'],
            "progress": job_data.get('progress', 0),
            "message": job_data.get('progress_message', ''),
            "result": job_data.get('result'),
            "error": job_data.get('error'),
            "created_at": job_data['created_at'],
            "started_at": job_data.get('started_at'),
            "completed_at": job_data.get('completed_at')
        }
    except Exception as e:
        logger.error(f"❌ Failed to get job status: {str(e)}")
        return {"success": False, "error": str(e)}

@app.get("/api/jobs/{user_id}")
async def get_user_jobs(user_id: str, limit: int = 10):
    """Get user's recent processing jobs"""
    try:
        from services.background_jobs import job_processor
        
        jobs = job_processor.job_queue.get_user_jobs(user_id, limit)
        
        job_data = []
        for job in jobs:
            job_data.append({
                "job_id": job.job_id,
                "status": job.status.value,
                "progress": job.progress,
                "message": job.progress_message,
                "created_at": job.created_at.isoformat(),
                "task_name": job.task_name
            })
        
        return {
            "success": True,
            "jobs": job_data,
            "total": len(job_data)
        }
    except Exception as e:
        logger.error(f"❌ Failed to get user jobs: {str(e)}")
        return {"success": False, "error": str(e)}

@app.delete("/api/job/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a background processing job"""
    try:
        from services.background_jobs import job_processor
        
        cancelled = await job_processor.cancel_job(job_id)
        
        if cancelled:
            return {
                "success": True,
                "message": f"Job {job_id} cancelled successfully"
            }
        else:
            return {
                "success": False,
                "error": "Job cannot be cancelled (may be running or already completed)"
            }
    except Exception as e:
        logger.error(f"❌ Failed to cancel job: {str(e)}")
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
