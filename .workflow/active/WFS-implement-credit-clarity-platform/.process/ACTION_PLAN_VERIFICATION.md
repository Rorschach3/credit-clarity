# Action Plan Verification Report

**Session**: WFS-implement-credit-clarity-platform
**Generated**: 2026-03-07
**Artifacts Analyzed**: docs/PRD-Feature-Specifications.md, docs/PRD-Technical-Architecture.md, IMPL_PLAN.md, 12 task JSON files
**Authority Source**: PRD docs (synthesized output of WFS-brainstorm-for-a-prd)

---

## Executive Summary

- **Overall Risk Level**: HIGH
- **Recommendation**: PROCEED_WITH_FIXES — 0 critical blockers, but 5 high-priority gaps that should be resolved before execution begins
- **Critical Issues**: 0
- **High Issues**: 5
- **Medium Issues**: 5
- **Low Issues**: 2

---

## Findings Summary

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| H1 | Coverage | HIGH | PRD F5 (RICE 960) | Bundle Pricing (3-letter $24 bundle, RICE 960 highest in P1) has zero task coverage | Add bundle pricing to IMPL-005/006 or create IMPL-013 |
| H2 | Consistency | HIGH | IMPL-003 vs PRD F1 | SLA conflict: IMPL-003 says 45s/<5MB & 90s/5-10MB; PRD F1 says <30s for <10MB | Reconcile SLA — align IMPL-003 acceptance criteria to PRD (or update PRD if architect decision overrides) |
| H3 | Coverage | HIGH | PRD F4, IMPL-010 | F4 requires "Status history audit trail" — no `status_history` table in IMPL-001 migrations and IMPL-010 doesn't cover audit trail write | Add status_history table to IMPL-001 migration; add audit trail write to IMPL-010 |
| H4 | Coverage | HIGH | PRD F8 (RICE 800) | USPS/Lob tracking webhook updates (Lob delivery status callbacks) not covered — IMPL-008 only gets initial tracking_number | Add Lob webhook handling to IMPL-008 or create IMPL-013 |
| H5 | Dependency | HIGH | IMPL-011 | IMPL-011 references "upgrade to premium" CTA but has no dependency on IMPL-006 (Stripe frontend) | Add IMPL-006 to IMPL-011 depends_on |
| M1 | Coverage | MEDIUM | PRD F4, IMPL-010 | F4 "Filter/sort by bureau and status" not in IMPL-010 acceptance criteria | Add filter/sort acceptance criterion to IMPL-010 |
| M2 | NFR | MEDIUM | PRD F4 success metric | "Dashboard load time <2s" NFR not represented in any task acceptance criteria | Add load time criterion to IMPL-010 |
| M3 | NFR | MEDIUM | PRD F3 success metric | "Payment + mailing in <2 minutes" timing NFR not in IMPL-008 acceptance criteria | Add timing criterion to IMPL-008 |
| M4 | NFR | MEDIUM | PRD F6 success metric | "Email delivery rate >98%" not in IMPL-009 acceptance criteria | Add delivery rate criterion to IMPL-009 |
| M5 | Coverage | MEDIUM | PRD F1, IMPL-003 | Celery migration of PDF processing must not regress F1 detection accuracy (95%+) — no regression check in IMPL-003 | Add accuracy regression check to IMPL-003 acceptance criteria |
| L1 | Scope | LOW | PRD F7, F8 | F7 SEO Content Hub (RICE 800) and F8 USPS Tracking (RICE 800) not planned — should be explicitly noted as deferred | Add explicit deferral note to IMPL_PLAN.md |
| L2 | Spec | LOW | IMPL-004 | IMPL-004 and IMPL-003 listed as parallel but both use Redis — should note different DB indices to avoid confusion | Add note that IMPL-004 uses Redis DB0 (same as cache via cache_service) while Celery uses DB1/DB2 |

---

## Requirements Coverage Analysis

