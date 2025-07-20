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

from fastapi import FastAPI, UploadFile, File, HTTPException, Form # type: ignore
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

from dotenv import load_dotenv # type: ignore
load_dotenv()

# Import chatbot service
from services.chatbot_service import CreditChatbotService

# Enhanced logging setup
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables with debugging
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us")
PROCESSOR_ID = os.getenv("DOCUMENT_AI_PROCESSOR_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = "https://gywohmbqohytziwsjrps.supabase.co"
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

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

# Initialize chatbot service
try:
    if supabase and GEMINI_API_KEY:
        chatbot_service = CreditChatbotService(supabase, GEMINI_API_KEY)
        logger.info("✅ Chatbot service initialized")
    else:
        logger.error("❌ Chatbot service initialization failed - missing dependencies")
        chatbot_service = None
except Exception as e:
    logger.error(f"❌ Chatbot service initialization failed: {e}")
    chatbot_service = None

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

# Zod-like validation using Pydantic
class TradelineSchema(BaseModel):
    creditor_name: str = "NULL"
    account_balance: str = ""
    credit_limit: str = ""
    monthly_payment: str = ""
    account_number: str = ""
    date_opened: str = "xx/xx/xxxxx"
    account_type: str = ""
    account_status: str = ""
    credit_bureau: str = ""
    is_negative: bool = False
    dispute_count: int = 0

app = FastAPI(title="Credit Report Processor", debug=True)

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
            result = self.client.process_document(request=request)
            
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
    
    def _get_text(self, text_anchor, full_text: str) -> str:
        """Extract text from Document AI text anchor"""
        if not text_anchor or not text_anchor.text_segments:
            return ""
        
        text_segments = []
        for segment in text_anchor.text_segments:
            start_index = int(segment.start_index) if segment.start_index else 0
            end_index = int(segment.end_index) if segment.end_index else len(full_text)
            text_segments.append(full_text[start_index:end_index])
        
        return "".join(text_segments)
    
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
            
            # Group form fields by proximity and likely tradeline groupings
            tradelines = []
            field_groups = self._group_form_fields_by_tradeline(form_fields)
            
            for group in field_groups:
                tradeline = self._extract_tradeline_from_field_group(group)
                if tradeline and tradeline.get("creditor_name"):
                    tradelines.append(tradeline)
            
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
        
        for field in field_group:
            field_name = field["field_name"].lower()
            field_value = field["field_value"].strip()
            
            if not field_value:
                continue
            
            # Map field names to tradeline fields using enhanced patterns
            if any(keyword in field_name for keyword in ["name", "creditor", "lender", "bank"]):
                tradeline["creditor_name"] = field_value
            
            elif any(keyword in field_name for keyword in ["high credit", "credit limit", "limit", "maximum", "credit line"]):
                if field_mapper.validate_currency_format(field_value):
                    tradeline["credit_limit"] = field_value
            
            elif any(keyword in field_name for keyword in ["payment", "monthly", "minimum", "pay amt"]):
                if field_mapper.validate_currency_format(field_value):
                    tradeline["monthly_payment"] = field_value
            
            elif any(keyword in field_name for keyword in ["balance", "current", "amount owed"]):
                if field_mapper.validate_currency_format(field_value):
                    tradeline["account_balance"] = field_value
            
            elif any(keyword in field_name for keyword in ["account", "number", "acct"]):
                tradeline["account_number"] = field_value
            
            elif any(keyword in field_name for keyword in ["date", "opened", "start"]):
                tradeline["date_opened"] = field_value
            
            elif any(keyword in field_name for keyword in ["type", "kind", "category"]):
                account_type = field_mapper.extract_account_type(field_value, tradeline["creditor_name"])
                if account_type:
                    tradeline["account_type"] = account_type.replace("_", " ").title()
            
            elif any(keyword in field_name for keyword in ["status", "condition", "state"]):
                tradeline["account_status"] = field_value
        
        return tradeline

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

        ACCOUNT_TYPE indicators:
        - "R" or "Rev" or "Revolving" = Credit Card
        - "I" or "Inst" or "Installment" = Installment Loan  
        - "M" or "Mtg" or "Mortgage" = Mortgage
        - Look at creditor name for context (FORD = Auto, NAVIENT = Student)

        OCR ERROR HANDLING:
        - Text may have extra spaces: "High Cr edit" instead of "High Credit"
        - Numbers may be split: "2, 500.00" instead of "2,500.00"
        - Dollar signs may be separate: "$ 1,234" instead of "$1,234"
        - Field names may be broken across lines

        REAL CREDIT REPORT EXAMPLES:
        Example 1: "CHASE BANK    High Credit: $5,000    Payment: $125    Balance: $1,250"
        Example 2: "Capital One   Limit $3,000   Min Payment $89   Current Bal $892"
        Example 3: "FORD CREDIT   Original Amount: $25,000   Monthly Pmt: $389   Balance: $18,500"

        Return ONLY a JSON array with these exact fields:
        - creditor_name (string): Bank/lender name
        - account_balance (string): Current balance with $ (e.g., "$1,234.56")
        - credit_limit (string): High credit/limit with $ (e.g., "$5,000.00") - PRIORITY FIELD
        - monthly_payment (string): Monthly/min payment with $ (e.g., "$125.00") - PRIORITY FIELD  
        - account_number (string): Account number (e.g., "****1234")
        - date_opened (string): Date opened (MM/DD/YYYY format)
        - account_type (string): "Credit Card", "Auto Loan", "Mortgage", "Student Loan", "Personal Loan", "Store Card", "Line of Credit"
        - account_status (string): "Open", "Closed", "Current", "Late", "Charged Off"
        - credit_bureau (string): "Experian", "Equifax", "TransUnion"
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
        logger.debug(f"📝 Raw Gemini response: {response_text[:500]}...")
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = re.sub(r'^```json\s*', '', response_text)
            response_text = re.sub(r'\s*```$', '', response_text)
        
        # Find JSON array
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            import json
            tradelines = json.loads(json_match.group())
            logger.info(f"🔍 Gemini extracted {len(tradelines)} raw tradelines")
            
            # Validate and score Gemini results
            validated_tradelines = []
            for tradeline in tradelines:
                validation_result = field_validator.validate_tradeline(tradeline)
                
                # Add validation metadata
                tradeline["_validation"] = {
                    "confidence_score": validation_result["confidence_score"],
                    "is_valid": validation_result["is_valid"],
                    "warnings": validation_result["warnings"],
                    "errors": validation_result["errors"]
                }
                
                # Include tradelines with reasonable confidence
                if validation_result["confidence_score"] >= 0.4:  # Higher threshold for Gemini
                    validated_tradelines.append(tradeline)
                else:
                    logger.warning(f"⚠️ Excluding low-confidence Gemini tradeline: {tradeline.get('creditor_name')} (confidence: {validation_result['confidence_score']:.2f})")
            
            logger.info(f"✅ Gemini extracted {len(validated_tradelines)}/{len(tradelines)} valid tradelines")
            return validated_tradelines
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

# Import the new field mapper and validator
from utils.credit_report_field_mappings import field_mapper
from utils.field_validator import field_validator

def parse_tradelines_basic(text: str) -> List[Dict[str, Any]]:
    """Basic tradeline parsing as backup"""
    try:
        logger.info("🔧 Using basic tradeline parsing as fallback")
        tradelines = []
        lines = text.split('\n')
        
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
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for creditor names
            for pattern in creditor_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Save previous tradeline if it exists
                    if current_tradeline and current_tradeline.get("creditor_name"):
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
                    break
            
            # Enhance data extraction for current tradeline using the new field mapper
            if current_tradeline:
                # Look for account numbers (various formats)
                account_patterns = [
                    r'\*{4,}\d{4}',  # ****1234
                    r'x{4,}\d{4}',   # xxxx1234
                    r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}',  # Full card numbers
                    r'Account\s*#?\s*:?\s*(\d+)',  # Account #: 123456
                    r'Acct\s*#?\s*:?\s*(\d+)'     # Acct #: 123456
                ]
                
                for pattern in account_patterns:
                    account_match = re.search(pattern, line, re.IGNORECASE)
                    if account_match:
                        current_tradeline["account_number"] = account_match.group(0)
                        break
                
                # Use enhanced field mapper for better extraction
                if not current_tradeline["credit_limit"]:
                    extracted_limit = field_mapper.extract_credit_limit(line)
                    if extracted_limit:
                        current_tradeline["credit_limit"] = extracted_limit
                
                if not current_tradeline["monthly_payment"]:
                    extracted_payment = field_mapper.extract_monthly_payment(line)
                    if extracted_payment:
                        current_tradeline["monthly_payment"] = extracted_payment
                
                # Update account type using enhanced mapping
                extracted_type = field_mapper.extract_account_type(line, current_tradeline["creditor_name"])
                if extracted_type:
                    # Convert internal format to display format
                    type_display_map = {
                        "credit_card": "Credit Card",
                        "auto_loan": "Auto Loan", 
                        "mortgage": "Mortgage",
                        "student_loan": "Student Loan",
                        "personal_loan": "Personal Loan",
                        "store_card": "Store Card",
                        "line_of_credit": "Line of Credit",
                        "installment": "Installment Loan",
                        "business": "Business",
                        "secured": "Secured"
                    }
                    current_tradeline["account_type"] = type_display_map.get(extracted_type, extracted_type.replace("_", " ").title())
                
                # Fallback: Look for dollar amounts with basic context
                dollar_matches = re.findall(r'\$[\d,]+\.?\d*', line)
                balance_keywords = ['balance', 'amount', 'owed', 'debt', 'current']
                
                for amount in dollar_matches:
                    line_lower = line.lower()
                    
                    # Check context for balance (only if not already set)
                    if any(kw in line_lower for kw in balance_keywords) and not current_tradeline["account_balance"]:
                        current_tradeline["account_balance"] = amount
                    # Default assignment if no other fields set
                    elif not current_tradeline["account_balance"] and not current_tradeline["credit_limit"] and not current_tradeline["monthly_payment"]:
                        current_tradeline["account_balance"] = amount
                
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
            tradelines.append(current_tradeline)
        
        # Validate and score all extracted tradelines
        validated_tradelines = []
        for tradeline in tradelines:
            validation_result = field_validator.validate_tradeline(tradeline)
            
            # Add validation metadata to tradeline
            tradeline["_validation"] = {
                "confidence_score": validation_result["confidence_score"],
                "is_valid": validation_result["is_valid"],
                "warnings": validation_result["warnings"],
                "errors": validation_result["errors"]
            }
            
            # Only include tradelines with reasonable confidence
            if validation_result["confidence_score"] >= 0.3:  # Minimum 30% confidence
                validated_tradelines.append(tradeline)
            else:
                logger.warning(f"⚠️ Excluding low-confidence tradeline: {tradeline.get('creditor_name')} (confidence: {validation_result['confidence_score']:.2f})")
        
        logger.info(f"✅ Basic parsing extracted {len(validated_tradelines)}/{len(tradelines)} valid tradelines")
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
            
        logger.info(f"💾 Saving tradeline to Supabase: {tradeline.get('creditor_name', 'unknown')}")
        
        # Validate with Pydantic (Zod equivalent)
        validated_tradeline = TradelineSchema(**tradeline)
        
        # Call Supabase RPC function
        result = supabase.rpc('upsert_tradeline', {
            'p_account_balance': validated_tradeline.account_balance,
            'p_account_number': validated_tradeline.account_number,
            'p_account_status': validated_tradeline.account_status,
            'p_account_type': validated_tradeline.account_type,
            'p_credit_bureau': validated_tradeline.credit_bureau,
            'p_credit_limit': validated_tradeline.credit_limit,
            'p_creditor_name': validated_tradeline.creditor_name,
            'p_monthly_payment': validated_tradeline.monthly_payment,
            'p_user_id': user_id
        }).execute()
        
        if result.data:
            logger.info(f"✅ Tradeline saved successfully: {validated_tradeline.creditor_name}")
            return True
        else:
            logger.error(f"❌ Failed to save tradeline - no data returned: {result}")
            return False
            
    except ValidationError as e:
        logger.error(f"❌ Validation error for tradeline: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Database error while saving tradeline: {e}")
        logger.error(f"📍 Traceback: {traceback.format_exc()}")
        return False
    

    # Add this endpoint to your main.py file (after the existing endpoints)

