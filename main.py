# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llm_parser import parse_tradeline
import json
import base64
import httpx
import os
from google.cloud import documentai


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8081", "http://127.0.0.1:8081"],  # Add new Vite dev server port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Document AI configuration
GOOGLE_PROJECT_ID = "1045000590097"  # Your project ID
PROCESSOR_ID = "38ae0476f612fc35"  # Your processor ID
PROCESSOR_URL = f"https://us-documentai.googleapis.com/v1/projects/{GOOGLE_PROJECT_ID}/locations/us/processors/{PROCESSOR_ID}/processorVersions/pretrained-form-parser-v2.1-2023-06-26:process"

class TradelineRequest(BaseModel):
    text: str

class DocumentAIRequest(BaseModel):
    base64: str

async def call_google_document_ai(base64_content: str) -> str:
    """
    Call Google Document AI to extract text from PDF
    """
    try:
        # First try direct Google Cloud Document AI if credentials are available
        if os.getenv('GOOGLE_APPLICATION_CREDENTIALS') or os.path.exists('./service-account.json'):
            try:
                # Initialize the Document AI client
                client = documentai.DocumentProcessorServiceClient()
                
                # The full resource name of the processor
                processor_name = f"projects/{GOOGLE_PROJECT_ID}/locations/us/processors/{PROCESSOR_ID}"
                
                # Decode the base64 content
                pdf_content = base64.b64decode(base64_content)
                
                # Configure the request
                request = documentai.ProcessRequest(
                    name=processor_name,
                    raw_document=documentai.RawDocument(
                        content=pdf_content,
                        mime_type="application/pdf"
                    )
                )
                
                # Process the document
                result = client.process_document(request=request)
                
                # Extract the text
                document = result.document
                print(f"✅ Direct Document AI extracted {len(document.text)} characters")
                return document.text
                
            except Exception as direct_error:
                print(f"Direct Document AI failed: {direct_error}")
                # Fall through to Express server fallback
        
        # Fallback to the Express server
        print("🔄 Falling back to Express server...")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8001/document-ai",
                json={"base64": base64_content},
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                if "document" in result and "text" in result["document"]:
                    extracted_text = result["document"]["text"]
                    print(f"✅ Express server extracted {len(extracted_text)} characters")
                    return extracted_text
                else:
                    print("⚠️ No text found in Express server response")
                    return "No text extracted from document"
            else:
                print(f"❌ Express server error: {response.status_code}")
                return "Error extracting text from document"
                
    except Exception as e:
        print(f"❌ All Document AI methods failed: {e}")
        return "Error processing document with AI"

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Credit Clarity AI Server is running", "endpoints": ["/parse-tradeline", "/document-ai"]}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "credit-clarity-ai"}

@app.post("/document-ai")
async def document_ai_endpoint(request: DocumentAIRequest):
    """
    Document AI endpoint for processing PDF files
    """
    try:
        print(f"✅ Received Document AI request with base64 length: {len(request.base64)}")
        
        # Decode base64 to get file content
        try:
            pdf_content = base64.b64decode(request.base64)
            print(f"✅ Successfully decoded PDF, size: {len(pdf_content)} bytes")
        except Exception as decode_error:
            print(f"❌ Base64 decode error: {decode_error}")
            raise HTTPException(status_code=400, detail="Invalid base64 content")
        
        # Use Google Document AI for text extraction
        print("🔍 Extracting text with Google Document AI...")
        extracted_text = await call_google_document_ai(request.base64)
        print(f"✅ Extracted text length: {len(extracted_text)} characters")
        print(f"✅ First 200 chars: {extracted_text[:200]}")
        
        if len(extracted_text) < 50:
            print("⚠️ Warning: Very little text extracted from document")
        
        # Parse the extracted text using your existing LLM parser
        print("🔍 Parsing extracted text with LLM...")
        parsed_result = parse_tradeline(extracted_text)
        
        # Return Document AI compatible response
        response = {
            "document": {
                "text": extracted_text,
                "pages": [
                    {
                        "pageNumber": 1,
                        "dimension": {"width": 612, "height": 792, "unit": "PIXELS"},
                        "layout": {
                            "textAnchor": {
                                "textSegments": [{"startIndex": 0, "endIndex": len(extracted_text)}]
                            },
                            "confidence": 0.95
                        }
                    }
                ]
            },
            "entities": [parsed_result] if parsed_result else [],
            "pages": 1,
            "metadata": {
                "source": "llm-parser",
                "processingTime": "1.2s"
            }
        }
        
        print(f"✅ Successfully processed document, returning {len(response['entities'])} entities")
        return response
        
    except Exception as e:
        print(f"❌ Document AI processing error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.post("/parse-tradeline")
async def parse_tradeline_endpoint(request: TradelineRequest):
    from llm_parser import parse_tradeline

    try:
        print(f"✅ Received request with text length: {len(request.text)}")
        print(f"✅ First 100 chars: {request.text[:100]}")

        print("🔍 Calling parse_tradeline...")
        result = parse_tradeline(request.text)
        print(f"✅ Raw result: {repr(result)}")
        print(f"📊 Response type: {type(result)}")

        if result is None:
            print("❌ LLM returned None")
            raise HTTPException(status_code=500, detail="LLM returned None")

        if not isinstance(result, str) or not result.strip():
            print("❌ LLM returned empty or invalid response")
            raise HTTPException(status_code=500, detail="LLM returned empty or invalid response")

        try:
            parsed = json.loads(result.strip())
            print(f"✅ Successfully parsed JSON with {len(parsed)} fields")
            return parsed
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            print(f"🔍 Problematic response: {repr(result)}")
            raise HTTPException(status_code=500, detail=f"Invalid JSON response from LLM: {str(e)}")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing tradeline: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Credit Clarity AI Server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)