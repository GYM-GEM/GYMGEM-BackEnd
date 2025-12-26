from django.urls import path
from .views import ProfileView, ProfileUpdateView, ProfileBalanceView, ProfileAdminView

urlpatterns = [
    path('create', ProfileView.as_view(), name='profile-list'),
    path('update/<int:profile_id>', ProfileUpdateView.as_view(), name='profile-detail'),
    path('balance', ProfileBalanceView.as_view(), name='profile-balance'),
    path('admin/<int:profile_id>', ProfileAdminView.as_view(), name='profile-admin-detail'),
]
