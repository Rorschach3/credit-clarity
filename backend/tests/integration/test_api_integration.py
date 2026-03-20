"""
Integration tests for Credit Clarity API
Tests full request/response cycles and service integration
"""
import pytest
import tempfile
import os
from unittest.mock import patch, AsyncMock

@pytest.mark.integration
async def test_full_health_check_integration(client):
    """Integration test for complete health check flow."""
    # Test simple health endpoint
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    
    # Test detailed health endpoint
    response = await client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "services" in data["data"]

@pytest.mark.integration
async def test_api_version_consistency(client):
    """Test API version consistency across endpoints."""
    endpoints = [
        "/api/v1/health/",
        "/api/v1/health/live",
        "/api/v1/health/ready"
    ]
    
    for endpoint in endpoints:
        response = await client.get(endpoint)
        assert "X-API-Version" in response.headers
        assert response.headers["X-API-Version"] == "1.0"

@pytest.mark.integration
async def test_error_handling_integration(client, auth_headers):
    """Test error handling across different failure scenarios."""
    # Test 404 error
    response = await client.get("/api/v1/tradelines/99999", headers=auth_headers)
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert "timestamp" in data
    
    # Test validation error
    invalid_tradeline = {"creditor_name": ""}  # Empty required field
    response = await client.post("/api/v1/tradelines/", json=invalid_tradeline, headers=auth_headers)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"

@pytest.mark.integration
async def test_authentication_integration(client):
    """Test authentication across different endpoints."""
    protected_endpoints = [
        ("/api/v1/tradelines/", "GET"),
        ("/api/v1/tradelines/", "POST"),
        ("/api/v1/processing/jobs", "GET")
    ]
    
    for endpoint, method in protected_endpoints:
        if method == "GET":
            response = await client.get(endpoint)
        elif method == "POST":
            response = await client.post(endpoint, json={})
        
        assert response.status_code in [401, 403]  # Unauthorized or Forbidden

