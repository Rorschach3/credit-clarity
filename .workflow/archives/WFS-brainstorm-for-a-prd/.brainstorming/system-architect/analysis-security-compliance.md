# Security & Compliance Architecture

**Parent Document**: @analysis.md
**Framework Reference**: @../guidance-specification.md (Section 5: Data Architect Decisions - Data Privacy & Compliance)

---

## Overview

This section details the security and compliance architecture to meet FCRA requirements, protect sensitive credit data, and ensure regulatory compliance across all phases.

---

## FCRA Compliance Requirements

### Fair Credit Reporting Act (15 U.S.C. § 1681)

**Key Provisions Affecting Architecture**:

1. **§ 1681i**: Consumer's Right to Dispute**
   - Consumers have the right to dispute inaccurate information
   - Bureaus must investigate within 30 days
   - Automated dispute systems must be FCRA-compliant

2. **§ 1681c**: Duration of Negative Information**
   - Most negative items: 7 years from date of delinquency
   - Bankruptcies: 10 years
   - Positive items: No time limit
   - **Architecture Impact**: Data retention policies required

3. **§ 1681g**: Disclosure Requirements**
   - Users must consent to data collection and usage
   - Clear disclosure of how data is used
   - **Architecture Impact**: Consent management system

4. **§ 1681e(b)**: Maximum Possible Accuracy**
   - Reasonable procedures to assure maximum accuracy
   - **Architecture Impact**: AI classification must be explainable

**Compliance Architecture Decisions**:

```python
# FCRA compliance layer
class FCRACompliance:
    """Ensure FCRA compliance across application."""

    @staticmethod
    def validate_dispute_letter(letter: str) -> Dict[str, Any]:
        """Validate dispute letter meets FCRA requirements."""

        required_elements = [
            "consumer_name",
            "consumer_address",
            "account_identification",
            "dispute_reason",
            "request_for_investigation"
        ]

        validation_result = {
            "is_compliant": True,
            "missing_elements": [],
            "warnings": []
        }

        # Check for required elements
        for element in required_elements:
            if not re.search(FCRA_PATTERNS[element], letter):
                validation_result["is_compliant"] = False
                validation_result["missing_elements"].append(element)

        # Check for prohibited language
        prohibited_terms = ["guarantee", "promise", "will be deleted"]
        for term in prohibited_terms:
            if term.lower() in letter.lower():
                validation_result["warnings"].append(f"Avoid language: '{term}'")

        return validation_result

    @staticmethod
    def enforce_data_retention(user_id: str):
        """Enforce 7-year data retention policy."""

        cutoff_date = datetime.utcnow() - timedelta(days=365 * 7)

        # Delete old credit reports and tradelines
        deleted_count = await delete_old_data(user_id, cutoff_date)

        logger.info(f"Deleted {deleted_count} records for user {user_id} (FCRA retention)")

        return deleted_count
```

---

## Authentication & Authorization Architecture

### Supabase Auth Integration

**Current Setup** (from existing codebase):
```python
# Existing: backend/core/security.py
from supabase import create_client

class SupabaseAuth:
    def __init__(self):
        self.client = create_client(
            settings.supabase_url,
            settings.supabase_anon_key
        )

    async def verify_jwt(self, token: str) -> Dict[str, Any]:
        """Verify Supabase JWT token."""

        try:
            # Verify JWT signature and expiration
            user = self.client.auth.get_user(token)
            return {
                "user_id": user.id,
                "email": user.email,
                "role": user.role
            }
        except Exception as e:
            raise AuthenticationError("Invalid token")
```

**JWT Token Structure**:
```json
{
  "aud": "authenticated",
  "exp": 1704067200,
  "sub": "user-uuid",
  "email": "user@example.com",
  "role": "authenticated",
  "app_metadata": {
    "provider": "email"
  },
  "user_metadata": {
    "full_name": "John Doe"
  }
}
```

**Authorization Middleware**:
```python
# API request authorization
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Verify authentication for protected endpoints."""

    # Skip auth for public endpoints
    if request.url.path in ["/health", "/docs", "/openapi.json"]:
        return await call_next(request)

    # Extract JWT from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")

    token = auth_header.split(" ")[1]

    # Verify JWT
    try:
        user_data = await supabase_auth.verify_jwt(token)
        request.state.user_id = user_data["user_id"]
        request.state.user_email = user_data["email"]
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid token")

    return await call_next(request)
```

### Row-Level Security (RLS) Policies

