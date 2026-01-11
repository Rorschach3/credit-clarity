<div align="center">

![Credit Clarity Logo](https://i.ibb.co/21wJjHWr/Credit-Clarity-Ghost.png)
</div>

<h1 align="center"><span style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #2C3E50;">CreditClarityAI</span></h1>

<p align="center"><em>AI-powered credit report analysis and dispute‐letter generation to improve your credit score.</em></p>

---

<div align="center">

** Table of Contents**

1. [Overview](#overview)
2. [Key Metrics](#key-metrics)
3. [Features](#features)
4. [Tech Stack](#tech-stack)
5. [Screenshots](#screenshots)
6. [Getting Started](#getting-started)
7. [Project Structure](#project-structure)
8. [FAQ Highlights](#faq-highlights)

</div>

---

## <span style="color: #16A085;">Overview</span>

<p>
Created by a former credit repair specialist, <strong>CreditClarityAI</strong> uses OCR + AI to:
</p>

<ul>
  <li> Identify credit‐report errors with high accuracy</li>
  <li> Generate customized, FCRA-compliant dispute letters</li>
  <li> Automate the credit-repair workflow</li>
</ul>


---


## <span style="color: #D35400;">Features</span>

-  <strong>Dispute Generator</strong>: Upload or enter report, AI drafts letters.
-  <strong>OCR Integration</strong>: Scan PDFs & images for errors.
-  <strong>Custom Templates</strong>: Review & edit letters pre-send.
-  <strong>Progress Dashboard</strong>: Track submissions, responses, score changes.

---

## <span style="color: #27AE60;">Tech Stack</span>

| Layer          | Technology                    |
| -------------- | ----------------------------- |
| Frontend       | React, Tailwind CSS           |
| Backend        | Flask (Python)                |
| OCR Processing | Tesseract, OpenCV             |
| AI / NLP       | PyTorch, Hugging Face         |
| Database       | PostgreSQL                    |
| Auth           | JWT / Flask-Login             |
| Deployment     | Docker, AWS Elastic Beanstalk |

---

## <span style="color: #34495E;">Screenshots</span>

<p align="center">
  <img src="./images/dashboard.png" alt="Dashboard" width="600"/>
  <br><em>Dashboard</em>
</p>
<p align="center">
  <img src="images/disputeGenerator.png" alt="Generator" width="600"/>
  <br><em>Dispute Generator</em>
</p>
<p align="center">
  <img src="images/disputes.png" alt="Disputes" width="600"/>
  <br><em>Disputes</em>
</p>

---

## <span style="color: #7F8C8D;">Getting Started</span>

<ol>
  <li>**Clone**  
    <pre><code>git clone https://github.com/rorschach3/credit-clarity-ai-assist.git
cd creditclarityai</code></pre>
  </li>
  <li>**Virtual Env**  
    <pre><code>python3 -m venv venv
source venv/bin/activate</code></pre>
  </li>
  <li>**Install**  
    <pre><code>pip install -r requirements.txt</code></pre>
  </li>
  <li>**Configure**  
    <pre><code>cp .env.example .env
# Fill in FLASK_SECRET_KEY, DATABASE_URL, OCR_SERVICE_KEY</code></pre>
  </li>
  <li>**Migrate DB**  
    <pre><code>flask db upgrade</code></pre>
  </li>
  <li>**Run**  
    <pre><code>flask run --host=0.0.0.0 --port=5000</code></pre>
  </li>
</ol>

> Open <a href="http://localhost:5000">localhost:5000</a> in your browser.

---

## <span style="color: #2E86C1;">Project Structure</span>

```text
creditclarityai/
├─ app/
│  ├─ templates/   # Jinja2 HTML
│  ├─ static/      # CSS, JS, images
│  ├─ ocr/         # OCR modules
│  ├─ ai/          # Model code
│  ├─ auth.py      # Auth logic
│  └─ disputes.py  # Dispute routes
├─ migrations/     # DB migrations
├─ tests/          # Unit & integration tests
├─ requirements.txt
├─ .env.example
└─ run.py          # App entry point
```

---

## <span style="color: #2C3E50;">FAQ Highlights</span>

> ### Why are dispute letters effective?
>
> Under the FCRA, bureaus must investigate disputes within 30 days. If they do not verify within 30 days they must remove inaccuracies.

> ### How does AI boost success?
>
> Trained on thousands of letters, our models optimize tone, legal wording, and proof patterns.

> ### What can be disputed?
>
> Late payments, collections, charge-offs, repossessions, bankruptcies, student loans, auto loans, mortgages, child support.

For full FAQs, see [`faq.html`](app/templates/faq.html)

------------------------
CreditReportUploadPage.tsx
TradelinesPage.tsx
DisputeLetterPage.tsx
DisputePacketPage.tsx
DisputeWizardPage.tsx
<div align="center">

![Credit Clarity Logo](https://i.ibb.co/21wJjHWr/Credit-Clarity-Ghost.png)
</div>

<h1 align="center"><span style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #2C3E50;">CreditClarityAI</span></h1>

<p align="center"><em>AI-powered credit report analysis and dispute‐letter generation to improve your credit score.</em></p>

---

<div align="center">

**Table of Contents**

1. [Overview](#overview)
2. [Key Metrics](#key-metrics)
3. [Features](#features)
4. [Tech Stack](#tech-stack)
5. [Screenshots](#screenshots)
6. [Getting Started](#getting-started)
7. [Project Structure](#project-structure)
8. [FAQ Highlights](#faq-highlights)

</div>

---

## <span style="color: #16A085;">Overview</span>

<p>
Created by a former credit repair specialist, <strong>CreditClarityAI</strong> uses OCR + AI to:
</p>

<ul>
  <li>Identify credit‐report errors with high accuracy</li>
  <li>Generate customized, FCRA-compliant dispute letters</li>
  <li>Automate the credit-repair workflow</li>
</ul>


---


## <span style="color: #D35400;">Features</span>

- <strong>Dispute Generator</strong>: Upload or enter report, AI drafts letters.
- <strong>OCR Integration</strong>: Scan PDFs & images for errors.
- <strong>Custom Templates</strong>: Review & edit letters pre-send.
- <strong>Progress Dashboard</strong>: Track submissions, responses, score changes.

---

## <span style="color: #27AE60;">Tech Stack</span>

| Layer          | Technology                    |
| -------------- | ----------------------------- |
| Frontend       | React, Tailwind CSS           |
| Backend        | Flask (Python)                |
| OCR Processing | Tesseract, OpenCV             |
| AI / NLP       | PyTorch, Hugging Face         |
| Database       | PostgreSQL                    |
| Auth           | JWT / Flask-Login             |
| Deployment     | Docker, AWS Elastic Beanstalk |

---

## <span style="color: #34495E;">Screenshots</span>

<p align="center">
  <img src="./images/dashboard.png" alt="Dashboard" width="600"/>
  <br><em>Dashboard</em>
</p>
<p align="center">
  <img src="images/disputeGenerator.png" alt="Generator" width="600"/>
  <br><em>Dispute Generator</em>
</p>
<p align="center">
  <img src="images/disputes.png" alt="Disputes" width="600"/>
  <br><em>Disputes</em>
</p>

---

## <span style="color: #7F8C8D;">Getting Started</span>

<ol>
  <li>Clone  
    <pre><code>git clone https://github.com/rorschach3/credit-clarity-ai-assist.git
cd credit-clarity-ai-assist</code></pre>
  </li>
  <li>npm install  
    <pre><code>npm install</code></pre>
  </li>
  <li>Configure  
    <pre><code>.env.example
# Fill in your secrets from the .env example file</code></pre>
  </li>
  <li>Run  
    <pre><code>npm run dev</code></pre>
  </li>
  <li>Test
    <pre><code>run npm test</code></pre>
  </li>
  <li>Extended Tests  
    <pre><code>npm run test:coverage</code></pre>
</ol>

> Open <a href="http://localhost:8080">localhost:8080</a> in your browser.

---

## <span style="color: #E67E22;">Usage - Credit Report Tradeline Extraction</span>

### Starting the Servers

#### Backend Server (FastAPI - Port 8000)

```bash
cd backend
python3 -m venv venv  # Create virtual environment if needed
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Verify backend is running:
```bash
curl http://localhost:8000/api/health
# Response: {"status":"healthy","service":"credit-report-processor"}
```

#### Frontend Server (Vite - Port 8080)

```bash
cd frontend
npm install
npm run dev
```

Access the web interface at: **http://localhost:8080**

---

### Extracting Tradelines from Credit Reports

#### Method 1: Using the Web Interface

1. **Open your browser** and navigate to `http://localhost:8080`
2. **Go to Credit Report Upload page** (typically `/upload` route)
3. **Upload your PDF credit report** (TransUnion, Experian, or Equifax)
4. **Select processing method**: Choose "AI Analysis (Advanced)" for best results
5. **Monitor progress**: Watch the processing indicator
6. **Review results**: All extracted tradelines will be displayed with the following 9 fields:
   - `creditor_name` - Name of the creditor/lender
   - `account_number` - Masked account number (****1234)
   - `credit_bureau` - Credit bureau (TransUnion, Experian, Equifax)
   - `date_opened` - Account opening date
   - `account_balance` - Current balance owed
   - `monthly_payment` - Monthly payment amount
   - `account_type` - Type of account (Credit Card, Auto Loan, Mortgage, etc.)
   - `account_status` - Account status (Open, Closed, etc.)
   - `credit_limit` - Credit limit or high balance

#### Method 2: Using the API (curl)

**Quick Test - Extract Text Only:**
```bash
curl -X POST "http://localhost:8000/api/quick-test" \
  -F "file=@TransUnion-06-10-2025.pdf"
```

**Full Extraction - Get All Tradelines:**
```bash
curl -X POST "http://localhost:8000/api/process-credit-report" \
  -F "file=@your-credit-report.pdf" \
  -o results.json

# View results
cat results.json | python3 -m json.tool
```

**Example Response:**
```json
{
  "success": true,
  "job_id": "847c25e8-7a59-45ee-83df-af6840fadc93",
  "detected_bureau": "TransUnion",
  "tradelines_count": 26,
  "tradelines": [
    {
      "id": 1,
      "creditor_name": "Capital One",
      "account_number": "2365****",
      "credit_bureau": "TransUnion",
      "date_opened": "2022-10-19",
      "account_balance": "459",
      "monthly_payment": "28",
      "account_type": "Credit Card",
      "account_status": "Open",
      "credit_limit": null,
      "confidence_score": 0.95
    }
  ],
  "message": "Successfully extracted 26 tradelines"
}
```

---

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/process-credit-report` | POST | Full PDF processing and tradeline extraction |
| `/api/quick-test` | POST | Quick PDF text extraction test |
| `/api/upload` | POST | Simple file upload |
| `/api/llm/status` | GET | LLM service status |

---

### Supported Credit Bureaus

- ✅ **TransUnion** - Fully tested and working
- ✅ **Experian** - Pattern-based extraction
- ✅ **Equifax** - Pattern-based extraction

The system automatically detects which bureau your report is from and applies bureau-specific extraction rules.

---

### Extraction Results

**Recent Test Results:**
- **PDF**: TransUnion-06-10-2025.pdf (54 pages, 60,710 characters)
- **Bureau Detected**: TransUnion (high confidence)
- **Tradelines Extracted**: 26 accounts
- **Fields Captured**: All 9 required fields per tradeline
- **Confidence Scores**: Range 0.5 - 0.95

---

### Troubleshooting

**Backend Server Won't Start:**
```bash
# Check for import errors
cd backend
venv/bin/python -c "from routers.parse_router import router"
```

**No Tradelines Extracted:**
- Check PDF text extraction: Use `/api/quick-test` endpoint
- Verify bureau detection: Look for bureau name in text preview
- Review extraction logs: Check backend console output

**Low Extraction Quality:**
- Ensure PDF is text-based (not scanned image)
- For image-based PDFs, consider using Document AI
- Check that the PDF is from a supported credit bureau

**Port Already in Use:**
```bash
# Find process using port 8000
lsof -i :8000
# Kill the process
kill -9 <PID>
```

---

### Documentation

For detailed documentation on improvements and prompt optimization, see:
- **[EXTRACTION_IMPROVEMENTS.md](EXTRACTION_IMPROVEMENTS.md)** - Comprehensive guide with API usage, test results, and future enhancements
- **[ralph-loop-setup-prompt.md](ralph-loop-setup-prompt.md)** - Setup instructions for the ralph-loop method

---

## <span style="color: #2E86C1;">Project Structure</span>

```text
creditclarityai/
├─ app/
│  ├─ templates/   # Jinja2 HTML
│  ├─ static/      # CSS, JS, images
│  ├─ ocr/         # OCR modules
│  ├─ ai/          # Model code
│  ├─ auth.py      # Auth logic
│  └─ disputes.py  # Dispute routes
├─ migrations/     # DB migrations
├─ tests/          # Unit & integration tests
├─ requirements.txt
├─ .env.example
└─ run.py          # App entry point
```
<p style="text-align: center; font-weight: bold; font-size: 1.5rem;">
 Tradeline Data Flow with Duplicate Prevention
</p>

```mermaid
graph TD
    A[User Uploads PDF] --> B(OCR Process)
    B --> C{Extract Raw Tradeline Text}
    C --> D[LLM Parser]
    D --> E{Parsed Tradeline Data}
    E -- Add user_id and enrich data --> F[Edge Function: add-tradeline]
    F --> G{Validate Tradelines
    with Zod Schema}
    G -- If validation fails --> H[Return 400 Error]
    G -- If validation passes --> I{Check for Existing Tradelines}
    I -- Conflict/Duplicate found --> J[UPSERT: Update Existing Tradeline]
    I -- No conflict/New tradeline --> K[UPSERT: Insert New Tradeline]
    J --> L[Supabase Database: tradelines table]
    K --> L
    L --> M[Return Success Response]
    F -- Database/Function Error --> N[Return 500 Error]
  ```
---

## <span style="color: #2C3E50;">FAQ Highlights</span>

> ### Why are dispute letters effective?
>
> Under the FCRA, bureaus must investigate disputes within 30 days. If they do not verify within 30 days they must remove inaccuracies.

> ### How does AI boost success?
>
> Trained on thousands of letters, our models optimize tone, legal wording, and proof patterns.

> ### What can be disputed?
>
> Late payments, collections, charge-offs, repossessions, bankruptcies, student loans, auto loans, mortgages, child support.

For full FAQs, see [`faq.html`](app/templates/faq.html)

------------------------

Tradeline data extraction workflow: 
```mermaid
flowchart TD
    A[User]  --> B["Uploads PDF or document via Web App"]
    B --> C["document-ai-parser.ts Frontend"]
    C -- Converts file to base64 if needed --> D["Converts file to base64 if needed"]
    D -- Sends base64 file to FastAPI backend endpoint --> E["main.py FastAPI Backend"]
    E -- Tries direct Google Document AI Python client --> F["Google Document AI Cloud OCR"]
    F -- Extracted Text --> G["Extracted Text"]
    E -- If Python client fails or unavailable --> H["Fallback Proxy server document-ai.js on Node/Express"]
    H -- Google Document AI via REST API --> I["Google Document AI via REST API"]
    I -- Extracted Text --> J["Extracted Text"]
    E -- If Node proxy unavailable --> K["Supabase Edge Function for OCR optional"]
    K -- Extracted Text --> L["Extracted Text"]
    E -- Text Extraction Success --> M["Text Extraction Success"]
    M --> N["llm_parser.py Backend LLM Parsing"]
    N -- Parsed Tradeline Data JSON --> O["Parsed Tradeline Data JSON"]
    O -- Backend returns parsed data to Frontend --> P["Backend returns parsed data to Frontend"]
    P -- Frontend displays results and saves to Supabase DB --> Q["Frontend displays results and saves to Supabase DB"]
```

```mermaid
flowchart TD
    A[User (Frontend)] --> B[Uploads PDF or document via Web App]
    B --> C[document-ai-parser.ts (Frontend)]
    C --> D[Converts file to base64 (if needed)]
    D --> E[Sends base64 file to FastAPI backend endpoint]
    E --> F[main.py (FastAPI Backend)]
        v
[ document-ai-parser.ts (Frontend) ]
        |
        |---> Converts file to base64 (if needed)
        |
        v
[ Sends base64 file to FastAPI backend endpoint ]
        |
        v
[ main.py (FastAPI Backend) ]
        |
        |---> Tries direct Google Document AI (Python client)
        |         |
        |         |--(If credentials available)
        |         v
        |     [ Google Document AI (Cloud OCR) ]
        |         |
        |         v
        |     [ Extracted Text ]
        |
        |---> If Python client fails or unavailable:
        |         |
        |         v
        |     [ Fallback: Proxy server (document-ai.js on Node/Express) ]
        |         |
        |         v
        |     [ Google Document AI via REST API ]
        |         |
        |         v
        |     [ Extracted Text ]
        |
        |---> If Node proxy unavailable:
        |         |
        |         v
        |     [ Supabase Edge Function for OCR (optional) ]
        |         |
        |         v
        |     [ Extracted Text ]
        |
        v
[ Text Extraction Success ]
        |
        v
[ llm_parser.py (Backend LLM Parsing) ]
        |
        v
[ Parsed Tradeline Data (JSON) ]
        |
        v
[ Backend returns parsed data to Frontend ]
        |
        v
[ Frontend displays results and saves to Supabase DB ]
```

Example Tradeline json
```json
{
  "creditor_name": "Bank or Credit Union",
  "account_number": "000000XXXX",
  "account_balance": "$0",
  "created_at": "0000-00-00",
  "credit_limit": "$0",
  "monthly_payment": "$0",
  "date_opened": "00/0000",
  "is_negative": false,
  "account_type": "credit_card, collection, mortgage, etc.",
  "account_status": "closed",
  "dispute_count": 0
}


  The PDF tradeline extraction process follows a comprehensive multi-stage pipeline. Here's the complete workflow:

  Stage 1: File Upload & Preprocessing

  - Entry Point: backend/main.py handles file uploads
  - Storage: backend/services/storage_service.py stores uploaded PDFs

  Stage 2: OCR Processing

  - File: backend/services/ocr_service.py
  - Process: Adds OCR text layer using OCRmyPDF + Tesseract for better text extraction

  Stage 3: PDF Chunking

  - File: backend/services/pdf_chunking_service.py
  - Process: Splits large PDFs into ≤30 page chunks using pikepdf/PyPDF2

  Stage 4: Document AI Processing

  - Main Orchestrator: backend/services/document_processor_service.py
  - Document AI Service: backend/services/document_ai_service.py
  - Process: Google Document AI extracts text, tables, and structured data from each chunk

  Stage 5: LLM Processing

  - File: backend/services/llm_parser_service.py
  - Process: AI processes raw text to extract structured tradeline data
  - Config: backend/config/llm_config.py for LLM settings

  Stage 6: Bureau Detection & Parsing

  - Bureau Detection: backend/enhanced_bureau_detection.py
  - Bureau Parsers: backend/bureau_specific_parsers.py
  - Process: Identifies credit bureau (Experian/Equifax/TransUnion) and applies bureau-specific parsing rules

  Stage 7: Enhanced Processing & Validation

  - Enhanced Service: backend/services/enhanced_tradeline_service.py
  - Validation: backend/utils/field_validator.py
  - Deduplication: backend/tradeline_deduplication.py
  - Process: Validates data, handles duplicates, enriches existing tradelines

  Stage 8: Data Models & Storage

  - Models: backend/models/tradeline_models.py defines data structures
  - Database Operations: Final tradelines stored in Supabase

  Frontend Integration

  - PDF Processor: frontend/src/utils/pdf-processor.ts
  - Document AI Parser: frontend/src/utils/document-ai-parser.ts
  - Tradeline Parser: frontend/src/utils/tradeline/parser.ts
  - UI Components: frontend/src/components/credit-upload/ directory

  Key Processing Flow:

  1. PDF Upload → OCR Text Layer → PDF Chunking → Document AI → LLM Processing → Bureau Detection → Bureau-Specific Parsing → Validation & Deduplication → Database Storage

  The system handles the complete pipeline from raw PDF credit reports to structured tradeline data with comprehensive error handling and validation at each stage.



  --------------------------



  📁 Recommended File Structure
backend/
├── main.py                     # FastAPI app entry point
├── config/
│   ├── __init__.py
│   ├── settings.py            # Environment variables & config
│   └── database.py            # Supabase client setup
├── core/
│   ├── __init__.py
│   ├── coordination.py        # CoordinatedBackend system
│   └── exceptions.py          # Custom exceptions
├── models/
│   ├── __init__.py
│   ├── tradeline.py          # Pydantic models
│   └── chat.py               # Chat models
├── services/
│   ├── __init__.py
│   ├── document_ai.py        # Document AI processing
│   ├── gemini.py             # Gemini AI processing
│   ├── pdf_processing.py     # PDF extraction & parsing
│   ├── credit_bureau.py      # Bureau detection logic
│   ├── tradeline_parser.py   # Tradeline parsing logic
│   ├── supabase_service.py   # Database operations
│   └── chatbot_service.py    # Keep existing chatbot
├── api/
│   ├── __init__.py
│   ├── dependencies.py       # FastAPI dependencies
│   └── routes/
│       ├── __init__.py
│       ├── upload.py         # File upload endpoints
│       ├── processing.py     # Credit report processing
│       ├── tradelines.py     # Tradeline CRUD
│       ├── chat.py           # Chat endpoints
│       └── health.py         # Health check endpoints
└── utils/
    ├── __init__.py
    ├── field_mappings.py      # Credit report field mappings
    ├── validators.py          # Data validation
    └── file_helpers.py        # File handling utilities
Would you like me to:

Start with the core configuration files (settings.py, database.py, main.py)?
Focus on the service layer (document_ai.py, gemini.py, etc.)?
Create the API routes structure (upload.py, processing.py, etc.)?
Break down the coordination system first
