# 📚 Credit Clarity API - Documentation

## 🎯 **API Overview**

The Credit Clarity API is a high-performance, modular credit report processing system built with FastAPI. It provides secure endpoints for PDF processing, tradeline management, and system monitoring.

**Base URL**: `https://api.creditclarity.com`  
**Current Version**: `v1`  
**Architecture**: Modular, scalable, production-ready

## 🔐 **Authentication**

All API endpoints (except health checks) require authentication using JWT Bearer tokens.

### **Authentication Header**
```
Authorization: Bearer <your_jwt_token>
```

### **Getting Started**
1. Register for an account at [https://app.creditclarity.com](https://app.creditclarity.com)
2. Obtain your API token from the dashboard
3. Include the token in all API requests

## 📋 **API Endpoints**

### **Health Check Endpoints**

#### `GET /health`
Simple health check for load balancers.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "3.0.0"
}
```

#### `GET /api/v1/health/`
Comprehensive health check with system information.

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "3.0.0",
    "environment": "production",
    "features": {
      "security": true,
      "performance_optimization": true,
      "background_jobs": true,
      "caching": true,
      "monitoring": true
    },
    "services": {
      "optimized_processor": true,
      "background_jobs": true,
      "cache": true,
      "database": true
    },
    "system_health": {
      "status": "healthy",
      "issues": []
    }
  },
  "message": "System is healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0"
}
```

#### `GET /api/v1/health/metrics`
Basic system metrics (requires authentication).

**Parameters:**
- `minutes` (optional): Time range in minutes (default: 5)

**Response:**
```json
{
  "success": true,
  "data": {
    "system": {
      "avg_cpu_percent": 45.2,
      "avg_memory_percent": 62.1,
      "sample_count": 5
    },
    "api": {
      "total_requests": 150,
      "error_count": 2,
      "avg_response_time_ms": 250.5
    },
    "business": {
      "metrics": {
        "user_activity": {"count": 25}
      }
    },
    "background_jobs": {},
    "cache": {}
  },
  "message": "Metrics for last 5 minutes"
}
```

### **Credit Report Processing**

#### `POST /api/v1/processing/upload`
Process a credit report PDF file.

**Authentication**: Required  
**Content-Type**: `multipart/form-data`

**Parameters:**
- `file`: PDF file (required)
- `use_ocr`: Enable OCR processing (default: true)
- `use_ai_analysis`: Enable AI analysis (default: true)
- `priority`: Processing priority - "low", "normal", "high" (default: "normal")
- `save_to_database`: Save results to database (default: true)

**Request Example:**
```bash
curl -X POST "https://api.creditclarity.com/api/v1/processing/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@credit_report.pdf" \
  -F "use_ai_analysis=true" \
  -F "priority=normal"
```

**Response (Small Files - Synchronous):**
```json
{
  "success": true,
  "data": {
    "status": "completed",
    "tradelines_found": 5,
    "processing_method": "optimized_sync",
    "cost_estimate": 0.25,
    "processing_time": {
      "start_time": 1704067200,
      "duration_ms": 3500,
      "method": "synchronous"
    },
    "performance_metrics": {
      "file_size_mb": 2.3,
      "processing_time_ms": 3500,
      "method_used": "concurrent_extraction",
      "cache_hit": false,
      "tradelines_processed": 5,
      "optimization_level": "sync"
    },
    "cache_hit": false
  },
  "message": "Successfully processed 5 tradelines"
}
```

**Response (Large Files - Background Job):**
```json
{
  "success": true,
  "data": {
    "job_id": "job_abc123",
    "status": "queued",
    "progress": 0,
    "tradelines_found": 0,
    "processing_method": "background_job",
    "performance_metrics": {
      "file_size_mb": 15.7,
      "job_id": "job_abc123",
      "optimization_level": "background",
      "priority": "normal"
    }
  },
  "message": "File submitted for background processing. Job ID: job_abc123"
}
```

#### `GET /api/v1/processing/job/{job_id}`
Get background job status and results.

**Authentication**: Required

**Response:**
```json
{
  "success": true,
  "data": {
    "job_id": "job_abc123",
    "status": "completed",
    "progress": 100,
    "message": "Processing completed successfully",
    "result": {
      "tradelines_found": 8,
      "processing_method": "background_optimized",
      "cost_estimate": 0.75
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:02:30Z",
    "processing_time": 150.5
  },
  "message": "Job status retrieved"
}
```

#### `GET /api/v1/processing/jobs`
Get user's processing jobs.

**Authentication**: Required

