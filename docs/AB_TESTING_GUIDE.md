# A/B Testing Integration Guide

## 🎯 Overview

The A/B testing framework is now **fully integrated** into the main OCR workflow. It automatically routes users between different processing pipelines and tracks performance metrics for data-driven optimization.

## 🏗️ Architecture

### Components
- **ABTestManager**: Core framework managing variant assignment and metrics
- **Processing Routes**: V1 (legacy) + V2 (new optimized pipeline) + A/B enabled V1
- **Metrics Tracking**: Automatic performance tracking for all processing attempts
- **Admin Endpoints**: Configuration and results analysis

### Integration Points
1. **Main Processing Endpoint** (`/api/v1/processing/upload`)
   - Automatically assigns users to test variants
   - Tracks all processing attempts with A/B metadata
   - Routes to appropriate pipeline based on variant

2. **V2 Processing Endpoint** (`/api/v1/processing/v2/upload`)
   - Dedicated endpoint for testing new pipeline
   - Full A/B testing capabilities with advanced routing

## 🚀 How to Use A/B Testing

### 1. **Automatic Processing (Recommended)**

Users are automatically enrolled in A/B tests when using the standard endpoint:

```bash
curl -X POST "http://localhost:8000/api/v1/processing/upload" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@credit_report.pdf"
```

The system automatically:
- Assigns user to control (V1) or treatment (V2) variant
- Tracks processing time, success rate, cost, and tradelines extracted
- Stores metrics for analysis

### 2. **Manual Pipeline Selection**

For testing specific pipelines:

```bash
# Force V2 pipeline
curl -X POST "http://localhost:8000/api/v1/processing/v2/upload" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@credit_report.pdf" \
  -F "pipeline_version=v2"

# Force V1 pipeline  
curl -X POST "http://localhost:8000/api/v1/processing/v2/upload" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@credit_report.pdf" \
  -F "pipeline_version=v1"
```

### 3. **View Test Results**

Get comprehensive A/B test analysis:

```bash
# Admin only - get test results
curl -X GET "http://localhost:8000/api/v1/processing/ab-test/results?days=7&test_name=pipeline_v2" \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

### 4. **Monitor Test Status**

Check active tests and configuration:

```bash
curl -X GET "http://localhost:8000/api/v1/processing/ab-test/status" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 5. **Update Test Configuration**

Admins can modify test parameters:

```bash
# Change treatment percentage to 50%
curl -X POST "http://localhost:8000/api/v1/processing/ab-test/config" \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "test_name": "pipeline_v2",
    "treatment_percentage": 50.0,
    "enabled": true,
    "file_size_threshold_mb": 10.0
  }'
```

## 📊 Metrics Tracked

For each processing attempt, the system tracks:

- **Variant**: control/treatment assignment
- **User ID**: For consistent assignment
- **File Size**: Processing complexity indicator
- **Processing Time**: Performance metric
- **Tradelines Extracted**: Accuracy metric
- **Success Rate**: Reliability metric
- **Cost**: Economic efficiency
- **Method Used**: Processing technique
- **Error Messages**: Failure analysis

## 🎛️ Configuration Options

### Default Configuration
```python
ABTestConfig(
    test_name='pipeline_v2',
    treatment_percentage=30.0,    # 30% to V2 pipeline
    enabled=True,
    start_date=now,
    end_date=now + 30_days,
    user_whitelist=[],            # Force specific users to treatment
    user_blacklist=[],            # Force specific users to control
    file_size_threshold_mb=None   # Route large files to specific variant
)
```

### Variant Assignment Logic
1. **Whitelist Check**: Users in whitelist → Treatment
2. **Blacklist Check**: Users in blacklist → Control
3. **File Size Check**: Large files → Control (if threshold set)
4. **Hash-based**: Consistent assignment based on user ID hash

## 📈 Analysis & Recommendations

The system provides automated analysis with recommendations:

- **`treatment_winner_launch`**: V2 significantly better, recommend full rollout
- **`control_winner_stop_test`**: V1 better, stop test and optimize V2
- **`no_significant_difference`**: Results too close, need more data
- **`continue_testing`**: Mixed results, continue collecting data
- **`insufficient_sample_size`**: Need more samples for statistical significance

## 🔧 Development & Testing

### Run Integration Tests
```bash
cd backend
source venv/bin/activate
python test_ab_integration.py
```

### Monitor Real-time Metrics
```python
from services.ab_testing import ab_test_manager

# Check current metrics
results = ab_test_manager.get_test_results('pipeline_v2', days=1)
print(f"Samples today: {results['total_samples']}")
print(f"Recommendation: {results['recommendation']}")
```

### Debug Variant Assignment
```python
from services.ab_testing import ab_test_manager

# Test specific user assignment
variant = ab_test_manager.assign_variant('user_123', 2.5)
print(f"User will be routed to: {variant.value}")
```

## 🛡️ Security & Access Control

- **Admin Endpoints**: Require admin privileges for configuration and detailed results
- **User Endpoints**: Standard authentication for processing and basic status
- **Rate Limiting**: Applied to all A/B testing endpoints
- **Audit Logging**: All configuration changes are logged

## 🚨 Important Notes

1. **Consistent Assignment**: Users get the same variant based on hash of user ID
2. **File Size Routing**: Large files (>threshold) can be forced to control variant for stability
3. **Background Jobs**: A/B variant info is passed to background processing jobs
4. **Error Tracking**: Failed processing attempts are tracked with error details
5. **Production Ready**: Framework includes proper error handling and monitoring

## 📋 Quick Start Checklist

- ✅ A/B testing framework integrated into main processing flow
- ✅ Automatic variant assignment and metrics tracking
- ✅ Admin endpoints for configuration and analysis  
- ✅ Error handling and failure tracking
- ✅ Integration tests passing
- ✅ Documentation complete

The A/B testing system is now **fully operational** and ready to help optimize your OCR pipeline performance!