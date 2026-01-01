"""
Health check endpoints for monitoring and load balancer probes.
"""
import logging
from typing import Dict, Any

from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse, HttpRequest
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

import redis
from django.conf import settings


logger = logging.getLogger('gymgem')


def check_database() -> Dict[str, Any]:
    """Check database connectivity."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return {"status": "healthy", "latency_ms": None}
    except Exception as e:
        logger.error("Database health check failed: %s", str(e))
        return {"status": "unhealthy", "error": str(e)}


def check_redis() -> Dict[str, Any]:
    """Check Redis connectivity."""
    try:
        client = redis.Redis(
            host=getattr(settings, 'REDIS_HOST', '127.0.0.1'),
            port=getattr(settings, 'REDIS_PORT', 6379),
            db=getattr(settings, 'REDIS_DB', 0),
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        client.ping()
        return {"status": "healthy"}
    except Exception as e:
        logger.error("Redis health check failed: %s", str(e))
        return {"status": "unhealthy", "error": str(e)}


def check_cache() -> Dict[str, Any]:
    """Check Django cache connectivity."""
    try:
        cache.set('health_check', 'ok', 10)
        value = cache.get('health_check')
        if value == 'ok':
            return {"status": "healthy"}
        return {"status": "unhealthy", "error": "Cache read/write mismatch"}
    except Exception as e:
        logger.error("Cache health check failed: %s", str(e))
        return {"status": "unhealthy", "error": str(e)}


@extend_schema(
    tags=["Health"],
    summary="Basic health check",
    description="Simple health check endpoint for load balancers. Returns 200 if service is running.",
    responses={
        200: {"type": "object", "properties": {"status": {"type": "string"}}},
    }
)
@api_view(['GET'])
@permission_classes([])
def health_check(request: HttpRequest) -> Response:
    """
    Basic health check endpoint.
    
    Returns 200 OK if the service is running.
    Used by load balancers for simple health checks.
    """
    return Response({"status": "healthy"})


@extend_schema(
    tags=["Health"],
    summary="Readiness check",
    description="Checks if the service is ready to accept traffic. Verifies database and Redis connectivity.",
    responses={
        200: {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "checks": {
                    "type": "object",
                    "properties": {
                        "database": {"type": "object"},
                        "redis": {"type": "object"},
                        "cache": {"type": "object"},
                    }
                }
            }
        },
        503: {"description": "Service unavailable - one or more checks failed"},
    }
)
@api_view(['GET'])
@permission_classes([])
def readiness_check(request: HttpRequest) -> Response:
    """
    Readiness check endpoint.
    
    Verifies that all dependencies (database, Redis, cache) are healthy.
    Used by Kubernetes for readiness probes.
    """
    checks = {
        "database": check_database(),
        "redis": check_redis(),
        "cache": check_cache(),
    }
    
    # Determine overall status
    all_healthy = all(
        check.get("status") == "healthy" for check in checks.values()
    )
    
    response_data = {
        "status": "healthy" if all_healthy else "unhealthy",
        "checks": checks,
    }
    
    status_code = 200 if all_healthy else 503
    
    if not all_healthy:
        logger.warning("Readiness check failed: %s", checks)
    
    return Response(response_data, status=status_code)


@extend_schema(
    tags=["Health"],
    summary="Liveness check",
    description="Simple liveness check. Returns 200 if the service process is running.",
    responses={
        200: {"type": "object", "properties": {"status": {"type": "string"}}},
    }
)
@api_view(['GET'])
@permission_classes([])
def liveness_check(request: HttpRequest) -> Response:
    """
    Liveness check endpoint.
    
    Returns 200 if the service is alive.
    Used by Kubernetes for liveness probes.
    """
    return Response({"status": "alive"})


@extend_schema(
    tags=["Health"],
    summary="Detailed health status",
    description="Returns detailed health information including version and uptime.",
    responses={
        200: {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "version": {"type": "string"},
                "checks": {"type": "object"},
            }
        },
    }
)
@api_view(['GET'])
@permission_classes([])
def health_detailed(request: HttpRequest) -> Response:
    """
    Detailed health check with version info.
    
    Returns comprehensive health information for monitoring dashboards.
    """
    from django import get_version
    
    checks = {
        "database": check_database(),
        "redis": check_redis(),
        "cache": check_cache(),
    }
    
    all_healthy = all(
        check.get("status") == "healthy" for check in checks.values()
    )
    
    return Response({
        "status": "healthy" if all_healthy else "degraded",
        "version": "1.0.0",
        "django_version": get_version(),
        "checks": checks,
    })

