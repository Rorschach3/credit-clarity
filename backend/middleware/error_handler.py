"""
Global exception handler middleware.
Converts exceptions to error envelope format and adds request_id to all responses.
"""
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Optional, Tuple, List

from fastapi import HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Scope, Receive, Send

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


def _has_header(headers: List[Tuple[bytes, bytes]], name: bytes) -> bool:
    name_l = name.lower()
    return any(k.lower() == name_l for (k, _v) in headers)


class ErrorHandlerMiddleware:
    """
    Middleware for consistent error handling across all API responses.

    Features:
    - Generates unique request_id for each request
    - Catches all exceptions and formats them consistently
    - Logs errors with request_id for correlation
    - Adds request_id to all responses
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = ResponseFormatter.generate_request_id()
        token = request_id_context.set(request_id)
        scope.setdefault("state", {})["request_id"] = request_id

        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "")
        logger.info(f"[{request_id}] {method} {path}")

        start_time = time.perf_counter()

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                if not _has_header(headers, b"x-request-id"):
                    headers.append((b"x-request-id", request_id.encode("ascii")))
                if not _has_header(headers, b"x-process-time"):
                    headers.append((b"x-process-time", f"{(time.perf_counter() - start_time):.6f}".encode("ascii")))
                path = scope.get("path", "")
                if isinstance(path, str) and path.startswith("/api/v1/"):
                    if not _has_header(headers, b"x-api-version"):
                        headers.append((b"x-api-version", b"1.0"))
                    if not _has_header(headers, b"x-api-revision"):
                        headers.append((b"x-api-revision", b"2025.01"))
                    if not _has_header(headers, b"x-api-architecture"):
                        headers.append((b"x-api-architecture", b"modular"))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except CreditClarityException as exc:
            logger.error(f"[{request_id}] App exception: {exc.error_code} - {exc.message}")
            response = JSONResponse(
                status_code=exc.status_code,
                content=ResponseFormatter.from_exception(exc, request_id),
            )
            await response(scope, receive, send_wrapper)
        except HTTPException as exc:
            status = exc.status_code
            if status == 404:
                code = "RESOURCE_NOT_FOUND"
            elif status == 401:
                code = "UNAUTHORIZED"
            elif status == 403:
                code = "FORBIDDEN"
            else:
                code = "HTTP_ERROR"
            response = JSONResponse(
                status_code=status,
                content=ResponseFormatter.error_response(
                    code=code,
                    message=str(exc.detail) if exc.detail else "Request failed",
                    request_id=request_id,
                ),
            )
            await response(scope, receive, send_wrapper)
        except RequestValidationError as exc:
            response = JSONResponse(
                status_code=422,
                content=ResponseFormatter.error_response(
                    code="VALIDATION_ERROR",
                    message="Request validation failed",
                    details={"errors": exc.errors()},
                    request_id=request_id,
                ),
            )
            await response(scope, receive, send_wrapper)
        except Exception as exc:
            logger.exception(f"[{request_id}] Unexpected error: {str(exc)}")
            response = JSONResponse(
                status_code=500,
                content=ResponseFormatter.error_response(
                    code="INTERNAL_ERROR",
                    message="An unexpected error occurred. Please try again later.",
                    request_id=request_id,
                ),
            )
            await response(scope, receive, send_wrapper)
        finally:
            request_id_context.reset(token)


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

    @staticmethod
    async def handle_http_exception(
        request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        """Handle FastAPI HTTPException with the standard error envelope."""
        request_id = getattr(request.state, "request_id", None) or ResponseFormatter.generate_request_id()

        status = exc.status_code
        if status == 404:
            code = "RESOURCE_NOT_FOUND"
        elif status == 401:
            code = "UNAUTHORIZED"
        elif status == 403:
            code = "FORBIDDEN"
        else:
            code = "HTTP_ERROR"

        error_response = ResponseFormatter.error_response(
            code=code,
            message=str(exc.detail) if exc.detail else "Request failed",
            request_id=request_id,
        )
        return JSONResponse(status_code=status, content=error_response, headers={"X-Request-ID": request_id})

    @staticmethod
    async def handle_validation_exception(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Handle request body/query validation errors with the standard error envelope."""
        request_id = getattr(request.state, "request_id", None) or ResponseFormatter.generate_request_id()
        error_response = ResponseFormatter.error_response(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details={"errors": exc.errors()},
            request_id=request_id,
        )
        return JSONResponse(status_code=422, content=error_response, headers={"X-Request-ID": request_id})


def setup_exception_handlers(app) -> None:
    """
    Setup exception handlers on FastAPI app.

    Args:
        app: FastAPI application instance
    """
    # Register custom exception handlers
    app.add_exception_handler(HTTPException, ExceptionHandlers.handle_http_exception)
    app.add_exception_handler(RequestValidationError, ExceptionHandlers.handle_validation_exception)
    app.add_exception_handler(CreditClarityException, ExceptionHandlers.handle_credit_clarity_exception)
    app.add_exception_handler(Exception, ExceptionHandlers.handle_generic_exception)
