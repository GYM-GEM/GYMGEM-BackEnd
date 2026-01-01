"""
Custom middleware for the accounts application.

Note: Rate limiting has been moved to use django-ratelimit decorators
on individual views for more granular control. This middleware is kept
for any additional request processing needs.
"""
import logging
from typing import Callable, Any

from django.http import HttpRequest, HttpResponse

logger = logging.getLogger('gymgem')


class RequestLoggingMiddleware:
    """
    Middleware to log incoming requests for debugging and monitoring.
    """
    
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Log request info (excluding sensitive data)
        logger.debug(
            "Request: %s %s from %s",
            request.method,
            request.path,
            self._get_client_ip(request)
        )
        
        response = self.get_response(request)
        
        # Log response status
        logger.debug(
            "Response: %s %s -> %d",
            request.method,
            request.path,
            response.status_code
        )
        
        return response
    
    @staticmethod
    def _get_client_ip(request: HttpRequest) -> str:
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')


# Legacy RateLimitMiddleware - Deprecated
# Use @ratelimit decorator from django-ratelimit on views instead
class RateLimitMiddleware:
    """
    DEPRECATED: This middleware is kept for backwards compatibility.
    Rate limiting is now handled via django-ratelimit decorators.
    
    This middleware now just passes through requests without rate limiting.
    Remove from MIDDLEWARE settings when confident all views use decorators.
    """
    
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        logger.info("RateLimitMiddleware initialized (deprecated - using django-ratelimit)")

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Pass through - rate limiting handled by decorators
        return self.get_response(request)
