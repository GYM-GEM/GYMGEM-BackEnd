from django.urls import include, path

urlpatterns = [
    path("accounts/", include("accounts.urls")),
    path("auth/", include("authenticationAndAuthorization.urls")),
    path("profiles/", include("profiles.urls")),
    path("trainers/", include("trainers.urls")),
    path("courses/", include("courses.urls")),
    path("chat/", include("chat.urls")),
    path("interactive-sessions/", include("interactive_sessions.urls")),
    path("trainees/", include("trainees.urls")),
    path("utils/", include("utils.urls")),
    path("stores/", include("stores.urls")),
]
