"""
Integration tests for error handling.
Tests the full error handling pipeline including middleware.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import FastAPI, Request
import httpx
from httpx import AsyncClient

from core.exceptions import CreditClarityException, ValidationError, AuthenticationError
from core.response import ResponseFormatter
from middleware.error_handler import ErrorHandlerMiddleware, setup_exception_handlers

pytestmark = pytest.mark.asyncio


def create_test_app():
    """Create a test FastAPI app with error handling."""
    app = FastAPI()

    # Add error handler middleware
    app.add_middleware(ErrorHandlerMiddleware)
    setup_exception_handlers(app)

    @app.get("/success")
    async def success_endpoint():
        return ResponseFormatter.success_response(data={"status": "ok"})

    @app.get("/error/validation")
    async def validation_error():
        raise ValidationError("Invalid input", field="email")

    @app.get("/error/auth")
    async def auth_error():
        raise AuthenticationError("Invalid credentials")

    @app.get("/error/custom")
    async def custom_error():
        raise CreditClarityException(
            message="Custom error message",
            error_code="CUSTOM_ERROR",
            status_code=422
        )

    @app.get("/error/generic")
    async def generic_error():
        raise ValueError("Something went wrong")

    @app.get("/error/not-found")
    async def not_found_error():
        from core.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError("Document", "doc-123")

    return app


class TestErrorHandlingIntegration:
    """Integration tests for error handling."""

    @pytest.fixture
    def app(self):
        return create_test_app()

    @pytest_asyncio.fixture
    async def client(self, app):
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    async def test_success_endpoint(self, client):
        """Test successful endpoint returns correct format."""
        response = await client.get("/success")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == {"status": "ok"}
        assert data["error"] is None
        assert "request_id" in data
        assert data["request_id"].startswith("req-")

    async def test_validation_error(self, client):
        """Test validation error returns correct format."""
        response = await client.get("/error/validation")

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert data["error"]["field"] == "email"
        assert "request_id" in data

    async def test_auth_error(self, client):
        """Test authentication error returns correct format."""
        response = await client.get("/error/auth")

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"
        assert "request_id" in data

    async def test_custom_exception(self, client):
        """Test custom exception returns correct format."""
        response = await client.get("/error/custom")

        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "CUSTOM_ERROR"
        assert data["error"]["message"] == "Custom error message"
        assert "request_id" in data

    async def test_generic_error(self, client):
        """Test generic exception returns correct format."""
        response = await client.get("/error/generic")

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INTERNAL_ERROR"
        assert "request_id" in data

    async def test_not_found_error(self, client):
        """Test not found error returns correct format."""
        response = await client.get("/error/not-found")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
        assert "request_id" in data


class TestErrorHandlingWithHeaders:
    """Tests for error handling with request headers."""

    @pytest.fixture
    def app(self):
        return create_test_app()

    @pytest_asyncio.fixture
    async def client(self, app):
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    async def test_request_id_in_response_headers(self, client):
        """Test request ID is included in response headers."""
        response = await client.get("/success")

        assert "x-request-id" in response.headers
        assert response.headers["x-request-id"].startswith("req-")

    async def test_error_request_id_in_headers(self, client):
        """Test request ID is included in error response headers."""
        response = await client.get("/error/validation")

        assert "x-request-id" in response.headers
        assert response.headers["x-request-id"].startswith("req-")


class TestErrorHandlingEdgeCases:
    """Edge case tests for error handling."""

    @pytest.fixture
    def app(self):
        app = FastAPI()
        app.add_middleware(ErrorHandlerMiddleware)
        setup_exception_handlers(app)

        @app.get("/exception/no-message")
        async def no_message():
            raise CreditClarityException(message="")

        @app.get("/exception/no-code")
        async def no_code():
            raise CreditClarityException(message="Error", error_code="")

        return app

    @pytest_asyncio.fixture
    async def client(self, app):
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    async def test_exception_with_empty_message(self, client):
        """Test handling exception with empty message."""
        response = await client.get("/exception/no-message")

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False

    async def test_exception_with_empty_code(self, client):
        """Test handling exception with empty code."""
        response = await client.get("/exception/no-code")

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False


class TestErrorHandlingWithRouteContext:
    """Tests for error handling with route context."""

    @pytest.fixture
    def app(self):
        app = FastAPI()
        app.add_middleware(ErrorHandlerMiddleware)
        setup_exception_handlers(app)

        @app.get("/context")
        async def with_context(request: Request):
            # Access request state
            request_id = getattr(request.state, "request_id", None)
            return ResponseFormatter.success_response(
                data={"request_id": request_id}
            )

        @app.get("/context-error")
        async def context_error(request: Request):
            raise ValidationError("Error in context", field="test")

        return app

    @pytest_asyncio.fixture
    async def client(self, app):
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    async def test_request_id_in_route_context(self, client):
        """Test request ID is available in route context."""
        response = await client.get("/context")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["request_id"].startswith("req-")

    async def test_context_preserved_on_error(self, client):
        """Test request context is preserved on error."""
        response = await client.get("/context-error")

        assert response.status_code == 400
        data = response.json()
        # The request_id should still be generated even on error
        assert "request_id" in data
