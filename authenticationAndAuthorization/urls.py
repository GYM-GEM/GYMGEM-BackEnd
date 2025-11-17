from django.urls import path

from .google_callback import GoogleLoginView
from .views import (
    MyTokenRefreshView,
    AccountLoginView,
    LogoutView,
    LogoutAllView,
)

urlpatterns = [
    path("social/google/login/", GoogleLoginView.as_view(), name="google_login"),
    # Rich login: returns tokens + account info
    path('login', AccountLoginView.as_view(), name='account_login'),

    # Refresh access token
    path('refresh-token', MyTokenRefreshView.as_view(), name='token_refresh'),

    # Logout endpoints
    path('logout', LogoutView.as_view(), name='logout'),
    path('logout-all', LogoutAllView.as_view(), name='logout_all'),
]
