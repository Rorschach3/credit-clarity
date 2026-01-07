---
stepsCompleted: [1, 2, "step-01b-continue", 3, 4, 5, 6, 7, 8]
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - docs/COMPLETE_PACKET_IMPLEMENTATION.md
  - docs/FUZZY_MATCHING_README.md
  - docs/ARCHITECTURE_GUIDE.md
  - docs/PERFORMANCE_SETUP.md
  - docs/API_DOCUMENTATION.md
  - docs/TRADELINE_EXTRACTION_SUMMARY.md
  - docs/DOCUMENT_AI_CHUNKING_README.md
  - docs/parsing-validation-results.md
  - docs/SECURITY_SETUP.md
  - docs/CUSTOM_DOCUMENT_AI_TRAINING_PLAN.md
  - docs/OCR_Fast_Processing_Plan.md
  - docs/CLAUDE.md
workflowType: 'architecture'
project_name: 'credit-clarity'
user_name: 'Rorschache'
date: '2026-01-04T08:14:23Z'
lastStep: 8
status: 'complete'
completedAt: '2026-01-04T20:54:45Z'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
39 FRs across user onboarding, report ingestion, tradeline extraction, data normalization, dispute packet creation, dispute monitoring, paid fulfillment, admin operations, mailing workflows, developer support, notifications, and support tickets. These require a reliable extraction pipeline, multi-role access controls, and operational workflows for mailing and support.

**Non-Functional Requirements:**
Performance (2 min analysis, 1 min letter generation), security/privacy (encryption, RBAC, audit logs), reliability (99.5% uptime, <1% failures), scalability (~3k users/12 months; 13% paid), and integration resilience with Supabase + Document AI.

**Scale & Complexity:**
- Primary domain: api_backend + web_app
- Complexity level: medium-high
- Estimated architectural components: 8-10 (ingestion, extraction, normalization, storage, dispute generation, monitoring, fulfillment ops, admin/support tooling, integrations, auth)

### Technical Constraints & Dependencies

- Supabase Auth + Postgres for identity and data storage.
- Supabase storage buckets for PDFs and packet artifacts.
- Google Document AI / OCR for parsing.
- Strict accuracy and correctness targets for critical fields and dispute letters.
- Compliance deferred for now.

### Cross-Cutting Concerns Identified

- Authentication/RBAC across user, admin, and operator roles.
- Confidence scoring and low-confidence review paths.
- Data lineage from source PDFs to output letters.
- Reliability and retry handling for third-party services.
- Audit logging and traceability for sensitive documents.

## Core Architectural Decisions

### Data Architecture

**Database & ORM:**
- Decision: SQLAlchemy 2.0.x (latest: 2.0.45) as primary ORM.
- Rationale: Mature ORM, strong ecosystem, fits Postgres/Supabase.

**Schema & Validation:**
- Decision: Pydantic v1 (latest: 1.10.26).
- Rationale: Aligns with current codebase and minimizes migration risk.

**Migrations:**
- Decision: Alembic (latest: 1.17.2) for schema migrations.
- Rationale: Standard with SQLAlchemy, explicit change tracking.

**Caching / Queueing:**
- Decision: Redis (python client latest: 7.1.0) for caching, job state, and rate limiting.

**Security Boundary:**
- Decision: Supabase RLS is authoritative for data access; server uses service-role keys for privileged workflows.

**Cascading Implications:**
- FastAPI version must remain compatible with Pydantic v1 or use v1 compatibility mode when upgrading.

### Authentication & Security

**Authentication Method:**
- Decision: Supabase Auth (JWT) is the source of truth.
- Rationale: Native integration with Supabase RLS and existing stack.

**Authorization Pattern:**
- Decision: RLS + roles/claims in Supabase, with app-level checks for defense-in-depth.

**Rate Limiting:**
- Decision: Redis-backed rate limiting per user + IP.

**Encryption:**
- Decision: Supabase encryption at rest + TLS in transit; application handles secrets and tokens only.

**Audit Logging:**
- Decision: Structured audit logs for access to documents, tradelines, and dispute workflows.

**Cascading Implications:**
- Ensure JWT claims include role + tenant context to align with RLS policies.

### API & Communication Patterns

**API Style:**
- Decision: REST with FastAPI + OpenAPI documentation.

**Error Handling Standard:**
- Decision: Structured JSON error envelope (code/message/field/request_id).

**External Service Reliability:**
- Decision: Standardized retry/backoff wrappers + circuit breaker for Document AI/LLMs.

**Async Processing:**
- Decision: Background jobs (Redis queue) for OCR/LLM-heavy tasks.

