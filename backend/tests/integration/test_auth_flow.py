"""
Integration tests for authentication flow
Tests full authentication workflows with mocked Supabase
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))


# Mock Supabase client
def create_mock_user(id="user-123", email="test@example.com", metadata=None):
    """Create mock Supabase user."""
    user = MagicMock()
    user.id = id
    user.email = email
    user.user_metadata = metadata or {"first_name": "John", "last_name": "Doe"}
    return user


def create_mock_session(access_token="access-token", refresh_token="refresh-token", expires_in=3600):
    """Create mock Supabase session."""
    session = MagicMock()
    session.access_token = access_token
    session.refresh_token = refresh_token
    session.expires_in = expires_in
    return session


class TestRegistrationFlow:
    """Test user registration flow."""
    
    @patch('api.v1.routes.auth.supabase_client')
    def test_register_success(self, mock_supabase):
        """Test successful registration."""
        from fastapi.testclient import TestClient
        from api.v1.routes.auth import router
        from fastapi import FastAPI
        
        # Setup mock
        mock_user = create_mock_user(id="new-user-456")
        mock_response = MagicMock()
        mock_response.user = mock_user
        mock_supabase.auth.sign_up.return_value = mock_response
        
        # Create app
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # Make request
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecureP@ss123",
                "first_name": "Jane",
                "last_name": "Smith"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] == True
        assert data["data"]["user_id"] == "new-user-456"
        assert "message" in data["data"]
        mock_supabase.auth.sign_up.assert_called_once()
    
    @patch('api.v1.routes.auth.supabase_client')
    def test_register_duplicate_email(self, mock_supabase):
        """Test registration with duplicate email."""
        from fastapi.testclient import TestClient
        from api.v1.routes.auth import router
        from fastapi import FastAPI
        
        # Setup mock to raise error for duplicate email
        mock_supabase.auth.sign_up.side_effect = Exception("User already registered")
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.post(
            "/auth/register",
            json={
                "email": "existing@example.com",
                "password": "SecureP@ss123",
                "first_name": "John",
                "last_name": "Doe"
            }
        )
        
        assert response.status_code == 409
        data = response.json()
        assert data["success"] == False
    
    def test_register_invalid_password(self):
        """Test registration with invalid password."""
        from fastapi.testclient import TestClient
        from api.v1.routes.auth import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "weak",
                "first_name": "John",
                "last_name": "Doe"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_register_invalid_email(self):
        """Test registration with invalid email."""
        from fastapi.testclient import TestClient
        from api.v1.routes.auth import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecureP@ss123",
                "first_name": "John",
                "last_name": "Doe"
            }
        )
        
        assert response.status_code == 422  # Validation error


class TestLoginFlow:
    """Test user login flow."""
    
    @patch('api.v1.routes.auth.supabase_client')
    def test_login_success(self, mock_supabase):
        """Test successful login."""
        from fastapi.testclient import TestClient
        from api.v1.routes.auth import router
        from fastapi import FastAPI
        
        # Setup mock
        mock_user = create_mock_user(
            id="user-123",
            email="test@example.com",
            metadata={"first_name": "John", "last_name": "Doe"}
        )
        mock_session = create_mock_session(
            access_token="access-token-123",
            refresh_token="refresh-token-456"
        )
        
        mock_response = MagicMock()
        mock_response.user = mock_user
        mock_response.session = mock_session
        mock_supabase.auth.sign_in_with_password.return_value = mock_response
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "SecureP@ss123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["data"]["user"]["email"] == "test@example.com"
        assert data["data"]["tokens"]["access_token"] == "access-token-123"
    
    @patch('api.v1.routes.auth.supabase_client')
    def test_login_invalid_credentials(self, mock_supabase):
        """Test login with invalid credentials."""
        from fastapi.testclient import TestClient
        from api.v1.routes.auth import router
        from fastapi import FastAPI
        
        mock_supabase.auth.sign_in_with_password.side_effect = Exception("Invalid credentials")
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] == False
    
    @patch('api.v1.routes.auth.supabase_client')
    @patch('api.v1.routes.auth.check_rate_limit')
    def test_login_rate_limited(self, mock_rate_limit, mock_supabase):
        """Test login rate limiting."""
        from fastapi.testclient import TestClient
        from api.v1.routes.auth import router
        from fastapi import FastAPI
        
        mock_rate_limit.return_value = False
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "SecureP@ss123"
            }
        )
        
        assert response.status_code == 429
        data = response.json()
        assert data["success"] == False
        assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"


class TestLogoutFlow:
    """Test user logout flow."""
    
    @patch('api.v1.routes.auth.supabase_client')
    def test_logout_success(self, mock_supabase):
        """Test successful logout."""
        from fastapi.testclient import TestClient
        from api.v1.routes.auth import router
        from fastapi import FastAPI
        
        mock_supabase.auth.sign_out.return_value = None
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.post(
            "/auth/logout",
            json={
                "access_token": "test-access-token"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "message" in data["data"]
        mock_supabase.auth.sign_out.assert_called_once()


class TestPasswordResetFlow:
    """Test password reset flow."""
    
    @patch('api.v1.routes.auth.supabase_client')
    def test_password_reset_request_success(self, mock_supabase):
        """Test password reset request."""
        from fastapi.testclient import TestClient
        from api.v1.routes.auth import router
        from fastapi import FastAPI
        
        mock_supabase.auth.reset_password_email.return_value = None
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.post(
            "/auth/password-reset/request",
            json={
                "email": "test@example.com"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        # Should return generic message (don't reveal if email exists)
        assert "message" in data["data"]
    
    @patch('api.v1.routes.auth.supabase_client')
    @patch('api.v1.routes.auth.verify_supabase_jwt')
    def test_password_reset_confirm_success(self, mock_verify_jwt, mock_supabase):
        """Test password reset confirmation."""
        from fastapi.testclient import TestClient
        from api.v1.routes.auth import router
        from fastapi import FastAPI
        
        mock_verify_jwt.return_value = {"id": "user-123", "email": "test@example.com"}
        mock_supabase.auth.update_user.return_value = None
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.post(
            "/auth/password-reset/confirm",
            json={
                "new_password": "NewSecure@456",
                "access_token": "valid-token"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "message" in data["data"]


class TestTokenRefreshFlow:
    """Test token refresh flow."""
    
    @patch('api.v1.routes.auth.supabase_client')
    def test_refresh_token_success(self, mock_supabase):
        """Test successful token refresh."""
        from fastapi.testclient import TestClient
        from api.v1.routes.auth import router
        from fastapi import FastAPI
        
        mock_session = create_mock_session(
            access_token="new-access-token",
            refresh_token="new-refresh-token",
            expires_in=3600
        )
        
        mock_response = MagicMock()
        mock_response.session = mock_session
        mock_supabase.auth.refresh_session.return_value = mock_response
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.post(
            "/auth/refresh",
            json={
                "refresh_token": "old-refresh-token"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["data"]["access_token"] == "new-access-token"
        assert data["data"]["refresh_token"] == "new-refresh-token"
    
    @patch('api.v1.routes.auth.supabase_client')
    def test_refresh_token_invalid(self, mock_supabase):
        """Test refresh with invalid token."""
        from fastapi.testclient import TestClient
        from api.v1.routes.auth import router
        from fastapi import FastAPI
        
        mock_supabase.auth.refresh_session.side_effect = Exception("Invalid refresh token")
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.post(
            "/auth/refresh",
            json={
                "refresh_token": "invalid-token"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] == False


class TestAuthResponseFormat:
    """Test response format consistency."""
    
    @patch('api.v1.routes.auth.supabase_client')
    def test_response_includes_request_id(self, mock_supabase):
        """Test that all responses include request_id."""
        from fastapi.testclient import TestClient
        from api.v1.routes.auth import router
        from fastapi import FastAPI
        
        mock_user = create_mock_user()
        mock_session = create_mock_session()
        
        mock_response = MagicMock()
        mock_response.user = mock_user
        mock_response.session = mock_session
        mock_supabase.auth.sign_in_with_password.return_value = mock_response
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "SecureP@ss123"
            }
        )
        
        data = response.json()
        assert "request_id" in data
        assert data["request_id"] is not None
    
    @patch('api.v1.routes.auth.supabase_client')
    def test_response_includes_version(self, mock_supabase):
        """Test that all responses include version."""
        from fastapi.testclient import TestClient
        from api.v1.routes.auth import router
        from fastapi import FastAPI
        
        mock_user = create_mock_user()
        mock_session = create_mock_session()
        
        mock_response = MagicMock()
        mock_response.user = mock_user
        mock_response.session = mock_session
        mock_supabase.auth.sign_in_with_password.return_value = mock_response
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "SecureP@ss123"
            }
        )
        
        data = response.json()
        assert "version" in data
        assert data["version"] == "1.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
