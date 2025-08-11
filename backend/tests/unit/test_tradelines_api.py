"""
Unit tests for tradelines API endpoints
Tests CRUD operations and business logic
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

def test_get_user_tradelines_success(client: TestClient, auth_headers, sample_tradelines):
    """Test successful retrieval of user tradelines."""
    with patch('services.database_optimizer.db_optimizer') as mock_db:
        # Mock database response
        mock_db.get_user_tradelines_paginated.return_value = {
            "items": sample_tradelines,
            "meta": {
                "page": 1,
                "limit": 50,
                "total": len(sample_tradelines),
                "pages": 1,
                "has_next": False,
                "has_prev": False
            }
        }
        
        response = client.get("/api/v1/tradelines/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert len(data["data"]) == len(sample_tradelines)
        assert "meta" in data
        assert data["meta"]["total"] == len(sample_tradelines)

def test_get_user_tradelines_with_pagination(client: TestClient, auth_headers):
    """Test tradelines retrieval with pagination parameters."""
    with patch('services.database_optimizer.db_optimizer') as mock_db:
        mock_db.get_user_tradelines_paginated.return_value = {
            "items": [],
            "meta": {
                "page": 2,
                "limit": 10,
                "total": 15,
                "pages": 2,
                "has_next": False,
                "has_prev": True
            }
        }
        
        response = client.get(
            "/api/v1/tradelines/?page=2&limit=10&sort_by=created_at&sort_order=desc",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["meta"]["page"] == 2
        assert data["meta"]["limit"] == 10

def test_get_user_tradelines_with_filters(client: TestClient, auth_headers):
    """Test tradelines retrieval with filters."""
    with patch('services.database_optimizer.db_optimizer') as mock_db:
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
        
        response = client.get(
            "/api/v1/tradelines/?credit_bureau=Experian&is_negative=true&disputed=false",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify filters were passed to database
        mock_db.get_user_tradelines_paginated.assert_called_once()
        call_args = mock_db.get_user_tradelines_paginated.call_args
        filters = call_args.kwargs['filters']
        
        assert filters['credit_bureau'] == 'Experian'
        assert filters['is_negative'] is True

def test_get_single_tradeline_success(client: TestClient, auth_headers, sample_tradeline):
    """Test successful retrieval of a single tradeline."""
    with patch('services.database_optimizer.db_optimizer') as mock_db:
        mock_db.get_tradeline_by_id.return_value = {
            **sample_tradeline,
            "id": 1,
            "user_id": "test_user_123",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": None
        }
        
        response = client.get("/api/v1/tradelines/1", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["id"] == 1
        assert data["data"]["creditor_name"] == sample_tradeline["creditor_name"]

def test_get_single_tradeline_not_found(client: TestClient, auth_headers):
    """Test retrieval of non-existent tradeline."""
    with patch('services.database_optimizer.db_optimizer') as mock_db:
        mock_db.get_tradeline_by_id.return_value = None
        
        response = client.get("/api/v1/tradelines/999", headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        
        assert data["success"] is False
        assert "error" in data

def test_create_tradeline_success(client: TestClient, auth_headers, sample_tradeline):
    """Test successful tradeline creation."""
    with patch('services.database_optimizer.db_optimizer') as mock_db:
        created_tradeline = {
            **sample_tradeline,
            "id": 1,
            "user_id": "test_user_123",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": None
        }
        mock_db.create_tradeline.return_value = created_tradeline
        
        response = client.post(
            "/api/v1/tradelines/",
            json=sample_tradeline,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["id"] == 1
        assert data["data"]["creditor_name"] == sample_tradeline["creditor_name"]
        assert "created_at" in data["data"]

def test_create_tradeline_validation_error(client: TestClient, auth_headers):
    """Test tradeline creation with invalid data."""
    invalid_data = {
        "creditor_name": "",  # Required field empty
        "account_type": "Invalid Type"
    }
    
    response = client.post(
        "/api/v1/tradelines/",
        json=invalid_data,
        headers=auth_headers
    )
    
    assert response.status_code == 422
    data = response.json()
    
    assert data["success"] is False
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"

def test_update_tradeline_success(client: TestClient, auth_headers, sample_tradeline):
    """Test successful tradeline update."""
    with patch('services.database_optimizer.db_optimizer') as mock_db:
        # Mock existing tradeline
        existing_tradeline = {
            **sample_tradeline,
            "id": 1,
            "user_id": "test_user_123"
        }
        mock_db.get_tradeline_by_id.return_value = existing_tradeline
        
        # Mock updated tradeline
        updated_tradeline = {
            **existing_tradeline,
            "creditor_name": "Updated Credit Card",
            "updated_at": "2024-01-02T00:00:00"
        }
        mock_db.update_tradeline.return_value = updated_tradeline
        
        update_data = {"creditor_name": "Updated Credit Card"}
        
        response = client.put(
            "/api/v1/tradelines/1",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["creditor_name"] == "Updated Credit Card"
        assert "updated_at" in data["data"]

def test_update_tradeline_not_found(client: TestClient, auth_headers):
    """Test updating non-existent tradeline."""
    with patch('services.database_optimizer.db_optimizer') as mock_db:
        mock_db.get_tradeline_by_id.return_value = None
        
        update_data = {"creditor_name": "Updated Name"}
        
        response = client.put(
            "/api/v1/tradelines/999",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
        data = response.json()
        
        assert data["success"] is False

def test_update_tradeline_no_data(client: TestClient, auth_headers, sample_tradeline):
    """Test update with no data provided."""
    with patch('services.database_optimizer.db_optimizer') as mock_db:
        mock_db.get_tradeline_by_id.return_value = {
            **sample_tradeline,
            "id": 1,
            "user_id": "test_user_123"
        }
        
        response = client.put(
            "/api/v1/tradelines/1",
            json={},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.json()
        
        assert data["success"] is False
        assert "No update data provided" in data["error"]["message"]

def test_delete_tradeline_success(client: TestClient, auth_headers, sample_tradeline):
    """Test successful tradeline deletion."""
    with patch('services.database_optimizer.db_optimizer') as mock_db:
        mock_db.get_tradeline_by_id.return_value = {
            **sample_tradeline,
            "id": 1,
            "user_id": "test_user_123"
        }
        mock_db.delete_tradeline.return_value = True
        
        response = client.delete("/api/v1/tradelines/1", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["id"] == "1"
        assert data["data"]["status"] == "deleted"

def test_delete_tradeline_not_found(client: TestClient, auth_headers):
    """Test deleting non-existent tradeline."""
    with patch('services.database_optimizer.db_optimizer') as mock_db:
        mock_db.get_tradeline_by_id.return_value = None
        
        response = client.delete("/api/v1/tradelines/999", headers=auth_headers)
        
        assert response.status_code == 404

def test_get_tradelines_stats(client: TestClient, auth_headers):
    """Test tradelines statistics endpoint."""
    with patch('services.database_optimizer.db_optimizer') as mock_db:
        mock_stats = {
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
            }
        }
        mock_db.get_tradelines_statistics.return_value = mock_stats
        
        response = client.get("/api/v1/tradelines/stats/summary", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["total_tradelines"] == 10
        assert data["data"]["positive_tradelines"] == 7
        assert "by_credit_bureau" in data["data"]

def test_bulk_tradeline_update(client: TestClient, auth_headers, sample_tradelines):
    """Test bulk update operation."""
    with patch('services.database_optimizer.db_optimizer') as mock_db:
        # Mock existing tradelines
        for i, tradeline in enumerate(sample_tradelines, 1):
            tradeline_with_id = {**tradeline, "id": i, "user_id": "test_user_123"}
            mock_db.get_tradeline_by_id.return_value = tradeline_with_id
        
        mock_db.bulk_update_tradelines.return_value = {"affected_count": 2}
        
        bulk_operation = {
            "operation": "update",
            "tradeline_ids": [1, 2],
            "update_data": {"dispute_count": 1},
            "batch_size": 50
        }
        
        response = client.post(
            "/api/v1/tradelines/bulk",
            json=bulk_operation,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["operation"] == "update"
        assert data["data"]["affected_count"] == 2

def test_bulk_tradeline_delete(client: TestClient, auth_headers, sample_tradelines):
    """Test bulk delete operation."""
    with patch('services.database_optimizer.db_optimizer') as mock_db:
        # Mock existing tradelines
        for i, tradeline in enumerate(sample_tradelines, 1):
            tradeline_with_id = {**tradeline, "id": i, "user_id": "test_user_123"}
            mock_db.get_tradeline_by_id.return_value = tradeline_with_id
        
        mock_db.bulk_delete_tradelines.return_value = {"affected_count": 2}
        
        bulk_operation = {
            "operation": "delete",
            "tradeline_ids": [1, 2],
            "batch_size": 50
        }
        
        response = client.post(
            "/api/v1/tradelines/bulk",
            json=bulk_operation,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["operation"] == "delete"

def test_bulk_tradeline_dispute(client: TestClient, auth_headers, sample_tradelines):
    """Test bulk dispute operation."""
    with patch('services.database_optimizer.db_optimizer') as mock_db:
        # Mock existing tradelines
        for i, tradeline in enumerate(sample_tradelines, 1):
            tradeline_with_id = {**tradeline, "id": i, "user_id": "test_user_123"}
            mock_db.get_tradeline_by_id.return_value = tradeline_with_id
        
        mock_db.bulk_update_tradelines.return_value = {"affected_count": 3}
        
        bulk_operation = {
            "operation": "dispute",
            "tradeline_ids": [1, 2, 3],
            "batch_size": 50
        }
        
        response = client.post(
            "/api/v1/tradelines/bulk",
            json=bulk_operation,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["operation"] == "dispute"
        assert data["data"]["affected_count"] == 3

def test_unauthorized_access(client: TestClient):
    """Test endpoints without authentication."""
    endpoints = [
        "/api/v1/tradelines/",
        "/api/v1/tradelines/1",
        "/api/v1/tradelines/stats/summary"
    ]
    
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 403  # Unauthorized

def test_user_isolation(client: TestClient, auth_headers):
    """Test that users can only access their own tradelines."""
    with patch('services.database_optimizer.db_optimizer') as mock_db:
        # Mock tradeline belonging to different user
        mock_db.get_tradeline_by_id.return_value = {
            "id": 1,
            "user_id": "different_user_123",
            "creditor_name": "Test"
        }
        
        response = client.get("/api/v1/tradelines/1", headers=auth_headers)
        
        # Should verify user ownership in the database call
        mock_db.get_tradeline_by_id.assert_called_with(1, "test_user_123")

@pytest.mark.asyncio
async def test_tradelines_async_operations(async_client, auth_headers):
    """Test tradelines endpoints with async client."""
    with patch('services.database_optimizer.db_optimizer') as mock_db:
        mock_db.get_user_tradelines_paginated.return_value = {
            "items": [],
            "meta": {
                "page": 1, "limit": 50, "total": 0, "pages": 0,
                "has_next": False, "has_prev": False
            }
        }
        
        response = await async_client.get("/api/v1/tradelines/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True