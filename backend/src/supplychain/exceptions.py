"""
Centralized exception handling for the Supply Chain API.

This module provides:
- Custom exception handler for DRF that formats all errors consistently
- Custom exception classes for domain-specific errors
- Structured logging integration for all exceptions
"""

import structlog
from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = structlog.get_logger(__name__)


# =============================================================================
# Custom Exception Classes
# =============================================================================


class SupplyChainException(APIException):
    """Base exception for all supply chain domain errors."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "A supply chain error occurred."
    default_code = "supply_chain_error"


class ResourceNotFoundException(SupplyChainException):
    """Raised when a requested resource is not found."""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "The requested resource was not found."
    default_code = "resource_not_found"


class ResourceConflictException(SupplyChainException):
    """Raised when there's a conflict with existing resources."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "A conflict occurred with an existing resource."
    default_code = "resource_conflict"


class BlockchainException(SupplyChainException):
    """Raised when blockchain operations fail."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Blockchain service is temporarily unavailable."
    default_code = "blockchain_error"


class ValidationException(SupplyChainException):
    """Raised when validation fails with custom business logic."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Validation failed."
    default_code = "validation_error"


class AuthorizationException(SupplyChainException):
    """Raised when user lacks permission for an action."""

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You do not have permission to perform this action."
    default_code = "authorization_error"


class RateLimitException(SupplyChainException):
    """Raised when rate limit is exceeded."""

    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = "Rate limit exceeded. Please try again later."
    default_code = "rate_limit_exceeded"


# =============================================================================
# Exception Handler
# =============================================================================


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses
    with structured logging.

    Response format:
    {
        "error": {
            "code": "error_code",
            "message": "Human-readable message",
            "details": {...}  # Optional, for validation errors
        },
        "request_id": "uuid"  # If available from middleware
    }
    """
    # Get request info for logging
    request = context.get("request")
    view = context.get("view")

    # Extract request metadata for logging
    log_context = _build_log_context(request, view)

    # Handle Django's built-in exceptions
    if isinstance(exc, Http404):
        exc = ResourceNotFoundException(detail=str(exc) or "Resource not found.")
    elif isinstance(exc, PermissionDenied):
        exc = AuthorizationException(detail=str(exc) or "Permission denied.")
    elif isinstance(exc, DjangoValidationError):
        # Convert Django ValidationError to DRF format
        if hasattr(exc, "message_dict"):
            detail = exc.message_dict
        elif hasattr(exc, "messages"):
            detail = exc.messages
        else:
            detail = str(exc)
        exc = ValidationException(detail=detail)

    # Let DRF handle the rest
    response = drf_exception_handler(exc, context)

    if response is not None:
        # Format the error response consistently
        error_response = _format_error_response(exc, response, request)

        # Log the exception
        _log_exception(exc, log_context, response.status_code)

        return Response(error_response, status=response.status_code)

    # Unhandled exception - log it and return 500
    logger.exception(
        "unhandled_exception",
        error_type=type(exc).__name__,
        error_message=str(exc),
        **log_context,
    )

    return Response(
        {
            "error": {
                "code": "internal_server_error",
                "message": "An unexpected error occurred. Please try again later.",
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _build_log_context(request, view):
    """Build context dictionary for structured logging."""
    context = {}

    if request:
        context.update(
            {
                "method": request.method,
                "path": request.path,
                "user_id": getattr(request.user, "id", None) if hasattr(request, "user") else None,
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                "remote_addr": _get_client_ip(request),
            }
        )
        # Include request_id if set by middleware
        if hasattr(request, "request_id"):
            context["request_id"] = request.request_id

    if view:
        context["view"] = view.__class__.__name__

    return context


def _get_client_ip(request):
    """Extract client IP from request, handling proxy headers."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _format_error_response(exc, response, request):
    """Format exception into consistent error response structure."""
    # Determine error code
    if hasattr(exc, "default_code"):
        code = exc.default_code
    elif hasattr(exc, "get_codes"):
        codes = exc.get_codes()
        if isinstance(codes, dict):
            code = "validation_error"
        elif isinstance(codes, list):
            code = codes[0] if codes else "error"
        else:
            code = codes
    else:
        code = "error"

    # Build error message
    if hasattr(exc, "detail"):
        detail = exc.detail
    else:
        detail = str(exc)

    # Structure the response
    if isinstance(detail, dict):
        # Validation errors with field-specific messages
        error_response = {
            "error": {
                "code": code,
                "message": "Validation failed.",
                "details": _serialize_errors(detail),
            }
        }
    elif isinstance(detail, list):
        # List of errors
        error_response = {
            "error": {
                "code": code,
                "message": detail[0] if detail else "An error occurred.",
                "details": _serialize_errors(detail) if len(detail) > 1 else None,
            }
        }
    else:
        # Single error message
        error_response = {
            "error": {
                "code": code,
                "message": str(detail),
            }
        }

    # Add request_id if available
    if request and hasattr(request, "request_id"):
        error_response["request_id"] = request.request_id

    # Remove None values
    if "details" in error_response["error"] and error_response["error"]["details"] is None:
        del error_response["error"]["details"]

    return error_response


def _serialize_errors(detail):
    """Recursively serialize error details to plain Python types."""
    if isinstance(detail, dict):
        return {key: _serialize_errors(value) for key, value in detail.items()}
    elif isinstance(detail, list):
        return [_serialize_errors(item) for item in detail]
    else:
        return str(detail)


def _log_exception(exc, context, status_code):
    """Log exception with appropriate severity level."""
    log_data = {
        "error_type": type(exc).__name__,
        "error_code": getattr(exc, "default_code", "unknown"),
        "status_code": status_code,
        **context,
    }

    # Choose log level based on status code
    if status_code >= 500:
        logger.error("api_error", error_message=str(exc.detail) if hasattr(exc, "detail") else str(exc), **log_data)
    elif status_code >= 400:
        logger.warning("api_client_error", error_message=str(exc.detail) if hasattr(exc, "detail") else str(exc), **log_data)
    else:
        logger.info("api_exception", error_message=str(exc.detail) if hasattr(exc, "detail") else str(exc), **log_data)
