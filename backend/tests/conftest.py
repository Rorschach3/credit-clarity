"""
Pytest configuration and shared fixtures
Test setup, database fixtures, and mocking utilities
"""
import asyncio
import os
import tempfile
from typing import AsyncGenerator, Generator, Dict, Any
from unittest.mock import Mock, AsyncMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Set testing environment
os.environ["ENVIRONMENT"] = "testing"

from main_modular import app
from core.config import get_settings
from core.logging.logger import get_logger
from services.cache_service import cache
from services.database_optimizer import db_optimizer

logger = get_logger(__name__)

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def settings():
    """Get test settings."""
    return get_settings()

@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create test client for synchronous tests."""
    with TestClient(app) as test_client:
        yield test_client

@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client for asynchronous tests."""
    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client

@pytest.fixture
def mock_user() -> Dict[str, Any]:
    """Mock user data for authentication tests."""
    return {
        "id": "test_user_123",
        "email": "test@example.com",
        "role": "user",
        "name": "Test User"
    }

@pytest.fixture
def mock_admin_user() -> Dict[str, Any]:
    """Mock admin user data."""
    return {
        "id": "admin_123",
        "email": "admin@creditclarity.com",
        "role": "admin",
        "name": "Admin User"
    }

@pytest.fixture
def auth_headers(mock_user) -> Dict[str, str]:
    """Mock authentication headers."""
    return {
        "Authorization": "Bearer mock_jwt_token",
        "Content-Type": "application/json"
    }

@pytest.fixture
def admin_auth_headers(mock_admin_user) -> Dict[str, str]:
    """Mock admin authentication headers."""
    return {
        "Authorization": "Bearer mock_admin_jwt_token",
        "Content-Type": "application/json"
    }

@pytest.fixture
def sample_tradeline() -> Dict[str, Any]:
    """Sample tradeline data for tests."""
    return {
        "creditor_name": "Test Credit Card",
        "account_number": "****1234",
        "account_type": "Credit Card",
        "account_status": "Open",
        "account_balance": "$1,500",
        "credit_limit": "$5,000",
        "monthly_payment": "$50",
        "date_opened": "2020-01-01",
        "credit_bureau": "Experian",
        "is_negative": False,
        "dispute_count": 0
    }

@pytest.fixture
def sample_tradelines() -> list[Dict[str, Any]]:
    """Multiple sample tradelines for testing."""
    return [
        {
            "creditor_name": "Test Credit Card 1",
            "account_type": "Credit Card",
            "account_status": "Open",
            "credit_bureau": "Experian",
            "is_negative": False,
            "dispute_count": 0
        },
        {
            "creditor_name": "Test Loan",
            "account_type": "Auto Loan", 
            "account_status": "Closed",
            "credit_bureau": "Equifax",
            "is_negative": True,
            "dispute_count": 1
        },
        {
            "creditor_name": "Test Mortgage",
            "account_type": "Mortgage",
            "account_status": "Open",
            "credit_bureau": "TransUnion",
            "is_negative": False,
            "dispute_count": 0
        }
    ]

@pytest.fixture
def sample_pdf_content() -> bytes:
    """Sample PDF content for testing."""
    # Minimal PDF structure for testing
    return b"""%PDF-1.4
1 0 obj
<< /Type /Pages /Kids [2 0 R] /Count 1 >>
endobj
2 0 obj
<< /Type /Page /Parent 1 0 R /MediaBox [0 0 612 792]
   /Contents 3 0 R /Resources << /Font << /F1 4 0 R >> >>
>>
endobj
3 0 obj
<< /Length 55 >>
stream
BT
/F1 12 Tf
100 700 Td
(Test Credit Report) Tj
ET
endstream
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000178 00000 n 
0000000284 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
355
%%EOF"""

