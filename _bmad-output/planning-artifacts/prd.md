---
stepsCompleted: [1, 2, 3, 4, 7, 8, 9, 10, 11]
inputDocuments:
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
documentCounts:
  briefs: 0
  research: 0
  brainstorming: 0
  projectDocs: 12
workflowType: 'prd'
lastStep: 11
---

# Product Requirements Document - credit-clarity

**Author:** Rorschache
**Date:** 2026-01-04T07:00:29Z

## Executive Summary

Credit Clarity will deliver bureau-agnostic tradeline extraction from any PDF credit report (Experian, Equifax, TransUnion, CreditKarma, etc.) with a 98% accuracy target across required fields (measured per-field, not just per-tradeline). The system will detect tradeline sections across heterogeneous layouts (including OCR noise), normalize and validate key fields (creditor name, account number, account type, status, balance, credit limit, date opened, and positive/negative indicator), and handle missing data consistently (blank for non-monetary fields, $0 for monetary fields). To avoid downstream dispute errors, extraction will include confidence scoring, validation checks, and auditability signals that surface low-confidence items for user review and explain why each field was extracted.

This extraction layer powers an automated credit repair workflow: users upload ID, SSN card, and a utility bill, then the platform generates dispute letters, tracks dispute progress, and supports two fulfillment paths - free DIY (print + ship) or paid fully managed mailing.

### What Makes This Special

Credit Clarity blends **bureau-agnostic coverage**, a **free core**, and **end-to-end automation**. The standout experience is a single-upload journey that yields accurate tradelines, ready-to-mail dispute packets, and ongoing dispute monitoring, with an optional hands-off paid fulfillment path.

## Project Classification

**Technical Type:** web_app + api_backend
**Domain:** fintech
**Complexity:** high
**Project Context:** Brownfield - extending existing system

This initiative upgrades extraction accuracy and dispute automation across heterogeneous PDF formats while preserving the existing architecture and workflows.

## Success Criteria

### User Success

- Users complete a full dispute packet from upload to ready-to-mail within a single session and report "this was easy."
- Users see dispute packets completed and begin to see negative items removed from their credit report.
- Primary outcome target: users remove at least $5,000 in negative debt from their credit report.

### Business Success

- User growth is sustained at ~8% month-over-month.
- 6-month user target: 500-1,000 users (range until baseline data is available).
- Revenue target: $50k by month 6.
- Profitability target: net profit > $5k/month by month 8.

### Technical Success

- Tradeline extraction accuracy: 98% per-field across all required fields.
- Critical field accuracy: 100% for bureau, creditor name, account number, and balance.
- Credit report analysis completes in under 2 minutes per PDF.
- Dispute letter generation completes in under 1 minute.
- Dispute letters have 100% correctness: no wrong data and no incorrect bureau/tradeline data.

### Measurable Outcomes

- Time-to-packet completion: < 1 session (user can complete within one visit).
- Extraction error rate for critical fields: 0%.
- Processing success rate: > 99% of PDFs complete without user-blocking errors.
- Dispute progress tracking available for every generated packet.

## Product Scope

### MVP - Minimum Viable Product

- Bureau-agnostic PDF tradeline extraction for required fields.
- Confidence scoring + low-confidence review prompts.
- Automated dispute packet creation using uploaded ID/SSN/utility bill.
- Dispute progress tracking.
- Free DIY path: user prints and ships packet.

### Growth Features (Post-MVP)

- Paid fully managed mailing flow.
- Expanded dispute monitoring and reminders.
- Improved analytics on dispute outcomes.

### Vision (Future)

- Fully automated end-to-end credit repair workflow with minimal user input.
- Scaling across more report formats and improved extraction intelligence.

## User Journeys

