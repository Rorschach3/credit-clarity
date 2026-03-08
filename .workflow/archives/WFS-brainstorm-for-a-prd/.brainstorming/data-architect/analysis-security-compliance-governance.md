# Data Security, Compliance & Governance

**Parent Document**: @analysis.md
**Reference**: @../guidance-specification.md Section 5 (Data Architect Decisions - Data Privacy & Compliance)

## 1. Regulatory Compliance Framework

### 1.1 FCRA (Fair Credit Reporting Act) Requirements

**Regulatory Scope**: Credit Clarity handles consumer credit reports and dispute processes, which fall under FCRA jurisdiction.

**FCRA Compliance Obligations**:

1. **Data Accuracy & Dispute Rights (15 U.S.C. § 1681i)**:
   - Consumers have the right to dispute inaccurate information
   - Credit Clarity must facilitate FCRA-compliant dispute letter generation
   - **Data implication**: Store dispute letter content and delivery proof (tracking numbers) for audit trail

2. **Consumer Consent for Data Collection (15 U.S.C. § 1681b)**:
   - User must consent to credit report upload and AI processing
   - User must explicitly opt-in to AI training data usage (anonymized reports)
   - **Data implication**: Store consent timestamps and consent scope in `users` table

3. **Data Retention & Disposal (15 U.S.C. § 1681c)**:
   - Negative credit items remain reportable for 7 years (10 years for bankruptcies)
   - Credit Clarity must retain dispute records for 7 years minimum
   - After retention period, data must be securely deleted (right to erasure)
   - **Data implication**: Implement automated data deletion policy after 7-year retention

4. **Data Security & Access Controls (15 U.S.C. § 1681e)**:
   - Credit data must be protected against unauthorized access
   - Access logs required for audit purposes
   - **Data implication**: Supabase RLS for access control, audit logging for all data access

5. **Adverse Action Notices (15 U.S.C. § 1681m)**:
   - If AI classifies tradeline as negative, user must be notified
   - User has right to dispute AI classification
   - **Data implication**: Store AI classification rationale (`negative_reason` field) for transparency

**Compliance Data Schema Additions**:

```sql
-- Add FCRA compliance fields to users table
ALTER TABLE users ADD COLUMN fcra_consent_given BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN fcra_consent_timestamp TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN ai_training_consent BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN ai_training_consent_timestamp TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN data_retention_expiry DATE;  -- Calculated as 7 years from account creation

-- Add audit trail for data access (FCRA requirement)
CREATE TABLE data_access_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    accessed_by UUID,  -- Admin user ID or NULL for user's own access
    access_type ENUM('read', 'write', 'delete'),
    table_name TEXT NOT NULL,
    record_id UUID,
    access_timestamp TIMESTAMPTZ DEFAULT NOW(),
    ip_address TEXT,
    user_agent TEXT
);

-- Index for audit queries
CREATE INDEX idx_data_access_log_user ON data_access_log (user_id, access_timestamp DESC);
```

**FCRA Consent Collection Flow**:

```python
@app.post("/api/v1/onboarding/fcra-consent")
async def collect_fcra_consent(user_id: str, consent_data: dict):
    """
    Collect user consent for FCRA-compliant data processing.

    consent_data = {
        "fcra_consent": True,  # Required: Consent to credit report upload and dispute processing
        "ai_training_consent": False  # Optional: Consent to use anonymized data for AI training
    }
    """
    # Update user consent fields
    supabase.table('users').update({
        "fcra_consent_given": consent_data['fcra_consent'],
        "fcra_consent_timestamp": datetime.now().isoformat(),
        "ai_training_consent": consent_data.get('ai_training_consent', False),
        "ai_training_consent_timestamp": datetime.now().isoformat() if consent_data.get('ai_training_consent') else None,
        "data_retention_expiry": (datetime.now() + timedelta(days=7*365)).date()  # 7 years from now
    }).eq('id', user_id).execute()

    return {"consent_recorded": True}
```

**Automated Data Deletion Policy** (7-year retention):

