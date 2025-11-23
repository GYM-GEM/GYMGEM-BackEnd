from django.urls import path
from .views import (
    MyTokenRefreshView,
    AccountLoginView,
    LogoutView,
    LogoutAllView,
    SwitchProfileView,
)

urlpatterns = [
    # Rich login: returns tokens + account info
    path('login', AccountLoginView.as_view(), name='account_login'),
    path('switch-profile', SwitchProfileView.as_view(), name='switch_profile'),

    # Refresh access token
    path('refresh-token', MyTokenRefreshView.as_view(), name='token_refresh'),

    # Logout endpoints
    path('logout', LogoutView.as_view(), name='logout'),
    path('logout-all', LogoutAllView.as_view(), name='logout_all'),
]
