"""
Unit tests for authentication routes
Tests validation, rate limiting, and response formats
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Test imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from fastapi.testclient import TestClient
from pydantic import ValidationError


class TestPasswordValidation:
    """Test password complexity validation."""
    
    def test_password_too_short(self):
        """Password must be at least 8 characters."""
        from api.v1.routes.auth import RegisterRequest
        
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com",
                password="Ab1!",
                first_name="John",
                last_name="Doe"
            )
        assert "at least 8 characters" in str(exc_info.value)
    
    def test_password_missing_uppercase(self):
        """Password must contain uppercase letter."""
        from api.v1.routes.auth import RegisterRequest
        
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com",
                password="abc123!@#",
                first_name="John",
                last_name="Doe"
            )
        assert "uppercase" in str(exc_info.value)
    
    def test_password_missing_lowercase(self):
        """Password must contain lowercase letter."""
        from api.v1.routes.auth import RegisterRequest
        
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com",
                password="ABC123!@#",
                first_name="John",
                last_name="Doe"
            )
        assert "lowercase" in str(exc_info.value)
    
    def test_password_missing_number(self):
        """Password must contain number."""
        from api.v1.routes.auth import RegisterRequest
        
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com",
                password="Abcdef!@#",
                first_name="John",
                last_name="Doe"
            )
        assert "number" in str(exc_info.value)
    
    def test_password_missing_special_char(self):
        """Password must contain special character."""
        from api.v1.routes.auth import RegisterRequest
        
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com",
                password="Abcdef123",
                first_name="John",
                last_name="Doe"
            )
        assert "special character" in str(exc_info.value)
    
    def test_valid_password(self):
        """Valid password should pass validation."""
        from api.v1.routes.auth import RegisterRequest
        
        request = RegisterRequest(
            email="test@example.com",
            password="SecureP@ss123",
            first_name="John",
            last_name="Doe"
        )
        assert request.email == "test@example.com"
        assert request.password == "SecureP@ss123"


class TestLoginRequestValidation:
    """Test login request validation."""
    
    def test_valid_login_request(self):
        """Valid login request should pass."""
        from api.v1.routes.auth import LoginRequest
        
        request = LoginRequest(
            email="user@example.com",
            password="password123"
        )
        assert request.email == "user@example.com"
        assert request.password == "password123"
    
    def test_invalid_email(self):
        """Invalid email should fail validation."""
        from api.v1.routes.auth import LoginRequest
        
        with pytest.raises(ValidationError):
            LoginRequest(
                email="not-an-email",
                password="password123"
            )


class TestPasswordResetValidation:
    """Test password reset request validation."""
    
    def test_valid_password_reset_confirm(self):
        """Valid password reset confirm should pass."""
        from api.v1.routes.auth import PasswordResetConfirmRequest
        
        request = PasswordResetConfirmRequest(
            new_password="NewSecure@123",
            access_token="test-token"
        )
        assert request.new_password == "NewSecure@123"
    
    def test_password_reset_confirm_too_short(self):
        """Password reset confirm with short password should fail."""
        from api.v1.routes.auth import PasswordResetConfirmRequest
        
        with pytest.raises(ValidationError):
            PasswordResetConfirmRequest(
                new_password="Short1!",
                access_token="test-token"
            )


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_check_rate_limit_allows_first_requests(self):
        """First requests should be allowed."""
        from api.v1.routes.auth import check_rate_limit, rate_limit_store
        
        # Clean up
        rate_limit_store.clear()
        
        # First 10 requests should be allowed
        for i in range(10):
            assert check_rate_limit("test_ip", max_attempts=10, window_seconds=60) == True
    
    def test_check_rate_limit_blocks_after_limit(self):
        """Requests should be blocked after rate limit exceeded."""
        from api.v1.routes.auth import check_rate_limit, rate_limit_store
        
        # Clean up
        rate_limit_store.clear()
        
        # Fill up the rate limit
        for i in range(10):
            check_rate_limit("test_ip", max_attempts=10, window_seconds=60)
        
        # 11th request should be blocked
        assert check_rate_limit("test_ip", max_attempts=10, window_seconds=60) == False
    
    def test_get_rate_limit_retry_after(self):
        """Retry after should return correct value."""
        from api.v1.routes.auth import get_rate_limit_retry_after, rate_limit_store
        
        # Clean up
        rate_limit_store.clear()
        
        rate_limit_store["test_ip"] = [datetime.now()]
        
        retry_after = get_rate_limit_retry_after("test_ip", window_seconds=60)
        assert retry_after >= 0


class TestResponseFormatting:
    """Test response formatting functions."""
    
    def test_create_success_response(self):
        """Success response should have correct structure."""
        from api.v1.routes.auth import create_success_response
        
        response = create_success_response(
            data={"user_id": "123"},
            message="Success",
            request_id="test-123"
        )
        
        assert response["success"] == True
        assert response["data"]["user_id"] == "123"
        assert response["error"] == None
        assert response["request_id"] == "test-123"
    
    def test_create_error_response(self):
        """Error response should have correct structure."""
        from api.v1.routes.auth import create_error_response
        from core.exceptions import AuthenticationError
        
        exc = AuthenticationError("Invalid credentials")
        response = create_error_response(exc, request_id="test-456")
        
        assert response["success"] == False
        assert response["data"] == None
        assert response["error"]["code"] == "AUTHENTICATION_ERROR"
        assert response["error"]["message"] == "Invalid credentials"
        assert response["request_id"] == "test-456"
    
    def test_generate_request_id(self):
        """Request ID should be generated and unique."""
        from api.v1.routes.auth import generate_request_id
        
        id1 = generate_request_id()
        id2 = generate_request_id()
        
        assert id1 != id2
        assert len(id1) == 8  # UUID truncated to 8 chars


class TestUserResponse:
    """Test user response model."""
    
    def test_user_response_model(self):
        """User response should have correct structure."""
        from api.v1.routes.auth import UserResponse
        
        user = UserResponse(
            id="user-123",
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            created_at="2025-01-01T00:00:00Z"
        )
        
        assert user.id == "user-123"
        assert user.email == "test@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"


class TestAuthTokensResponse:
    """Test auth tokens response model."""
    
    def test_auth_tokens_response_model(self):
        """Auth tokens response should have correct structure."""
        from api.v1.routes.auth import AuthTokensResponse
        
        tokens = AuthTokensResponse(
            access_token="access-token-123",
            refresh_token="refresh-token-456",
            token_type="bearer",
            expires_in=3600
        )
        
        assert tokens.access_token == "access-token-123"
        assert tokens.refresh_token == "refresh-token-456"
        assert tokens.token_type == "bearer"
        assert tokens.expires_in == 3600


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