**Parameters:**
- `limit`: Maximum jobs to return (default: 20)
- `status_filter`: Filter by status - "pending", "processing", "completed", "failed"

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "job_id": "job_abc123",
      "status": "completed",
      "progress": 100,
      "message": "Processing completed",
      "created_at": "2024-01-01T00:00:00Z",
      "processing_time": 150.5
    }
  ],
  "message": "Retrieved 1 jobs"
}
```

### **Tradelines Management**

#### `GET /api/v1/tradelines/`
Get user's tradelines with pagination and filtering.

**Authentication**: Required

**Parameters:**
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 50, max: 100)
- `sort_by`: Field to sort by
- `sort_order`: "asc" or "desc" (default: "desc")
- `credit_bureau`: Filter by credit bureau
- `account_type`: Filter by account type
- `is_negative`: Filter by negative status (true/false)
- `disputed`: Filter by dispute status (true/false)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "user_id": "user_123",
      "creditor_name": "Chase Credit Card",
      "account_number": "****1234",
      "account_type": "Credit Card",
      "account_status": "Open",
      "account_balance": "$1,500.00",
      "credit_limit": "$5,000.00",
      "monthly_payment": "$50.00",
      "date_opened": "2020-01-01",
      "credit_bureau": "Experian",
      "is_negative": false,
      "dispute_count": 0,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": null
    }
  ],
  "meta": {
    "page": 1,
    "limit": 50,
    "total": 1,
    "pages": 1,
    "has_next": false,
    "has_prev": false
  },
  "message": "Retrieved 1 tradelines"
}
```

#### `GET /api/v1/tradelines/{id}`
Get specific tradeline by ID.

**Authentication**: Required

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "creditor_name": "Chase Credit Card",
    "account_type": "Credit Card",
    // ... other fields
  },
  "message": "Tradeline retrieved"
}
```

#### `POST /api/v1/tradelines/`
Create a new tradeline.

**Authentication**: Required  
**Content-Type**: `application/json`

**Request Body:**
```json
{
  "creditor_name": "New Credit Card",
  "account_number": "****5678",
  "account_type": "Credit Card",
  "account_status": "Open",
  "account_balance": "$2,000.00",
  "credit_limit": "$8,000.00",
  "monthly_payment": "$75.00",
  "date_opened": "2023-06-01",
  "credit_bureau": "Equifax",
  "is_negative": false,
  "dispute_count": 0
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 2,
    "creditor_name": "New Credit Card",
    "user_id": "user_123",
    "created_at": "2024-01-01T00:00:00Z",
    // ... other fields
  },
  "message": "Tradeline created successfully"
}
```

#### `PUT /api/v1/tradelines/{id}`
Update existing tradeline.

**Authentication**: Required  
**Content-Type**: `application/json`

**Request Body:**
```json
{
  "creditor_name": "Updated Credit Card Name",
  "account_status": "Closed"
}
```

#### `DELETE /api/v1/tradelines/{id}`
Delete a tradeline.

**Authentication**: Required

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "1",
    "status": "deleted"
  },
  "message": "Tradeline deleted successfully"
}
```

#### `GET /api/v1/tradelines/stats/summary`
Get comprehensive tradelines statistics.

**Authentication**: Required

**Response:**
```json
{
  "success": true,
  "data": {
    "total_tradelines": 10,
    "positive_tradelines": 7,
    "negative_tradelines": 3,
    "disputed_tradelines": 2,
    "by_credit_bureau": {
      "Experian": 4,
      "Equifax": 3,
      "TransUnion": 3
    },
    "by_account_type": {
      "Credit Card": 6,
      "Auto Loan": 2,
      "Mortgage": 2
    },
    "by_account_status": {
      "Open": 8,
      "Closed": 2
    },
    "average_account_age_months": 36.5,
    "total_credit_limit": 85000.00,
    "total_balance": 12500.00,
    "credit_utilization_ratio": 0.147
  },
  "message": "Tradeline statistics retrieved"
}
```

#### `POST /api/v1/tradelines/bulk`
Perform bulk operations on multiple tradelines.

**Authentication**: Required  
**Content-Type**: `application/json`

**Request Body:**
```json
{
  "operation": "update",
  "tradeline_ids": [1, 2, 3],
  "update_data": {
    "dispute_count": 1
  },
  "batch_size": 50
}
```

**Operations:**
- `update`: Bulk update tradelines
- `delete`: Bulk delete tradelines  
- `dispute`: Increment dispute count

### **Admin Endpoints**

*Note: Admin endpoints require admin authentication*

#### `GET /api/v1/admin/metrics/detailed`
Get detailed system metrics for monitoring.

