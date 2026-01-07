"""
Response formatter for consistent API responses.
Provides standardized success/error/paginated response envelopes.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Structured error detail."""
    code: str
    message: str
    field: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ErrorEnvelope(BaseModel):
    """Error envelope format matching API specification."""
    success: bool = False
    error: Optional[ErrorDetail] = None
    data: Optional[Any] = None
    request_id: str


class SuccessEnvelope(BaseModel):
    """Success envelope format matching API specification."""
    success: bool = True
    data: Optional[Any] = None
    error: Optional[Any] = None
    request_id: str


class PaginatedEnvelope(BaseModel):
    """Paginated response envelope."""
    success: bool = True
    data: List[Dict[str, Any]]
    error: Optional[Any] = None
    request_id: str
    pagination: Dict[str, Any]


class ResponseFormatter:
    """Format all API responses consistently."""

    @staticmethod
    def generate_request_id() -> str:
        """Generate unique request ID."""
        return f"req-{uuid.uuid4().hex[:8]}"

    @staticmethod
    def success_response(
        data: Optional[Any] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create success response envelope.

        Args:
            data: Response data
            request_id: Optional request ID (generated if not provided)

        Returns:
            Success envelope dict
        """
        req_id = request_id or ResponseFormatter.generate_request_id()

        return {
            "success": True,
            "data": data,
            "error": None,
            "request_id": req_id
        }

    @staticmethod
    def error_response(
        code: str,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create error response envelope.

        Args:
            code: Error code (e.g., "AUTH_INVALID_CREDENTIALS")
            message: Error message
            field: Optional field name that caused the error
            details: Additional error details
            request_id: Optional request ID (generated if not provided)

        Returns:
            Error envelope dict
        """
        req_id = request_id or ResponseFormatter.generate_request_id()

        error_detail = ErrorDetail(
            code=code,
            message=message,
            field=field,
            details=details
        )

        return {
            "success": False,
            "error": error_detail.model_dump(),
            "data": None,
            "request_id": req_id
        }

    @staticmethod
    def paginated_response(
        data: List[Dict[str, Any]],
        total: int,
        page: int,
        per_page: int,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create paginated response envelope.

        Args:
            data: List of items
            total: Total number of items
            page: Current page number
            per_page: Items per page
            request_id: Optional request ID (generated if not provided)

        Returns:
            Paginated envelope dict
        """
        req_id = request_id or ResponseFormatter.generate_request_id()

        pagination = {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page if total > 0 else 0,
            "has_next": page * per_page < total,
            "has_prev": page > 1
        }

        return {
            "success": True,
            "data": data,
            "error": None,
            "request_id": req_id,
            "pagination": pagination
        }

    @staticmethod
    def from_exception(
        exception: Exception,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create error response from exception.

        Args:
            exception: Exception to format
            request_id: Optional request ID

        Returns:
            Error envelope dict
        """
        from core.exceptions import CreditClarityException

        req_id = request_id or ResponseFormatter.generate_request_id()

        if isinstance(exception, CreditClarityException):
            return ResponseFormatter.error_response(
                code=exception.error_code,
                message=exception.message,
                field=exception.details.get("field") if exception.details else None,
                details=exception.details,
                request_id=req_id
            )

        # Generic error for unknown exceptions
        return ResponseFormatter.error_response(
            code="INTERNAL_ERROR",
            message=str(exception) if str(exception) else "An unexpected error occurred",
            request_id=req_id
        )


# Convenience functions
def success_response(data: Optional[Any] = None, request_id: Optional[str] = None) -> Dict[str, Any]:
    """Create success response."""
    return ResponseFormatter.success_response(data, request_id)


def error_response(
    code: str,
    message: str,
    field: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create error response."""
    return ResponseFormatter.error_response(code, message, field, details, request_id)


def paginated_response(
    data: List[Dict[str, Any]],
    total: int,
    page: int,
    per_page: int,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create paginated response."""
    return ResponseFormatter.paginated_response(data, total, page, per_page, request_id)
