# Credit Clarity - AI-Powered Credit Report Analysis

## Project Overview
Credit Clarity is a full-stack application that helps users analyze credit reports, identify negative items, and generate dispute letters. The application uses AI/ML for document processing and provides an intuitive dashboard for credit management.

## Architecture
- **Frontend**: React/TypeScript with Vite
- **Backend**: Python with Supabase
- **Database**: PostgreSQL via Supabase
- **Document Processing**: Google Document AI, OCR
- **Authentication**: Supabase Auth

## Key Directories
- `backend/` - Python backend services
- `frontend/` - React frontend application  
- `supabase/` - Database migrations and edge functions
- `.claude/` - Claude Code configuration

## Development Commands
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Frontend (if using frontend directory)
cd frontend
npm install
npm run dev

# Supabase
npx supabase start
npx supabase db reset
```

## Testing
```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests (if applicable)
cd frontend
npm test
```

## Key Features
- Credit report upload and parsing
- AI-powered tradeline extraction
- Dispute letter generation
- Real-time processing status
- User dashboard with credit insights