**Cascading Implications:**
- Job status endpoints and idempotency keys required for long-running uploads.

### Frontend Architecture

**State Management:**
- Decision: Global store (Zustand or Redux) for cross-cutting app state.

**Routing:**
- Decision: React Router (current) remains the routing solution.

**Forms & Validation:**
- Decision: React Hook Form + Zod.

**UI Components:**
- Decision: Tailwind + Radix + shadcn-style components (current).

**Cascading Implications:**
- Define global state boundaries to avoid duplicating server state already managed by React Query.

### Infrastructure & Deployment

**Hosting Strategy:**
- Decision: Frontend on Vercel; backend on Railway or Render; Supabase managed.

**CI/CD:**
- Decision: GitHub Actions for tests and deploys.

**Environments:**
- Decision: Separate dev / staging / prod with distinct Supabase projects.

**Monitoring & Logging:**
- Decision: Sentry + structured application logs.

**Cascading Implications:**
- Environment-specific secrets and service-role keys must be isolated per Supabase project.

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Supabase Auth + RLS as the security boundary.
- SQLAlchemy + Alembic for data access and migrations.
- REST API + OpenAPI with structured error envelope.
- Redis-backed background jobs for OCR/LLM workloads.
- Separate dev/staging/prod environments with distinct Supabase projects.

**Important Decisions (Shape Architecture):**
- Redis-backed rate limiting (per user + IP).
- React Router + React Hook Form + Zod.
- Global frontend store (Zustand/Redux).
- Sentry + structured logging.

**Deferred Decisions (Post-MVP):**
- None currently deferred.

### Decision Impact Analysis

**Implementation Sequence:**
1) Provision Supabase projects + RLS policies + JWT claims.
2) Establish SQLAlchemy models + Alembic migrations.
3) Add Redis and queue infrastructure for async processing + rate limiting.
4) Define REST API contracts + error envelope + job status endpoints.
5) Frontend integration: global store, forms, routing, API hooks.
6) CI/CD and deployment pipelines for FE/BE + env secret isolation.
7) Monitoring and audit logging.

**Cross-Component Dependencies:**
- JWT claims must align with RLS policies.
- Job status + idempotency required for async OCR/LLM flow.
- Redis used by both rate limiting and async queue.
- Environment-specific secrets for Supabase, Redis, and LLM providers.

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:**
5 areas where AI agents could make different choices (naming, structure, formats, communication, process)

### Naming Patterns

**Database Naming Conventions:**
- Tables: `snake_case` plural (e.g., `user_documents`)
- Columns: `snake_case` (e.g., `user_id`, `created_at`)
- Foreign keys: `snake_case` (e.g., `user_id`)
- Indexes: `idx_<table>_<column>` (e.g., `idx_user_documents_user_id`)

**API Naming Conventions:**
- REST endpoints: plural nouns (e.g., `/tradelines`, `/disputes`)
- Route params: `{id}` in OpenAPI, `:id` in router definitions
- Query params: `snake_case` (e.g., `credit_bureau`)

**Code Naming Conventions:**
- React components: `PascalCase` filenames and exports (e.g., `DisputeWizard.tsx`)
- Non-component files: `kebab-case` (e.g., `tradeline-parser.ts`)
- Functions/variables: `camelCase` (e.g., `parseTradeline`)

### Structure Patterns

**Project Organization:**
- Tests live in separate `__tests__/` folders.
- Frontend components organized by type (components/pages/layouts/hooks).
- Backend follows `routers/`, `services/`, `models/`, `schemas/`, `db/` pattern.

**File Structure Patterns:**
- Config files remain at project root or feature root.
- Static assets stay under `frontend/public/` or `frontend/src/assets/`.
- Environment files stored per app with `.env.*` conventions.

### Format Patterns

**API Response Formats:**
- Standard wrapper: `{ success, data, error, request_id }`
- Error shape: `{ error: { code, message, field } }`
- Date/time: ISO-8601 strings

**Data Exchange Formats:**
- Backend JSON: `snake_case`
- Frontend JSON: `camelCase` (mapping at API boundary)
- Booleans: `true/false`
- Null handling: explicit `null` for missing optional fields

### Communication Patterns

**Event System Patterns:**
- No event bus in MVP; async handled via Redis job queue.

**State Management Patterns:**
- Global UI state in a single store (Zustand/Redux).
- Server state managed via React Query to avoid duplication.

### Process Patterns

**Error Handling Patterns:**
- Backend returns structured error envelope with `request_id`.
- Frontend surfaces user-facing errors and logs detailed errors.