```sql
-- Scheduled job: Delete user data after 7-year retention period
CREATE OR REPLACE FUNCTION delete_expired_user_data()
RETURNS VOID AS $$
BEGIN
    -- Find users whose retention period has expired
    DELETE FROM users
    WHERE data_retention_expiry < CURRENT_DATE;
    -- Note: CASCADE deletes all related records (credit_reports, tradelines, disputes, etc.)
END;
$$ LANGUAGE plpgsql;

-- Schedule monthly execution (via pg_cron extension)
SELECT cron.schedule('delete-expired-data', '0 2 1 * *', 'SELECT delete_expired_user_data()');
```

### 1.2 GDPR & CCPA Compliance (Privacy Regulations)

**Applicability**:
- **GDPR**: If Credit Clarity has EU users (not in initial scope)
- **CCPA**: California Consumer Privacy Act applies to California residents

**Key Requirements**:

1. **Right to Access (GDPR Art. 15, CCPA § 1798.100)**:
   - Users can request copy of all personal data stored
   - **Implementation**: Export all user's data as JSON via API endpoint

2. **Right to Erasure / Right to Delete (GDPR Art. 17, CCPA § 1798.105)**:
   - Users can request complete data deletion (except records required for legal retention)
   - **Implementation**: Cascade delete on `users` table, respecting FCRA 7-year retention for dispute records

3. **Data Portability (GDPR Art. 20)**:
   - Users can export data in machine-readable format
   - **Implementation**: JSON export of user's credit reports, tradelines, disputes

4. **Breach Notification (GDPR Art. 33-34, CCPA § 1798.150)**:
   - Data breaches must be reported within 72 hours (GDPR) or "without unreasonable delay" (CCPA)
   - **Implementation**: Incident response plan with automated breach detection alerts

**Data Export API** (Right to Access):

```python
@app.get("/api/v1/users/{user_id}/data-export")
async def export_user_data(user_id: str):
    """
    Export all user's personal data in JSON format (GDPR/CCPA compliance).
    """
    # Fetch all user's data across all tables
    user_data = {
        "user_profile": fetch_user_profile(user_id),
        "credit_reports": fetch_user_credit_reports(user_id),
        "tradelines": fetch_user_tradelines(user_id),
        "dispute_letters": fetch_user_dispute_letters(user_id),
        "dispute_tracking": fetch_user_dispute_tracking(user_id),
        "status_history": fetch_user_status_history(user_id),
        "mailing_records": fetch_user_mailing_records(user_id),
        "analytics": fetch_user_analytics(user_id)
    }

    return {
        "export_date": datetime.now().isoformat(),
        "data": user_data
    }
```

**Data Deletion API** (Right to Erasure):

```python
@app.delete("/api/v1/users/{user_id}")
async def delete_user_account(user_id: str, deletion_request: dict):
    """
    Delete user account and all associated data (GDPR/CCPA compliance).

    Respects FCRA 7-year retention: Dispute records marked as "deleted" but not purged until retention period expires.
    """
    # Check if user has active disputes within 7-year retention period
    active_disputes = check_active_disputes(user_id)

    if active_disputes:
        # Anonymize user data but retain dispute records for FCRA compliance
        anonymize_user_data(user_id)
        return {
            "status": "anonymized",
            "message": "User data anonymized. Dispute records retained for FCRA compliance (7-year retention)."
        }
    else:
        # No active disputes - safe to delete
        supabase.table('users').delete().eq('id', user_id).execute()  # Cascade deletes all related records
        return {
            "status": "deleted",
            "message": "User account and all associated data deleted."
        }
```

## 2. Data Encryption Strategy

### 2.1 Encryption at Rest

**Platform-Level Encryption**: Supabase PostgreSQL (managed service)

**Supabase Encryption Features**:
- **Database encryption**: AES-256 encryption for entire PostgreSQL database
- **Backup encryption**: All database backups encrypted with same AES-256 key
- **Key management**: Supabase manages encryption keys (rotated quarterly)
- **Compliance**: SOC 2 Type II certified, GDPR/CCPA compliant