| Requirement | PRD Ref | RICE | Phase | Has Task? | Task IDs | Notes |
|-------------|---------|------|-------|-----------|----------|-------|
| AI Negative Item Scanner | F1 | 600 | P0 | Partial | IMPL-003 | Celery migration only; no new scanner work (existing pipeline OK) |
| Free Dispute Letter Generation | F2 | 1000 | P0 | Yes | IMPL-011, IMPL-004 | Rate limiting + 12 reasons + preview |
| Paid Automated Mailing (Lob) | F3 | 640 | P0 | Yes | IMPL-008, IMPL-005 | Timing NFR missing (H3) |
| Multi-Bureau Dashboard | F4 | 600 | P0 | Partial | IMPL-010 | Missing: status_history table, filter/sort, load time NFR |
| Bundle Pricing | F5 | 960 | P1 | **No** | — | **HIGH: Zero coverage** |
| Email Notifications | F6 | 800 | P1 | Yes | IMPL-009 | Delivery rate NFR missing |
| SEO Content Hub | F7 | 800 | P1 | No | — | LOW: Intentional deferral (content work) |
| USPS Tracking Integration | F8 | 800 | P1 | Partial | IMPL-008 | Lob initial tracking_number only; webhook updates not covered |
| Manual Status Updates | F9 | 900 | P1 | Yes | IMPL-010 | Covered |
| CROA Compliance Gate | EP-008 | — | P0 | Yes | IMPL-007 | Fully covered |
| Stripe Payments + Webhooks | EP-005 | — | P0 | Yes | IMPL-005, IMPL-006 | Covered |
| Celery Workers | EP-002 | — | P0 | Yes | IMPL-003 | SLA conflict (H2) |
| Rate Limiting (Redis) | D-013, D-018 | — | P0 | Yes | IMPL-004 | Covered |
| Email FCRA Reminders | EP-010 | — | P1 | Yes | IMPL-009 | Covered |
| DB Schema (payments etc) | EP-003 | — | P0 | Yes | IMPL-001 | Missing status_history (H3) |

**Coverage Metrics**:
- P0 MVP Features: 3/4 fully covered, 1 partial (F4)
- P1 Enhancement Features: 3/5 covered, 1 partially (F8), 1 zero (F5)
- Critical Infrastructure (EP-002,003,005,007,008,010): 6/6 covered

---

## Dependency Graph Issues

**Circular Dependencies**: None detected

**Broken Dependencies**: None detected

**Missing Dependencies**:
- **IMPL-011** `depends_on: ["IMPL-004", "IMPL-007"]` — missing `"IMPL-006"` (Stripe frontend must exist for upgrade CTA to function)

**Logical Ordering**: Sound — Group 1→2→3→4 progression is correct

---

## Synthesis Alignment Issues

| Issue | PRD Ref | IMPL_PLAN/Task | Impact | Recommendation |
|-------|---------|----------------|--------|----------------|
| SLA Conflict | PRD F1: "<30s for <10MB PDFs" | IMPL-003: "45s for <5MB, 90s for 5-10MB" | HIGH | The PRD synthesized this from the system-architect analysis (EP-009 SLA tiering: <5MB=45s, 5-10MB=90s). The EP-009 decision supersedes the earlier F1 AC. Update F1 in PRD or mark as resolved. For the plan, the SLA tiers are correct per EP-009. |
| Bundle Pricing not planned | PRD F5 RICE=960 | No task | HIGH | F5 is the highest RICE P1 feature and is purely a Stripe config + UI change (1 person-week effort per PRD). Should be folded into IMPL-005/006 |
| status_history not in schema | PRD F4 "audit trail" | IMPL-001 has no status_history migration | HIGH | Add migration for status_history table (dispute_id, status, changed_at, changed_by) |

---

## NFR Coverage

| NFR | Source | Tasks Covering | Gap |
|-----|--------|---------------|-----|
| PDF processing <30s (P0 target) | PRD F1 | IMPL-003 (tiered SLA) | Note: EP-009 overrides with 45s/90s tiers — should document reconciliation |
| Dashboard load <2s | PRD F4 | None | MEDIUM gap — add to IMPL-010 acceptance criteria |
| Payment+mailing <2min | PRD F3 | None | MEDIUM gap — add to IMPL-008 acceptance criteria |
| Email delivery >98% | PRD F6 | None | MEDIUM gap — add to IMPL-009 acceptance criteria |
| Letter generation 99%+ | PRD F2 | None | MEDIUM gap — add to IMPL-011 acceptance criteria |
| 0 FCRA/CROA compliance incidents | PRD Phase 1 KPI | IMPL-007 (CROA gate) | Covered |
| Rate limit bypass = 0 | PRD F2 | IMPL-004 | Covered |