**Loading State Patterns:**
- Global spinner for app-wide blocking operations.
- Per-component skeletons for local data loading.

### Enforcement Guidelines

**All AI Agents MUST:**
- Use `snake_case` for backend DB/JSON and map to `camelCase` in frontend.
- Wrap API responses in `{ success, data, error, request_id }`.
- Place tests in `__tests__/` with naming aligned to source modules.

**Pattern Enforcement:**
- Linting/CI checks validate naming and test placement.
- PR review includes pattern compliance checks.
- Pattern updates require architecture doc change + explicit team note.

### Pattern Examples

**Good Examples:**
- `GET /api/v1/tradelines?credit_bureau=experian`
- `POST /api/v1/disputes` → `{ success: true, data: {...}, error: null, request_id }`
- `frontend/src/components/disputes/DisputeWizard.tsx`
- `frontend/src/utils/tradeline-parser.ts`

**Anti-Patterns:**
- `GET /api/v1/tradeline` (singular)
- Mixed `camelCase` keys from backend
- Co-located tests for some modules and `__tests__/` for others

## Project Structure & Boundaries

### Complete Project Directory Structure
```
credit-clarity/
├── README.md
├── package.json
├── package-lock.json
├── docs/
│   ├── ARCHITECTURE_GUIDE.md
│   ├── API_DOCUMENTATION.md
│   ├── SECURITY_SETUP.md
│   └── ...
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── public/
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── layouts/
│       ├── hooks/
│       ├── services/
│       ├── utils/
│       ├── assets/
│       ├── styles/
│       ├── test-utils/
│       └── __tests__/
├── backend/
│   ├── requirements.txt
│   ├── main.py
│   ├── api/
│   ├── services/
│   ├── models/
│   ├── schemas/
│   ├── db/
│   └── tests/
│       ├── unit/
│       └── integration/
└── supabase/
    ├── migrations/
    ├── functions/
    └── config.toml
```

### Architectural Boundaries

**API Boundaries:**
- External API surface lives in `backend/api/` and is exposed via FastAPI.
- Auth boundary enforced by Supabase JWT + RLS.

**Component Boundaries:**
- UI in `frontend/src/components/`, route-level in `frontend/src/pages/`.
- Business logic in `frontend/src/services/`.
- Shared helpers in `frontend/src/utils/`.

**Service Boundaries:**
- Parsing/extraction services in `backend/services/`.
- Validation/normalization in `backend/services/`.
- Data access in `backend/db/` and `backend/models/`.

**Data Boundaries:**
- Postgres schema via Supabase migrations.
- Redis used for async jobs and rate limiting.

### Requirements to Structure Mapping

**Credit Report Ingestion & Parsing**
- Backend: `backend/api/processing/`, `backend/services/document_*`
- Frontend: `frontend/src/pages/CreditReportUpload*`, `frontend/src/services/`

**Tradelines CRUD & Review**
- Backend: `backend/api/tradelines/`, `backend/services/tradelines/`
- Frontend: `frontend/src/pages/Tradelines*`, `frontend/src/components/tradelines/`

**Dispute Packet Creation**
- Backend: `backend/api/disputes/`, `backend/services/disputes/`
- Frontend: `frontend/src/pages/Dispute*`, `frontend/src/components/disputes/`

**Admin / Operations**
- Backend: `backend/api/admin/`, `backend/services/monitoring/`
- Frontend: `frontend/src/pages/Admin*`, `frontend/src/components/admin/`

### Integration Points

**Internal Communication:**
- Frontend ↔ Backend via REST API.
- Backend ↔ Supabase (Auth, DB, Storage).
- Backend ↔ Redis for jobs/rate limits.

**External Integrations:**
- Document AI/OCR providers
- OpenAI + Anthropic for normalization

**Data Flow:**
Upload → OCR/AI extraction → validation/normalization → DB storage → dispute packet generation → status tracking.

### File Organization Patterns

**Configuration Files:**
- App configs in each app root (`frontend/`, `backend/`)
- Environment files per app (`.env.*`)

**Source Organization:**
- Frontend by type, Backend by layer (api/services/models/schemas/db)

**Test Organization:**
- Frontend: `frontend/src/__tests__/`
- Backend: `backend/tests/unit/` + `backend/tests/integration/`

**Asset Organization:**
- Static assets: `frontend/public/`
- App assets: `frontend/src/assets/`

### Development Workflow Integration

**Development Server Structure:**
- `frontend` uses Vite dev server
- `backend` uses Uvicorn

**Build Process Structure:**
- `frontend` build outputs static bundle
- `backend` deployable via Docker/host runtime

