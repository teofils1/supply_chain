"""
Middleware for the Supply Chain application.

Includes:
- CurrentUserMiddleware: Track the current user for automated event generation
- RequestLoggingMiddleware: Structured logging for all requests/responses (audit)
"""

import threading
import time
import uuid

import structlog
from django.utils.deprecation import MiddlewareMixin

logger = structlog.get_logger(__name__)

# Thread-local storage for the current user
_user = threading.local()


class CurrentUserMiddleware(MiddlewareMixin):
    """Middleware to store the current user in thread-local storage."""

    def process_request(self, request):
        """Store the current user when processing a request."""
        _user.value = getattr(request, "user", None)

    def process_response(self, request, response):
        """Clean up the thread-local storage after processing response."""
        if hasattr(_user, "value"):
            del _user.value
        return response

    def process_exception(self, request, exception):
        """Clean up the thread-local storage if an exception occurs."""
        if hasattr(_user, "value"):
            del _user.value


def get_current_user():
    """Get the current user from thread-local storage."""
    return getattr(_user, "value", None)


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware for structured request/response logging for audit purposes.

    Features:
    - Assigns unique request ID to each request
    - Logs request details (method, path, user, IP)
    - Logs response details (status code, duration)
    - Provides audit trail for compliance
    """

    # Paths to exclude from logging (health checks, static files, etc.)
    EXCLUDED_PATHS = {
        "/health/",
        "/favicon.ico",
    }

    # Paths with reduced logging (schema, docs)
    REDUCED_LOGGING_PATHS = {
        "/api/schema/",
        "/api/docs/",
        "/api/redoc/",
    }

    def process_request(self, request):
        """Log incoming request and attach request ID."""
        # Generate unique request ID
        request.request_id = str(uuid.uuid4())
        request._start_time = time.perf_counter()

        # Skip logging for excluded paths
        if request.path in self.EXCLUDED_PATHS:
            return

        # Build request context
        context = self._build_request_context(request)

        # Reduced logging for docs/schema
        if request.path in self.REDUCED_LOGGING_PATHS:
            logger.debug("request_started", **context)
        else:
            logger.info("request_started", **context)

    def process_response(self, request, response):
        """Log response details."""
        # Skip logging for excluded paths
        if request.path in self.EXCLUDED_PATHS:
            return response

        # Calculate request duration
        duration_ms = None
        if hasattr(request, "_start_time"):
            duration_ms = round((time.perf_counter() - request._start_time) * 1000, 2)

        # Build response context
        context = {
            "request_id": getattr(request, "request_id", None),
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "content_length": response.get("Content-Length", None),
        }

        # Add user info if authenticated
        if hasattr(request, "user") and request.user.is_authenticated:
            context["user_id"] = request.user.id
            context["username"] = request.user.username

        # Choose log level based on status code
        if response.status_code >= 500:
            logger.error("request_completed", **context)
        elif response.status_code >= 400:
            logger.warning("request_completed", **context)
        elif request.path in self.REDUCED_LOGGING_PATHS:
            logger.debug("request_completed", **context)
        else:
            logger.info("request_completed", **context)

        # Add request ID to response headers for client correlation
        response["X-Request-ID"] = getattr(request, "request_id", "unknown")

        return response

    def process_exception(self, request, exception):
        """Log unhandled exceptions."""
        context = {
            "request_id": getattr(request, "request_id", None),
            "method": request.method,
            "path": request.path,
            "error_type": type(exception).__name__,
            "error_message": str(exception),
        }

        if hasattr(request, "user") and request.user.is_authenticated:
            context["user_id"] = request.user.id
            context["username"] = request.user.username

        logger.exception("request_exception", **context)

    def _build_request_context(self, request):
        """Build context dictionary for request logging."""
        context = {
            "request_id": request.request_id,
            "method": request.method,
            "path": request.path,
            "query_string": request.META.get("QUERY_STRING", ""),
            "remote_addr": self._get_client_ip(request),
            "user_agent": request.META.get("HTTP_USER_AGENT", "")[:200],  # Truncate
        }

        # Add content type for POST/PUT/PATCH
        if request.method in ("POST", "PUT", "PATCH"):
            context["content_type"] = request.content_type
            context["content_length"] = request.META.get("CONTENT_LENGTH", 0)

        # Add user info if available (may not be set yet during auth)
        if hasattr(request, "user") and request.user.is_authenticated:
            context["user_id"] = request.user.id
            context["username"] = request.user.username

        return context

    def _get_client_ip(self, request):
        """Extract client IP from request, handling proxy headers."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")