**Supabase RLS Configuration**:
```sql
-- Enable RLS on all tables
ALTER TABLE tradelines ENABLE ROW LEVEL SECURITY;
ALTER TABLE disputes ENABLE ROW LEVEL SECURITY;
ALTER TABLE report_uploads ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only access their own data
CREATE POLICY "Users can view their own tradelines"
    ON tradelines FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own tradelines"
    ON tradelines FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own tradelines"
    ON tradelines FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own tradelines"
    ON tradelines FOR DELETE
    USING (auth.uid() = user_id);

-- Similar policies for disputes, report_uploads, etc.
```

**Benefits**:
- ✅ Database-level security (enforced even with direct SQL access)
- ✅ Automatic multi-tenancy (no application-level filtering needed)
- ✅ Protection against authorization bugs in application code

---

## Data Encryption Architecture

### Encryption at Rest

**Supabase PostgreSQL**:
- ✅ Full database encryption enabled by default (AES-256)
- ✅ Encrypted backups (automatic daily backups)
- ✅ Encryption keys managed by Supabase (AWS KMS)

**Supabase Storage** (for PDF uploads):
```python
# Upload PDF with encryption
async def upload_credit_report(file: UploadFile, user_id: str) -> str:
    """Upload credit report to Supabase Storage."""

    # Generate unique storage path
    file_hash = hashlib.sha256(await file.read()).hexdigest()
    storage_path = f"{user_id}/{file_hash}/{file.filename}"

    # Upload to Supabase Storage (automatically encrypted at rest)
    await supabase.storage.from_("credit-reports").upload(
        path=storage_path,
        file=file.file,
        file_options={
            "content-type": file.content_type,
            "cache-control": "3600"
        }
    )

    return storage_path
```

### Encryption in Transit

**HTTPS/TLS Configuration**:
```python
# Production HTTPS enforcement
if settings.environment == "production":
    # Redirect HTTP to HTTPS
    app.add_middleware(HTTPSRedirectMiddleware)

    # Strict Transport Security (HSTS)
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response
```

### Column-Level Encryption (PII Fields)

**Selective Encryption for SSN, Account Numbers**:
```python
# backend/utils/field_encryption.py
from cryptography.fernet import Fernet
from core.config import get_settings

settings = get_settings()

class FieldEncryption:
    """Application-level encryption for sensitive fields."""

    def __init__(self):
        # Encryption key from environment (32-byte base64-encoded key)
        self.cipher = Fernet(settings.encryption_key.encode())

    def encrypt_ssn(self, ssn: str) -> str:
        """Encrypt SSN for storage."""
        return self.cipher.encrypt(ssn.encode()).decode()

    def decrypt_ssn(self, encrypted_ssn: str) -> str:
        """Decrypt SSN for display."""
        return self.cipher.decrypt(encrypted_ssn.encode()).decode()

    def encrypt_account_number(self, account_number: str) -> str:
        """Encrypt account number for storage."""
        return self.cipher.encrypt(account_number.encode()).decode()

    def decrypt_account_number(self, encrypted_account: str) -> str:
        """Decrypt account number for display."""
        return self.cipher.decrypt(encrypted_account.encode()).decode()

# Usage in tradeline storage
field_encryption = FieldEncryption()

# Before saving to database
tradeline_data['ssn'] = field_encryption.encrypt_ssn(tradeline_data['ssn'])
tradeline_data['account_number'] = field_encryption.encrypt_account_number(
    tradeline_data['account_number']
)

# After retrieving from database
tradeline_data['ssn'] = field_encryption.decrypt_ssn(tradeline_data['ssn'])
tradeline_data['account_number'] = field_encryption.decrypt_account_number(
    tradeline_data['account_number']
)
```

**Key Management**:
```python
# core/config.py
class Settings(BaseSettings):
    # Encryption key for column-level encryption
    encryption_key: str = Field(
        default=None,
        env="ENCRYPTION_KEY"
    )

    @validator('encryption_key')
    def validate_encryption_key(cls, v):
        if not v and cls.environment == "production":
            raise ValueError("ENCRYPTION_KEY required in production")

        # Validate key format (32-byte base64)
        try:
            key_bytes = base64.urlsafe_b64decode(v)
            if len(key_bytes) != 32:
                raise ValueError("Encryption key must be 32 bytes")
        except Exception as e:
            raise ValueError(f"Invalid encryption key format: {e}")

        return v

# Generate encryption key (one-time setup)
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## Audit Trail & Logging

### Comprehensive Audit Logging

**Audit Trail for Dispute Status Changes**:
```python
# Already implemented in data infrastructure
async def update_dispute_status(
    dispute_id: str,
    new_status: str,
    changed_by: str,
    change_reason: str = None
):
    """Update dispute status with audit trail."""

    # Get current status
    current_dispute = await get_dispute(dispute_id)
    previous_status = current_dispute['status']

    # Update dispute record
    await execute_sql("""
        UPDATE disputes
        SET status = :status, status_updated_at = NOW()
        WHERE dispute_id = :dispute_id
    """, {"status": new_status, "dispute_id": dispute_id})

    # Log status change in audit trail
    await execute_sql("""
        INSERT INTO dispute_status_history (
            dispute_id, previous_status, new_status, changed_by, change_reason
        ) VALUES (:dispute_id, :previous_status, :new_status, :changed_by, :change_reason)
    """, {
        "dispute_id": dispute_id,
        "previous_status": previous_status,
        "new_status": new_status,
        "changed_by": changed_by,
        "change_reason": change_reason
    })

    logger.info(f"Dispute {dispute_id} status changed: {previous_status} → {new_status} by {changed_by}")