**Journey 1: Todd (Primary Free User) - "Dispute in Motion, No Paperwork"**
Todd finds Credit Clarity online while searching for ways to clean up his credit. He wants negative items removed but does not have his ID, SSN card, or utility bill ready. He uploads his credit report PDF and immediately sees extracted tradelines, but the system flags missing documents and guides him through what is required to proceed. Todd delays and returns later after finding his documents. Once he uploads them, the platform generates his dispute packet and gives him a clear DIY path to print and ship. The moment he sees "Dispute packet ready to mail," he feels relief - the process is finally moving.

**Journey 2: Gary (Paid User) - "Hands-Off Resolution"**
Gary finds Credit Clarity online but wants the entire process handled for him. He uploads his credit report and documents, then chooses the paid option. The system confirms accuracy of key tradelines, assembles the packet, and shows a shipping confirmation timeline. Gary receives updates as disputes are mailed and processed. His "aha" moment is seeing disputes sent without him touching a printer.

**Journey 3: Jake (Admin) - "Keep the Machine Running"**
Jake works in the office and is accountable for site reliability and user trust. A spike in user reports reveals failed extractions for a specific bureau layout. He reviews logs, uses admin tools to flag problematic PDFs, and coordinates fixes with the dev team. His success moment is restoring the pipeline without user-visible downtime and clearing the issue queue.

**Journey 4: James (Mailing Operator) - "Precision at Scale"**
James handles physical mail in the office. He receives a batch of generated packets but struggles with volume and organization. The system provides clear bureau-specific labels, checklists, and batching tools to ensure each packet matches the correct bureau and user documents. His success moment is shipping a full day's batch with zero mismatches and less cognitive load.

**Journey 5: Dan (Developer) - "Build Without Breaking"**
Dan is tasked with adding new extraction features and maintaining the system. He is not the most knowledgeable, so he relies on clear documentation, tests, and validation tools. He iterates on parsing logic, runs validation against the sample PDF, and confirms accuracy metrics. His success moment is shipping a change with measurable accuracy improvement and no regressions.

### Journey Requirements Summary

- Bureau-agnostic PDF ingestion and tradeline extraction.
- Missing-document flow with clear guidance and re-entry.
- Confidence scoring + review for low-confidence fields.
- Paid fulfillment option with status tracking and notifications.
- Admin tools for monitoring, issue triage, and extraction diagnostics.
- Mailing operator workflow: bureau labels, batching, and packet verification.
- Developer tooling: tests, sample PDF validation, and documentation.

## api_backend Specific Requirements

### Project-Type Overview

Credit Clarity exposes REST APIs that support PDF ingestion, tradeline extraction, normalization, dispute packet generation, and status tracking for both free and paid flows.

### Technical Architecture Considerations

- All endpoints authenticated with Supabase Auth tokens.
- JSON request/response bodies; file uploads use multipart/form-data.
- Versioning standardized under `/api/v1`.

### Endpoint Specifications

Core endpoints include:

- `POST /api/v1/reports/upload`
- `POST /api/v1/reports/parse` (parse_report)
- `POST /api/v1/tradelines/extract` (parse_extracted_data)
- `POST /api/v1/tradelines/normalize` (normalize_data)
- `POST /api/v1/tradelines/clean` (clean_data)
- `POST /api/v1/tradelines/sanitize` (sanitize_data)
- `GET /api/v1/tradelines` (display_data)
- `PATCH /api/v1/tradelines` (update_tradelines)
- `POST /api/v1/results/generate` (generate_results)
- `POST /api/v1/disputes/letters`
- `POST /api/v1/documents/upload` (upload_docs)

### Authentication Model

- Supabase Auth access tokens required for all user-facing endpoints.

### Data Schemas

- JSON for all request/response payloads.
- Multipart/form-data for PDF and document uploads.

### Rate Limits

- Letter generation: 3 per user per day.
- Report upload/extraction: 10 per user per day.

### Implementation Considerations

- Ensure consistent field naming and validation across extract/normalize/clean/sanitize steps.
- Maintain traceability from raw PDF to extracted fields to dispute packet.

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:** Problem-Solving MVP
**Resource Requirements:** Minimum 3-person team

### MVP Feature Set (Phase 1)

