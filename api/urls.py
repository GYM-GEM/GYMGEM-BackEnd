from django.urls import include, path

from .health import (
    health_check,
    readiness_check,
    liveness_check,
    health_detailed,
)

urlpatterns = [
    # Health check endpoints
    path("health/", health_check, name="health-check"),
    path("health/ready/", readiness_check, name="readiness-check"),
    path("health/live/", liveness_check, name="liveness-check"),
    path("health/detailed/", health_detailed, name="health-detailed"),
    
    # API routes
    path("accounts/", include("accounts.urls")),
    path("auth/", include("authenticationAndAuthorization.urls")),
    path("profiles/", include("profiles.urls")),
    path("trainers/", include("trainers.urls")),
    path("courses/", include("courses.urls")),
    path("chat/", include("chat.urls")),
    path("interactive-sessions/", include("interactive_sessions.urls")),
    path("trainees/", include("trainees.urls")),
    path("utils/", include("utils.urls")),
    path("community/", include("community.urls")),
    path("payment/", include("payment.urls")),
    path("stores/", include("stores.urls")),
]