@pytest.fixture
def temp_pdf_file(sample_pdf_content) -> Generator[str, None, None]:
    """Create temporary PDF file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(sample_pdf_content)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except FileNotFoundError:
        pass

@pytest_asyncio.fixture
async def mock_cache():
    """Mock cache service for testing."""
    mock_cache = AsyncMock()
    mock_cache.get.return_value = None
    mock_cache.set.return_value = True
    mock_cache.delete.return_value = True
    mock_cache.clear.return_value = True
    mock_cache.stats.return_value = {
        "hit_count": 0,
        "miss_count": 0,
        "hit_rate": 0.0
    }
    return mock_cache

@pytest_asyncio.fixture
async def mock_db():
    """Mock database for testing."""
    mock_db = AsyncMock()
    
    # Mock common database operations
    mock_db.get_user_tradelines_paginated.return_value = {
        "items": [],
        "meta": {
            "page": 1,
            "limit": 50,
            "total": 0,
            "pages": 0,
            "has_next": False,
            "has_prev": False
        }
    }
    
    mock_db.create_tradeline.return_value = {"id": 1, "created_at": "2024-01-01T00:00:00"}
    mock_db.get_tradeline_by_id.return_value = None
    mock_db.update_tradeline.return_value = {"id": 1, "updated_at": "2024-01-01T00:00:00"}
    mock_db.delete_tradeline.return_value = True
    mock_db.batch_insert_tradelines.return_value = {"inserted": 0}
    
    return mock_db

@pytest.fixture
def mock_processor():
    """Mock PDF processor for testing."""
    mock_proc = AsyncMock()
    mock_proc.process_credit_report_optimized.return_value = {
        "success": True,
        "tradelines": [],
        "method_used": "mock",
        "cost_estimate": 0.0,
        "cache_hit": False
    }
    return mock_proc

@pytest.fixture
def mock_job_processor():
    """Mock background job processor."""
    mock_jobs = AsyncMock()
    mock_jobs.is_running = True
    mock_jobs.submit_job.return_value = "job_123"
    mock_jobs.get_job_status.return_value = {
        "job_id": "job_123",
        "status": "pending",
        "progress": 0,
        "created_at": "2024-01-01T00:00:00",
        "user_id": "test_user_123"
    }
    mock_jobs.get_stats.return_value = {
        "pending_jobs": 0,
        "completed_jobs": 0,
        "failed_jobs": 0
    }
    return mock_jobs

@pytest_asyncio.fixture
async def setup_test_database():
    """Setup test database if needed."""
    # In a real application, you might set up a test database here
    # For now, we'll use mocks
    yield
    # Cleanup would go here

@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks before each test."""
    # This runs before each test to ensure clean state
    yield
    # Reset any global mocks if needed

# Mock security dependencies for testing
@pytest.fixture
def mock_auth_dependency(mock_user):
    """Mock authentication dependency."""
    async def mock_get_user():
        return mock_user
    return mock_get_user

@pytest.fixture
def mock_admin_dependency(mock_admin_user):
    """Mock admin authentication dependency."""
    async def mock_get_admin():
        return mock_admin_user
    return mock_get_admin

# Performance test fixtures
@pytest.fixture
def performance_threshold():
    """Performance thresholds for testing."""
    return {
        "api_response_time_ms": 1000,
        "database_query_time_ms": 500,
        "cache_operation_time_ms": 100
    }

# Error testing fixtures
@pytest.fixture
def mock_external_service_error():
    """Mock external service errors."""
    return Exception("External service unavailable")

@pytest.fixture
def mock_database_error():
    """Mock database errors."""
    return Exception("Database connection failed")

# Utility functions for tests
def assert_response_structure(response_data: dict):
    """Assert standard API response structure."""
    assert "success" in response_data
    assert "data" in response_data or "error" in response_data
    assert "timestamp" in response_data
    assert "version" in response_data

def assert_error_response_structure(response_data: dict):
    """Assert error response structure."""
    assert response_data["success"] is False
    assert "error" in response_data
    assert "code" in response_data["error"]
    assert "message" in response_data["error"]

def assert_pagination_structure(response_data: dict):
    """Assert paginated response structure."""
    assert "data" in response_data
    assert "meta" in response_data
    assert "page" in response_data["meta"]
    assert "limit" in response_data["meta"] 
    assert "total" in response_data["meta"]
    assert "pages" in response_data["meta"]

# Test data generators
def generate_test_tradelines(count: int = 5) -> list[Dict[str, Any]]:
    """Generate test tradeline data."""
    tradelines = []
    for i in range(count):
        tradelines.append({
            "creditor_name": f"Test Creditor {i+1}",
            "account_type": "Credit Card",
            "account_status": "Open",
            "credit_bureau": ["Experian", "Equifax", "TransUnion"][i % 3],
            "is_negative": i % 3 == 0,  # Every third is negative
            "dispute_count": i % 2  # Alternating dispute count
        })
    return tradelines