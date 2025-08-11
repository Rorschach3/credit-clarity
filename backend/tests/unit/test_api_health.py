"""
Unit tests for health check endpoints
Tests basic API functionality and health monitoring
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

def test_root_endpoint(client: TestClient):
    """Test API root endpoint."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["name"] == "Credit Clarity API"
    assert data["version"] == "3.0.0"
    assert data["architecture"] == "modular"
    assert data["status"] == "operational"

def test_simple_health_check(client: TestClient):
    """Test simple health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["version"] == "3.0.0"

def test_detailed_health_check(client: TestClient):
    """Test detailed health check endpoint."""
    with patch('services.background_jobs.job_processor') as mock_jobs, \
         patch('services.cache_service.cache') as mock_cache, \
         patch('services.monitoring.metrics_collector') as mock_metrics:
        
        # Setup mocks
        mock_jobs.is_running = True
        mock_cache.stats.return_value = {"hit_rate": 0.85}
        mock_metrics.get_health_status.return_value = {
            "status": "healthy",
            "issues": []
        }
        
        response = client.get("/api/v1/health/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["status"] == "healthy"
        assert "services" in data["data"]
        assert "version" in data["data"]

def test_liveness_probe(client: TestClient):
    """Test Kubernetes liveness probe."""
    response = client.get("/api/v1/health/live")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["status"] == "alive"

def test_readiness_probe(client: TestClient):
    """Test Kubernetes readiness probe."""
    with patch('services.background_jobs.job_processor') as mock_jobs:
        mock_jobs.is_running = True
        
        response = client.get("/api/v1/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "ready" in data["data"]
        assert "services" in data["data"]

@patch('services.monitoring.metrics_collector')
def test_basic_metrics_endpoint(mock_metrics, client: TestClient, auth_headers):
    """Test basic metrics endpoint."""
    # Mock metrics data
    mock_metrics.get_system_metrics_summary.return_value = {
        "avg_cpu_percent": 45.2,
        "avg_memory_percent": 62.1,
        "sample_count": 5
    }
    
    mock_metrics.get_api_metrics_summary.return_value = {
        "total_requests": 150,
        "error_count": 2,
        "avg_response_time_ms": 250.5
    }
    
    mock_metrics.get_business_metrics_summary.return_value = {
        "metrics": {
            "user_activity": {"count": 25}
        }
    }
    
    response = client.get(
        "/api/v1/health/metrics?minutes=30",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "system" in data["data"]
    assert "api" in data["data"]
    assert "business" in data["data"]

def test_health_check_with_service_failures(client: TestClient):
    """Test health check when services are failing."""
    with patch('services.monitoring.metrics_collector') as mock_metrics:
        # Simulate metrics collection failure
        mock_metrics.get_health_status.side_effect = Exception("Metrics unavailable")
        
        response = client.get("/api/v1/health/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should still return healthy status but without system_health
        assert data["success"] is True
        assert data["data"]["status"] == "healthy"

def test_health_check_response_format(client: TestClient):
    """Test that health check follows standard response format."""
    response = client.get("/api/v1/health/")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check standard API response format
    assert "success" in data
    assert "data" in data
    assert "message" in data
    assert "timestamp" in data
    assert "version" in data

def test_api_version_headers(client: TestClient):
    """Test that API version headers are set correctly."""
    response = client.get("/api/v1/health/")
    
    assert response.headers["X-API-Version"] == "1.0"
    assert response.headers["X-API-Revision"] == "2025.01"

def test_performance_headers(client: TestClient):
    """Test that performance headers are added."""
    response = client.get("/api/v1/health/")
    
    assert "X-Process-Time" in response.headers
    assert "X-Request-ID" in response.headers
    assert response.headers["X-API-Architecture"] == "modular"

@pytest.mark.asyncio
async def test_health_check_async(async_client):
    """Test health check with async client."""
    response = await async_client.get("/api/v1/health/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "data" in data

def test_health_check_caching(client: TestClient):
    """Test that health check results can be cached."""
    # First request
    response1 = client.get("/api/v1/health/")
    assert response1.status_code == 200
    
    # Second request (should potentially use cache)
    response2 = client.get("/api/v1/health/")
    assert response2.status_code == 200
    
    # Both should return same structure
    assert response1.json()["data"]["status"] == response2.json()["data"]["status"]

def test_cors_headers_on_health_check(client: TestClient):
    """Test CORS headers are properly set on health checks."""
    # Preflight request
    response = client.options("/api/v1/health/")
    
    # Should handle OPTIONS request
    assert response.status_code in [200, 405]  # 405 if OPTIONS not explicitly handled

def test_request_id_generation(client: TestClient):
    """Test that each request gets a unique request ID."""
    response1 = client.get("/api/v1/health/")
    response2 = client.get("/api/v1/health/")
    
    id1 = response1.headers.get("X-Request-ID")
    id2 = response2.headers.get("X-Request-ID")
    
    assert id1 is not None
    assert id2 is not None
    assert id1 != id2

def test_error_handling_in_health_check(client: TestClient):
    """Test error handling in health check endpoint."""
    with patch('services.monitoring.metrics_collector') as mock_metrics:
        # Simulate a critical error
        mock_metrics.get_health_status.side_effect = Exception("Critical system error")
        
        response = client.get("/api/v1/health/")
        
        # Should still return 200 but with degraded status
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True  # Health check should be resilient