"""
PDF Credit Report Processing with Document AI + Gemini fallback
Extracts tradelines and saves to Supabase
Enhanced with comprehensive debugging and error handling
"""
import os
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
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

# Debug environment variables
logger.info(f"🔧 Environment Check:")
logger.info(f"  PROJECT_ID: {'✅ Set' if PROJECT_ID else '❌ Missing'}")
logger.info(f"  LOCATION: {LOCATION}")
logger.info(f"  PROCESSOR_ID: {'✅ Set' if PROCESSOR_ID else '❌ Missing'}")
logger.info(f"  GEMINI_API_KEY: {'✅ Set' if GEMINI_API_KEY else '❌ Missing'}")
logger.info(f"  SUPABASE_URL: {'✅ Set' if SUPABASE_URL else '❌ Missing'}")
logger.info(f"  SUPABASE_KEY: {'✅ Set' if SUPABASE_KEY else '❌ Missing'}")

# Initialize services with error handling
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
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
        """Extract tradelines using Gemini AI"""
        try:
            logger.info(f"🧠 Starting Gemini tradeline extraction from {len(text)} characters")
            
            if not gemini_model:
                raise Exception("Gemini model not initialized")
            
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
            {text[:8000]}  # Limit text for token constraints

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
                
        except Exception as e:
            logger.error(f"❌ Gemini processing failed: {str(e)}")
            logger.error(f"📍 Traceback: {traceback.format_exc()}")
            return []

def parse_tradelines_basic(text: str) -> List[Dict[str, Any]]:
    """Basic tradeline parsing as backup"""
    try:
        logger.info("🔧 Using basic tradeline parsing as fallback")
        tradelines = []
        lines = text.split('\n')
        
        # Common creditor patterns
        creditor_patterns = [
            r'(CHASE|Chase|chase)',
            r'(CAPITAL ONE|Capital One|capital one)',
            r'(CITIBANK|Citibank|citibank|CITI|Citi)',
            r'(BANK OF AMERICA|Bank of America|BOA)',
            r'(WELLS FARGO|Wells Fargo)',
            r'(DISCOVER|Discover)',
            r'(AMERICAN EXPRESS|American Express|AMEX)',
            r'(SYNCHRONY|Synchrony)',
            r'(CREDIT ONE|Credit One)'
        ]
        
        current_tradeline = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for creditor names
            for pattern in creditor_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    if current_tradeline:
                        tradelines.append(current_tradeline)
                    current_tradeline = {
                        "creditor_name": re.search(pattern, line, re.IGNORECASE).group(0),
                        "account_type": "Credit Card",
                        "account_status": "Open", 
                        "credit_bureau": "Unknown",
                        "is_negative": False,
                        "account_balance": "",
                        "credit_limit": "",
                        "monthly_payment": "",
                        "account_number": "",
                        "date_opened": "xx/xx/xxxxx",
                        "dispute_count": 0
                    }
                    break
            
            # Look for account numbers
            if current_tradeline:
                account_match = re.search(r'\*{4,}\d{4}', line)
                if account_match:
                    current_tradeline["account_number"] = account_match.group(0)
                
                # Look for dollar amounts
                dollar_matches = re.findall(r'\$[\d,]+\.?\d*', line)
                for amount in dollar_matches:
                    if not current_tradeline["account_balance"]:
                        current_tradeline["account_balance"] = amount
                    elif not current_tradeline["credit_limit"]:
                        current_tradeline["credit_limit"] = amount
        
        if current_tradeline:
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

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",  # Will be updated
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
                "configured": bool(SUPABASE_URL and SUPABASE_KEY and supabase),
                "url": SUPABASE_URL
            }
        },
        "environment": {
            "python_version": "3.x",
            "fastapi_version": "0.x",
        }
    }
    
    # Update timestamp
    from datetime import datetime
    health_status["timestamp"] = datetime.utcnow().isoformat() + "Z"
    
    logger.info("🔍 Health check requested")
    return health_status

@app.post("/process-credit-report")
async def process_credit_report(
    file: UploadFile = File(...),
    user_id: str = Form(default="default-user")
):
    """
    Main endpoint: Process uploaded credit report PDF
    Enhanced with comprehensive debugging
    """
    temp_file_path = None
    
    try:
        logger.info("🚀 ===== NEW CREDIT REPORT PROCESSING REQUEST =====")
        logger.info(f"📄 File: {file.filename}")
        logger.info(f"📦 Content type: {file.content_type}")
        logger.info(f"👤 User ID: {user_id}")
        
        # Validate file type
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            logger.error("❌ Invalid file type")
            raise HTTPException(status_code=400, detail="Only PDF files allowed")
        
        # Read file content
        logger.info("📖 Reading file content...")
        content = await file.read()
        logger.info(f"📦 File size: {len(content)} bytes ({len(content)/1024/1024:.2f} MB)")
        
        if len(content) == 0:
            logger.error("❌ Empty file")
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(content)
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
                
                import PyPDF2 # type: ignore
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
                "file_name": file.filename,
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

if __name__ == "__main__":
    import uvicorn # type: ignore
    logger.info("🚀 Starting Credit Report Processor API...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")