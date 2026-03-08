# User Value & Requirements

**Framework Reference**: @../guidance-specification.md (Section 2: Core Features)
**Parent Document**: @./analysis.md
**Role**: Product Manager
**Generated**: 2026-01-03

---

## User Personas

### Persona 1: Tech-Savvy Millennials - "Sarah the Self-Service Optimizer"

**Demographics**:
- Age: 28
- Occupation: Software Engineer
- Income: $85K/year
- Tech Proficiency: High (comfortable with SaaS tools, mobile apps, AI services)

**Credit Profile**:
- 2-3 late payments from 2020 (pandemic-related)
- 1 collection account from medical debt ($450)
- Credit score: 640 (wants to improve to 720+ for mortgage)

**Goals**:
- Remove late payments and collection account before mortgage application (timeline: 6 months)
- Minimize time spent on credit repair (values efficiency)
- Avoid expensive credit repair agencies ($500-2000/year)
- Maintain full visibility and control over dispute process

**Pain Points**:
- Manual dispute process takes 30+ minutes per tradeline
- Confusion over FCRA-compliant letter formatting
- Tracking disputes across 3 bureaus separately is tedious
- Uncertainty about which negative items are most impactful to dispute first

**User Story**: "As a busy professional, I want to dispute negative items on my credit report with minimal effort so I can qualify for a mortgage without hiring an expensive agency."

**Acceptance Criteria**:
- Upload credit report and get negative items identified in <30 seconds
- Generate FCRA-compliant dispute letters in 1 click
- Mail letters professionally for <$10/letter
- Track all disputes across 3 bureaus in one dashboard

---

### Persona 2: First-Time Credit Builders - "Marcus the Motivated Buyer"

**Demographics**:
- Age: 24
- Occupation: Sales Associate
- Income: $42K/year
- Tech Proficiency: Medium (uses mobile apps, less familiar with complex SaaS)

**Credit Profile**:
- 1 late payment from student loan (90 days late)
- 1 charge-off from retail credit card ($800)
- Credit score: 580 (wants to improve to 650+ for auto loan)

**Goals**:
- Improve credit score urgently for car loan approval (timeline: 3 months)
- Ensure dispute letters look professional and credible to bureaus
- Understand which negative items to dispute first for maximum impact
- Get certified mail tracking for peace of mind

**Pain Points**:
- Limited knowledge of FCRA rights and dispute process
- Fear of making mistakes in letter formatting that could hurt credibility
- Needs professional presentation but can't afford $89-149/month agencies
- Wants reassurance that disputes are being processed (tracking)

**User Story**: "As a first-time credit builder, I want professional dispute letters mailed on my behalf so I can qualify for an auto loan without worrying about formatting mistakes."

**Acceptance Criteria**:
- See examples of FCRA-compliant letters before mailing
- Receive USPS tracking number immediately after payment
- Get delivery confirmation when bureaus receive letters
- View step-by-step guidance on dispute process

---

### Persona 3: Post-Financial Hardship Recovery - "Linda the Long-Term Rebuilder"

**Demographics**:
- Age: 42
- Occupation: Nurse
- Income: $68K/year
- Tech Proficiency: Medium (comfortable with email, social media, basic apps)

**Credit Profile**:
- Chapter 7 bankruptcy (discharged 2 years ago)
- 5+ negative items (charge-offs, collections, late payments)
- Multiple inaccuracies across all 3 bureaus
- Credit score: 520 (wants to improve to 650+ for financial stability)

**Goals**:
- Systematically dispute all inaccurate negative items over 12-24 months
- Track progress across multiple dispute rounds (initial + escalations)
- See historical trends (credit score improvement over time)
- Maximize removal success rate through strategic dispute timing

**Pain Points**:
- Complex disputes requiring multiple rounds across 3 bureaus (9+ disputes total)
- Difficulty tracking status changes over 12+ months
- Needs to prioritize which items to dispute first (limited budget)
- Wants visibility into overall success rate and progress trends

**User Story**: "As someone recovering from bankruptcy, I want to track all my disputes across multiple rounds and bureaus in one place so I can systematically rebuild my credit over 12-24 months."

**Acceptance Criteria**:
- View all disputes (past, current, future) in unified dashboard
- Track status changes per bureau per tradeline (Pending, Investigating, Deleted, etc.)
- See personal success statistics (% items removed, avg time to resolution)
- Get notified when disputes approach FCRA 30-day deadline

---

## User Journey Mapping

### Journey 1: Free User → Paid Mailing Conversion (Core Monetization Flow)

