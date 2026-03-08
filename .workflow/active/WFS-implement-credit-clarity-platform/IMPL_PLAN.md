---
identifier: WFS-implement-credit-clarity-platform
source: "PRD Synthesis (docs/PRD-*.md) + Brainstorm (WFS-brainstorm-for-a-prd, archived)"
context_package: .workflow/active/WFS-implement-credit-clarity-platform/.process/context-package.json
workflow_type: "implementation"
verification_history:
  action_plan_verify: "pending"
phase_progression: "brainstorm → prd-docs → planning → implementation"
---

# Implementation Plan: Credit Clarity Platform - Phase 1 MVP

## 1. Summary

This plan implements the **Credit Clarity Negative Tradeline Dispute Management Platform** Phase 1 MVP, converting the existing AI tradeline extraction foundation into a monetization-ready B2C SaaS platform.

**Core Objectives**:
- Add Stripe payments (per-letter $5-10, premium subscription) with idempotent webhook architecture
- Migrate PDF processing to Celery background workers (crash-recovery, SLA enforcement)
- Implement CROA compliance gate (legal requirement before letter generation)
- Integrate Lob API for paid physical mailing of dispute letters
- Add Redis-persisted rate limiting (2 uploads/3 letters/month free tier)
- Build email notification system with FCRA deadline reminders (Day 1/3/25)
- Enhance multi-bureau dashboard with dispute lifecycle tracking

**Business Targets (Phase 1 End, Month 6)**:
- 100+ active users
- 10-15% free-to-paid conversion rate
- $500-1,500 MRR
- 95%+ tradeline detection accuracy (already met)
- 0 FCRA/CROA compliance incidents

**PRD Reference**: `docs/PRD-Feature-Specifications.md` (F1-F4 P0, F6 P1)

## 2. Context Analysis

### Source Materials

- **PRD Suite**: `docs/PRD-Executive-Summary.md`, `docs/PRD-Technical-Architecture.md`, `docs/PRD-Feature-Specifications.md`, `docs/PRD-Data-Architecture.md`, `docs/PRD-Implementation-Roadmap.md`
- **Brainstorm Archive**: `.workflow/archives/WFS-brainstorm-for-a-prd/` (synthesis_completed, 10 enhancements applied)
- **Context Package**: `.workflow/active/WFS-implement-credit-clarity-platform/.process/context-package.json`

### Current Platform State

**Existing (functional)**:
- PDF upload → Document AI OCR → Gemini extraction → Supabase save pipeline
- Supabase auth (JWT) + RLS on tradelines table
- React dispute wizard UI with basic letter generation (edge function)
- Multi-bureau tradeline storage (unique per user/account/bureau)
- Redis cache service (cache: prefix)
- Background job skeleton (`services/background_jobs.py`, `services/job_service.py`)

**Missing for MVP**:
- Stripe payments and webhook processing
- Celery background workers (PDF jobs, email tasks)
- CROA legal compliance gate
- Lob physical mailing integration
- Redis rate limiting with monthly persistence
- Email notifications (SendGrid + Celery beat)
- Enhanced dashboard with dispute status lifecycle

### Conflict Risk Assessment: **Medium**

| Conflict | Risk | Mitigation |
|---------|------|-----------|
| Celery replaces BackgroundTasks | Medium | Add Celery as additive layer; migrate endpoints progressively; keep existing /upload working |
| Redis key collision (cache vs rate limit) | Low | Rate limit keys prefixed `ratelimit:` (cache uses `cache:` prefix) |
| CROA gate breaks existing wizard flow | Medium | Implement as React HOC/modal overlay; does not modify wizard step logic |
| New DB tables need RLS matching existing | Low | Copy RLS policy pattern from `20250720_update_tradeline_unique_constraint.sql` |

## 3. Module Structure

