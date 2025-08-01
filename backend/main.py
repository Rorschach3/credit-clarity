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

# Gemini AI imports
import google.generativeai as genai # type: ignore
from google.oauth2 import service_account # type: ignore

# Supabase
from supabase import create_client, Client
from datetime import datetime

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
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("✅ Gemini model initialized")
    else:
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

class DocumentAIProcessor:
    def __init__(self):
        if not PROJECT_ID or not PROCESSOR_ID:
            logger.error("❌ Document AI configuration incomplete")
            return
        
        opts = ClientOptions(api_endpoint=f"{LOCATION}-documentai.googleapis.com")
        self.client = documentai.DocumentProcessorServiceClient(
            client_options=opts, 
            credentials=credentials if 'credentials' in globals() else None
        )
        logger.info(f"✅ Document AI processor configured for {LOCATION}")
    
    def extract_text_and_entities(self, pdf_path: str) -> tuple[str, list]:
        """Extract both text and structured entities from PDF using Document AI Form Parser"""
        try:
            logger.info(f"📄 Starting Document AI form parsing from {pdf_path}")
            
            with open(pdf_path, "rb") as pdf_file:
                pdf_content = pdf_file.read()
            
            logger.info(f"📦 PDF content size: {len(pdf_content)} bytes")
            
            raw_document = documentai.RawDocument(
                content=pdf_content,
                mime_type="application/pdf"
            )
            
            name = self.client.processor_path(PROJECT_ID, LOCATION, PROCESSOR_ID)
            logger.info(f"🔗 Using Form Parser processor: {name}")
            
            request = documentai.ProcessRequest(name=name, raw_document=raw_document)
            
            logger.info("🚀 Sending request to Document AI Form Parser...")
            logger.info(f"📊 Request details - Document size: {len(pdf_content)} bytes, Processor: {name}")
            
            # Use asyncio timeout instead of signal for cross-platform compatibility
            try:
                result = self.client.process_document(request=request)
                logger.info("✅ Document AI request completed successfully")
            except Exception as e:
                logger.error(f"❌ Document AI error: {e}")
                raise
            
            document = result.document
            extracted_text = document.text
            logger.info(f"✅ Document AI extracted {len(extracted_text)} characters of text")
            
            # Extract form fields (key-value pairs)
            form_fields = []
            for page in document.pages:
                for form_field in page.form_fields:
                    field_name = ""
                    field_value = ""
                    
                    if form_field.field_name:
                        field_name = self._get_text(form_field.field_name, extracted_text)
                    if form_field.field_value:
                        field_value = self._get_text(form_field.field_value, extracted_text)
                    
                    if field_name and field_value:
                        form_fields.append({
                            "field_name": field_name.strip(),
                            "field_value": field_value.strip()
                        })
            
            logger.info(f"📋 Extracted {len(form_fields)} form fields")
            for field in form_fields[:5]:  # Log first 5 fields for debugging
                logger.debug(f"  Field: '{field['field_name']}' = '{field['field_value']}'")
            
            return extracted_text, form_fields
            
        except Exception as e:
            logger.error(f"❌ Document AI form parsing failed: {str(e)}")
            logger.error(f"📍 Traceback: {traceback.format_exc()}")
            raise
    
    def _get_text(self, layout, full_text: str) -> str:
        """Extract text from Document AI layout object"""
        if not layout:
            return ""
        
        # Handle Layout objects that have text_anchor property
        if hasattr(layout, 'text_anchor') and layout.text_anchor:
            text_anchor = layout.text_anchor
            if hasattr(text_anchor, 'text_segments') and text_anchor.text_segments:
                text_segments = []
                for segment in text_anchor.text_segments:
                    start_index = int(segment.start_index) if segment.start_index else 0
                    end_index = int(segment.end_index) if segment.end_index else len(full_text)
                    text_segments.append(full_text[start_index:end_index])
                return "".join(text_segments)
        
        # Fallback: if the layout object has text_segments directly (older API structure)
        if hasattr(layout, 'text_segments') and layout.text_segments:
            text_segments = []
            for segment in layout.text_segments:
                start_index = int(segment.start_index) if segment.start_index else 0
                end_index = int(segment.end_index) if segment.end_index else len(full_text)
                text_segments.append(full_text[start_index:end_index])
            return "".join(text_segments)
        
        return ""
    
    def extract_text(self, pdf_path: str) -> str:
        """Extract text from PDF using Document AI (backwards compatibility)"""
        try:
            # Use the new method but only return text
            text, _ = self.extract_text_and_entities(pdf_path)
            return text
            
        except Exception as e:
            logger.error(f"❌ Document AI failed: {str(e)}")
            logger.error(f"📍 Traceback: {traceback.format_exc()}")
            raise
    
    def extract_structured_tradelines(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract tradelines using Document AI form fields for better accuracy"""
        try:
            text, form_fields = self.extract_text_and_entities(pdf_path)
            logger.info(f"🔍 Processing {len(form_fields)} form fields for tradeline extraction")
            
            # 📊 LOG: Form fields data
            logger.info("📋 EXTRACTED FORM FIELDS:")
            for i, field in enumerate(form_fields[:10]):  # Log first 10 fields
                logger.info(f"  Field {i+1}: '{field['field_name']}' = '{field['field_value']}'")
            if len(form_fields) > 10:
                logger.info(f"  ... and {len(form_fields) - 10} more fields")
            
            # Group form fields by proximity and likely tradeline groupings
            tradelines = []
            field_groups = self._group_form_fields_by_tradeline(form_fields)
            
            # 📊 LOG: Field groupings
            logger.info(f"🗂️ GROUPED INTO {len(field_groups)} POTENTIAL TRADELINES:")
            for i, group in enumerate(field_groups):
                logger.info(f"  Group {i+1}: {len(group)} fields")
                for field in group[:3]:  # Log first 3 fields per group
                    logger.info(f"    - '{field['field_name']}' = '{field['field_value']}'")
                if len(group) > 3:
                    logger.info(f"    ... and {len(group) - 3} more fields")
            
            for i, group in enumerate(field_groups):
                logger.info(f"🔄 PROCESSING GROUP {i+1}/{len(field_groups)}:")
                tradeline = self._extract_tradeline_from_field_group(group)
                
                # 📊 LOG: Extracted tradeline data
                if tradeline:
                    logger.info(f"  📄 EXTRACTED TRADELINE {i+1}:")
                    logger.info(f"    Creditor: '{tradeline.get('creditor_name', 'N/A')}'")
                    logger.info(f"    Credit Limit: '{tradeline.get('credit_limit', 'N/A')}'")
                    logger.info(f"    Monthly Payment: '{tradeline.get('monthly_payment', 'N/A')}'")
                    logger.info(f"    Balance: '{tradeline.get('account_balance', 'N/A')}'")
                    logger.info(f"    Account Type: '{tradeline.get('account_type', 'N/A')}'")
                    logger.info(f"    Account Status: '{tradeline.get('account_status', 'N/A')}'")
                    
                    if tradeline.get("creditor_name"):
                        tradelines.append(tradeline)
                        logger.info(f"  ✅ ADDED to tradelines list")
                    else:
                        logger.info(f"  ❌ SKIPPED - no creditor name")
                else:
                    logger.info(f"  ❌ FAILED to extract tradeline from group {i+1}")
            
            logger.info(f"✅ Document AI structured extraction found {len(tradelines)} tradelines")
            return tradelines
            
        except Exception as e:
            logger.error(f"❌ Document AI structured extraction failed: {str(e)}")
            return []
    
    def _group_form_fields_by_tradeline(self, form_fields: List[Dict]) -> List[List[Dict]]:
        """Group form fields that likely belong to the same tradeline"""
        groups = []
        current_group = []
        
        # Simple grouping based on creditor names and field patterns
        for field in form_fields:
            field_name = field["field_name"].lower()
            field_value = field["field_value"]
            
            # Check if this might be a new tradeline (creditor name)
            is_creditor = any(keyword in field_name for keyword in ["name", "bank", "creditor", "lender"])
            is_company = any(keyword in field_value.upper() for keyword in ["BANK", "CREDIT", "FINANCIAL", "CAPITAL", "CHASE", "AMEX"])
            
            if (is_creditor or is_company) and current_group:
                # Start new group
                groups.append(current_group)
                current_group = [field]
            else:
                current_group.append(field)
        
        if current_group:
            groups.append(current_group)
        
        logger.debug(f"📊 Grouped {len(form_fields)} fields into {len(groups)} potential tradelines")
        return groups
    
    def _extract_tradeline_from_field_group(self, field_group: List[Dict]) -> Dict[str, Any]:
        """Extract tradeline data from a group of related form fields"""
        tradeline = {
            "creditor_name": "",
            "account_balance": "",
            "credit_limit": "",
            "monthly_payment": "",
            "account_number": "",
            "date_opened": "",
            "account_type": "Credit Card",
            "account_status": "Open",
            "credit_bureau": "",
            "is_negative": False,
            "dispute_count": 0
        }
        
        # First pass: collect potential creditor names and account numbers
        potential_creditors = []
        potential_account_numbers = []
        
        for field in field_group:
            field_name = field["field_name"].lower()
            field_value = field["field_value"].strip()
            
            if not field_value:
                continue
            
            # Enhanced creditor name detection
            if any(keyword in field_name for keyword in ["name", "creditor", "lender", "bank", "company"]):
                potential_creditors.append(field_value)
            elif self._is_likely_creditor_name(field_value):
                potential_creditors.append(field_value)
            
            # Enhanced account number detection
            if any(keyword in field_name for keyword in ["account", "number", "acct", "card"]):
                potential_account_numbers.append(field_value)
            elif self._is_likely_account_number(field_value):
                potential_account_numbers.append(field_value)
            
            # Standard field mapping
            if any(keyword in field_name for keyword in ["high credit", "credit limit", "limit", "maximum", "credit line"]):
                if self._is_currency_format(field_value):
                    tradeline["credit_limit"] = field_value
            
            elif any(keyword in field_name for keyword in ["payment", "monthly", "minimum", "pay amt"]):
                if self._is_currency_format(field_value):
                    tradeline["monthly_payment"] = field_value
            
            elif any(keyword in field_name for keyword in ["balance", "current", "amount owed"]):
                if self._is_currency_format(field_value):
                    tradeline["account_balance"] = field_value
            
            elif any(keyword in field_name for keyword in ["date", "opened", "start", "open"]):
                if self._is_likely_date(field_value):
                    tradeline["date_opened"] = field_value
            
            elif any(keyword in field_name for keyword in ["type", "kind", "category"]):
                account_type = self._extract_account_type_basic(field_value, tradeline["creditor_name"])
                if account_type:
                    tradeline["account_type"] = account_type.replace("_", " ").title()
            
            elif any(keyword in field_name for keyword in ["status", "condition", "state"]):
                tradeline["account_status"] = field_value
        
        # Select best creditor name (prefer actual company names over numeric codes)
        if potential_creditors:
            tradeline["creditor_name"] = self._select_best_creditor_name(potential_creditors)
        
        # Select best account number (prefer masked numbers)
        if potential_account_numbers:
            tradeline["account_number"] = self._select_best_account_number(potential_account_numbers)
        
        return tradeline
    
    def _is_likely_creditor_name(self, value: str) -> bool:
        """Check if a value is likely a creditor name (not a numeric code)"""
        if not value or len(value) < 3:
            return False
        
        # Skip purely numeric values (these are likely reference codes)
        if value.isdigit():
            return False
        
        # Look for company indicators
        company_indicators = ["bank", "credit", "financial", "capital", "corp", "inc", "llc", "card", "fund", "union"]
        value_lower = value.lower()
        
        # If contains company indicators, likely a creditor
        if any(indicator in value_lower for indicator in company_indicators):
            return True
        
        # If contains letters and has reasonable length, might be creditor
        has_letters = any(c.isalpha() for c in value)
        reasonable_length = 4 <= len(value) <= 50
        
        return has_letters and reasonable_length
    
    def _is_likely_account_number(self, value: str) -> bool:
        """Check if a value is likely an account number"""
        if not value or len(value) < 4:
            return False
        
        # Look for masked account number patterns
        masked_patterns = [
            r'\*+\d{4}',           # ****1234
            r'\d{4}\*+',           # 1234****
            r'x+\d{4}',            # xxxx1234
            r'\d{4}x+',            # 1234xxxx
            r'\*{4}.*\d{4}',       # ****-1234 or similar
            r'\d{4}.*\*{4}',       # 1234-**** or similar
        ]
        
        for pattern in masked_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        
        # Look for account-like numeric patterns (but not phone numbers or dates)
        if re.match(r'^\d{8,20}$', value):  # 8-20 digit numbers
            return True
        
        return False
    
    def _is_likely_date(self, value: str) -> bool:
        """Check if a value is likely a date"""
        if not value:
            return False
        
        # Common date patterns
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',     # MM/DD/YYYY
            r'\d{1,2}-\d{1,2}-\d{4}',     # MM-DD-YYYY
            r'\d{4}-\d{1,2}-\d{1,2}',     # YYYY-MM-DD
            r'\d{1,2}/\d{4}',             # MM/YYYY
            r'\d{1,2}-\d{4}',             # MM-YYYY
        ]
        
        for pattern in date_patterns:
            if re.match(pattern, value):
                return True
        
        return False
    
    def _select_best_creditor_name(self, candidates: List[str]) -> str:
        """Select the best creditor name from candidates"""
        if not candidates:
            return ""
        
        # Score each candidate
        scored_candidates = []
        for candidate in candidates:
            score = 0
            
            # Prefer non-numeric values
            if not candidate.isdigit():
                score += 10
            
            # Prefer values with company indicators
            company_indicators = ["bank", "credit", "financial", "capital", "corp", "inc", "llc", "card", "fund", "union"]
            if any(indicator in candidate.lower() for indicator in company_indicators):
                score += 5
            
            # Prefer reasonable length (not too short, not too long)
            if 4 <= len(candidate) <= 30:
                score += 3
            
            # Prefer values with mixed case (likely proper names)
            if candidate != candidate.upper() and candidate != candidate.lower():
                score += 2
            
            scored_candidates.append((candidate, score))
        
        # Return the highest scoring candidate
        best_candidate = max(scored_candidates, key=lambda x: x[1])
        return best_candidate[0]
    
    def _select_best_account_number(self, candidates: List[str]) -> str:
        """Select the best account number from candidates"""
        if not candidates:
            return ""
        
        # Prefer masked account numbers
        for candidate in candidates:
            if self._is_likely_account_number(candidate) and ("*" in candidate or "x" in candidate.lower()):
                return candidate
        
        # Fallback to first candidate
        return candidates[0]
    
    def _is_currency_format(self, value: str) -> bool:
        """Basic currency format validation"""
        return bool(re.match(r'^\$?[\d,]+\.?\d*$', value.strip()))
    
    def _extract_account_type_basic(self, value: str, creditor_name: str) -> str:
        """Basic account type extraction"""
        value_lower = value.lower()
        creditor_lower = creditor_name.lower()
        
        if any(term in value_lower for term in ["revolving", "credit card", "card"]):
            return "Credit Card"
        elif any(term in value_lower for term in ["installment", "loan"]):
            return "Installment Loan"
        elif any(term in creditor_lower for term in ["auto", "ford", "honda", "toyota"]):
            return "Auto Loan"
        elif any(term in creditor_lower for term in ["mortgage", "home"]):
            return "Mortgage"
        elif any(term in creditor_lower for term in ["student", "education"]):
            return "Student Loan"
        else:
            return "Credit Card"  # Default

class GeminiProcessor:
    def extract_tradelines(self, text: str) -> List[Dict[str, Any]]:
        """Extract tradelines using Gemini AI with chunking support"""
        try:
            logger.info(f"🧠 Starting Gemini tradeline extraction from {len(text)} characters")
            
            if not gemini_model:
                raise Exception("Gemini model not initialized")
            
            # If text is too long, process in chunks
            if len(text) > 15000:
                return self._extract_tradelines_chunked(text)
            else:
                return self._extract_tradelines_single(text)
                
        except Exception as e:
            logger.error(f"❌ Gemini processing failed: {str(e)}")
            logger.error(f"📍 Traceback: {traceback.format_exc()}")
            return []
    
    def _extract_tradelines_single(self, text: str) -> List[Dict[str, Any]]:
        """Extract tradelines from a single text chunk"""
        logger.info("🧠 GEMINI EXTRACTION - INPUT DATA:")
        logger.info(f"  Text length: {len(text)} characters")
        logger.info(f"  First 200 chars: {text[:200]}...")
        logger.info(f"  Last 200 chars: ...{text[-200:]}")
        
        prompt = f"""
        You are analyzing a credit report that may have OCR errors. Extract credit tradeline information carefully.

        CRITICAL FIELD PATTERNS TO FIND:
        
        CREDIT_LIMIT field names (look for these exact phrases):
        - "High Credit", "High Cr edit", "HighCredit"
        - "Credit Limit", "Credit Lim it", "CreditLimit" 
        - "Limit", "Lmt", "Credit Line", "CL"
        - "Maximum", "Max", "Original Amount"
        - "Available Credit", "Credit Available"
        
        MONTHLY_PAYMENT field names (look for these exact phrases):
        - "Monthly Payment", "Monthly Pay ment", "MonthlyPayment"
        - "Payment", "Pay ment", "Pmt", "Pay"
        - "Min Payment", "Minimum Payment", "Min Pmt"
        - "Payment Amount", "Payment Amt", "PaymentAmt"
        - "Amount Due", "Due Amount"

        ACCOUNT_NUMBER patterns (PRIORITY - look for these):
        - Masked numbers: "****1234", "xxxx5678", "1234****", "5678xxxx"
        - Account references: "Account #: 1234****", "Acct: ****5678"  
        - Card numbers: "4123 **** **** 5678", "5555-****-****-1234"
        - Special formats: "CBA0000000001022****", "25068505471E0012024052124****"
        - Look near creditor names for account identifiers
        
        ACCOUNT_TYPE indicators:
        - "R" or "Rev" or "Revolving" = Revolving (Credit Cards)
        - "I" or "Inst" or "Installment" = Installment (Loans)  
        - "M" or "Mtg" or "Mortgage" = Installment
        - Look at creditor name for context (FORD = Auto, NAVIENT = Student)

        OCR ERROR HANDLING:
        - Text may have extra spaces: "High Cr edit" instead of "High Credit"
        - Numbers may be split: "2, 500.00" instead of "2,500.00"
        - Dollar signs may be separate: "$ 1,234" instead of "$1,234"
        - Field names may be broken across lines
        - Account numbers may be split: "1234 ****" or "* * * * 5678"

        REAL CREDIT REPORT EXAMPLES:
        Example 1: "CHASE BANK    High Credit: $5,000    Payment: $125    Balance: $1,250"
        Example 2: "Capital One   Limit $3,000   Min Payment $89   Current Bal $892"
        Example 3: "FORD CREDIT   Original Amount: $25,000   Monthly Pmt: $389   Balance: $18,500"

        Return ONLY a JSON array with these exact fields:
        - creditor_name (string): Bank/lender name (required)
        - account_number (string): Account number with masking (e.g., "****1234", "1234****") - PRIORITY FIELD
        - account_balance (string): Current balance with $ (e.g., "$1,234.56") or null
        - credit_limit (string): High credit/limit with $ (e.g., "$5,000.00") - PRIORITY FIELD  
        - monthly_payment (string): Monthly/min payment with $ (e.g., "$125.00") - PRIORITY FIELD
        - date_opened (string): Date opened (MM/DD/YYYY format) or null
        - account_type (string): "Revolving" or "Installment" (standardized)
        - account_status (string): "Current", "Closed", "Late" (standardized)
        - credit_bureau (string): "Experian", "Equifax", "TransUnion" or null
        - is_negative (boolean): true if negative marks present

        FOCUS ESPECIALLY on finding credit_limit and monthly_payment values - these are the most important fields.

        Text to analyze:
        {text[:15000]}

        Return only valid JSON array, no explanations:
        """
        
        logger.info("🚀 Sending request to Gemini...")
        response = gemini_model.generate_content(prompt)
        logger.info(f"✅ Gemini response received: {len(response.text)} characters")
        
        # Clean up response to extract JSON
        response_text = response.text.strip()
        logger.info(f"📝 GEMINI RAW RESPONSE:")
        logger.info(f"  Full response: {response_text}")
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = re.sub(r'^```json\s*', '', response_text)
            response_text = re.sub(r'\s*```$', '', response_text)
            logger.info(f"  Cleaned response: {response_text}")
        
        # Find JSON array
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            import json
            try:
                tradelines = json.loads(json_match.group())
                logger.info(f"🔍 GEMINI EXTRACTED {len(tradelines)} RAW TRADELINES:")
                
                # 📊 LOG: Each raw tradeline from Gemini
                for i, tradeline in enumerate(tradelines):
                    logger.info(f"  🧠 RAW TRADELINE {i+1}:")
                    logger.info(f"    Creditor: '{tradeline.get('creditor_name', 'N/A')}'")
                    logger.info(f"    Credit Limit: '{tradeline.get('credit_limit', 'N/A')}'")
                    logger.info(f"    Monthly Payment: '{tradeline.get('monthly_payment', 'N/A')}'")
                    logger.info(f"    Balance: '{tradeline.get('account_balance', 'N/A')}'")
                    logger.info(f"    Account Type: '{tradeline.get('account_type', 'N/A')}'")
                    logger.info(f"    Account Status: '{tradeline.get('account_status', 'N/A')}'")
                    logger.info(f"    Is Negative: {tradeline.get('is_negative', False)}")
                
                # Basic validation - keep tradelines with creditor names
                validated_tradelines = []
                logger.info("🔍 VALIDATING GEMINI TRADELINES:")
                
                for i, tradeline in enumerate(tradelines):
                    logger.info(f"  🔍 VALIDATING TRADELINE {i+1}: {tradeline.get('creditor_name', 'N/A')}")
                    
                    # Basic validation - must have creditor name
                    has_creditor = bool(tradeline.get('creditor_name', '').strip())
                    has_data = bool(tradeline.get('credit_limit') or tradeline.get('monthly_payment') or tradeline.get('account_balance'))
                    
                    if has_creditor and has_data:
                        validated_tradelines.append(tradeline)
                        logger.info(f"    ✅ ACCEPTED - has creditor and data")
                    else:
                        logger.warning(f"    ❌ REJECTED - missing creditor ({has_creditor}) or data ({has_data})")
                
                logger.info(f"✅ GEMINI FINAL RESULT: {len(validated_tradelines)}/{len(tradelines)} valid tradelines")
                return validated_tradelines
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse Gemini JSON: {e}")
                logger.error(f"  Attempted to parse: {json_match.group()}")
                return []
        else:
            logger.warning("⚠️ No JSON array found in Gemini response")
            return []
    
    def _extract_tradelines_chunked(self, text: str) -> List[Dict[str, Any]]:
        """Extract tradelines from text by processing in chunks"""
        logger.info(f"📖 Processing large text in chunks: {len(text)} characters")
        
        chunk_size = 15000
        overlap = 500  # Overlap to avoid cutting tradelines
        chunks = []
        
        # Split text into overlapping chunks
        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i + chunk_size]
            chunks.append(chunk)
        
        logger.info(f"🔄 Split into {len(chunks)} chunks")
        
        all_tradelines = []
        seen_tradelines = set()  # To avoid duplicates
        
        for i, chunk in enumerate(chunks):
            try:
                logger.info(f"🔍 Processing chunk {i+1}/{len(chunks)}")
                chunk_tradelines = self._extract_tradelines_single(chunk)
                
                # Deduplicate tradelines based on creditor name + account number
                for tradeline in chunk_tradelines:
                    identifier = f"{tradeline.get('creditor_name', '')}_{tradeline.get('account_number', '')}"
                    if identifier not in seen_tradelines:
                        seen_tradelines.add(identifier)
                        all_tradelines.append(tradeline)
                        
            except Exception as e:
                logger.error(f"❌ Failed to process chunk {i+1}: {str(e)}")
                continue
        
        logger.info(f"✅ Total tradelines extracted from all chunks: {len(all_tradelines)}")
        return all_tradelines

def parse_tradelines_basic(text: str) -> List[Dict[str, Any]]:
    """Basic tradeline parsing as backup"""
    try:
        logger.info("🔧 BASIC PARSING - INPUT DATA:")
        logger.info(f"  Text length: {len(text)} characters")
        logger.info(f"  Number of lines: {len(text.split('\n'))}")
        logger.info(f"  First 300 chars: {text[:300]}...")
        
        tradelines = []
        lines = text.split('\n')
        
        logger.info("🔍 BASIC PARSING - ANALYZING LINES:")
        for i, line in enumerate(lines[:20]):  # Log first 20 lines
            if line.strip():
                logger.info(f"  Line {i+1}: {line.strip()}")
        if len(lines) > 20:
            logger.info(f"  ... and {len(lines) - 20} more lines")
        
        # Comprehensive creditor patterns
        creditor_patterns = [
            # Major Banks
            r'(CHASE|Chase|chase|JP MORGAN|JPMorgan|JPMORGAN)',
            r'(CAPITAL ONE|Capital One|capital one|CAP ONE|CAPONE)',
            r'(CITIBANK|Citibank|citibank|CITI|Citi|citi)',
            r'(BANK OF AMERICA|Bank of America|BOA|B OF A)',
            r'(WELLS FARGO|Wells Fargo|WELLS|Wells)',
            r'(DISCOVER|Discover|discover)',
            r'(AMERICAN EXPRESS|American Express|AMEX|AmEx|amex)',
            r'(SYNCHRONY|Synchrony|synchrony)',
            r'(CREDIT ONE|Credit One|credit one)',
            r'(US BANK|US Bank|U\.S\. Bank|USBANK)',
            r'(PNC|PNC Bank|pnc)',
            r'(TD BANK|TD Bank|td bank)',
            r'(REGIONS|Regions|regions)',
            r'(ALLY|Ally|ally)',
            r'(MARCUS|Marcus|marcus)',
            r'(BARCLAYS|Barclays|barclays)',
            r'(HSBC|hsbc)',
            
            # Credit Cards
            r'(MASTERCARD|MasterCard|mastercard)',
            r'(VISA|Visa|visa)',
            r'(STORE CARD|Store Card|store card)',
            
            # Store Cards
            r'(AMAZON|Amazon|amazon)',
            r'(TARGET|Target|target)',
            r'(HOME DEPOT|Home Depot|HOMEDEPOT)',
            r'(LOWES|Lowe\'s|LOWE\'S|lowes)',
            r'(WALMART|Walmart|walmart)',
            r'(COSTCO|Costco|costco)',
            r'(NORDSTROM|Nordstrom|nordstrom)',
            r'(MACY\'S|Macy\'s|macys)',
            r'(KOHL\'S|Kohl\'s|kohls)',
            r'(BEST BUY|Best Buy|bestbuy)',
            r'(APPLE|Apple|apple)',
            
            # Auto Loans
            r'(FORD CREDIT|Ford Credit|ford credit)',
            r'(HONDA FINANCIAL|Honda Financial|honda financial)',
            r'(TOYOTA FINANCIAL|Toyota Financial|toyota financial)',
            r'(NISSAN MOTOR|Nissan Motor|nissan motor)',
            r'(GM FINANCIAL|GM Financial|gm financial)',
            r'(CHRYSLER CAPITAL|Chrysler Capital|chrysler capital)',
            r'(ALLY AUTO|Ally Auto|ally auto)',
            r'(SANTANDER|Santander|santander)',
            
            # Student Loans
            r'(NAVIENT|Navient|navient)',
            r'(GREAT LAKES|Great Lakes|great lakes)',
            r'(NELNET|Nelnet|nelnet)',
            r'(FEDLOAN|FedLoan|fedloan)',
            r'(MOHELA|MOHELA|mohela)',
            r'(DEPT OF EDUCATION|Department of Education|dept of education)',
            r'(STUDENT LOAN|Student Loan|student loan)',
            
            # Mortgage
            r'(QUICKEN LOANS|Quicken Loans|quicken loans)',
            r'(ROCKET MORTGAGE|Rocket Mortgage|rocket mortgage)',
            r'(FREEDOM MORTGAGE|Freedom Mortgage|freedom mortgage)',
            r'(PENNYMAC|PennyMac|pennymac)',
            r'(CALIBER HOME|Caliber Home|caliber home)',
            r'(MORTGAGE|Mortgage|mortgage)',
            
            # Credit Unions
            r'(NAVY FEDERAL|Navy Federal|navy federal)',
            r'(USAA|usaa)',
            r'(PENTAGON FCU|Pentagon FCU|pentagon fcu)',
            r'(CREDIT UNION|Credit Union|credit union)',
            
            # Other Financial
            r'(PAYPAL|PayPal|paypal)',
            r'(AFFIRM|Affirm|affirm)',
            r'(KLARNA|Klarna|klarna)',
            r'(AFTERPAY|Afterpay|afterpay)',
            r'(UPLIFT|Uplift|uplift)',
            r'(LENDING CLUB|Lending Club|lending club)',
            r'(PROSPER|Prosper|prosper)',
            r'(SOFI|SoFi|sofi)',
            r'(AVANT|Avant|avant)',
            r'(ONEMAIN|OneMain|onemain)',
            r'(SPRINGLEAF|Springleaf|springleaf)',
            r'(PERSONAL LOAN|Personal Loan|personal loan)'
        ]
        
        current_tradeline = {}
        tradeline_count = 0
        
        logger.info("🔍 BASIC PARSING - SEARCHING FOR CREDITORS:")
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Look for creditor names
            for pattern_idx, pattern in enumerate(creditor_patterns):
                if re.search(pattern, line, re.IGNORECASE):
                    logger.info(f"  📍 FOUND CREDITOR on line {line_num+1}: '{line}'")
                    logger.info(f"    Pattern #{pattern_idx+1}: {pattern}")
                    
                    # Save previous tradeline if it exists
                    if current_tradeline and current_tradeline.get("creditor_name"):
                        tradeline_count += 1
                        logger.info(f"  💾 SAVING PREVIOUS TRADELINE #{tradeline_count}:")
                        logger.info(f"    Creditor: '{current_tradeline.get('creditor_name')}'")
                        logger.info(f"    Credit Limit: '{current_tradeline.get('credit_limit')}'")
                        logger.info(f"    Monthly Payment: '{current_tradeline.get('monthly_payment')}'")
                        logger.info(f"    Balance: '{current_tradeline.get('account_balance')}'")
                        tradelines.append(current_tradeline)
                    
                    # Extract creditor name
                    creditor_match = re.search(pattern, line, re.IGNORECASE)
                    creditor_name = creditor_match.group(0) if creditor_match else "Unknown"
                    
                    # Determine account type based on creditor
                    account_type = "Credit Card"  # default
                    if any(loan_type in creditor_name.upper() for loan_type in ["AUTO", "FORD", "HONDA", "TOYOTA", "NISSAN", "GM", "CHRYSLER", "ALLY AUTO", "SANTANDER"]):
                        account_type = "Auto Loan"
                    elif any(loan_type in creditor_name.upper() for loan_type in ["STUDENT", "NAVIENT", "GREAT LAKES", "NELNET", "FEDLOAN", "MOHELA", "DEPT OF EDUCATION"]):
                        account_type = "Student Loan"
                    elif any(loan_type in creditor_name.upper() for loan_type in ["MORTGAGE", "QUICKEN", "ROCKET", "FREEDOM", "PENNYMAC", "CALIBER"]):
                        account_type = "Mortgage"
                    elif any(loan_type in creditor_name.upper() for loan_type in ["PERSONAL", "LENDING", "PROSPER", "SOFI", "AVANT", "ONEMAIN", "SPRINGLEAF"]):
                        account_type = "Personal Loan"
                    
                    current_tradeline = {
                        "creditor_name": creditor_name,
                        "account_type": account_type,
                        "account_status": "Open",
                        "credit_bureau": "Unknown", 
                        "is_negative": False,
                        "account_balance": "",
                        "credit_limit": "",
                        "monthly_payment": "",
                        "account_number": "",
                        "date_opened": "",
                        "dispute_count": 0
                    }
                    
                    logger.info(f"  🆕 CREATED NEW TRADELINE:")
                    logger.info(f"    Creditor: '{creditor_name}'")
                    logger.info(f"    Account Type: '{account_type}'")
                    
                    break
            
            # Enhance data extraction for current tradeline
            if current_tradeline:
                logger.debug(f"    🔍 Analyzing line for tradeline data: '{line}'")
                
                # Look for account numbers (enhanced patterns)
                account_patterns = [
                    r'\*{4,}\d{4,}',  # ****1234
                    r'x{4,}\d{4,}',   # xxxx1234 
                    r'\d{4,}\*{4,}',  # 1234****
                    r'\d{4,}x{4,}',   # 1234xxxx
                    r'(?:account|acct|card)\s*#?\s*:?\s*(\*{4,}\d{4,}|\d{4,}\*{4,})',  # Account #: ****1234
                    r'(?:account|acct|card)\s*#?\s*:?\s*(x{4,}\d{4,}|\d{4,}x{4,})',    # Account #: xxxx1234
                    r'\d{13,19}',     # Full card numbers
                    r'[A-Z]{2,3}\d{10,}\*{4,}',  # CBA0000000001022****
                    r'\d{8,}[A-Z]\d{4,}\*{4,}',  # 25068505471E0012024052124****
                    r'Account\s*#?\s*:?\s*(\d+)',  # Account #: 123456
                    r'Acct\s*#?\s*:?\s*(\d+)'     # Acct #: 123456
                ]
                
                for pattern in account_patterns:
                    account_match = re.search(pattern, line, re.IGNORECASE)
                    if account_match:
                        old_account = current_tradeline["account_number"]
                        current_tradeline["account_number"] = account_match.group(0)
                        logger.info(f"    💳 FOUND ACCOUNT NUMBER: '{old_account}' → '{current_tradeline['account_number']}'")
                        break
                
                # Look for credit limits
                credit_limit_patterns = [
                    r'(high credit|credit limit|limit|maximum|credit line|available credit)\s*:?\s*\$?([\d,]+\.?\d*)',
                    r'\$?([\d,]+\.?\d*)\s*(high credit|credit limit|limit|maximum)',
                    r'(high|limit|max)\s*\$?([\d,]+\.?\d*)'
                ]
                
                for pattern in credit_limit_patterns:
                    limit_match = re.search(pattern, line, re.IGNORECASE)
                    if limit_match and not current_tradeline["credit_limit"]:
                        amount = limit_match.group(2) if len(limit_match.groups()) > 1 else limit_match.group(1)
                        if amount.isdigit() or ',' in amount or '.' in amount:
                            current_tradeline["credit_limit"] = f"${amount}"
                            logger.info(f"    💰 FOUND CREDIT LIMIT: '{current_tradeline['credit_limit']}' from line: '{line}'")
                            break
                
                # Look for monthly payments
                payment_patterns = [
                    r'(monthly payment|payment|min payment|minimum payment|pay amt|amount due)\s*:?\s*\$?([\d,]+\.?\d*)',
                    r'\$?([\d,]+\.?\d*)\s*(monthly payment|payment|min payment|minimum)',
                    r'(pmt|pay)\s*\$?([\d,]+\.?\d*)'
                ]
                
                for pattern in payment_patterns:
                    payment_match = re.search(pattern, line, re.IGNORECASE)
                    if payment_match and not current_tradeline["monthly_payment"]:
                        amount = payment_match.group(2) if len(payment_match.groups()) > 1 else payment_match.group(1)
                        if amount.isdigit() or ',' in amount or '.' in amount:
                            current_tradeline["monthly_payment"] = f"${amount}"
                            logger.info(f"    💸 FOUND MONTHLY PAYMENT: '{current_tradeline['monthly_payment']}' from line: '{line}'")
                            break
                
                # Look for balances
                balance_patterns = [
                    r'(balance|current|amount owed|owed)\s*:?\s*\$?([\d,]+\.?\d*)',
                    r'\$?([\d,]+\.?\d*)\s*(balance|current|owed)'
                ]
                
                for pattern in balance_patterns:
                    balance_match = re.search(pattern, line, re.IGNORECASE)
                    if balance_match and not current_tradeline["account_balance"]:
                        amount = balance_match.group(2) if len(balance_match.groups()) > 1 else balance_match.group(1)
                        if amount.isdigit() or ',' in amount or '.' in amount:
                            current_tradeline["account_balance"] = f"${amount}"
                            logger.info(f"    💳 FOUND BALANCE: '{current_tradeline['account_balance']}' from line: '{line}'")
                            break
                
                # Look for dates
                date_patterns = [
                    r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # MM/DD/YYYY or MM-DD-YYYY
                    r'\d{2,4}[/-]\d{1,2}[/-]\d{1,2}',  # YYYY/MM/DD or YYYY-MM-DD
                    r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}',  # Month DD, YYYY
                    r'\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}'  # DD Month YYYY
                ]
                
                for pattern in date_patterns:
                    date_match = re.search(pattern, line, re.IGNORECASE)
                    if date_match and not current_tradeline["date_opened"]:
                        current_tradeline["date_opened"] = date_match.group(0)
                        break
                
                # Look for status indicators
                status_patterns = {
                    'Current': r'current|open|active|good standing',
                    'Closed': r'closed|terminated|paid off|satisfied',
                    'Late': r'late|delinquent|past due|30 days|60 days|90 days',
                    'Charged Off': r'charged off|charge off|written off',
                    'Collection': r'collection|collections|assigned'
                }
                
                for status, pattern in status_patterns.items():
                    if re.search(pattern, line, re.IGNORECASE):
                        current_tradeline["account_status"] = status
                        # Mark as negative if it's a bad status
                        if status in ['Late', 'Charged Off', 'Collection']:
                            current_tradeline["is_negative"] = True
                        break
                
                # Look for credit bureau mentions
                bureau_patterns = {
                    'Experian': r'experian|exp\b',
                    'Equifax': r'equifax|eqf\b',
                    'TransUnion': r'transunion|trans union|tru\b'
                }
                
                for bureau, pattern in bureau_patterns.items():
                    if re.search(pattern, line, re.IGNORECASE):
                        current_tradeline["credit_bureau"] = bureau
                        break
        
        # Add the last tradeline if it exists
        if current_tradeline and current_tradeline.get("creditor_name"):
            tradeline_count += 1
            logger.info(f"💾 SAVING FINAL TRADELINE #{tradeline_count}:")
            logger.info(f"  Creditor: '{current_tradeline.get('creditor_name')}'")
            logger.info(f"  Credit Limit: '{current_tradeline.get('credit_limit')}'")
            logger.info(f"  Monthly Payment: '{current_tradeline.get('monthly_payment')}'")
            logger.info(f"  Balance: '{current_tradeline.get('account_balance')}'")
            tradelines.append(current_tradeline)
        
        logger.info(f"🔧 BASIC PARSING EXTRACTED {len(tradelines)} RAW TRADELINES")
        
        # Basic validation - keep tradelines with creditor names and some data
        validated_tradelines = []
        logger.info("🔍 VALIDATING BASIC PARSING TRADELINES:")
        
        for i, tradeline in enumerate(tradelines):
            logger.info(f"  🔍 VALIDATING TRADELINE {i+1}: {tradeline.get('creditor_name', 'N/A')}")
            
            has_creditor = bool(tradeline.get('creditor_name', '').strip())
            has_data = bool(tradeline.get('credit_limit') or tradeline.get('monthly_payment') or tradeline.get('account_balance'))
            
            if has_creditor:
                validated_tradelines.append(tradeline)
                logger.info(f"    ✅ ACCEPTED - has creditor name")
            else:
                logger.warning(f"    ❌ REJECTED - no creditor name")
        
        logger.info(f"✅ BASIC PARSING FINAL RESULT: {len(validated_tradelines)}/{len(tradelines)} valid tradelines")
        return validated_tradelines
        
    except Exception as e:
        logger.error(f"❌ Basic parsing failed: {str(e)}")
        return []

async def save_tradeline_to_supabase(tradeline: Dict[str, Any], user_id: str) -> bool:
    """Save tradeline to Supabase using RPC function"""
    try:
        if not supabase:
            logger.warning("⚠️ Supabase not initialized, skipping save")
            return False
            
        logger.info(f"💾 SUPABASE SAVE - Starting save for: {tradeline.get('creditor_name', 'unknown')}")
        logger.info(f"    User ID: {user_id}")
        
        # 📊 LOG: Input tradeline data before validation
        logger.info(f"    📄 INPUT TRADELINE DATA:")
        logger.info(f"      Creditor: '{tradeline.get('creditor_name', 'N/A')}'")
        logger.info(f"      Credit Limit: '{tradeline.get('credit_limit', 'N/A')}'")
        logger.info(f"      Monthly Payment: '{tradeline.get('monthly_payment', 'N/A')}'")
        logger.info(f"      Balance: '{tradeline.get('account_balance', 'N/A')}'")
        logger.info(f"      Account Type: '{tradeline.get('account_type', 'N/A')}'")
        logger.info(f"      Account Status: '{tradeline.get('account_status', 'N/A')}'")
        logger.info(f"      Credit Bureau: '{tradeline.get('credit_bureau', 'N/A')}'")
        logger.info(f"      Account Number: '{tradeline.get('account_number', 'N/A')}'")
        
        # Normalize tradeline data first
        logger.info("    🔧 NORMALIZING tradeline data...")
        normalized_tradeline = tradeline_normalizer.normalize_tradeline(tradeline)
        
        # 📊 LOG: Normalized tradeline data
        logger.info(f"    📄 NORMALIZED TRADELINE DATA:")
        logger.info(f"      Creditor: '{normalized_tradeline.get('creditor_name', 'N/A')}'")
        logger.info(f"      Credit Limit: '{normalized_tradeline.get('credit_limit', 'N/A')}'")
        logger.info(f"      Monthly Payment: '{normalized_tradeline.get('monthly_payment', 'N/A')}'")
        logger.info(f"      Balance: '{normalized_tradeline.get('account_balance', 'N/A')}'")
        logger.info(f"      Account Type: '{normalized_tradeline.get('account_type', 'N/A')}'")
        logger.info(f"      Account Status: '{normalized_tradeline.get('account_status', 'N/A')}'")
        logger.info(f"      Credit Bureau: '{normalized_tradeline.get('credit_bureau', 'N/A')}'")
        logger.info(f"      Account Number: '{normalized_tradeline.get('account_number', 'N/A')}'")
        logger.info(f"      Date Opened: '{normalized_tradeline.get('date_opened', 'N/A')}'")
        
        # Validate with field validator
        logger.info("    🔍 VALIDATING with field validator...")
        validation_result = field_validator.validate_tradeline(normalized_tradeline)
        logger.info(f"    📊 Validation confidence: {validation_result['confidence_score']:.2f}")
        
        if not validation_result['is_valid']:
            logger.warning(f"    ⚠️ Tradeline validation failed: {validation_result['errors']}")
            # Continue anyway but log the issues
        
        # Validate with Pydantic (use normalized data)
        logger.info("    🔍 VALIDATING with Pydantic schema...")
        # Convert None values to empty strings for Pydantic compatibility
        pydantic_data = {k: (v if v is not None else "") for k, v in normalized_tradeline.items()}
        validated_tradeline = TradelineSchema(**pydantic_data)
        logger.info("    ✅ Pydantic validation passed")
        
        # 📊 LOG: Validated tradeline data
        logger.info(f"    📄 VALIDATED TRADELINE DATA:")
        logger.info(f"      Creditor: '{validated_tradeline.creditor_name}'")
        logger.info(f"      Credit Limit: '{validated_tradeline.credit_limit}'")
        logger.info(f"      Monthly Payment: '{validated_tradeline.monthly_payment}'")
        logger.info(f"      Balance: '{validated_tradeline.account_balance}'")
        logger.info(f"      Account Type: '{validated_tradeline.account_type}'")
        logger.info(f"      Account Status: '{validated_tradeline.account_status}'")
        logger.info(f"      Credit Bureau: '{validated_tradeline.credit_bureau}'")
        logger.info(f"      Account Number: '{validated_tradeline.account_number}'")
        
        # Ensure date_opened is in ISO format for PostgreSQL
        raw_date = normalized_tradeline.get('date_opened')
        iso_date = normalize_date_for_postgres(raw_date) if raw_date else None
        
        if raw_date and raw_date != iso_date:
            logger.info(f"📅 Date normalized for PostgreSQL: '{raw_date}' → '{iso_date}'")
        
        # Prepare RPC parameters
        rpc_params = {
            'p_account_balance': validated_tradeline.account_balance,
            'p_account_number': validated_tradeline.account_number,
            'p_account_status': validated_tradeline.account_status,
            'p_account_type': validated_tradeline.account_type,
            'p_credit_bureau': validated_tradeline.credit_bureau,
            'p_credit_limit': validated_tradeline.credit_limit,
            'p_creditor_name': validated_tradeline.creditor_name,
            'p_monthly_payment': validated_tradeline.monthly_payment,
            'p_date_opened': iso_date,  # Use ISO formatted date for PostgreSQL compatibility
            'p_is_negative': validated_tradeline.is_negative,
            'p_user_id': user_id
        }
        
        logger.info(f"    🚀 CALLING Supabase RPC 'upsert_tradeline'...")
        logger.info(f"      Parameters: {rpc_params}")
        
        # Call Supabase RPC function
        result = supabase.rpc('upsert_tradeline', rpc_params).execute()
        
        logger.info(f"    📨 SUPABASE RESPONSE:")
        logger.info(f"      Data: {result.data}")
        logger.info(f"      Count: {getattr(result, 'count', 'N/A')}")
        
        if result.data:
            logger.info(f"    ✅ SUPABASE SAVE SUCCESSFUL: {validated_tradeline.creditor_name}")
            return True
        else:
            logger.error(f"    ❌ SUPABASE SAVE FAILED - no data returned")
            logger.error(f"      Full result: {result}")
            return False
            
    except ValidationError as e:
        logger.error(f"❌ PYDANTIC VALIDATION ERROR:")
        logger.error(f"  Tradeline: {tradeline}")
        logger.error(f"  Error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ SUPABASE DATABASE ERROR:")
        logger.error(f"  Error: {e}")
        logger.error(f"  Tradeline: {tradeline}")
        logger.error(f"  Traceback: {traceback.format_exc()}")
        return False

@app.post("/save-tradelines")
async def save_tradelines_endpoint(request: dict):
    """
    Endpoint to save tradelines to database
    """
    try:
        user_id = request.get('userId')
        tradelines = request.get('tradelines', [])
        
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        
        if not tradelines:
            raise HTTPException(status_code=400, detail="No tradelines provided")
        
        logger.info(f"💾 Saving {len(tradelines)} tradelines for user {user_id}")
        
        saved_count = 0
        failed_count = 0
        
        if supabase:
            # Save each tradeline to Supabase
            for tradeline in tradelines:
                try:
                    success = await save_tradeline_to_supabase(tradeline, user_id)
                    if success:
                        saved_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"❌ Failed to save tradeline: {e}")
                    failed_count += 1
        else:
            logger.warning("⚠️ Supabase not available, cannot save tradelines")
            raise HTTPException(status_code=503, detail="Database not available")
        
        return {
            "success": True,
            "message": f"Saved {saved_count} tradelines successfully",
            "saved_count": saved_count,
            "failed_count": failed_count,
            "total_tradelines": len(tradelines)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Save endpoint failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save tradelines: {str(e)}")

def check_supabase_connection():
    """Check if Supabase is properly configured"""
    global supabase
    
    logger.info("🔍 Checking Supabase configuration...")
    
    if not SUPABASE_URL:
        logger.error("❌ SUPABASE_URL environment variable not set")
        return False
        
    if not SUPABASE_ANON_KEY:
        logger.error("❌ SUPABASE_ANON_KEY environment variable not set")
        return False
    
    try:
        # Test the connection
        result = supabase.table('tradelines').select('id').limit(1).execute()
        logger.info("✅ Supabase connection test successful")
        return True
    except Exception as e:
        logger.error(f"❌ Supabase connection test failed: {e}")
        return False

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    supabase_available = check_supabase_connection() if supabase else False
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "services": {
            "document_ai": {
                "configured": bool(PROJECT_ID and PROCESSOR_ID and client),
                "project_id": PROJECT_ID,
                "location": LOCATION,
                "processor_id": PROCESSOR_ID[:8] + "..." if PROCESSOR_ID else None
            },
            "gemini": {
                "configured": bool(GEMINI_API_KEY and gemini_model),
                "model": "gemini-1.5-flash" if gemini_model else None
            },
            "supabase": {
                "configured": bool(SUPABASE_URL and SUPABASE_ANON_KEY),
                "available": supabase_available,
                "url": SUPABASE_URL[:30] + "..." if SUPABASE_URL else None
            }
        },
        "environment": {
            "python_version": "3.x",
            "fastapi_version": "0.x",
        }
    }
    
    logger.info("🔍 Health check requested")
    return health_status

@app.post("/debug-parsing")
async def debug_parsing(
    file: UploadFile = File(...),
    method: str = Form(default="all")  # "all", "gemini", "basic"
):
    """Debug endpoint to test different parsing methods"""
    try:
        logger.info(f"🐛 Debug parsing request: method={method}")
        
        # Read file content
        content = await file.read()
        logger.info(f"📦 File size: {len(content)} bytes")
        
        # Extract text using PyPDF2
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
            
            logger.info(f"📖 Extracted {len(text)} characters from PDF")
            
            results = {
                "text_length": len(text),
                "first_500_chars": text[:500],
                "methods": {}
            }
            
            # Test different methods
            if method in ["all", "gemini"]:
                try:
                    gemini_processor = GeminiProcessor()
                    gemini_tradelines = gemini_processor.extract_tradelines(text)
                    results["methods"]["gemini"] = {
                        "tradelines": gemini_tradelines,
                        "count": len(gemini_tradelines)
                    }
                except Exception as e:
                    results["methods"]["gemini"] = {
                        "error": str(e),
                        "count": 0
                    }
            
            if method in ["all", "basic"]:
                try:
                    basic_tradelines = parse_tradelines_basic(text)
                    results["methods"]["basic"] = {
                        "tradelines": basic_tradelines,
                        "count": len(basic_tradelines)
                    }
                except Exception as e:
                    results["methods"]["basic"] = {
                        "error": str(e),
                        "count": 0
                    }
            
            return results
            
        finally:
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
    except Exception as e:
        logger.error(f"❌ Debug parsing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Debug parsing failed: {str(e)}")

@app.post("/process-credit-report")
async def process_credit_report(
    file: UploadFile = File(...),
    user_id: str = Form(default="default-user")
):
    """
    Main endpoint: Process uploaded credit report PDF
    """
    temp_file_path = None
    start_time = datetime.utcnow()
    
    try:
        logger.info("🚀 ===== NEW CREDIT REPORT PROCESSING REQUEST =====")
        logger.info(f"⏰ Processing started at: {start_time.isoformat()}Z")
        
        # Store filename early before file operations
        original_filename = file.filename or "unknown.pdf"
        file_content_type = file.content_type
        
        logger.info(f"📄 File: {original_filename}")
        logger.info(f"📦 Content type: {file_content_type}")
        logger.info(f"👤 User ID: {user_id}")
        logger.info(f"🔍 Request received - Processing method will be determined...")
        
        # Validate file type using stored filename
        if not original_filename.lower().endswith('.pdf'):
            logger.error("❌ Invalid file type")
            raise HTTPException(status_code=400, detail="Only PDF files allowed")
        
        # Read file content ONCE
        logger.info("📖 Reading file content...")
        content = await file.read()
        logger.info(f"📦 File size: {len(content)} bytes ({len(content)/1024/1024:.2f} MB)")
        
        if len(content) == 0:
            logger.error("❌ Empty file")
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Save uploaded file using content, not re-reading file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(content)  # Use already-read content
            temp_file_path = temp_file.name
        
        logger.info(f"💾 Temporary file saved: {temp_file_path}")
        
        # Initialize processors
        document_ai = DocumentAIProcessor()
        gemini_processor = GeminiProcessor()
        
        tradelines = []
        processing_method = "none"
        detected_bureau = "Unknown"  # Initialize with default value
        
        # Step 1: Try Document AI Form Parser first (enhanced structured extraction)
        try:
            if client and PROJECT_ID and PROCESSOR_ID:
                logger.info("🤖 Attempting Document AI Form Parser processing...")
                processing_method = "document_ai_form_parser"
                
                try:
                    # Try structured extraction first (best for credit_limit and monthly_payment)
                    logger.info("🔍 Attempting structured tradeline extraction...")
                    structured_tradelines = document_ai.extract_structured_tradelines(temp_file_path)
                    
                    if structured_tradelines:
                        # For structured extraction, we still need to extract text to detect bureau
                        logger.info("📖 Extracting text for bureau detection...")
                        extracted_text = document_ai.extract_text(temp_file_path)
                        detected_bureau = detect_credit_bureau(extracted_text)
                        logger.info(f"🏢 Credit bureau detected from structured path: {detected_bureau}")
                        
                        tradelines = structured_tradelines
                        processing_method = "document_ai_structured"
                        logger.info(f"✅ Document AI structured extraction successful: {len(tradelines)} tradelines")
                    else:
                        # Fallback to text + AI extraction
                        logger.info("📖 Structured extraction failed, trying text extraction...")
                        extracted_text = document_ai.extract_text(temp_file_path)
                        logger.info(f"✅ Document AI text extraction successful: {len(extracted_text)} chars")
                        
                        # Detect credit bureau from extracted text
                        detected_bureau = detect_credit_bureau(extracted_text)
                        logger.info(f"🏢 Credit bureau detected: {detected_bureau}")
                        
                        # Try Gemini for tradeline extraction
                        if gemini_model:
                            logger.info("🧠 Attempting Gemini tradeline extraction...")
                            tradelines = gemini_processor.extract_tradelines(extracted_text)
                            if tradelines:
                                processing_method = "document_ai + gemini"
                                logger.info(f"✅ Gemini extraction successful: {len(tradelines)} tradelines")
                            else:
                                logger.info("⚠️ Gemini found no tradelines, trying basic parsing...")
                                tradelines = parse_tradelines_basic(extracted_text)
                                processing_method = "document_ai + basic"
                        else:
                            logger.info("⚠️ Gemini not available, using basic parsing...")
                            tradelines = parse_tradelines_basic(extracted_text)
                            processing_method = "document_ai + basic"
                    
                except Exception as inner_error:
                    logger.error(f"❌ Document AI inner error: {inner_error}")
                    raise inner_error
                    
            else:
                logger.warning("⚠️ Document AI not properly configured")
                raise Exception("Document AI not configured")
                
        except Exception as doc_ai_error:
            logger.error(f"❌ Document AI processing failed: {str(doc_ai_error)}")
            logger.error(f"📍 Error type: {type(doc_ai_error).__name__}")
            
            # Fallback: Try Enhanced PyPDF2 + Gemini
            try:
                logger.info("🔄 Trying Enhanced PyPDF2 + Gemini fallback...")
                processing_method = "pypdf2_enhanced_fallback"
                
                # Enhanced PDF text extraction with table structure preservation
                extracted_text = _extract_text_with_table_structure(temp_file_path)
                
                logger.info(f"📖 Enhanced PyPDF2 extracted {len(extracted_text)} characters")
                
                # Detect credit bureau from extracted text
                detected_bureau = detect_credit_bureau(extracted_text)
                logger.info(f"🏢 Credit bureau detected: {detected_bureau}")
                
                if gemini_model and extracted_text.strip():
                    tradelines = gemini_processor.extract_tradelines(extracted_text)
                    processing_method = "pypdf2_enhanced + gemini"
                    logger.info(f"✅ Enhanced PyPDF2 + Gemini successful: {len(tradelines)} tradelines")
                
                if not tradelines:
                    logger.info("🔧 Using enhanced basic parsing as final fallback...")
                    tradelines = parse_tradelines_basic(extracted_text)
                    processing_method = "pypdf2_enhanced + basic"
                    
            except Exception as fallback_error:
                logger.error(f"❌ All processing methods failed: {str(fallback_error)}")
                logger.error(f"📍 Traceback: {traceback.format_exc()}")
                raise HTTPException(status_code=500, detail="Could not process PDF with any method")
        
        logger.info(f"📊 Processing completed using: {processing_method}")
        logger.info(f"📈 Found {len(tradelines)} tradelines")
        
        # Apply detected credit bureau to all tradelines if not already set
        if detected_bureau != "Unknown":
            applied_count = 0
            for tradeline in tradelines:
                if not tradeline.get('credit_bureau') or tradeline.get('credit_bureau') == "Unknown" or tradeline.get('credit_bureau') == "":
                    tradeline['credit_bureau'] = detected_bureau
                    applied_count += 1
            if applied_count > 0:
                logger.info(f"🏢 Applied bureau '{detected_bureau}' to {applied_count} tradelines")
        
        # Step 1.5: Normalize tradelines for consistent frontend display
        logger.info("🔧 Normalizing tradelines for frontend response...")
        normalized_tradelines = []
        for i, tradeline in enumerate(tradelines):
            try:
                logger.debug(f"🔧 Normalizing tradeline {i+1}/{len(tradelines)}: {tradeline.get('creditor_name', 'unknown')}")
                
                # Apply normalization
                normalized_tradeline = tradeline_normalizer.normalize_tradeline(tradeline)
                
                # Convert None values back to empty strings for frontend compatibility
                frontend_tradeline = {k: (v if v is not None else "") for k, v in normalized_tradeline.items()}
                
                normalized_tradelines.append(frontend_tradeline)
                logger.debug(f"✅ Normalized: {frontend_tradeline.get('creditor_name')} -> {frontend_tradeline.get('account_type')}")
                
            except Exception as norm_error:
                logger.warning(f"⚠️ Failed to normalize tradeline {i+1}: {norm_error}")
                # Fallback to original tradeline if normalization fails
                normalized_tradelines.append(tradeline)
        
        logger.info(f"✅ Successfully normalized {len(normalized_tradelines)} tradelines")
        
        # Log normalization summary for debugging
        if normalized_tradelines:
            sample = normalized_tradelines[0]
            logger.info(f"📊 NORMALIZATION SAMPLE:")
            logger.info(f"    Creditor: '{sample.get('creditor_name', 'N/A')}'")
            logger.info(f"    Account Type: '{sample.get('account_type', 'N/A')}'")
            logger.info(f"    Account Status: '{sample.get('account_status', 'N/A')}'")
            logger.info(f"    Account Number: '{sample.get('account_number', 'N/A')}'")
            logger.info(f"    Date Opened: '{sample.get('date_opened', 'N/A')}'")
        
        # Replace raw tradelines with normalized ones for response
        tradelines = normalized_tradelines
        
        # Step 2: Save tradelines to Supabase (if available)
        saved_count = 0
        failed_count = 0
        
        if supabase:
            logger.info("💾 Saving tradelines to Supabase...")
            for i, tradeline in enumerate(tradelines):
                logger.debug(f"💾 Saving tradeline {i+1}/{len(tradelines)}: {tradeline.get('creditor_name', 'unknown')}")
                success = await save_tradeline_to_supabase(tradeline, user_id)
                if success:
                    saved_count += 1
                else:
                    failed_count += 1
        else:
            logger.warning("⚠️ Supabase not available, skipping database save")
        
        # Step 3: Cleanup temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
            logger.info("🗑️ Temporary file cleaned up")
        
        # Step 4: Calculate processing time and return response
        end_time = datetime.utcnow()
        processing_duration = (end_time - start_time).total_seconds()
        
        response = {
            "success": True,
            "message": f"Successfully processed {len(tradelines)} tradelines using {processing_method}",
            "tradelines_found": len(tradelines),
            "tradelines_saved": saved_count,
            "tradelines_failed": failed_count,
            "processing_method": processing_method,
            "tradelines": tradelines,
            "processing_time": {
                "start_time": start_time.isoformat() + "Z",
                "end_time": end_time.isoformat() + "Z",
                "duration_seconds": round(processing_duration, 2),
                "duration_formatted": f"{int(processing_duration // 60)}m {int(processing_duration % 60)}s"
            },
            "debug_info": {
                "file_size_bytes": len(content),
                "file_name": original_filename,
                "user_id": user_id,
                "supabase_available": supabase is not None,
                "document_ai_available": client is not None,
                "gemini_available": gemini_model is not None
            }
        }
        
        # Completion logging
        logger.info("🎉 ===== PROCESSING COMPLETED SUCCESSFULLY =====")
        logger.info(f"⏰ Processing finished at: {end_time.isoformat()}Z")
        logger.info(f"⏱️ Total processing time: {processing_duration:.2f} seconds ({int(processing_duration // 60)}m {int(processing_duration % 60)}s)")
        logger.info(f"📊 Final results:")
        logger.info(f"   📈 Tradelines found: {len(tradelines)}")
        logger.info(f"   💾 Tradelines saved: {saved_count}")
        logger.info(f"   ❌ Tradelines failed: {failed_count}")
        logger.info(f"   🔧 Processing method: {processing_method}")
        logger.info(f"   📄 File: {original_filename} ({len(content)/1024/1024:.2f} MB)")
        logger.info(f"   👤 User: {user_id}")
        logger.info("🏁 ===== PROCESSING SESSION COMPLETE =====")
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        end_time = datetime.utcnow()
        processing_duration = (end_time - start_time).total_seconds()
        
        logger.error("❌ ===== PROCESSING FAILED =====")
        logger.error(f"⏰ Processing failed at: {end_time.isoformat()}Z")
        logger.error(f"⏱️ Processing duration before failure: {processing_duration:.2f} seconds")
        logger.error(f"💥 Error: {str(e)}")
        logger.error(f"📍 Traceback: {traceback.format_exc()}")
        
        # Cleanup temp file on error
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.info("🗑️ Temporary file cleaned up after error")
            except Exception as cleanup_error:
                logger.error(f"❌ Failed to cleanup temp file: {cleanup_error}")
        
        logger.error("🏁 ===== PROCESSING SESSION FAILED =====")
        
        raise HTTPException(
            status_code=500, 
            detail=f"Processing failed: {str(e)}"
        )

def _extract_text_with_table_structure(pdf_path: str) -> str:
    """Enhanced PyPDF2 text extraction that preserves table structure for financial documents"""
    try:
        logger.info(f"📊 Enhanced PyPDF2 extraction with table structure preservation from {pdf_path}")
        
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            enhanced_text = ""
            
            for page_num, page in enumerate(reader.pages):
                logger.debug(f"Processing page {page_num + 1}")
                
                # Extract text with better spacing preservation
                page_text = page.extract_text()
                
                # Apply enhanced table structure detection
                structured_text = _enhance_table_structure(page_text)
                
                # Add page separators
                if page_num > 0:
                    enhanced_text += "\n\n===== PAGE BREAK =====\n\n"
                
                enhanced_text += structured_text
        
        logger.info(f"✅ Enhanced extraction completed: {len(enhanced_text)} characters")
        return enhanced_text
        
    except Exception as e:
        logger.error(f"❌ Enhanced PyPDF2 extraction failed: {str(e)}")
        # Fallback to basic PyPDF2
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text

def _enhance_table_structure(text: str) -> str:
    """Enhance table structure in extracted text for better field recognition"""
    lines = text.split('\n')
    enhanced_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Detect potential table rows by looking for patterns common in credit reports
        if _is_likely_tradeline_row(line):
            # Add extra spacing around tradeline data for better field separation
            enhanced_line = _format_tradeline_row(line)
            enhanced_lines.append(enhanced_line)
        else:
            enhanced_lines.append(line)
    
    return '\n'.join(enhanced_lines)

def _is_likely_tradeline_row(line: str) -> bool:
    """Detect if a line likely contains tradeline data"""
    line_lower = line.lower()
    
    # Look for patterns that indicate tradeline data
    tradeline_indicators = [
        # Dollar amounts
        r'\$\d+',
        # Account numbers
        r'\*{4,}\d{4}',
        r'x{4,}\d{4}',
        # Dates
        r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
        # Credit terms
        r'\b(credit|limit|payment|balance|high)\b',
        # Bank names
        r'\b(bank|credit|capital|chase|amex|discover|wells|citi)\b',
    ]
    
    matches = 0
    for pattern in tradeline_indicators:
        if re.search(pattern, line_lower):
            matches += 1
    
    # If multiple indicators present, likely a tradeline row
    return matches >= 2

def _format_tradeline_row(line: str) -> str:
    """Format a tradeline row to improve field extraction"""
    # Split on multiple spaces to preserve field boundaries
    parts = re.split(r'\s{2,}', line)
    
    formatted_parts = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Add labels to help field recognition
        if re.match(r'^\$\d+', part):
            # This looks like a dollar amount - try to identify what type
            if any(keyword in line.lower() for keyword in ['limit', 'high', 'maximum', 'credit line']):
                formatted_parts.append(f"Credit Limit: {part}")
            elif any(keyword in line.lower() for keyword in ['payment', 'monthly', 'minimum']):
                formatted_parts.append(f"Monthly Payment: {part}")
            elif any(keyword in line.lower() for keyword in ['balance', 'current', 'owed']):
                formatted_parts.append(f"Current Balance: {part}")
            else:
                formatted_parts.append(part)
        else:
            formatted_parts.append(part)
    
    # Join with clear separators
    return '    |    '.join(formatted_parts)

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting FastAPI server on localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)