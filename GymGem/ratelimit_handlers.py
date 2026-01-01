"""
Custom rate limit handlers for django-ratelimit.
"""
import logging
from typing import Any

from django.http import HttpRequest, JsonResponse

logger = logging.getLogger('gymgem')


def ratelimit_handler(request: HttpRequest, exception: Any) -> JsonResponse:
    """
    Custom handler for rate limit exceeded responses.
    Returns a JSON response with appropriate error message.
    """
    logger.warning(
        "Rate limit exceeded for IP: %s, Path: %s, Method: %s",
        get_client_ip(request),
        request.path,
        request.method
    )
    
    return JsonResponse(
        {
            "detail": "Too many requests. Please slow down and try again later.",
            "code": "RATE_LIMIT_EXCEEDED"
        },
        status=429
    )


def get_client_ip(request: HttpRequest) -> str:
    """
    Extract the client IP address from the request.
    Handles proxied requests via X-Forwarded-For header.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    return ip

