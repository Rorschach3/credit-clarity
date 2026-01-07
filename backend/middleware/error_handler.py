"""
Global exception handler middleware.
Converts exceptions to error envelope format and adds request_id to all responses.
"""
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Callable, Dict, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from core.exceptions import CreditClarityException
from core.response import ResponseFormatter

logger = logging.getLogger(__name__)


class RequestContext:
    """Context manager for request ID tracking."""

    def __init__(self, request_id: Optional[str] = None):
        self.request_id = request_id or ResponseFormatter.generate_request_id()

    def __enter__(self):
        return self.request_id

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


# Store request_id in context variable for access in exception handlers
import contextvars

request_id_context = contextvars.ContextVar("request_id", default="")


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware for consistent error handling across all API responses.

    Features:
    - Generates unique request_id for each request
    - Catches all exceptions and formats them consistently
    - Logs errors with request_id for correlation
    - Adds request_id to all responses
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with error handling."""
        # Generate request_id
        request_id = ResponseFormatter.generate_request_id()
        request_id_context.set(request_id)

        # Add request_id to request state for access in route handlers
        request.state.request_id = request_id

        # Log request
        logger.info(f"[{request_id}] {request.method} {request.url.path}")

        try:
            # Process request
            response = await call_next(request)

            # Add request_id to response headers
            if isinstance(response, JSONResponse):
                # For JSON responses, we can modify the body
                # This is handled by the response formatter in route handlers
                pass

            # Add request_id to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except CreditClarityException as exc:
            # Handle known application exceptions
            logger.error(f"[{request_id}] App exception: {exc.error_code} - {exc.message}")

            error_response = ResponseFormatter.from_exception(exc, request_id)
            return JSONResponse(
                status_code=exc.status_code,
                content=error_response,
                headers={"X-Request-ID": request_id}
            )

        except ValueError as exc:
            # Handle validation errors
            logger.warning(f"[{request_id}] Value error: {str(exc)}")

            error_response = ResponseFormatter.error_response(
                code="VALIDATION_ERROR",
                message=str(exc) or "Invalid value provided",
                request_id=request_id
            )
            return JSONResponse(
                status_code=400,
                content=error_response,
                headers={"X-Request-ID": request_id}
            )

        except PermissionError as exc:
            # Handle permission errors
            logger.warning(f"[{request_id}] Permission denied: {str(exc)}")

            error_response = ResponseFormatter.error_response(
                code="PERMISSION_DENIED",
                message=str(exc) or "You don't have permission to perform this action",
                request_id=request_id
            )
            return JSONResponse(
                status_code=403,
                content=error_response,
                headers={"X-Request-ID": request_id}
            )

        except FileNotFoundError as exc:
            # Handle file not found errors
            logger.warning(f"[{request_id}] File not found: {str(exc)}")

            error_response = ResponseFormatter.error_response(
                code="RESOURCE_NOT_FOUND",
                message=str(exc) or "Requested resource not found",
                request_id=request_id
            )
            return JSONResponse(
                status_code=404,
                content=error_response,
                headers={"X-Request-ID": request_id}
            )

        except ConnectionError as exc:
            # Handle connection errors (database, redis, etc.)
            logger.error(f"[{request_id}] Connection error: {str(exc)}")

            error_response = ResponseFormatter.error_response(
                code="CONNECTION_ERROR",
                message="Unable to connect to required service. Please try again later.",
                details={"original_error": str(exc)} if str(exc) else None,
                request_id=request_id
            )
            return JSONResponse(
                status_code=503,
                content=error_response,
                headers={"X-Request-ID": request_id}
            )

        except TimeoutError as exc:
            # Handle timeout errors
            logger.warning(f"[{request_id}] Timeout error: {str(exc)}")

            error_response = ResponseFormatter.error_response(
                code="REQUEST_TIMEOUT",
                message="The request timed out. Please try again.",
                request_id=request_id
            )
            return JSONResponse(
                status_code=408,
                content=error_response,
                headers={"X-Request-ID": request_id}
            )

        except Exception as exc:
            # Handle unexpected exceptions
            logger.exception(f"[{request_id}] Unexpected error: {str(exc)}")

            error_response = ResponseFormatter.error_response(
                code="INTERNAL_ERROR",
                message="An unexpected error occurred. Please try again later.",
                request_id=request_id
            )
            return JSONResponse(
                status_code=500,
                content=error_response,
                headers={"X-Request-ID": request_id}
            )


def get_current_request_id() -> str:
    """Get current request_id from context."""
    return request_id_context.get() or ""


@asynccontextmanager
async def request_context(request: Request) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Context manager for request processing.

    Yields:
        Dict with request context including request_id
    """
    request_id = getattr(request.state, "request_id", None) or ResponseFormatter.generate_request_id()
    request.state.request_id = request_id

    context = {
        "request_id": request_id,
        "request": request,
        "user_id": getattr(request.state, "user_id", None)
    }

    token = request_id_context.set(request_id)
    try:
        yield context
    finally:
        request_id_context.reset(token)


class ExceptionHandlers:
    """
    Collection of exception handlers for use with FastAPI's exception_handlers.
    """

    @staticmethod
    async def handle_credit_clarity_exception(
        request: Request,
        exc: CreditClarityException
    ) -> JSONResponse:
        """Handle CreditClarityException."""
        request_id = getattr(request.state, "request_id", None) or ResponseFormatter.generate_request_id()

        error_response = ResponseFormatter.from_exception(exc, request_id)
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response,
            headers={"X-Request-ID": request_id}
        )

    @staticmethod
    async def handle_generic_exception(
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        """Handle generic exceptions."""
        request_id = getattr(request.state, "request_id", None) or ResponseFormatter.generate_request_id()

        logger.exception(f"[{request_id}] Unhandled exception: {str(exc)}")

        error_response = ResponseFormatter.error_response(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            request_id=request_id
        )
        return JSONResponse(
            status_code=500,
            content=error_response,
            headers={"X-Request-ID": request_id}
        )


def setup_exception_handlers(app) -> None:
    """
    Setup exception handlers on FastAPI app.

    Args:
        app: FastAPI application instance
    """
    # Register custom exception handlers
    app.add_exception_handler(CreditClarityException, ExceptionHandlers.handle_credit_clarity_exception)
    app.add_exception_handler(Exception, ExceptionHandlers.handle_generic_exception)