@app.post("/save-tradelines")
async def save_tradelines_endpoint(request: dict):
    """
    Endpoint to save tradelines to database
    """
    try:
        user_id = request.get('userId')
        tradelines = request.get('tradelines', [])
        supabase.table('tradelines').select('*').execute()

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

# Also add this function to check/fix Supabase connection
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

# Update the health endpoint to include Supabase status
@app.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    supabase_available = check_supabase_connection() if supabase else False
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z", # type: ignore
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
                "available": supabase_available,  # ✅ Added availability check
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

# Chatbot endpoints
@app.post("/chat")
async def chat_endpoint(request: dict):
    """
    Main chatbot endpoint for credit-focused conversations
    """
    try:
        if not chatbot_service:
            raise HTTPException(status_code=503, detail="Chatbot service not available")
        
        user_id = request.get('userId')
        message = request.get('message')
        conversation_history = request.get('conversationHistory', [])
        
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        logger.info(f"💬 Chat request from user {user_id}: {message[:100]}...")
        
        # Generate response using chatbot service
        result = await chatbot_service.generate_response(user_id, message, conversation_history)
        
        if result["success"]:
            logger.info(f"✅ Chat response generated for user {user_id}")
            return {
                "success": True,
                "response": result["response"],
                "user_context": result.get("user_context", {}),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        else:
            logger.error(f"❌ Chat response failed: {result.get('error')}")
            return {
                "success": False,
                "error": result.get("error"),
                "response": result.get("response", "Sorry, I couldn't process your request."),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Chat endpoint failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat request failed: {str(e)}")

@app.get("/chat/history/{user_id}")
async def get_chat_history(user_id: str, limit: int = 10):
    """
    Get conversation history for a user
    """
    try:
        if not chatbot_service:
            raise HTTPException(status_code=503, detail="Chatbot service not available")
        
        logger.info(f"📜 Fetching chat history for user {user_id}")
        
        history = await chatbot_service.get_conversation_history(user_id, limit)
        
        return {
            "success": True,
            "history": history,
            "count": len(history),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"❌ Chat history request failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch chat history: {str(e)}")

@app.get("/chat/suggestions/{user_id}")
async def get_credit_suggestions(user_id: str):
    """
    Get proactive credit improvement suggestions for a user
    """
    try:
        if not chatbot_service:
            raise HTTPException(status_code=503, detail="Chatbot service not available")
        
        logger.info(f"💡 Generating credit suggestions for user {user_id}")
        
        suggestions = await chatbot_service.suggest_credit_actions(user_id)
        
        return {
            "success": suggestions["success"],
            "suggestions": suggestions.get("suggestions", []),
            "user_summary": suggestions.get("user_summary", {}),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"❌ Credit suggestions request failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate suggestions: {str(e)}")

@app.post("/process-credit-report")
async def process_credit_report(
    file: UploadFile = File(...),
    user_id: str = Form(default="default-user")
):
    """
    Main endpoint: Process uploaded credit report PDF
    FIXED: Properly handle file upload without filename attribute errors
    """
    temp_file_path = None
    
    try:
        logger.info("🚀 ===== NEW CREDIT REPORT PROCESSING REQUEST =====")
        
        # ✅ FIXED: Store filename early before file operations
        original_filename = file.filename or "unknown.pdf"
        file_content_type = file.content_type
        
        logger.info(f"📄 File: {original_filename}")
        logger.info(f"📦 Content type: {file_content_type}")
        logger.info(f"👤 User ID: {user_id}")
        
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
        
        # ✅ FIXED: Save uploaded file using content, not re-reading file
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
                
                # Try structured extraction first (best for credit_limit and monthly_payment)
                structured_tradelines = document_ai.extract_structured_tradelines(temp_file_path)
                if structured_tradelines:
                    # For structured extraction, we still need to extract text to detect bureau
                    extracted_text = document_ai.extract_text(temp_file_path)
                    detected_bureau = detect_credit_bureau(extracted_text)
                    logger.info(f"🏢 Credit bureau detected from structured path: {detected_bureau}")
                    
                    tradelines = structured_tradelines
                    processing_method = "document_ai_structured"
                    logger.info(f"✅ Document AI structured extraction successful: {len(tradelines)} tradelines")
                else:
                    # Fallback to text + AI extraction
                    extracted_text = document_ai.extract_text(temp_file_path)
                    logger.info(f"✅ Document AI text extraction successful")
                    
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
            else:
                logger.warning("⚠️ Document AI not properly configured")
                raise Exception("Document AI not configured")
                
        except Exception as doc_ai_error:
            logger.error(f"❌ Document AI processing failed: {str(doc_ai_error)}")
            
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
        
        # Step 4: Return response
        response = {
            "success": True,
            "message": f"Successfully processed {len(tradelines)} tradelines using {processing_method}",
            "tradelines_found": len(tradelines),
            "tradelines_saved": saved_count,
            "tradelines_failed": failed_count,
            "processing_method": processing_method,
            "tradelines": tradelines,
            "debug_info": {
                "file_size_bytes": len(content),
                "file_name": original_filename,  # ✅ Use stored filename
                "user_id": user_id,
                "supabase_available": supabase is not None,
                "document_ai_available": client is not None,
                "gemini_available": gemini_model is not None
            }
        }
        
        logger.info("✅ ===== PROCESSING COMPLETED SUCCESSFULLY =====")
        logger.info(f"📊 Final stats: {len(tradelines)} found, {saved_count} saved, {failed_count} failed")
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error("❌ ===== PROCESSING FAILED =====")
        logger.error(f"💥 Error: {str(e)}")
        logger.error(f"📍 Traceback: {traceback.format_exc()}")
        
        # Cleanup temp file on error
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.info("🗑️ Temporary file cleaned up after error")
            except Exception as cleanup_error:
                logger.error(f"❌ Failed to cleanup temp file: {cleanup_error}")
        
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