**Stage 1: Discovery & Signup (Day 0)**
- **Touchpoint**: Google search "how to dispute late payments on credit report"
- **Action**: User finds Credit Clarity SEO article, clicks "Try Free" CTA
- **Emotion**: Hopeful but skeptical (has seen expensive agencies before)
- **Pain Point**: Concerned about hidden fees or subscription commitments
- **Solution**: Clear freemium messaging on landing page: "Free AI scanner, pay only when you mail ($5-10/letter)"

**Stage 2: Onboarding & Credit Report Upload (Day 0)**
- **Touchpoint**: Signup flow, credit report upload screen
- **Action**: User creates account, uploads PDF credit report
- **Emotion**: Curious but cautious (sharing sensitive financial data)
- **Pain Point**: Privacy concerns about AI scanning credit report
- **Solution**: Prominent security badges, "Your data is encrypted and never shared" messaging

**Stage 3: AI Negative Item Detection (Day 0, <30 seconds)**
- **Touchpoint**: Processing screen → Results dashboard
- **Action**: AI identifies 3 negative items (2 late payments, 1 collection)
- **Emotion**: Impressed (AI found items user didn't notice) + relieved (clear next steps)
- **Pain Point**: Uncertainty about which items to dispute first
- **Solution**: AI prioritizes items by impact (e.g., "This late payment is likely easiest to remove")

**Stage 4: Free Dispute Letter Generation (Day 0)**
- **Touchpoint**: "Generate Letter" button for each negative item
- **Action**: User generates 3 dispute letters (within 3/month free limit)
- **Emotion**: Satisfied (got free value, professional FCRA letters)
- **Pain Point**: Realizes manually printing and mailing 3 letters to 9 bureaus = 27 total mailings + postage costs
- **Solution**: Upgrade prompt appears: "30 minutes of work vs $5-10 per letter. We'll mail it for you with USPS tracking."

**Stage 5: Conversion Decision Point (Day 0)**
- **Touchpoint**: Upgrade modal with convenience messaging
- **Action**: User compares time/cost of DIY mailing vs paid service
- **Emotion**: Torn between saving money and saving time
- **Pain Point**: Wants professional certified mail but $30-90 total cost seems high
- **Solution**:
  - Bundle pricing: "Mail all 3 letters for $12" (vs $15-30 individually)
  - Social proof: "127 users mailed letters this week"
  - Time value calculator: "Your time is worth $30/hour. Save 1.5 hours for $12."

**Stage 6: Paid Mailing Conversion (Day 0 or Day 1-7)**
- **Touchpoint**: Payment screen, USPS tracking confirmation
- **Action**: User pays $12 for 3-letter bundle, receives tracking numbers immediately
- **Emotion**: Relieved (task complete) + confident (professional mailing, certified mail)
- **Pain Point**: Wants reassurance letters will actually be delivered
- **Solution**: Immediate USPS tracking links, email confirmation, delivery ETA estimate

**Stage 7: Post-Mailing Engagement (Days 8-45)**
- **Touchpoint**: Multi-bureau dispute dashboard, status updates
- **Action**: User manually updates dispute status as bureau response letters arrive
- **Emotion**: Engaged (seeing progress) + hopeful (tracking results)
- **Pain Point**: Forgetting to check status, missing FCRA 30-day deadline
- **Solution**: Email reminders: "It's been 25 days since you mailed to Equifax. Expect response by Day 30."

**Stage 8: Success & Repeat Purchase (Day 30-90)**
- **Touchpoint**: "Item Deleted" status update, success notification
- **Action**: User sees 1/3 items removed, considers disputing more items or escalating
- **Emotion**: Excited (visible results) + motivated (want to continue)
- **Pain Point**: Wants to escalate remaining items but only has 1 free letter remaining this month
- **Solution**: Upgrade prompt: "Escalate your verified items for $5 each. Users who escalate have 40% success rate on second round."

---

### Journey 2: Power User Long-Term Engagement (12-24 Month Retention)

**Month 1-3: Initial Dispute Wave**
- User uploads credit report, disputes 5-8 negative items
- Converts to paid mailing for first batch ($25-40 spend)
- Tracks status updates, sees 30-40% success rate (2-3 items removed)

**Month 4-6: Escalation & Repeat Disputes**
- User escalates verified items with additional evidence
- Purchases 2-3 additional mailings ($10-15 spend)
- Begins to see credit score improvement (20-30 points)

**Month 7-12: Maintenance & Monitoring**
- User uploads updated credit report (uses 2nd free upload)
- Disputes new late payments or inaccuracies
- Occasional paid mailings (1-2 per quarter, $5-10 spend)

**Month 13-24: Premium Upgrade Consideration (Phase 3)**
- User interested in credit score prediction and trend analysis
- Upgrades to premium tier ($10-20/month) for advanced features
- Continues using dispute mailing as needed (included in premium)

**Total Lifetime Value (LTV)**: $50-150 over 24 months
- Initial disputes: $25-40
- Escalations: $10-30
- Maintenance: $10-20
- Premium tier: $120-240 (12 months × $10-20/month)

---

## Core User Requirements (Feature-Driven)

### Requirement 1: AI-Powered Negative Tradeline Scanner

**User Story**: "As a user, I want AI to automatically identify all negative items on my credit report so I don't miss disputable errors."

**Functional Requirements**:
- Upload PDF credit report (max 10MB file size)
- AI extracts and parses tradelines across all 3 bureaus
- AI classifies negative items (late payments, charge-offs, collections, bankruptcies, foreclosures, repossessions, tax liens, judgments)
- AI prioritizes items by dispute impact (e.g., recent late payments vs old charge-offs)

**Acceptance Criteria**:
- ✅ Processing completes in <30 seconds for files <10MB
- ✅ AI detects 95%+ of negative items (validated against manual review)
- ✅ AI identifies negative item type correctly (late payment vs charge-off, etc.)
- ✅ User can review, edit, or exclude AI-identified items before generating letters
- ✅ Background processing for files >10MB with progress tracking

**User Validation**:
- User can manually add items AI missed
- User can remove false positives (items AI incorrectly flagged as negative)

---

### Requirement 2: Free Dispute Letter Generation Service

**User Story**: "As a user, I want to generate professional FCRA-compliant dispute letters for free so I can review them before deciding to mail."

**Functional Requirements**:
- Rate limit: 2 credit report uploads per month, 3 dispute letters generated per month
- Letter templates for each bureau (Equifax, TransUnion, Experian)
- FCRA-compliant formatting and legal language
- Customizable dispute reasons (inaccurate balance, account not mine, paid in full, etc.)
- Preview letter before generating

**Acceptance Criteria**:
- ✅ User can generate up to 3 letters per month without payment
- ✅ Rate limit enforcement persists across server restarts (Redis backup)
- ✅ Rate limit reset notification: "You'll get 3 more letters on [date]"
- ✅ Letter preview shows exact formatting and content before generation
- ✅ User can customize dispute reason from dropdown (10-15 common reasons)

**User Validation**:
- User can download PDF letter for manual mailing
- User sees upgrade prompt after generating letter ("Mail it for $5-10")

---

### Requirement 3: Paid Automated Dispute Letter Mailing Service

**User Story**: "As a user, I want to mail my dispute letters with one click so I don't have to spend 30 minutes printing, addressing, and mailing them myself."

**Functional Requirements**:
- One-click upgrade from generated letter to paid mailing
- Payment processing (Stripe integration)
- Lob.com API integration for certified mail (Phase 1)
- USPS tracking number returned immediately after payment
- Delivery confirmation notifications

**Acceptance Criteria**:
- ✅ User can pay and mail letter in <2 minutes
- ✅ USPS tracking number displayed immediately after payment confirmation
- ✅ Delivery confirmation email sent when letter delivered to bureau
- ✅ Letter status updated to "Pending" automatically after mailing
- ✅ Bundle pricing available (3 letters for $12-15, vs $15-30 individually)

**User Validation**:
- User receives tracking link via email and in dashboard
- User can view letter content even after mailing (audit trail)

---

### Requirement 4: Multi-Bureau Dispute Progress Dashboard

**User Story**: "As a user, I want to track all my disputes across Equifax, TransUnion, and Experian in one place so I don't have to manage 3 separate spreadsheets."

**Functional Requirements**:
- Side-by-side comparison of same tradeline across 3 bureaus
- Status tracking per bureau: Pending, Investigating, Verified, Deleted, Updated, Escalated, Expired, Blank
- Manual status update via dropdown (primary method)
- Optional OCR for bureau response letters (upload PDF, AI extracts status)
- Timeline view showing dispute progression over time

**Acceptance Criteria**:
- ✅ User can update status for each tradeline-bureau combination manually
- ✅ OCR extracts status from bureau response PDFs with 85%+ accuracy (confidence score shown)
- ✅ User can correct AI-extracted results before saving
- ✅ Status history audit trail (when status changed, by whom)
- ✅ Color-coded status indicators (green = Deleted, yellow = Investigating, red = Verified, etc.)

**User Validation**:
- User sees unified view of all disputes across all bureaus
- User can filter by status (show only Investigating, show only Deleted, etc.)
- User can sort by tradeline name, bureau, or status

---

### Requirement 5: Personal Success Statistics & Analytics

**User Story**: "As a user, I want to see my overall success rate and progress so I feel motivated to continue disputing."

**Functional Requirements**:
- Personal success statistics dashboard
- Metrics: Total disputes initiated, success rate (% items removed), items successfully deleted, avg time to resolution per bureau
- Real-time updates when status changes
- Historical data (Phase 1: basic, Phase 3: advanced with TimescaleDB)

**Acceptance Criteria**:
- ✅ Success rate calculation: (Deleted items / Total disputes) × 100%
- ✅ Average time to resolution: Mean days from "Pending" to "Deleted" or "Verified"
- ✅ Per-bureau breakdown (Equifax success rate vs TransUnion vs Experian)
- ✅ Statistics update in real-time when user changes dispute status
- ✅ Visual progress indicators (progress bar for success rate, trend charts in Phase 3)

**User Validation**:
- User can export statistics as PDF report
- User sees encouraging messaging ("You've removed 3/8 items - 38% success rate! Keep going!")

---

## User Acceptance Criteria Summary

### Feature 1: AI Negative Item Scanner
| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Processing Speed | <30 seconds | 95th percentile processing time for <10MB files |
| Detection Accuracy | 95%+ | Negative items detected / Total negative items (manual validation) |
| False Positive Rate | <5% | Incorrect negative flags / Total items flagged |
| User Correction Rate | <10% | Users who manually edit AI results / Total users |

### Feature 2: Free Letter Generation
| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Rate Limit Enforcement | 100% | Zero rate limit bypass incidents |
| FCRA Compliance | 100% | Legal review confirms all templates FCRA-compliant |
| Letter Preview Usage | 80%+ | Users who preview before generating / Total generators |
| Customization Rate | 60%+ | Users who customize dispute reason / Total generators |

### Feature 3: Paid Mailing Service
| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Conversion Rate | 10-15% | Users who mail / Users who generate letters |
| Payment Success Rate | 95%+ | Successful payments / Total payment attempts |
| Tracking Delivery | 98%+ | USPS tracking links working / Total mailings |
| User Satisfaction | 4.5+ / 5 | Post-mailing survey rating |

### Feature 4: Multi-Bureau Dashboard
| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Status Update Frequency | 3+ updates/user | Average status updates per user in 90 days |
| OCR Accuracy | 85%+ | Correct status extractions / Total OCR attempts |
| Dashboard Load Time | <2 seconds | 95th percentile page load time |
| Filter/Sort Usage | 40%+ | Users who use filters / Total dashboard users |

### Feature 5: Personal Analytics
| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Statistics Accuracy | 100% | Manual verification of calculations |
| Real-time Update Speed | <1 second | Time from status change to statistics refresh |
| Engagement Lift | 20%+ | Repeat usage increase after viewing statistics |
| Export Usage | 15%+ | Users who export PDF report / Total users |

---

## User Feedback Integration Plan

### Phase 1 (Months 1-6): MVP User Testing

**Beta User Recruitment**:
- 20-30 early adopters from Reddit, Facebook groups
- Mix of personas (tech-savvy, first-time builders, post-bankruptcy)
- Weekly feedback sessions (user interviews, surveys)

**Key Questions to Validate**:
1. Is AI negative item detection accurate enough to trust?
2. Do users understand the freemium rate limits and find them fair?
3. Is $5-10/letter pricing acceptable vs DIY mailing?
4. Do users prefer manual status updates or want automatic OCR?
5. Are personal statistics motivating or overwhelming?

**Iteration Priorities**:
- Fix any AI detection accuracy issues (<95% target)
- Refine upgrade messaging based on conversion data
- Adjust rate limits if conversion <8% or >20% (optimize for 10-15%)

### Phase 2-4 (Months 7-24): Continuous Improvement

**Feedback Channels**:
- In-app feedback widget (Intercom or similar)
- Post-mailing satisfaction survey (email after 30 days)
- Quarterly user interviews with power users
- Support ticket analysis for common pain points

**Feature Request Prioritization**:
- Use RICE framework (Reach × Impact × Confidence / Effort)
- Prioritize requests from paying users (higher LTV)
- Validate requests through user surveys before building

---

**Document Status**: COMPLETE
**Framework Alignment**: Addresses Section 2 (Core Features) with user-centric perspective
**Next Document**: @./analysis-business-model.md
