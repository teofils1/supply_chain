"""
Caching utilities for the Supply Chain API.

Provides decorators and utilities for caching frequently accessed data
to improve API response times.
"""

import functools
import hashlib
import json
from typing import Any, Callable

from django.core.cache import cache

import structlog

logger = structlog.get_logger(__name__)

# Cache key prefixes for different entity types
CACHE_PREFIXES = {
    "product": "prod",
    "batch": "batch",
    "pack": "pack",
    "shipment": "ship",
    "event": "event",
    "user": "user",
}

# Default cache timeouts (in seconds)
CACHE_TIMEOUTS = {
    "product_list": 60,  # 1 minute
    "product_detail": 300,  # 5 minutes
    "batch_list": 30,  # 30 seconds
    "batch_detail": 120,  # 2 minutes
    "pack_list": 30,  # 30 seconds
    "pack_detail": 120,  # 2 minutes
    "shipment_list": 30,  # 30 seconds (frequently updated)
    "shipment_detail": 60,  # 1 minute
    "event_list": 60,  # 1 minute
    "statistics": 300,  # 5 minutes
    "default": 60,  # 1 minute
}


def make_cache_key(*args, **kwargs) -> str:
    """
    Create a cache key from arguments.

    Uses MD5 hash for consistency and to handle complex arguments.
    """
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def cache_response(
    timeout: int | None = None,
    key_prefix: str = "",
    vary_on_user: bool = False,
    vary_on_query_params: bool = True,
):
    """
    Decorator to cache API responses.

    Args:
        timeout: Cache timeout in seconds (None uses default)
        key_prefix: Prefix for the cache key
        vary_on_user: Include user ID in cache key
        vary_on_query_params: Include query parameters in cache key

    Usage:
        @cache_response(timeout=60, key_prefix="products")
        def list(self, request):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, request, *args, **kwargs):
            # Build cache key components
            key_parts = [key_prefix or func.__name__]

            # Add view class name
            key_parts.append(self.__class__.__name__)

            # Add request path
            key_parts.append(request.path)

            # Add user ID if varying on user
            if vary_on_user and request.user.is_authenticated:
                key_parts.append(f"user:{request.user.id}")

            # Add query parameters
            if vary_on_query_params and request.query_params:
                params = dict(sorted(request.query_params.items()))
                key_parts.append(json.dumps(params, sort_keys=True))

            # Generate cache key
            cache_key = f"api:{make_cache_key(*key_parts)}"

            # Try to get from cache
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                logger.debug(
                    "cache_hit",
                    cache_key=cache_key[:50],
                    view=self.__class__.__name__,
                )
                return cached_response

            # Call the actual view
            response = func(self, request, *args, **kwargs)

            # Only cache successful responses
            if 200 <= response.status_code < 300:
                cache_timeout = timeout or CACHE_TIMEOUTS.get(
                    key_prefix, CACHE_TIMEOUTS["default"]
                )
                cache.set(cache_key, response, cache_timeout)
                logger.debug(
                    "cache_set",
                    cache_key=cache_key[:50],
                    view=self.__class__.__name__,
                    timeout=cache_timeout,
                )

            return response

        return wrapper

    return decorator


def invalidate_cache(prefix: str, entity_id: int | None = None):
    """
    Invalidate cache entries for a specific entity type.

    Note: This is a simple implementation. For production with Redis,
    consider using Redis pattern matching or cache tags.

    Args:
        prefix: Entity type prefix (e.g., 'product', 'batch')
        entity_id: Specific entity ID to invalidate (optional)
    """
    # For simple invalidation, we'd need to track keys
    # With Redis, you could use pattern-based deletion
    logger.info(
        "cache_invalidate_request",
        prefix=prefix,
        entity_id=entity_id,
    )

    # Simple approach: Clear specific known keys
    if entity_id:
        cache.delete(f"api:{prefix}:detail:{entity_id}")

    # For list invalidation, you'd need a more sophisticated approach
    # such as versioning or cache tags


def get_cached_or_compute(
    cache_key: str,
    compute_func: Callable[[], Any],
    timeout: int | None = None,
) -> Any:
    """
    Get a value from cache or compute it if not present.

    Args:
        cache_key: The cache key
        compute_func: Function to call if value not in cache
        timeout: Cache timeout in seconds

    Returns:
        The cached or computed value
    """
    cached_value = cache.get(cache_key)
    if cached_value is not None:
        return cached_value

    value = compute_func()
    cache.set(cache_key, value, timeout or CACHE_TIMEOUTS["default"])
    return value


def cache_model_count(model_class, filter_kwargs: dict | None = None, timeout: int = 300) -> int:
    """
    Cache the count of model instances.

    Useful for dashboard statistics that don't need real-time accuracy.

    Args:
        model_class: Django model class
        filter_kwargs: Optional filter arguments
        timeout: Cache timeout in seconds

    Returns:
        Count of matching instances
    """
    filter_kwargs = filter_kwargs or {}
    cache_key = f"count:{model_class.__name__}:{make_cache_key(**filter_kwargs)}"

    def compute_count():
        return model_class.objects.filter(**filter_kwargs).count()

    return get_cached_or_compute(cache_key, compute_count, timeout)