```
backend/
├── api/v1/routes/
│   ├── payments.py              [NEW] Stripe checkout + webhook + history
│   ├── subscriptions.py         [NEW] Subscribe, status, cancel
│   ├── mailing.py               [NEW] Lob dispatch + tracking
│   └── users.py                 [MOD] Add /croa-accept endpoint
├── services/
│   ├── stripe_service.py        [NEW] Stripe client wrapper
│   ├── lob_service.py           [NEW] Lob API wrapper
│   ├── email_service.py         [NEW] SendGrid transactional email
│   └── rate_limit_service.py    [NEW] Redis rate limiting (ratelimit: prefix)
├── workers/
│   ├── __init__.py              [NEW]
│   ├── celery_app.py            [NEW] Celery app + beat schedule
│   ├── pdf_worker.py            [NEW] PDF processing Celery task
│   └── email_worker.py          [NEW] Email notification Celery task
└── core/
    └── config.py                [MOD] Add STRIPE/LOB/CELERY/SENDGRID settings

frontend/src/
├── pages/
│   ├── PricingPage.tsx          [MOD] Add Stripe checkout flow
│   ├── DisputeWizardPage.tsx    [MOD] Add CROA gate, mailing step, rate limit meter
│   ├── DashboardPage.tsx        [MOD] Add bureau columns, dispute status
│   └── SubscriptionPage.tsx     [NEW] Subscription management
├── components/
│   └── croa/
│       └── CROADisclosureModal.tsx [NEW] CROA legal disclosure
└── hooks/
    └── use-auth.tsx             [MOD] Add subscription_tier, croa_disclosure_accepted

supabase/migrations/
├── YYYYMMDD_subscription_tier.sql     [NEW] ALTER profiles, add CROA fields
├── YYYYMMDD_payments_schema.sql       [NEW] payments + stripe_webhook_events tables
├── YYYYMMDD_notification_log.sql      [NEW] notification_log table
└── YYYYMMDD_user_analytics_trigger.sql [NEW] user_analytics TABLE + trigger
```

## 4. Implementation Strategy

### Execution Strategy: **Group-Parallel with Sequential Groups**

```
Group 1 (Parallel - No dependencies): IMPL-001 || IMPL-002
Group 2 (Parallel - After Group 1):   IMPL-003 || IMPL-004 || IMPL-005
Group 3 (Parallel - Mixed deps):       IMPL-006 || IMPL-007 || IMPL-008 || IMPL-009 || IMPL-010
Group 4 (Sequential - All complete):   IMPL-011 → IMPL-012
```

**Rationale**: Database migrations and config must come first. Services can be built in parallel once dependencies are available. Testing gates all completion.

### Key Architecture Decisions (from PRD D-0xx references)

| Decision | PRD Ref | Implementation |
|---------|---------|----------------|
| Celery over BackgroundTasks | EP-002 | `backend/workers/celery_app.py` with Redis broker |
| TimescaleDB as Supabase extension | D-015, EP-001 | Phase 2 (not Phase 1 MVP) |
| trigger-based user_analytics | EP-007 | IMPL-001 migration with PL/pgSQL trigger |
| Stripe webhook idempotency | EP-005 | `stripe_webhook_events` ON CONFLICT (stripe_event_id) DO NOTHING |
| Lob first, USPS Phase 2 | D-020 | IMPL-008 uses lob-python only |
| CROA gate Phase 1 | EP-008 | IMPL-007 modal + backend enforcement |
| Rate limit Redis persistence | D-018 | IMPL-004 `ratelimit:` prefix keys, 32-day TTL |
| Email Day 1/3/25 reminders | EP-010 | IMPL-009 Celery beat daily task |

### Dependencies Graph

```
IMPL-001 ──┬──→ IMPL-003
IMPL-002 ──┤    IMPL-004
           ├──→ IMPL-005 ──→ IMPL-006
           │    IMPL-007        ↑
           └──→ IMPL-008 ──────┘
                IMPL-009 (also needs IMPL-003)
                IMPL-010 (needs IMPL-001 only)

All above → IMPL-011 → IMPL-012
```

## 5. Task Breakdown Summary

### Task Count: **12 tasks**

| Task | Title | Priority | Effort | Type | Group |
|------|-------|----------|--------|------|-------|
| IMPL-001 | Supabase DB Schema Migrations | Critical | 3-4d | Database | 1 |
| IMPL-002 | Backend Configuration & Dependencies | Critical | 1d | Config | 1 |
| IMPL-003 | Celery Worker Infrastructure | Critical | 3-4d | Backend | 2 |
| IMPL-004 | Redis Rate Limiting Service | Critical | 2d | Backend | 2 |
| IMPL-005 | Stripe Backend Integration | Critical | 4-5d | Backend | 2 |
| IMPL-006 | Stripe Frontend Integration | High | 3d | Frontend | 3 |
| IMPL-007 | CROA Compliance Gate | Critical | 2d | Fullstack | 3 |
| IMPL-008 | Lob Mailing Service Integration | Critical | 4-5d | Fullstack | 3 |
| IMPL-009 | Email Notification Service | High | 3d | Backend | 3 |
| IMPL-010 | Multi-Bureau Dashboard & Dispute Tracking | High | 3d | Fullstack | 3 |
| IMPL-011 | Dispute Letter Generation Enhancements | High | 2-3d | Fullstack | 4 |
| IMPL-012 | End-to-End Integration Testing & QA | High | 3-4d | Testing | 4 |

