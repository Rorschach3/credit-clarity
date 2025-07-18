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
    
    def extract_text(self, pdf_path: str) -> str:
        """Extract text from PDF using Document AI"""
        try:
            logger.info(f"📄 Starting Document AI text extraction from {pdf_path}")
            
            with open(pdf_path, "rb") as pdf_file:
                pdf_content = pdf_file.read()
            
            logger.info(f"📦 PDF content size: {len(pdf_content)} bytes")
            
            raw_document = documentai.RawDocument(
                content=pdf_content,
                mime_type="application/pdf"
            )
            
            name = self.client.processor_path(PROJECT_ID, LOCATION, PROCESSOR_ID)
            logger.info(f"🔗 Using processor: {name}")
            
            request = documentai.ProcessRequest(name=name, raw_document=raw_document)
            
            logger.info("🚀 Sending request to Document AI...")
            result = self.client.process_document(request=request)
            
            extracted_text = result.document.text
            logger.info(f"✅ Document AI extracted {len(extracted_text)} characters")
            logger.debug(f"📝 First 500 chars: {extracted_text[:500]}...")
            
            return extracted_text
            
        except Exception as e:
            logger.error(f"❌ Document AI failed: {str(e)}")
            logger.error(f"📍 Traceback: {traceback.format_exc()}")
            raise

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
        Extract credit tradeline information from this credit report text. 
        Return ONLY a JSON array of objects with these exact fields:
        - creditor_name (string)
        - account_balance (string, include $ if present)
        - credit_limit (string, include $ if present) 
        - monthly_payment (string, include $ if present)
        - account_number (string)
        - date_opened (string, format: MM/DD/YYYY)
        - account_type (string: Credit Card, Mortgage, Auto Loan, etc.)
        - account_status (string: Open, Closed, Current, etc.)
        - credit_bureau (string: Experian, Equifax, TransUnion)
        - is_negative (boolean: true if account has negative marks)

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
            logger.info(f"✅ Gemini extracted {len(tradelines)} tradelines")
            return tradelines
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
            
            # Enhance data extraction for current tradeline
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
                
                # Look for dollar amounts with better context
                dollar_matches = re.findall(r'\$[\d,]+\.?\d*', line)
                balance_keywords = ['balance', 'amount', 'owed', 'debt']
                limit_keywords = ['limit', 'credit limit', 'maximum']
                payment_keywords = ['payment', 'monthly', 'minimum']
                
                for amount in dollar_matches:
                    line_lower = line.lower()
                    
                    # Check context for balance
                    if any(kw in line_lower for kw in balance_keywords) and not current_tradeline["account_balance"]:
                        current_tradeline["account_balance"] = amount
                    # Check context for credit limit
                    elif any(kw in line_lower for kw in limit_keywords) and not current_tradeline["credit_limit"]:
                        current_tradeline["credit_limit"] = amount
                    # Check context for payment
                    elif any(kw in line_lower for kw in payment_keywords) and not current_tradeline["monthly_payment"]:
                        current_tradeline["monthly_payment"] = amount
                    # Default assignment if no context
                    elif not current_tradeline["account_balance"]:
                        current_tradeline["account_balance"] = amount
                    elif not current_tradeline["credit_limit"]:
                        current_tradeline["credit_limit"] = amount
                
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
        
        logger.info(f"✅ Basic parsing extracted {len(tradelines)} tradelines")
        return tradelines
        
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
        
        # Step 1: Try Document AI first
        try:
            if client and PROJECT_ID and PROCESSOR_ID:
                logger.info("🤖 Attempting Document AI processing...")
                processing_method = "document_ai"
                
                extracted_text = document_ai.extract_text(temp_file_path)
                logger.info(f"✅ Document AI text extraction successful")
                
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
            
            # Fallback: Try PyPDF2 + Gemini
            try:
                logger.info("🔄 Trying PyPDF2 + Gemini fallback...")
                processing_method = "pypdf2_fallback"
                
                with open(temp_file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text()
                
                logger.info(f"📖 PyPDF2 extracted {len(text)} characters")
                
                if gemini_model and text.strip():
                    tradelines = gemini_processor.extract_tradelines(text)
                    processing_method = "pypdf2 + gemini"
                    logger.info(f"✅ PyPDF2 + Gemini successful: {len(tradelines)} tradelines")
                
                if not tradelines:
                    logger.info("🔧 Using basic parsing as final fallback...")
                    tradelines = parse_tradelines_basic(text)
                    processing_method = "pypdf2 + basic"
                    
            except Exception as fallback_error:
                logger.error(f"❌ All processing methods failed: {str(fallback_error)}")
                logger.error(f"📍 Traceback: {traceback.format_exc()}")
                raise HTTPException(status_code=500, detail="Could not process PDF with any method")
        
        logger.info(f"📊 Processing completed using: {processing_method}")
        logger.info(f"📈 Found {len(tradelines)} tradelines")
        
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