**Deployment Structure:**
- Frontend on Vercel
- Backend on Railway/Render
- Supabase managed separately

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
All selected technologies are compatible: FastAPI + SQLAlchemy + Alembic + Redis + Supabase Auth/RLS aligns with the current stack and deployment targets.

**Pattern Consistency:**
Naming, structure, and format rules are consistent across backend/frontend boundaries, with explicit mapping between snake_case and camelCase.

**Structure Alignment:**
The project tree matches current repo layout and supports the defined patterns and integrations.

### Requirements Coverage Validation ✅

**Epic/Feature Coverage:**
All PRD functional areas map to backend services and frontend pages/components.

**Functional Requirements Coverage:**
Ingestion, extraction, normalization, dispute workflows, and admin tooling are explicitly supported.

**Non-Functional Requirements Coverage:**
Performance, security, reliability, and scalability considerations are addressed via async processing, Redis, RLS, and environment separation.

### Implementation Readiness Validation ✅

**Decision Completeness:**
Critical decisions have versions and clear rationale.

**Structure Completeness:**
Complete tree and boundaries are defined.

**Pattern Completeness:**
Naming/format/process patterns and examples are provided.

### Gap Analysis Results

- Critical Gaps: None
- Important Gaps: Backend test framework specifics (pytest vs unittest) to confirm
- Nice-to-Have: Explicit CI workflow file naming and baseline pipeline steps

### Validation Issues Addressed

- Noted backend test framework selection and CI details as follow-up items.

### Architecture Completeness Checklist

**✅ Requirements Analysis**

- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**✅ Architectural Decisions**

- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed

**✅ Implementation Patterns**

- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**✅ Project Structure**

- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** High

**Key Strengths:**
- Clear security boundaries via Supabase Auth + RLS
- Async processing strategy for OCR/LLM workloads
- Strong consistency rules to prevent AI agent drift

**Areas for Future Enhancement:**
- Decide backend test framework and CI pipeline standardization

### Implementation Handoff

**AI Agent Guidelines:**
- Follow all architectural decisions exactly as documented
- Use implementation patterns consistently across all components
- Respect project structure and boundaries
- Refer to this document for all architectural questions

**First Implementation Priority:**
- Stabilize async job queue + error envelope + job status endpoints.

## Starter Template Evaluation

### Primary Technology Domain

Full-stack web application: React (Vite) frontend + FastAPI backend + Postgres (Supabase).

### Starter Options Considered

1) Vite official React + TypeScript scaffold (frontend-only)
- Command: `npm create vite@latest my-frontend -- --template react-ts`
- Decisions it sets: React + TypeScript, Vite dev server/build/preview, ESM modules, minimal defaults (router/state/tests added separately).

2) FastAPI Full-Stack Template (FastAPI + React/Vite)
- Command: `pipx run copier copy https://github.com/fastapi/full-stack-fastapi-template my-app --trust`
- Decisions it sets: FastAPI backend, React + TypeScript + Vite frontend, PostgreSQL, Docker Compose-based local/prod stack, Traefik reverse proxy.

### Selected Starter: Existing Credit Clarity Codebase (Brownfield)

**Rationale for Selection:**
We already have a React + Vite + TypeScript frontend and a FastAPI backend wired to Supabase/Postgres. Re-scaffolding would add churn without benefit. The current repo structure is the baseline starter for all future work.

**Initialization Command:**
N/A (brownfield). For new greenfield modules:
- Frontend: `npm create vite@latest my-frontend -- --template react-ts`
- Full-stack reference: `pipx run copier copy https://github.com/fastapi/full-stack-fastapi-template my-app --trust`

**Architectural Decisions Provided by Starter:**

**Language & Runtime:**
- Frontend: TypeScript + React on Vite.
- Backend: Python + FastAPI.
- Database: PostgreSQL via Supabase.

**Styling Solution:**
- Tailwind CSS + Radix UI components (shadcn-style utilities), with animation helpers.

**Build Tooling:**
- Vite build pipeline for frontend.
- Uvicorn for FastAPI dev server.

**Testing Framework:**
- Jest + Testing Library for frontend.
- Backend testing framework to be confirmed (kept consistent with current backend setup).

**Code Organization:**
- Monorepo-style structure: `frontend/`, `backend/`, `supabase/`, `docs/`.

**Development Experience:**
- Vite dev server, ESLint, TypeScript tooling.
- Concurrent frontend/backend dev script.

**Note:** For any new service spun up from scratch, use the Vite or FastAPI template commands above to preserve consistency.
