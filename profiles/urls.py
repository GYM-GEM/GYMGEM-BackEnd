from django.urls import path
from .views import ProfileView, ProfileUpdateView, ProfileBalanceView

urlpatterns = [
    path('create', ProfileView.as_view(), name='profile-list'),
    path('update/<int:profile_id>', ProfileUpdateView.as_view(), name='profile-detail'),
    path('balance', ProfileBalanceView.as_view(), name='profile-balance'),
]
