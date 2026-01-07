"""
Unit tests for error envelope formatting.
Tests ResponseFormatter and error response generation.
"""
import pytest
from datetime import datetime

from core.response import (
    ResponseFormatter,
    success_response,
    error_response,
    paginated_response,
    ErrorDetail,
    ErrorEnvelope,
    SuccessEnvelope,
)
from core.exceptions import (
    CreditClarityException,
    ValidationError,
    AuthenticationError,
    NotFoundError,
    ProcessingError,
    RateLimitExceededError,
)


class TestResponseFormatter:
    """Tests for ResponseFormatter class."""

    def test_generate_request_id(self):
        """Test request ID generation."""
        req_id = ResponseFormatter.generate_request_id()
        assert req_id.startswith("req-")
        assert len(req_id) == 12  # "req-" + 8 hex chars

    def test_generate_request_id_unique(self):
        """Test that request IDs are unique."""
        ids = [ResponseFormatter.generate_request_id() for _ in range(100)]
        assert len(ids) == len(set(ids))  # All unique

    def test_success_response_with_data(self):
        """Test success response with data."""
        data = {"key": "value"}
        response = ResponseFormatter.success_response(data=data)

        assert response["success"] is True
        assert response["data"] == data
        assert response["error"] is None
        assert response["request_id"].startswith("req-")

    def test_success_response_without_data(self):
        """Test success response without data."""
        response = ResponseFormatter.success_response()

        assert response["success"] is True
        assert response["data"] is None
        assert response["error"] is None
        assert response["request_id"].startswith("req-")

    def test_success_response_with_custom_request_id(self):
        """Test success response with custom request ID."""
        response = ResponseFormatter.success_response(request_id="custom-req-id")

        assert response["request_id"] == "custom-req-id"

    def test_error_response(self):
        """Test error response generation."""
        response = ResponseFormatter.error_response(
            code="AUTH_INVALID_CREDENTIALS",
            message="Invalid email or password",
            field="password"
        )

        assert response["success"] is False
        assert response["error"]["code"] == "AUTH_INVALID_CREDENTIALS"
        assert response["error"]["message"] == "Invalid email or password"
        assert response["error"]["field"] == "password"
        assert response["data"] is None
        assert response["request_id"].startswith("req-")

    def test_error_response_with_details(self):
        """Test error response with additional details."""
        details = {"min_length": 8, "required_chars": ["uppercase", "number"]}
        response = ResponseFormatter.error_response(
            code="PASSWORD_WEAK",
            message="Password does not meet requirements",
            details=details
        )

        assert response["error"]["details"] == details

    def test_paginated_response(self):
        """Test paginated response generation."""
        data = [{"id": 1}, {"id": 2}]
        response = ResponseFormatter.paginated_response(
            data=data,
            total=100,
            page=2,
            per_page=10
        )

        assert response["success"] is True
        assert response["data"] == data
        assert response["pagination"]["total"] == 100
        assert response["pagination"]["page"] == 2
        assert response["pagination"]["per_page"] == 10
        assert response["pagination"]["total_pages"] == 10
        assert response["pagination"]["has_next"] is True
        assert response["pagination"]["has_prev"] is True

    def test_paginated_response_last_page(self):
        """Test paginated response on last page."""
        data = [{"id": 91}]
        response = ResponseFormatter.paginated_response(
            data=data,
            total=100,
            page=10,
            per_page=10
        )

        assert response["pagination"]["has_next"] is False
        assert response["pagination"]["has_prev"] is True

    def test_paginated_response_first_page(self):
        """Test paginated response on first page."""
        data = [{"id": 1}]
        response = ResponseFormatter.paginated_response(
            data=data,
            total=100,
            page=1,
            per_page=10
        )

        assert response["pagination"]["has_next"] is True
        assert response["pagination"]["has_prev"] is False

    def test_from_exception_credit_clarity(self):
        """Test error response from CreditClarityException."""
        exc = ValidationError("Invalid email format", field="email")
        response = ResponseFormatter.from_exception(exc)

        assert response["success"] is False
        assert response["error"]["code"] == "VALIDATION_ERROR"
        assert response["error"]["message"] == "Invalid email format"
        assert response["error"]["field"] == "email"

    def test_from_exception_generic(self):
        """Test error response from generic Exception."""
        exc = ValueError("Some value error")
        response = ResponseFormatter.from_exception(exc)

        assert response["success"] is False
        assert response["error"]["code"] == "INTERNAL_ERROR"
        assert response["error"]["message"] == "Some value error"


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_success_response_function(self):
        """Test success_response convenience function."""
        response = success_response(data={"status": "ok"})
        assert response["success"] is True
        assert response["data"] == {"status": "ok"}

    def test_error_response_function(self):
        """Test error_response convenience function."""
        response = error_response(
            code="TEST_ERROR",
            message="Test error message",
            field="test_field"
        )
        assert response["success"] is False
        assert response["error"]["code"] == "TEST_ERROR"
        assert response["error"]["field"] == "test_field"

    def test_paginated_response_function(self):
        """Test paginated_response convenience function."""
        data = [{"id": 1}]
        response = paginated_response(data=data, total=50, page=1, per_page=10)
        assert response["success"] is True
        assert response["pagination"]["total"] == 50