```

**Structured Logging for Security Events**:
```python
# Structured JSON logging
import structlog

logger = structlog.get_logger()

# Log authentication events
logger.info(
    "user_login",
    user_id=user_id,
    email=user_email,
    ip_address=request.client.host,
    user_agent=request.headers.get("User-Agent"),
    timestamp=datetime.utcnow().isoformat()
)

# Log data access events
logger.info(
    "credit_report_accessed",
    user_id=user_id,
    report_id=report_id,
    action="view",
    ip_address=request.client.host,
    timestamp=datetime.utcnow().isoformat()
)

# Log suspicious activity
logger.warning(
    "rate_limit_exceeded",
    user_id=user_id,
    action="upload",
    limit=2,
    attempts=3,
    ip_address=request.client.host,
    timestamp=datetime.utcnow().isoformat()
)
```

---

## User Consent Management

### Consent Collection & Tracking

**Consent Schema**:
```sql
-- User consent tracking
CREATE TABLE user_consents (
    consent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Consent type
    consent_type VARCHAR(50) NOT NULL CHECK (
        consent_type IN ('data_collection', 'ml_training', 'marketing', 'analytics')
    ),

    -- Consent status
    consent_given BOOLEAN NOT NULL,
    consent_date TIMESTAMP DEFAULT NOW(),

    -- Consent version (for updated terms)
    consent_version VARCHAR(20) DEFAULT '1.0',

    -- IP address and user agent for audit
    ip_address VARCHAR(45),
    user_agent TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes
    INDEX idx_consents_user (user_id, consent_type),
    UNIQUE (user_id, consent_type)
);

-- Enable RLS
ALTER TABLE user_consents ENABLE ROW LEVEL SECURITY;

CREATE POLICY consents_user_policy ON user_consents
    FOR ALL
    USING (auth.uid() = user_id);
```

**Consent Collection UI**:
```python
# API endpoint for consent management
@router.post("/api/v1/users/me/consents")
async def update_consent(
    consent_type: str,
    consent_given: bool,
    request: Request
):
    """Update user consent preferences."""

    user_id = request.state.user_id

    # Record consent
    await execute_sql("""
        INSERT INTO user_consents (user_id, consent_type, consent_given, ip_address, user_agent)
        VALUES (:user_id, :consent_type, :consent_given, :ip_address, :user_agent)
        ON CONFLICT (user_id, consent_type)
        DO UPDATE SET
            consent_given = :consent_given,
            consent_date = NOW(),
            ip_address = :ip_address,
            user_agent = :user_agent
    """, {
        "user_id": user_id,
        "consent_type": consent_type,
        "consent_given": consent_given,
        "ip_address": request.client.host,
        "user_agent": request.headers.get("User-Agent")
    })

    logger.info(f"User {user_id} updated consent: {consent_type} = {consent_given}")

    return {"success": True}
```

**Consent Enforcement**:
```python
# Check consent before ML training
async def can_use_for_ml_training(user_id: str) -> bool:
    """Check if user has consented to ML training."""

    consent = await execute_sql("""
        SELECT consent_given
        FROM user_consents
        WHERE user_id = :user_id
          AND consent_type = 'ml_training'
    """, {"user_id": user_id})

    return consent[0]['consent_given'] if consent else False

# Usage
if await can_use_for_ml_training(user_id):
    # Include data in ML training dataset
    await add_to_training_dataset(tradelines, anonymized=True)
```

---

## Data Retention & Deletion

### Automated Data Retention

**7-Year Retention Policy** (FCRA Compliance):
```python
# Scheduled job: Run monthly
@scheduler.scheduled_job('cron', day=1, hour=2)  # 1st of month at 2am
async def enforce_data_retention():
    """Delete credit data older than 7 years."""

    cutoff_date = datetime.utcnow() - timedelta(days=365 * 7)

    # Delete old tradelines
    deleted_tradelines = await execute_sql("""
        DELETE FROM tradelines
        WHERE created_at < :cutoff_date
        RETURNING tradeline_id
    """, {"cutoff_date": cutoff_date})

    # Delete old reports
    deleted_reports = await execute_sql("""
        DELETE FROM report_uploads
        WHERE uploaded_at < :cutoff_date
        RETURNING id
    """, {"cutoff_date": cutoff_date})

    logger.info(f"Data retention: Deleted {len(deleted_tradelines)} tradelines, {len(deleted_reports)} reports")

    # Delete associated storage files
    for report in deleted_reports:
        await supabase.storage.from_("credit-reports").remove(report['storage_path'])
