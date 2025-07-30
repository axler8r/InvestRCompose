"""Common exception handling utilities for InvestR services.

This module provides utilities for standardized error handling across
all microservices using the ErrorResponse schema.
"""

from typing import Any, Dict, Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from investr.common.schemas import ErrorResponse


def create_error_response(
    error: str,
    message: str,
    status_code: int = 500,
    details: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """Create a standardized error response using ErrorResponse schema.

    Args:
        error: Error type or category
        message: Human-readable error message
        status_code: HTTP status code
        details: Optional additional error details

    Returns:
        JSONResponse with ErrorResponse format

    """
    error_response = ErrorResponse(
        error=error,
        message=message,
        details=details,
    )

    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Convert HTTPException to standardized ErrorResponse format.

    Args:
        request: FastAPI request object
        exc: HTTPException to convert

    Returns:
        JSONResponse with ErrorResponse format

    """
    # Extract error details from the exception
    error_type = "HTTPException"
    if exc.status_code == 400:
        error_type = "BadRequest"
    elif exc.status_code == 401:
        error_type = "Unauthorized"
    elif exc.status_code == 404:
        error_type = "NotFound"
    elif exc.status_code == 422:
        error_type = "ValidationError"
    elif exc.status_code >= 500:
        error_type = "InternalServerError"

    details = None
    if hasattr(exc, "detail") and isinstance(exc.detail, dict):
        details = exc.detail

    return create_error_response(
        error=error_type,
        message=str(exc.detail) if exc.detail else "An error occurred",
        status_code=exc.status_code,
        details=details,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with standardized ErrorResponse format.

    Args:
        request: FastAPI request object
        exc: Unexpected exception

    Returns:
        JSONResponse with ErrorResponse format

    """
    return create_error_response(
        error="InternalServerError",
        message="An unexpected error occurred",
        status_code=500,
        details={"exception_type": type(exc).__name__},
    )
