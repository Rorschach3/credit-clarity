# 🔐 Security Setup Guide - Credit Clarity

## 🚨 CRITICAL: Phase 1 Security Implementation

This document outlines the security enhancements implemented in Phase 1 of the Credit Clarity security audit.

## ✅ What's Been Fixed

### 1. **Environment Variables Secured**
- ✅ Created `.env.example` template with all required variables
- ✅ Enhanced `.gitignore` to prevent future key exposure
- ✅ Implemented secure configuration management with validation

### 2. **Authentication System Implemented**
- ✅ JWT-based authentication middleware
- ✅ Supabase JWT token verification
- ✅ User context extraction and validation

### 3. **Rate Limiting Added**
- ✅ Request rate limiting (100 requests per hour by default)
- ✅ IP-based and user-based limiting
- ✅ Configurable limits via environment variables

### 4. **Security Headers & CORS**
- ✅ Security headers middleware (XSS protection, content type options, etc.)
- ✅ Environment-specific CORS configuration
- ✅ Content validation middleware

## 🚀 Quick Start (Secure Setup)

### 1. **Environment Configuration**

```bash
# Copy the example environment file
cp backend/.env.example backend/.env

# Edit .env file with your actual values
nano backend/.env
```

**Required Environment Variables:**
```env
# Security (REQUIRED for production)
JWT_SECRET=your-jwt-secret-key-minimum-32-characters
ENCRYPTION_KEY=your-encryption-key-32-characters

# Supabase (REQUIRED)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here

# API Keys (as needed)
GEMINI_API_KEY=your-gemini-api-key
GOOGLE_CLOUD_PROJECT_ID=your-project-id
DOCUMENT_AI_PROCESSOR_ID=your-processor-id

# Environment
NODE_ENV=production  # or development
ENVIRONMENT=production  # or development
```

### 2. **Install Secure Dependencies**

```bash
cd backend
pip install -r requirements-security.txt
```

### 3. **Run Secure Server**

```bash
# Development mode
python main_secure.py

# Production mode with environment variables
ENVIRONMENT=production python main_secure.py
```

## 🔒 Security Features

### **Authentication**
- **JWT Tokens**: Secure token-based authentication
- **Supabase Integration**: Native Supabase user authentication
- **Token Validation**: Automatic token verification and user extraction

### **Rate Limiting**
- **Default Limits**: 100 requests per hour per user/IP
- **Configurable**: Set via `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW`
- **Smart Detection**: Different limits for authenticated vs anonymous users

### **Security Headers**
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY  
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Strict-Transport-Security: max-age=31536000; includeSubDomains (production)
```

### **CORS Protection**
- **Development**: Allows localhost origins
- **Production**: Strict origin validation
- **Configurable**: Set allowed origins via `CORS_ORIGINS`

### **Content Validation**
- **File Size Limits**: 50MB maximum file size
- **Content Type Validation**: Only allows specified content types
- **Request Validation**: Validates all incoming requests

## 🛡️ API Endpoint Security

### **Protected Endpoints**
- `/process-credit-report` - Requires authentication + rate limiting
- All endpoints have security headers and request logging

### **Authentication Required**
```bash
# All requests to protected endpoints must include:
Authorization: Bearer <your-jwt-token>
```

### **Rate Limiting Headers**
```
X-RateLimit-Limit: 100
X-RateLimit-Window: 3600
Retry-After: 3600 (when limited)
```

## 🚨 Migration from Old System

### **Step 1: Update API Calls**
Replace calls to `main.py` with `main_secure.py`:

```javascript
// Old (insecure)
fetch('/api/process-credit-report', {
    method: 'POST',
    body: formData
});

// New (secure)
fetch('/api/process-credit-report', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${userToken}`
    },
    body: formData
});
```

### **Step 2: Handle Authentication**
Ensure your frontend handles authentication tokens:

```javascript
// Get user token from Supabase
const { data: { session } } = await supabase.auth.getSession();
const token = session?.access_token;

// Use token in API calls
const response = await fetch('/api/process-credit-report', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
    },
    body: formData
});
```

### **Step 3: Handle Rate Limiting**
Add proper error handling for rate limits:

```javascript
if (response.status === 429) {
    const retryAfter = response.headers.get('Retry-After');
    console.log(`Rate limited. Retry after ${retryAfter} seconds`);
    // Show user-friendly message
}
```

## ⚙️ Configuration Options

### **Security Settings**
```env
# JWT Configuration
JWT_SECRET=minimum-32-character-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# CORS
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
CORS_ALLOW_CREDENTIALS=true

# Environment
ENVIRONMENT=production
DEBUG=false
```

### **Production Checklist**
- [ ] `ENVIRONMENT=production`
- [ ] Strong `JWT_SECRET` (32+ characters)
- [ ] Specific `CORS_ORIGINS` (no wildcards)
- [ ] Valid SSL certificates
- [ ] Secure database connections
- [ ] API keys properly secured
- [ ] Rate limits configured appropriately
- [ ] Monitoring and logging enabled

## 📊 Monitoring & Logging

### **Request Logging**
All requests are automatically logged with:
- Method and URL
- Client IP address
- Response status and processing time
- Authentication status

### **Error Tracking**
- Structured error logging
- Request correlation IDs
- Security event logging
- Rate limit violation tracking

### **Health Checks**
```bash
curl -X GET https://your-api.com/health
```

Response includes service status and configuration info.

## 🚫 What's Blocked

### **File Types**
- Only PDF files are accepted
- All other file types return 415 Unsupported Media Type

### **Request Sizes**
- Maximum file size: 50MB
- Large requests are rejected with 413 Request Entity Too Large

### **Origins**
- Only configured origins allowed in production
- Development mode shows warnings for unconfigured origins

### **Rate Limits**
- 429 Too Many Requests after limit exceeded
- Automatic retry headers provided

## 🔄 Next Steps

### **Phase 2 - Performance** (Recommended)
1. Database query optimization
2. Caching layer implementation
3. Background job processing
4. Resource usage monitoring

### **Phase 3 - Architecture** (Future)
1. Microservices separation
2. API versioning
3. Advanced monitoring
4. Automated scaling

## 🆘 Troubleshooting

### **Common Issues**

**Authentication Fails**
```bash
# Check if JWT_SECRET is set
echo $JWT_SECRET

# Verify token format
curl -H "Authorization: Bearer <token>" /health
```

**Rate Limited**
```bash
# Check current limits
curl -I /health | grep RateLimit

# Wait for window to reset or increase limits
```

**CORS Issues**
```bash
# Check allowed origins
curl -H "Origin: https://your-domain.com" /health

# Update CORS_ORIGINS in .env
```

**File Upload Fails**
```bash
# Check file size and type
ls -la your-file.pdf

# Verify content type is application/pdf
file your-file.pdf
```

## 📞 Support

For security-related issues:
1. Check logs for detailed error messages
2. Verify environment configuration
3. Test with development mode first
4. Check authentication token validity

---

**⚠️ IMPORTANT**: Never commit `.env` files or service account keys to version control. Always use the `.env.example` template for new deployments.