```

### Right to Deletion (CCPA/GDPR)

**User-Initiated Data Deletion**:
```python
@router.delete("/api/v1/users/me/data")
async def delete_user_data(request: Request):
    """Delete all user data (CCPA/GDPR right to deletion)."""

    user_id = request.state.user_id

    # Delete all user data
    await execute_sql("DELETE FROM tradelines WHERE user_id = :user_id", {"user_id": user_id})
    await execute_sql("DELETE FROM disputes WHERE user_id = :user_id", {"user_id": user_id})
    await execute_sql("DELETE FROM report_uploads WHERE user_id = :user_id", {"user_id": user_id})

    # Delete storage files
    storage_files = await supabase.storage.from_("credit-reports").list(user_id)
    for file in storage_files:
        await supabase.storage.from_("credit-reports").remove(f"{user_id}/{file['name']}")

    # Log deletion
    logger.info(f"User {user_id} requested data deletion (CCPA/GDPR)")

    return {"message": "All user data has been deleted"}
```

---

## Security Headers & CORS

### Production Security Headers

```python
# backend/core/security.py
class SecurityHeadersMiddleware:
    """Add security headers to all responses."""

    async def __call__(self, request: Request, call_next):
        response = await call_next(request)

        # HTTPS Strict Transport Security
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Clickjacking protection
        response.headers["X-Frame-Options"] = "DENY"

        # XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https://api.creditclarity.com"
        )

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response
```

### CORS Configuration

```python
# CORS settings for production
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # ["https://creditclarity.com"]
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600  # Cache preflight requests for 1 hour
)
```

---

## Penetration Testing & Security Audits

### Phase 1 Security Checklist

**Pre-Launch Security Validation**:
- [ ] HTTPS/TLS certificate configured
- [ ] Supabase RLS policies tested
- [ ] Column-level encryption for SSN/account numbers
- [ ] JWT token expiration tested (15-minute access tokens)
- [ ] Rate limiting validated (freemium tier enforcement)
- [ ] CORS configured for production domain only
- [ ] Security headers validated (A+ SSL Labs rating)
- [ ] FCRA-compliant letter templates reviewed by legal
- [ ] Data retention policy implemented (7-year auto-deletion)
- [ ] User consent collection tested

### Phase 2 Security Enhancements

**Third-Party Security Audit**:
- Penetration testing by security firm
- OWASP Top 10 compliance validation
- PCI DSS compliance (if storing payment info)
- SOC 2 Type II certification (for enterprise customers)

---

## Incident Response Plan

### Security Incident Playbook

**Incident Detection**:
```python
# Automated security alerts
async def detect_security_incidents():
    """Monitor for suspicious activity."""

    # Alert 1: Multiple failed login attempts
    failed_logins = await get_failed_login_count(user_id, timeframe_minutes=10)
    if failed_logins > 5:
        await send_security_alert("Multiple failed logins", user_id=user_id)

    # Alert 2: Unusual data access patterns
    if await detect_unusual_access_pattern(user_id):
        await send_security_alert("Unusual data access pattern", user_id=user_id)

    # Alert 3: Rate limit abuse
    if await detect_rate_limit_abuse(user_id):
        await send_security_alert("Rate limit abuse detected", user_id=user_id)
```

**Incident Response**:
1. **Detection**: Automated monitoring triggers alert
2. **Containment**: Suspend user account, revoke JWT tokens
3. **Investigation**: Review audit logs, identify scope
4. **Remediation**: Fix vulnerability, reset credentials
5. **Notification**: Notify affected users (if required by law)
6. **Post-Incident**: Update security policies, improve monitoring

---

## Conclusion

The security architecture prioritizes FCRA compliance, data protection, and user privacy through multiple defense layers: database-level RLS, application-level encryption, comprehensive audit logging, and automated data retention policies.

**Key Strengths**:
- ✅ Supabase RLS provides automatic multi-tenancy security
- ✅ Column-level encryption protects SSN and account numbers
- ✅ Comprehensive audit trail for FCRA compliance
- ✅ User consent management for ML training and analytics
- ✅ Automated 7-year data retention enforcement

**Phase 1 Deliverables**:
- FCRA-compliant dispute letter validation
- Column-level encryption implementation
- User consent collection UI
- Security headers middleware
- Data retention scheduled job
- Audit logging for all data access
