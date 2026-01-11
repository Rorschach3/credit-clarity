# Ralph-Loop Setup & Credit Report Extraction Task

**Objective**: Set up development environment, start frontend and backend servers, upload a credit report PDF, and extract tradeline fields.

## Prerequisites
- File to process: `TransUnion-06-10-2025.pdf` (located in project root)
- Branch: `claude/ralph-loop-setup-prompt-rrm7I`

## Task Breakdown

### Phase 1: Backend Setup & Startup

#### 1. Create missing backend entry point (`backend/main.py`)
- Initialize FastAPI application
- Configure CORS for frontend communication (allow `http://localhost:8080`)
- Include the parse_router from `routers/parse_router.py`
- Add any additional routers for credit report processing
- Set up uvicorn server configuration

#### 2. Set up Python environment
```bash
cd backend
python -m venv venv  # Create virtual environment if needed
source venv/bin/activate  # On Linux/Mac (or venv\Scripts\activate on Windows)
pip install -r requirements.txt
```

#### 3. Start FastAPI backend server
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
- Server should run on `http://localhost:8000`
- Verify with `/docs` endpoint for API documentation

### Phase 2: Frontend Setup & Startup

#### 1. Install frontend dependencies (if needed)
```bash
cd frontend
npm install
```

#### 2. Start Vite development server
```bash
npm run dev
```
- Server should run on `http://localhost:8080`
- Hot module replacement (HMR) enabled

### Phase 3: Credit Report Upload & Extraction

#### 1. Navigate to Credit Report Upload Page
- Open browser to `http://localhost:8080`
- Navigate to the credit report upload page (path: `/upload` or similar)
- Component: `CreditReportUploadPage.tsx`

#### 2. Upload PDF file
- Select file: `TransUnion-06-10-2025.pdf`
- Choose processing method: **AI Analysis (Advanced)** for best extraction accuracy
- Monitor upload progress via `ProcessingProgress.tsx` component

#### 3. Extract the following tradeline fields
- `account_number` - Account identification number
- `credit_bureau` - Credit bureau name (TransUnion expected)
- `date_opened` - Account opening date
- `account_balance` - Current account balance
- `monthly_payment` - Monthly payment amount
- `creditor_name` - Name of the creditor/lender
- `account_type` - Type of account (revolving, installment, etc.)
- `account_status` - Current account status (open, closed, etc.)
- `credit_limit` - Credit limit for the account

#### 4. Verification
- Review extracted tradelines in `DisplayTradelinesList.tsx`
- Check for confidence scores (should be >0.3)
- Verify automatic database save to Supabase `tradelines` table
- Confirm bureau detection identified "TransUnion"

### Phase 4: Missing Infrastructure Setup (Ralph-Loop Core)

As this is the ralph-loop setup branch, you should also create these missing files:

#### 1. `backend/config/llm_config.py`
- LLM API configuration (OpenAI/Gemini)
- Model selection and parameters
- Token limits and retry logic

#### 2. `backend/models/llm_models.py`
- Pydantic models: `NormalizationResult`, `ValidationIssue`, `ConsumerInfo`
- Response structures for LLM completions

#### 3. `backend/services/prompt_templates.py`
- Prompt template manager class
- Methods for tradeline normalization, validation, and extraction prompts
- Bureau-specific prompt variations

## Expected Outputs
- Both servers running successfully
- Credit report uploaded and processed
- Tradelines extracted with all 9 specified fields
- Data persisted to database
- Confidence scores displayed for each extracted field

## Success Criteria
- ✅ Backend server accessible at `localhost:8000`
- ✅ Frontend server accessible at `localhost:8080`
- ✅ PDF upload completes without errors
- ✅ All 9 tradeline fields extracted for each account
- ✅ Bureau correctly identified as "TransUnion"
- ✅ Data saved to Supabase database
- ✅ Ralph-loop infrastructure files created

---

**Note**: The ralph-loop method refers to an iterative refinement process where LLM prompts are used to extract, normalize, and validate credit report data through multiple passes, improving accuracy with each iteration.