**Authentication**: Admin required

**Parameters:**
- `minutes`: Time range in minutes (default: 60, max: 1440)

**Response:**
```json
{
  "success": true,
  "data": {
    "system": {
      "period_minutes": 60,
      "avg_cpu_percent": 25.3,
      "max_cpu_percent": 45.2,
      "avg_memory_percent": 68.7,
      "disk_percent": 35.2,
      "active_users_last_hour": 15,
      "error_rate_trend": {
        "current_rate": 1.2,
        "status": "normal"
      }
    },
    "api": {
      "total_requests": 1250,
      "error_count": 15,
      "error_rate_percent": 1.2,
      "avg_response_time_ms": 185.3,
      "requests_per_minute": 20.8
    },
    "business": {
      "metrics": {
        "pdf_processing_time_ms": {
          "count": 45,
          "avg": 3250.5
        },
        "tradelines_extracted": {
          "count": 225,
          "sum": 225
        }
      }
    },
    "background_jobs": {
      "pending_jobs": 3,
      "completed_jobs": 125,
      "failed_jobs": 2,
      "avg_processing_time": 145.5
    },
    "cache": {
      "hit_rate": 0.87,
      "total_operations": 2500,
      "memory_usage_mb": 125.3
    }
  },
  "message": "Detailed metrics for last 60 minutes"
}
```

#### `POST /api/v1/admin/cache/manage`
Manage application cache.

**Authentication**: Admin required  
**Content-Type**: `application/json`

**Request Body:**
```json
{
  "action": "clear",
  "cache_type": "all"
}
```

**Actions:**
- `clear`: Clear cache
- `warm`: Warm cache with common data
- `stats`: Get cache statistics

**Cache Types:**
- `redis`: Redis cache only
- `memory`: In-memory cache only
- `all`: All cache layers

## 📊 **Response Format**

All API responses follow a standardized format:

### **Success Response**
```json
{
  "success": true,
  "data": { /* response data */ },
  "message": "Operation completed successfully",
  "timestamp": "2024-01-01T00:00:00Z",
  "request_id": "req_abc123",
  "version": "1.0"
}
```

### **Error Response**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "field": "creditor_name",
    "details": {
      "validation_errors": [...]
    }
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "request_id": "req_abc123",
  "version": "1.0"
}
```

### **Paginated Response**
```json
{
  "success": true,
  "data": [ /* array of items */ ],
  "meta": {
    "page": 1,
    "limit": 50,
    "total": 100,
    "pages": 2,
    "has_next": true,
    "has_prev": false
  },
  "message": "Data retrieved successfully"
}
```

## 🚨 **Error Codes**

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Request validation failed |
| `AUTHENTICATION_ERROR` | Authentication required or invalid |
| `AUTHORIZATION_ERROR` | Insufficient permissions |
| `RESOURCE_NOT_FOUND` | Requested resource not found |
| `PROCESSING_ERROR` | PDF processing failed |
| `DATABASE_ERROR` | Database operation failed |
| `CACHE_ERROR` | Cache operation failed |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `CONFIGURATION_ERROR` | System configuration error |
| `EXTERNAL_SERVICE_ERROR` | External service unavailable |
| `BUSINESS_LOGIC_ERROR` | Business rule violation |

## 📈 **Rate Limiting**

API requests are rate limited to ensure fair usage:

- **Default Limit**: 100 requests per minute
- **Burst Allowance**: 150 requests per minute (short bursts)
- **Admin Endpoints**: 50 requests per minute

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1609459200
```

## 🔧 **Development Tools**

### **Interactive Documentation**
- **Swagger UI**: `https://api.creditclarity.com/docs`
- **ReDoc**: `https://api.creditclarity.com/redoc`

### **API Testing**
```bash
# Health check
curl https://api.creditclarity.com/health

# Get tradelines
curl -H "Authorization: Bearer <token>" \
  https://api.creditclarity.com/api/v1/tradelines/

# Upload credit report
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -F "file=@report.pdf" \
  https://api.creditclarity.com/api/v1/processing/upload
```

## 📞 **Support**

- **Documentation**: [https://docs.creditclarity.com](https://docs.creditclarity.com)
- **API Status**: [https://status.creditclarity.com](https://status.creditclarity.com)
- **Developer Support**: [api-support@creditclarity.com](mailto:api-support@creditclarity.com)
- **GitHub Issues**: [https://github.com/creditclarity/api/issues](https://github.com/creditclarity/api/issues)

---

**Version**: 3.0.0 (Modular Architecture)  
**Last Updated**: January 2024  
**API Specification**: OpenAPI 3.0