class TestErrorEnvelopeModel:
    """Tests for Pydantic models."""

    def test_error_detail_model(self):
        """Test ErrorDetail model."""
        error = ErrorDetail(
            code="TEST_CODE",
            message="Test message",
            field="test_field",
            details={"key": "value"}
        )

        assert error.code == "TEST_CODE"
        assert error.message == "Test message"
        assert error.field == "test_field"
        assert error.details == {"key": "value"}

    def test_error_detail_optional_field(self):
        """Test ErrorDetail with optional field."""
        error = ErrorDetail(code="CODE", message="Message")

        assert error.field is None
        assert error.details is None

    def test_error_envelope_model(self):
        """Test ErrorEnvelope model."""
        envelope = ErrorEnvelope(
            error=ErrorDetail(code="CODE", message="Message"),
            request_id="req-123"
        )

        assert envelope.success is False
        assert envelope.error.code == "CODE"
        assert envelope.request_id == "req-123"

    def test_success_envelope_model(self):
        """Test SuccessEnvelope model."""
        envelope = SuccessEnvelope(
            data={"key": "value"},
            request_id="req-456"
        )

        assert envelope.success is True
        assert envelope.data == {"key": "value"}
        assert envelope.error is None


class TestExceptionErrorCodes:
    """Tests for exception error codes and formatting."""

    def test_validation_error_format(self):
        """Test ValidationError formats correctly."""
        exc = ValidationError("Invalid input", field="username")
        response = ResponseFormatter.from_exception(exc)

        assert response["error"]["code"] == "VALIDATION_ERROR"
        assert response["error"]["field"] == "username"

    def test_authentication_error_format(self):
        """Test AuthenticationError formats correctly."""
        exc = AuthenticationError("Invalid token")
        response = ResponseFormatter.from_exception(exc)

        assert response["error"]["code"] == "AUTHENTICATION_ERROR"
        assert response["status_code"] == 401

    def test_not_found_error_format(self):
        """Test NotFoundError formats correctly."""
        exc = NotFoundError("User", "user-123")
        response = ResponseFormatter.from_exception(exc)

        assert response["error"]["code"] == "RESOURCE_NOT_FOUND"
        assert "User" in response["error"]["message"]
        assert "user-123" in response["error"]["message"]

    def test_processing_error_format(self):
        """Test ProcessingError formats correctly."""
        exc = ProcessingError("PDF parsing failed", processing_stage="ocr")
        response = ResponseFormatter.from_exception(exc)

        assert response["error"]["code"] == "PROCESSING_ERROR"
        assert response["error"]["details"]["stage"] == "ocr"

    def test_rate_limit_error_format(self):
        """Test RateLimitExceededError formats correctly."""
        exc = RateLimitExceededError(retry_after=60)
        response = ResponseFormatter.from_exception(exc)

        assert response["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert response["error"]["details"]["retry_after"] == 60
