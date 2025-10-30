from django.urls import path
from .views import ProfileView, ProfileUpdateView

urlpatterns = [
    path('create', ProfileView.as_view(), name='profile-list'),
    path('update/<int:profile_id>', ProfileUpdateView.as_view(), name='profile-detail'),
]