---

## Task Specification Quality

**Artifacts Reference**: All 12 tasks reference context_package_path ✓
**Flow Control**: All tasks have implementation_approach and pre_analysis steps ✓
**Focus Paths**: All tasks have specific file paths ✓
**Acceptance Criteria**: All tasks have measurable criteria ✓ (with NFR gaps noted above)

---

## Feasibility Concerns

| Concern | Tasks Affected | Issue | Recommendation |
|---------|----------------|-------|----------------|
| Redis DB indices | IMPL-003, IMPL-004 | Both use Redis; Celery uses DBs 1/2, cache uses DB0 — parallel execution safe | Verify in celery_app.py: broker_url ends in /1, result_backend in /2 |
| F1 regression during Celery migration | IMPL-003 | Migrating PDF jobs to Celery could introduce new failure modes affecting accuracy | Add explicit regression test in IMPL-003: run existing test suite after migration |

---

## Metrics

- **Total PRD Features Analyzed**: 9 Phase 1 features (P0+P1)
- **Total Tasks**: 12
- **P0 Coverage**: 3.75/4 (93%)
- **P1 Coverage**: 3.5/5 (70% — F5 zero, F8 partial)
- **Critical Issues**: 0
- **High Issues**: 5
- **Medium Issues**: 5
- **Low Issues**: 2

---

## Recommended Fixes (PROCEED_WITH_FIXES)

### Fix 1 (H1): Add Bundle Pricing to IMPL-005 and IMPL-006
- **IMPL-005**: Add Stripe price object creation for bundle (3-letter, $24). Add `POST /payments/bundle-checkout` endpoint
- **IMPL-006**: Add bundle pricing card to PricingPage.tsx (single: $8/letter or bundle: $24/3 letters)
- Estimated: +4 hours

### Fix 2 (H2): Reconcile SLA in IMPL-003
- The 45s/<5MB, 90s/5-10MB tiers are from EP-009 (system-architect synthesis enhancement), which supersedes the original PRD F1 target of <30s
- **IMPL-003**: Update acceptance criteria to use the EP-009 tiered SLA and add a note explaining the reconciliation
- Estimated: +30 min

### Fix 3 (H3): Add status_history table to IMPL-001
- Add Migration 6: `status_history` table (id UUID, dispute_id UUID FK, status TEXT, changed_at TIMESTAMPTZ, changed_by UUID FK profiles)
- Update IMPL-010 acceptance criteria: "Each status change writes to status_history"
- Estimated: +2 hours

### Fix 4 (H4): Add Lob tracking webhook to IMPL-008
- Add to IMPL-008 acceptance criteria: Register Lob webhook endpoint `POST /api/v1/mailing/lob-webhook`, receives delivery status updates, updates disputes table tracking_status
- Estimated: +1 day

### Fix 5 (H5): Add IMPL-006 to IMPL-011 depends_on
- IMPL-011.json: Add "IMPL-006" to `depends_on` array
- Estimated: 1 min

---

## Next Actions

**Recommendation**: PROCEED_WITH_FIXES

Apply the 5 high-priority fixes above, then execute:

```bash
/workflow:execute --session WFS-implement-credit-clarity-platform
```

**Remediation Priority**:
1. Fix H5 (30 sec — dependency JSON edit)
2. Fix H2 (30 min — SLA note in IMPL-003)
3. Fix H1 (4 hrs — bundle pricing scope expansion)
4. Fix H3 (2 hrs — status_history migration + IMPL-010 AC)
5. Fix H4 (1 day — Lob webhook endpoint)
6. Fix M1-M5 (1 hr total — add NFR metrics to ACs)
