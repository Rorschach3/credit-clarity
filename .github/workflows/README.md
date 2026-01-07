# GitHub Actions Workflows

## Workflows

### `ci.yml` - Continuous Integration
**Triggers:** Push or PR to `main` or `master` branches
**Purpose:** Run linting, tests, and builds for quality checks

**Jobs:**
- `node_frontend`: Lint, test, and build all npm workspaces (frontend)
- `python_backend`: Lint (ruff), type-check (mypy), and test (pytest) backend

### `deploy.yml` - Production Deployment
**Triggers:** Push to `main` branch only
**Purpose:** Build and deploy to Vercel production

**Required Secrets:**
- `VITE_API_URL` - Backend API URL
- `VITE_SUPABASE_URL` - Supabase project URL
- `VITE_SUPABASE_ANON_KEY` - Supabase anonymous key
- `VERCEL_TOKEN` - Vercel deployment token
- `VERCEL_PROJECT_ID` - Vercel project ID
- `VERCEL_ORG_ID` - Vercel organization ID

## Local Testing

Test CI locally before pushing:

```bash
# Frontend checks
npm run lint
npm run test
npm run build

# Backend checks
cd backend
pip install -r requirements.txt -r requirements-test.txt
ruff check .
mypy . --ignore-missing-imports
pytest -v
```

## Configuration

All workflows use:
- Node.js 20
- Python 3.11
- npm workspaces for monorepo structure