**Application-Level Column Encryption**: Additional encryption for sensitive PII fields

**Encrypted Fields**:
1. **Social Security Number (SSN)**: Required for some credit repair scenarios (if collected)
2. **Account numbers**: Full account numbers (not just last 4 digits)
3. **User addresses**: Home address for mailing service

**Encryption Implementation**:

```python
from cryptography.fernet import Fernet
import base64
import os

# Generate encryption key (store in environment variable, not in code)
ENCRYPTION_KEY = os.getenv('COLUMN_ENCRYPTION_KEY')  # 32-byte key, base64-encoded
cipher = Fernet(ENCRYPTION_KEY.encode())

# Encrypt sensitive data before storing
def encrypt_field(plaintext: str) -> str:
    """Encrypt sensitive field using Fernet symmetric encryption."""
    if plaintext is None:
        return None
    encrypted_bytes = cipher.encrypt(plaintext.encode())
    return base64.b64encode(encrypted_bytes).decode()

# Decrypt when retrieving
def decrypt_field(ciphertext: str) -> str:
    """Decrypt sensitive field."""
    if ciphertext is None:
        return None
    encrypted_bytes = base64.b64decode(ciphertext.encode())
    decrypted_bytes = cipher.decrypt(encrypted_bytes)
    return decrypted_bytes.decode()

# Example: Encrypt SSN before inserting
user_ssn = "123-45-6789"
encrypted_ssn = encrypt_field(user_ssn)

supabase.table('users').update({
    "ssn_encrypted": encrypted_ssn
}).eq('id', user_id).execute()

# Example: Decrypt when displaying (backend only, never send to frontend)
user_record = supabase.table('users').select('ssn_encrypted').eq('id', user_id).execute()
decrypted_ssn = decrypt_field(user_record.data[0]['ssn_encrypted'])
```

**Encrypted Fields in Schema**:

```sql
-- Add encrypted columns to users table
ALTER TABLE users ADD COLUMN ssn_encrypted TEXT;  -- Encrypted SSN (if collected)
ALTER TABLE users ADD COLUMN address_encrypted JSONB;  -- Encrypted address JSON

-- Add encrypted columns to tradelines table
ALTER TABLE tradelines ADD COLUMN account_number_full_encrypted TEXT;  -- Encrypted full account number
```

**Key Management Best Practices**:
- **Environment variable**: Store `COLUMN_ENCRYPTION_KEY` in environment variable (not in code)
- **Key rotation**: Rotate encryption key annually, re-encrypt all data with new key
- **Key backup**: Store backup key in secure vault (AWS Secrets Manager, HashiCorp Vault)
- **Access control**: Limit key access to production servers only (no dev/staging access)

### 2.2 Encryption in Transit

**HTTPS/TLS for All API Calls**:

**Configuration**:
- **Minimum TLS version**: TLS 1.2 (prefer TLS 1.3)
- **Cipher suites**: Strong ciphers only (AES-256-GCM, ChaCha20-Poly1305)
- **Certificate**: Valid SSL/TLS certificate from trusted CA (Let's Encrypt)

**FastAPI HTTPS Enforcement**:

```python
from fastapi import FastAPI, Request
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app = FastAPI()

# Enforce HTTPS (redirect HTTP to HTTPS)
if os.getenv('ENVIRONMENT') == 'production':
    app.add_middleware(HTTPSRedirectMiddleware)

# HSTS (HTTP Strict Transport Security) header
@app.middleware("http")
async def add_hsts_header(request: Request, call_next):
    response = await call_next(request)
    if os.getenv('ENVIRONMENT') == 'production':
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

**Supabase API Calls**:
- All Supabase client API calls use HTTPS by default
- Supabase API keys transmitted via HTTPS Authorization header

**External API Integrations**:
- **Google Document AI**: HTTPS API endpoint, OAuth 2.0 authentication
- **Gemini AI**: HTTPS API endpoint, API key authentication
- **Lob.com**: HTTPS API endpoint, API key authentication
- **USPS API**: HTTPS API endpoint, API key authentication

## 3. Access Control & Row-Level Security

### 3.1 Supabase Row-Level Security (RLS) Policies

**Multi-Tenancy Enforcement**: Database-level access control ensures users only access their own data

**RLS Policy Design Pattern**:

```sql
-- Template: Users can only access their own records
CREATE POLICY "Users can view own {table}"
ON {table} FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own {table}"
ON {table} FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own {table}"
ON {table} FOR UPDATE
USING (auth.uid() = user_id);

-- Note: No DELETE policy for most tables (data retention for FCRA compliance)
```

**Applied RLS Policies** (see @analysis-data-models-schema-design.md for full list):

1. **users**: SELECT, UPDATE own profile (no DELETE until retention expires)
2. **credit_reports**: SELECT, INSERT own reports (no UPDATE/DELETE after processing)
3. **tradelines**: SELECT, UPDATE own tradelines (user can correct AI classifications)
4. **dispute_letters**: SELECT, INSERT, UPDATE own letters (no DELETE)
5. **dispute_tracking**: SELECT, UPDATE own disputes (status changes allowed)
6. **status_history**: SELECT only (immutable audit trail, no UPDATE/DELETE)
7. **mailing_records**: SELECT only (immutable mailing history)
8. **user_analytics**: SELECT only (read-only cached aggregations)

**RLS Performance Optimization**:
- **Denormalized user_id**: Every table includes `user_id` column to avoid JOINs in RLS policy evaluation
- **Indexes on user_id**: All tables have index on `user_id` for fast RLS filtering
- **Policy testing**: Use `SET ROLE` to impersonate users and verify policy enforcement

### 3.2 Admin Access Controls

**Admin User Management**:

```sql
-- Create admin role for internal support team
CREATE ROLE admin_user;

-- Grant limited admin access to specific tables
GRANT SELECT ON ALL TABLES IN SCHEMA public TO admin_user;
GRANT UPDATE ON users, dispute_tracking TO admin_user;  -- Allow status corrections

-- Admin users can view all data (bypass RLS for support purposes)
CREATE POLICY "Admins can view all data"
ON users FOR SELECT TO admin_user
USING (TRUE);  -- No user_id filter

-- Log all admin access (FCRA compliance)
CREATE OR REPLACE FUNCTION log_admin_access()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO data_access_log (
        user_id,
        accessed_by,
        access_type,
        table_name,
        record_id,
        access_timestamp
    ) VALUES (
        NEW.user_id,
        current_user,  -- Admin user's PostgreSQL role
        TG_OP,  -- 'INSERT', 'UPDATE', 'DELETE'
        TG_TABLE_NAME,
        NEW.id,
        NOW()
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger admin access logging on all tables
CREATE TRIGGER log_admin_access_users
AFTER INSERT OR UPDATE OR DELETE ON users
FOR EACH ROW EXECUTE FUNCTION log_admin_access();
```

**Admin Access Audit Trail**:
- All admin access logged in `data_access_log` table
- Monthly audit reports generated for compliance review
- Unauthorized admin access triggers alert

### 3.3 API Authentication & Authorization

**Supabase Auth Integration**:

```python
from supabase import create_client
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
security = HTTPBearer()

# Verify JWT token and extract user_id
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    # Verify token with Supabase Auth
    try:
        user = supabase.auth.get_user(token)
        return user.user.id
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

# Protect API endpoints with authentication
@app.get("/api/v1/tradelines")
async def get_user_tradelines(user_id: str = Depends(get_current_user)):
    # user_id extracted from JWT token, no need for user to pass it
    tradelines = fetch_tradelines(user_id)
    return tradelines
```

**JWT Token Security**:
- **Token expiration**: 1-hour access token, 7-day refresh token
- **Token rotation**: Refresh tokens rotated on every use (prevents replay attacks)
- **Token revocation**: User logout invalidates all tokens for that user

## 4. Data Governance Framework

### 4.1 Data Classification

**Classification Levels**:

1. **Public**: Non-sensitive data viewable by anyone
   - Example: Marketing content, blog posts, FAQs
   - **Encryption**: None required
   - **Access control**: No restrictions

2. **Internal**: Business data accessible to Credit Clarity employees
   - Example: User analytics aggregations (anonymized), system metrics
   - **Encryption**: In transit (HTTPS)
   - **Access control**: Admin role required

3. **Confidential**: Sensitive user data requiring strict access controls
   - Example: Credit report PDFs, tradeline details, dispute letters
   - **Encryption**: In transit (HTTPS) + at rest (database encryption)
   - **Access control**: Supabase RLS enforced, user-scoped

4. **Restricted**: Highly sensitive PII requiring column-level encryption
   - Example: SSN, full account numbers, user addresses
   - **Encryption**: In transit (HTTPS) + at rest (database + column-level encryption)
   - **Access control**: Encrypted fields only decrypted in backend, never sent to frontend

**Data Classification Matrix**:

| Data Type | Classification | Encryption | Access Control |
|-----------|---------------|------------|----------------|
| User email | Confidential | In transit + at rest | RLS (user-scoped) |
| SSN | Restricted | In transit + at rest + column-level | RLS + encrypted field |
| Credit report PDF | Confidential | In transit + at rest | RLS (user-scoped) |
| Tradeline details | Confidential | In transit + at rest | RLS (user-scoped) |
| Full account number | Restricted | In transit + at rest + column-level | RLS + encrypted field |
| Dispute letter | Confidential | In transit + at rest | RLS (user-scoped) |
| User analytics | Internal | In transit + at rest | Admin access only |
| Marketing content | Public | None | Public access |

### 4.2 Data Ownership & Stewardship

**Data Ownership Model**:

| Data Domain | Data Owner | Data Steward | Responsibilities |
|-------------|-----------|--------------|------------------|
| User Profile | Product Manager | Engineering Lead | User registration, profile management, consent collection |
| Credit Data | Compliance Officer | Data Architect | Credit report storage, FCRA compliance, 7-year retention |
| Dispute Data | Product Manager | Engineering Lead | Dispute letter generation, bureau tracking, mailing service |
| Analytics Data | Data Analyst | Data Engineer | User statistics, success metrics, performance monitoring |
| Audit Logs | Compliance Officer | Security Engineer | Access logging, breach detection, compliance reporting |

**Data Steward Responsibilities**:
1. **Data quality**: Monitor data completeness, accuracy, consistency
2. **Access management**: Review and approve admin access requests
3. **Compliance monitoring**: Ensure FCRA, GDPR, CCPA requirements met
4. **Incident response**: Coordinate data breach response and notification

### 4.3 Data Lifecycle Management

**Data Lifecycle Stages**:

```
Collection → Storage → Usage → Retention → Deletion
```

**Stage 1: Data Collection**:
- **Consent collection**: User consents to FCRA terms and data processing
- **Data validation**: Input validation at API boundaries (email format, date ranges, etc.)
- **PII detection**: Automatically identify and encrypt PII fields (SSN, account numbers)

**Stage 2: Data Storage**:
- **Encryption**: Apply encryption at rest (database) and column-level (PII)
- **Access control**: Enable Supabase RLS policies
- **Backup**: Daily backups with 7-day retention, weekly backups with 4-week retention

**Stage 3: Data Usage**:
- **Access logging**: Log all data access in `data_access_log` table
- **Audit trail**: Record all data modifications in `status_history` table
- **AI training**: Only use anonymized data from users who consented to `ai_training_consent`

**Stage 4: Data Retention**:
- **FCRA retention**: 7 years for credit data and dispute records
- **User retention**: User can request data deletion after closing account (respecting FCRA retention)
- **Backup retention**: Daily backups deleted after 7 days, weekly backups after 4 weeks

**Stage 5: Data Deletion**:
- **Automated deletion**: Monthly job deletes user data after 7-year retention expires
- **User-requested deletion**: User can request account deletion (anonymize if active disputes exist)
- **Secure deletion**: Overwrite deleted data in database (not just mark as deleted)

**Automated Retention Policy** (from Section 1.1):

```sql
-- Monthly scheduled job: Delete expired user data
SELECT cron.schedule('delete-expired-data', '0 2 1 * *', 'SELECT delete_expired_user_data()');

-- Function: Delete users whose retention period has expired
CREATE OR REPLACE FUNCTION delete_expired_user_data()
RETURNS VOID AS $$
BEGIN
    DELETE FROM users WHERE data_retention_expiry < CURRENT_DATE;
    -- CASCADE deletes all related records (credit_reports, tradelines, disputes, etc.)
END;
$$ LANGUAGE plpgsql;
```

## 5. Incident Response & Breach Notification

### 5.1 Data Breach Detection

**Automated Breach Detection**:

```python
# Monitor for suspicious access patterns
def detect_anomalous_access():
    """
    Detect potential data breaches via anomalous access patterns.
    - Multiple failed login attempts from same IP
    - Admin access to unusual number of user records
    - Data export requests exceeding threshold
    """
    # Query data_access_log for anomalies
    suspicious_access = supabase.rpc('detect_anomalies', {
        'time_window': '1 hour',
        'threshold': 100  # More than 100 records accessed in 1 hour
    }).execute()

    if suspicious_access.data:
        # Trigger breach alert
        send_breach_alert(suspicious_access.data)

# Schedule hourly anomaly detection
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(detect_anomalous_access, 'interval', hours=1)
scheduler.start()
```

**Manual Breach Reporting**:
- **User reports**: User reports unauthorized access or suspicious activity
- **Admin discovery**: Admin notices anomalous data access in audit logs
- **Security scan**: Automated security scans detect vulnerabilities

### 5.2 Breach Notification Process

**GDPR/CCPA Breach Notification Requirements**:
1. **Notify supervisory authority**: Within 72 hours of discovering breach (GDPR)
2. **Notify affected users**: Without unreasonable delay (GDPR/CCPA)
3. **Breach details**: Nature of breach, data affected, mitigation steps taken

**Breach Notification Workflow**:

```
Breach Detection (Automated or Manual)
    ↓
Security Team Assessment (<24 hours)
    ↓
Determine Severity (Low, Medium, High, Critical)
    ↓
[If High/Critical] Notify Compliance Officer (<12 hours)
    ↓
[If GDPR applicable] Notify Supervisory Authority (<72 hours)
    ↓
Notify Affected Users (Email + Dashboard Alert)
    ↓
Post-Incident Review (Within 1 week)
```

**User Breach Notification Email Template**:

```
Subject: Important Security Notice - Data Breach Notification

Dear [User Name],

We are writing to inform you of a data security incident that may have affected your personal information stored on Credit Clarity.

What Happened:
On [Date], we discovered [brief description of breach].

What Information Was Involved:
[List of data types affected, e.g., "email addresses, credit report upload dates, dispute letter content"].

What We Are Doing:
- Immediately secured the affected systems
- Engaged third-party security experts to investigate
- Notified relevant authorities as required by law

What You Can Do:
- Monitor your credit reports for suspicious activity
- Consider placing a fraud alert on your credit file
- Change your Credit Clarity password immediately

For More Information:
Contact our support team at [Email] or visit [URL] for FAQs.

We sincerely apologize for this incident and are committed to protecting your personal information.

Sincerely,
Credit Clarity Security Team
```

### 5.3 Post-Breach Remediation

**Remediation Steps**:
1. **Secure affected systems**: Revoke compromised credentials, patch vulnerabilities
2. **Forensic analysis**: Identify root cause and extent of breach
3. **User notification**: Notify affected users per GDPR/CCPA requirements
4. **Regulatory reporting**: File breach reports with relevant authorities
5. **Process improvements**: Update security policies and access controls to prevent recurrence

**Post-Incident Review Questions**:
- How was the breach detected? (automated vs manual)
- What was the root cause? (vulnerability, misconfiguration, social engineering)
- How many users were affected?
- What data was compromised?
- What security controls failed?
- What improvements are needed?

## 6. Training Data Strategy & Privacy

### 6.1 AI Training Data Collection (Phase 3)

**Training Data Sources** (from @../guidance-specification.md Section 5):

1. **User Upload Data**: Anonymized credit reports with user consent
   - **Consent requirement**: `ai_training_consent = TRUE`
   - **Anonymization**: Remove all PII (names, SSNs, addresses, account numbers)
   - **Retention**: Anonymized training data retained indefinitely for model improvement

2. **Synthetic Data**: Generated credit profiles based on FICO scoring rules
   - **Purpose**: Augment training data without privacy concerns
   - **Generation**: Rule-based synthetic tradeline generation

3. **Public Datasets**: Kaggle/research datasets on credit behavior
   - **Purpose**: Benchmark model accuracy against public data
   - **Source**: Publicly available credit datasets (no PII)

**Anonymization Process**:

```python
def anonymize_credit_report_for_training(report_id: str, user_id: str):
    """
    Anonymize credit report for AI training data.
    Only used if user consented to ai_training_consent.
    """
    # Check user consent
    user = supabase.table('users').select('ai_training_consent').eq('id', user_id).execute()
    if not user.data[0]['ai_training_consent']:
        return None  # User did not consent, do not use for training

    # Fetch credit report tradelines
    tradelines = supabase.table('tradelines').select('*').eq('credit_report_id', report_id).execute()

    # Anonymize each tradeline
    anonymized_tradelines = []
    for tradeline in tradelines.data:
        anonymized_tradelines.append({
            "account_type": tradeline['account_type'],  # Keep
            "status": tradeline['status'],  # Keep
            "balance": tradeline['balance'],  # Keep
            "credit_limit": tradeline['credit_limit'],  # Keep
            "payment_history": tradeline['payment_history'],  # Keep
            "is_negative": tradeline['is_negative'],  # Keep (label for training)
            "negative_type": tradeline['negative_type'],  # Keep (label for training)
            # Remove PII:
            "account_name": "ANONYMIZED",  # Remove creditor name
            "account_number_last_4": "XXXX",  # Remove account number
            "user_id": "ANONYMIZED"  # Remove user_id
        })

    # Store anonymized data in separate training dataset
    store_training_data(anonymized_tradelines)
```

**Training Data Storage**:
- **Separate database**: Anonymized training data stored in separate PostgreSQL database (not main production DB)
- **No linkage to users**: Anonymized data has no foreign key to `users` table
- **Retention**: Retained indefinitely for model improvement (user cannot request deletion after anonymization)

## Summary of Security, Compliance & Governance Decisions

1. **FCRA compliance**: 7-year retention for credit data, user consent for data collection, audit trail for disputes
2. **GDPR/CCPA compliance**: Right to access (data export API), right to erasure (account deletion API)
3. **Encryption at rest**: Supabase database encryption (AES-256) + column-level encryption for PII (SSN, account numbers)
4. **Encryption in transit**: HTTPS/TLS 1.2+ for all API calls, HSTS header enforcement
5. **Row-Level Security (RLS)**: Supabase RLS policies enforce user-scoped data access, prevents cross-user data leakage
6. **Admin access controls**: Admin role with limited permissions, all admin access logged in `data_access_log`
7. **API authentication**: Supabase JWT tokens with 1-hour expiration, token rotation on refresh
8. **Data classification**: 4 levels (Public, Internal, Confidential, Restricted) with appropriate encryption/access controls
9. **Data lifecycle management**: Collection → Storage → Usage → Retention (7 years) → Deletion
10. **Breach detection**: Automated anomaly detection on `data_access_log`, hourly monitoring
11. **Breach notification**: GDPR 72-hour notification requirement, user notification via email/dashboard
12. **AI training data**: Anonymized credit reports with user consent, synthetic data generation, public datasets

**Next Steps**:
- **@analysis-scalability-performance-capacity.md**: Performance optimization and capacity planning for viral growth (100 → 1000+ users)