**Total Estimated Effort**: 33-42 developer-days (~7-9 weeks solo, ~3-5 weeks with 2 devs

### Complexity Distribution

- **Critical** (P0): 6 tasks (IMPL-001, 002, 003, 004, 005, 007)
- **High** (P1): 6 tasks (IMPL-006, 008, 009, 010, 011, 012)

## 6. Phased Breakdown

### Group 1 (Days 1-4): Infrastructure Foundation

**Run in parallel**:
- **IMPL-001**: Database migrations (4 new tables + trigger)
- **IMPL-002**: Backend config (Stripe/Lob/Celery env vars)

**Deliverables**: All DB tables migrated, requirements.txt updated, config.py extended

### Group 2 (Days 4-12): Service Layer

**Run in parallel** (after Group 1):
- **IMPL-003**: Celery workers (PDF processing migrated from BackgroundTasks)
- **IMPL-004**: Rate limiting (Redis `ratelimit:` prefix, 2/month uploads, 3/month letters)
- **IMPL-005**: Stripe backend (checkout, webhooks, subscriptions)

**Deliverables**: PDF jobs on Celery, rate limits enforced, Stripe payments functional

### Group 3 (Days 12-20): Feature Integration

**Run in parallel** (after Group 2, except IMPL-010 which only needs Group 1):
- **IMPL-006**: Stripe frontend (PricingPage, SubscriptionPage checkout flow)
- **IMPL-007**: CROA gate (modal + backend enforcement)
- **IMPL-008**: Lob mailing (mailing step in wizard, Lob API dispatch)
- **IMPL-009**: Email notifications (SendGrid, Celery beat, FCRA reminders)
- **IMPL-010**: Dashboard enhancements (bureau columns, dispute lifecycle)

**Deliverables**: Full MVP feature set integrated end-to-end

### Group 4 (Days 20-27): Polish & Testing

**Sequential**:
- **IMPL-011**: Letter generation enhancements (12 dispute reasons, preview, rate meter UI)
- **IMPL-012**: E2E integration tests (Stripe webhooks, rate limits, CROA, Lob, email)

**Deliverables**: Polished MVP, test coverage on all critical paths

## 7. Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| Stripe webhook signature validation fails in dev | High | Medium | Use `stripe listen --forward-to` in development; verify raw body not parsed |
| Celery worker crash loses PDF job | High | Low | Celery retry (max_retries=3) + job status persisted in Supabase |
| Lob API sandbox rate limits | Medium | Low | Use Lob test mode keys; mock in tests |
| CROA modal blocks existing users | Medium | Low | Check existing accepted users on migration; default croa_disclosure_accepted=false for new users only |
| Redis `ratelimit:` key collision with `cache:` | Low | Low | Explicit prefix isolation verified in IMPL-004 |

## 8. Success Criteria

**Functional**:
- [ ] PDF upload → Celery job → tradeline extraction (with crash recovery)
- [ ] CROA disclosure shown once per user and enforced on all letter endpoints
- [ ] Stripe checkout → payment → premium upgrade flow works end-to-end
- [ ] Lob letter dispatched with tracking number for paid mailing
- [ ] Email notifications sent for Day 1/3/25 FCRA deadlines
- [ ] Rate limits enforced: 2 uploads/3 letters per month on free tier
- [ ] Dashboard shows bureau columns and dispute status lifecycle

**Technical Quality**:
- [ ] All new tables have RLS policies (tested with non-owner user query)
- [ ] Stripe webhook idempotency verified (duplicate event delivers once)
- [ ] Redis rate limit keys expire monthly (TTL = 32 days)
- [ ] Celery tasks retry on transient failures (max 3 times)
- [ ] pytest test coverage ≥80% on new modules

**Compliance**:
- [ ] CROA disclosure text approved / reviewed
- [ ] Zero bypass of letter generation without CROA acceptance
- [ ] notification_log records every user notification

---

**Document Version**: 1.0
**Last Updated**: 2026-03-07
**Status**: READY - Action planning complete, ready for /workflow:action-plan-verify then /workflow:execute