**Core User Journeys Supported:**
- Primary free user completes upload to extraction to dispute packet.
- Paid user completes upload to extraction to mailing workflow.
- Admin resolves extraction and dispute issues.
- Mailing operator sends correct packet to the correct bureau.

**Must-Have Capabilities:**
- Credit report analyzer with bureau-agnostic PDF parsing.
- Tradeline extraction + critical field accuracy.
- Dispute letter generation (100% data correctness).
- Dispute monitoring status tracking.

### Post-MVP Features

**Phase 2 (Growth):**
- Compliance and regulatory readiness.
- Detailed monitoring dashboard metrics (graphs/meters).

**Phase 3 (Expansion):**
- Sustainable pipeline of monthly paid users receiving consistent results and reporting satisfaction.

### Risk Mitigation Strategy

**Technical Risks:** Dispute letter accuracy - mitigate with validation rules, review checkpoints, and regression tests on sample PDFs.
**Market Risks:** Insufficient traffic - mitigate with early acquisition experiments and conversion tracking.
**Resource Risks:** Minimum 3-person team - prioritize core flows and defer non-essential features.

## Functional Requirements

### User Onboarding & Account Access
- FR1: Users can create and access an account to manage their credit repair workflow.
- FR2: Users can authenticate to access their reports, tradelines, and dispute packets.
- FR3: Users can upload required identity documents (ID, SSN card, utility bill).
- FR4: Users can update their profile information.

### Credit Report Ingestion
- FR5: Users can upload PDF credit reports from any bureau or provider.
- FR6: Users can view the processing status of uploaded reports.
- FR7: The system can associate uploaded reports with the correct user account.

### Tradeline Extraction & Review
- FR8: The system can detect tradeline sections within uploaded PDF reports.
- FR9: The system can extract tradeline fields (creditor name, account number, account type, status, balance, credit limit, date opened, positive/negative).
- FR10: The system can flag low-confidence tradelines or fields for user review.
- FR11: Users can view extracted tradelines in a readable format.
- FR12: Users can update or correct extracted tradelines.

### Data Normalization & Quality Controls
- FR13: The system can normalize extracted tradeline data into consistent formats.
- FR14: The system can apply validation rules to detect missing or inconsistent fields.
- FR15: The system can store confidence or quality indicators for extracted data.
- FR16: The system can trace extracted fields back to their source report.

### Dispute Packet Creation
- FR17: Users can generate dispute letters based on extracted tradelines.
- FR18: The system can assemble a complete dispute packet using required user documents.
- FR19: The system can ensure dispute letters contain no incorrect bureau or tradeline data.
- FR20: Users can download dispute packets for DIY mailing.

### Dispute Monitoring
- FR21: Users can view dispute status updates over time.
- FR22: The system can record dispute milestones (created, mailed, in progress, resolved).
- FR23: Users can access historical dispute packet records.

### Paid Fulfillment
- FR24: Users can select a paid option to have disputes mailed on their behalf.
- FR25: The system can track paid fulfillment status separately from DIY disputes.
- FR26: Users can receive confirmation when paid disputes are mailed.

### Admin Operations
- FR27: Admins can monitor system health and report processing status.
- FR28: Admins can review extraction errors and flagged reports.
- FR29: Admins can manage user issues related to report parsing and disputes.

### Mailing Operator Workflow
- FR30: Mailing operators can access a queue of packets ready to mail.
- FR31: Mailing operators can verify bureau destination for each packet.
- FR32: Mailing operators can mark packets as mailed.

### Developer & Maintenance Support
- FR33: Developers can access a validation workflow using a sample report.
- FR34: Developers can test and verify improvements to extraction accuracy.
- FR35: The system can expose API endpoints for report upload, extraction, tradeline updates, and dispute generation.

### Notifications & User Guidance
- FR36: The system can notify users about missing required documents.
- FR37: The system can notify users when dispute packets are ready.
- FR38: The system can notify users of dispute status updates.

### Support & Assistance
- FR39: Users can submit support tickets for issues with reports, extraction, or disputes.

