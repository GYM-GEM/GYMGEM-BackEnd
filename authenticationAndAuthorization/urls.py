from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from .views import (
    AccountLoginView,
    LogoutView,
    LogoutAllView,
)

urlpatterns = [
    # Rich login: returns tokens + account info
    path('login', AccountLoginView.as_view(), name='account_login'),

    # Refresh access token
    path('refresh-token', TokenRefreshView.as_view(), name='token_refresh'),

    # Logout endpoints
    path('logout', LogoutView.as_view(), name='logout'),
    path('logout-all', LogoutAllView.as_view(), name='logout_all'),
]