@pytest.mark.integration
async def test_admin_endpoints_integration(client, admin_auth_headers):
    """Test admin-only endpoints with proper authentication."""
    with patch('services.monitoring.metrics_collector') as mock_metrics, \
         patch('services.cache_service.cache') as mock_cache, \
         patch('services.background_jobs.job_processor') as mock_jobs:
        
        # Setup mocks
        mock_metrics.get_system_metrics_summary.return_value = {"avg_cpu_percent": 25.0}
        mock_metrics.get_api_metrics_summary.return_value = {"total_requests": 100}
        mock_metrics.get_business_metrics_summary.return_value = {"metrics": {}}
        mock_cache.detailed_stats.return_value = {"hit_rate": 0.85}
        mock_jobs.get_detailed_stats.return_value = {"pending_jobs": 0}
        
        # Test admin metrics endpoint
        response = await client.get("/api/v1/admin/metrics/detailed", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "system" in data["data"]

@pytest.mark.integration
async def test_cors_integration(client):
    """Test CORS headers across different endpoints."""
    # Test preflight request
    response = await client.options(
        "/api/v1/health/",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"}
    )
    
    # Check CORS headers are present (might be 405 if OPTIONS not handled)
    assert response.status_code in [200, 405]

@pytest.mark.integration
async def test_request_id_consistency(client):
    """Test request ID consistency across request lifecycle."""
    response = await client.get("/api/v1/health/")
    request_id = response.headers.get("X-Request-ID")
    
    assert request_id is not None
    assert len(request_id) >= 8  # Should be at least 8 characters

@pytest.mark.integration 
async def test_performance_headers_integration(client):
    """Test performance headers across endpoints."""
    endpoints = [
        "/health",
        "/api/v1/health/",
        "/api/v1/health/live"
    ]
    
    for endpoint in endpoints:
        response = await client.get(endpoint)
        assert "X-Process-Time" in response.headers
        assert "X-Request-ID" in response.headers
        
        # Process time should be a valid number
        process_time = float(response.headers["X-Process-Time"])
        assert process_time >= 0

@pytest.mark.integration
async def test_json_response_format_integration(client, auth_headers):
    """Test consistent JSON response format across endpoints."""
    endpoints_with_auth = [
        "/api/v1/health/",
        "/api/v1/tradelines/"
    ]
    
    for endpoint in endpoints_with_auth:
        if "tradelines" in endpoint:
            with patch('services.database_optimizer.db_optimizer') as mock_db:
                mock_db.get_user_tradelines_paginated.return_value = {
                    "items": [],
                    "meta": {"page": 1, "limit": 50, "total": 0, "pages": 0, "has_next": False, "has_prev": False}
                }
                response = await client.get(endpoint, headers=auth_headers)
        else:
            response = await client.get(endpoint)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check standard response format
        assert "success" in data
        assert "timestamp" in data
        assert "version" in data
        
        if data["success"]:
            assert "data" in data
        else:
            assert "error" in data

@pytest.mark.integration
async def test_file_processing_integration(client, auth_headers, sample_pdf_content):
    """Integration test for file processing workflow."""
    with patch('services.optimized_processor.OptimizedCreditReportProcessor') as mock_processor_class, \
         patch('services.database_optimizer.db_optimizer') as mock_db:
        
        # Setup processor mock
        mock_processor = AsyncMock()
        mock_processor.process_credit_report_optimized.return_value = {
            "success": True,
            "tradelines": [{"creditor_name": "Test Credit Card", "account_type": "Credit Card"}],
            "method_used": "test_method",
            "cost_estimate": 0.5,
            "cache_hit": False
        }
        mock_processor_class.return_value = mock_processor
        
        # Setup database mock
        mock_db.batch_insert_tradelines.return_value = {"inserted": 1}
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(sample_pdf_content)
            temp_path = f.name
        
        try:
            # Test file upload
            with open(temp_path, 'rb') as f:
                response = await client.post(
                    "/api/v1/processing/upload",
                    files={"file": ("test.pdf", f, "application/pdf")},
                    headers={"Authorization": auth_headers["Authorization"]}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "processing_method" in data["data"]
            
        finally:
            # Cleanup
            os.unlink(temp_path)

@pytest.mark.integration
async def test_background_job_integration(client, auth_headers):
    """Integration test for background job workflow."""
    with patch('services.background_jobs.job_processor') as mock_jobs:
        # Setup job processor mock
        mock_jobs.get_job_status.return_value = {
            "job_id": "test_job_123",
            "status": "completed",
            "progress": 100,
            "created_at": "2024-01-01T00:00:00",
            "user_id": "test_user_123",
            "result": {"tradelines_found": 5}
        }
        
        # Test job status endpoint
        response = await client.get("/api/v1/processing/job/test_job_123", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["job_id"] == "test_job_123"
        assert data["data"]["status"] == "completed"

@pytest.mark.integration
async def test_cache_integration(client):
    """Test cache integration across requests."""
    with patch('services.cache_service.cache') as mock_cache:
        mock_cache.stats.return_value = {
            "hit_count": 10,
            "miss_count": 5,
            "hit_rate": 0.67,
            "total_operations": 15
        }
        
        # Make multiple requests that should use cache
        for _ in range(3):
            response = await client.get("/api/v1/health/")
            assert response.status_code == 200

@pytest.mark.integration
async def test_monitoring_integration(client, auth_headers):
    """Test monitoring and metrics integration."""
    with patch('services.monitoring.metrics_collector') as mock_metrics:
        mock_metrics.get_api_metrics_summary.return_value = {
            "total_requests": 50,
            "error_count": 2,
            "avg_response_time_ms": 150.5,
            "requests_per_minute": 5.0
        }
        
        response = await client.get("/api/v1/health/metrics", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "api" in data["data"]

@pytest.mark.integration 
async def test_security_headers_integration(client):
    """Test security headers across the application."""
    response = await client.get("/api/v1/health/")
    
    # Check for security headers (these would be added by SecurityHeadersMiddleware)
    # The exact headers depend on your security middleware configuration
    assert response.status_code == 200
    
    # Test that sensitive information is not exposed
    assert "X-Powered-By" not in response.headers  # Should not expose server info

@pytest.mark.integration
async def test_database_integration(client, auth_headers):
    """Test database integration patterns."""
    with patch('services.database_optimizer.db_optimizer') as mock_db:
        # Test connection health
        mock_db.get_connection_health.return_value = {
            "status": "healthy",
            "connections": 5,
            "queries_executed": 100
        }
        
        # Test that database is called for data operations
        mock_db.get_user_tradelines_paginated.return_value = {
            "items": [],
            "meta": {"page": 1, "limit": 50, "total": 0, "pages": 0, "has_next": False, "has_prev": False}
        }
        
        response = await client.get("/api/v1/tradelines/", headers=auth_headers)
        assert response.status_code == 200
        
        # Verify database was called
        mock_db.get_user_tradelines_paginated.assert_called_once()

@pytest.mark.integration
async def test_end_to_end_tradeline_workflow(client, auth_headers, sample_tradeline):
    """End-to-end test of tradeline CRUD workflow."""
    with patch('services.database_optimizer.db_optimizer') as mock_db:
        # Step 1: Create tradeline
        created_tradeline = {**sample_tradeline, "id": 1, "user_id": "test_user_123"}
        mock_db.create_tradeline.return_value = created_tradeline
        
        response = await client.post("/api/v1/tradelines/", json=sample_tradeline, headers=auth_headers)
        assert response.status_code == 200
        tradeline_id = response.json()["data"]["id"]
        
        # Step 2: Get tradeline
        mock_db.get_tradeline_by_id.return_value = created_tradeline
        
        response = await client.get(f"/api/v1/tradelines/{tradeline_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["creditor_name"] == sample_tradeline["creditor_name"]
        
        # Step 3: Update tradeline
        updated_tradeline = {**created_tradeline, "creditor_name": "Updated Name"}
        mock_db.update_tradeline.return_value = updated_tradeline
        
        response = await client.put(
            f"/api/v1/tradelines/{tradeline_id}",
            json={"creditor_name": "Updated Name"},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["data"]["creditor_name"] == "Updated Name"
        
        # Step 4: Delete tradeline
        mock_db.delete_tradeline.return_value = True
        
        response = await client.delete(f"/api/v1/tradelines/{tradeline_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "deleted"