## Non-Functional Requirements

### Performance
- Credit report analysis completes within 2 minutes per PDF.
- Dispute letter generation completes within 1 minute.
- System maintains responsive interactions during processing (no blocking UI).

### Security & Privacy
- Data is encrypted in transit and at rest.
- Role-based access controls enforce least privilege for users, admins, and operators.
- Audit logs capture access to sensitive user documents and dispute data.
- Privacy is preserved for all user documents and extracted data.

### Reliability
- Monthly uptime target: 99.5%.
- Processing failure rate: < 1% of report uploads.

### Scalability
- System supports ~3,000 users within 12 months.
- System supports 13% paid users without performance degradation.
- Handles sustained ~8% monthly user growth.

### Integration Resilience
- Integrations with Supabase and Document AI use retries and graceful degradation on transient failures.
- Clear error surfaced when third-party services are unavailable.

## Assumptions

- Users can provide required identity documents (ID, SSN card, utility bill) to complete dispute packets.
- Credit report PDFs are sufficiently readable for OCR-based extraction with manual review fallback for low-confidence fields.
- Supabase Auth, Postgres, and storage buckets remain available and supported for user data and document artifacts.
- Google Document AI (or equivalent OCR) access is available for production workloads.
- Paid fulfillment relies on a third-party mailing provider (Lob.com or USPS API) for certified mail delivery.

## Dependencies

- Supabase Auth, Postgres, and storage buckets for reports, user documents, and dispute packets.
- Google Document AI / OCR services for report parsing.
- PDF generation libraries (`pdf-lib`, `jspdf`) for dispute packet assembly.
- Mailing provider integration for paid fulfillment (Lob.com in Phase 1, USPS API in Phase 2).
- Sample credit report datasets for regression testing and accuracy validation.

## Out of Scope (MVP)

- B2B white-label offering and agency-focused tooling.
- Mobile application delivery.
- Credit score prediction or financial chatbot features.
- Advanced analytics dashboards beyond basic dispute tracking.
- Full compliance/regulatory certification work (targeted for post-MVP).

## Open Questions

- Final decision on paid mailing vendor for Phase 1 (Lob.com vs USPS API) and migration timeline.
- Document verification requirements for identity uploads (manual review vs automated checks).
- Data retention and deletion policy for user documents and dispute packets.
- Source of dispute status updates and expected update cadence.
- Accuracy validation methodology and definition of the gold-standard dataset.

## Risks & Mitigations

- **Accuracy drift:** Mitigate with regression testing on a fixed sample set and periodic model evaluation.
- **OCR quality variability:** Mitigate with preprocessing, confidence scoring, and user review prompts.
- **Mailing errors or delays:** Mitigate with tracking confirmation, audit logs, and operator verification steps.
- **Traffic shortfall:** Mitigate with early acquisition experiments and conversion tracking.
- **Team capacity constraints:** Mitigate by deferring non-essential features and focusing on core flows.

## Milestones & Release Plan

### Phase 1 (Months 1-6) - MVP Launch
- Bureau-agnostic extraction, dispute letter generation, and DIY packet flow.
- Paid mailing via Lob.com integration.
- Basic analytics and dispute tracking.

### Phase 2 (Months 7-12) - Optimization
- USPS API migration and reliability improvements.
- Referral and growth loops.
- Expanded monitoring and operational tooling.

### Phase 3 (Months 13-18) - AI Enhancements
- Improved extraction accuracy and model refinements.
- Optional premium tier features.
- Historical analytics improvements.

### Phase 4 (Months 19-24) - Scale & B2B
- Mobile app feasibility and launch planning.
- White-label offerings for agencies.
- Growth systems for scale and retention.

## Success Metrics Recap

- 98% per-field extraction accuracy; 100% accuracy on critical fields.
- <2 minutes report analysis; <1 minute dispute letter generation.
- 99%+ processing success rate for uploaded PDFs.
- Sustained ~8% monthly user growth with $50k revenue by month 6.
