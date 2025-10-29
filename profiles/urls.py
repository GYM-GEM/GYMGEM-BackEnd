from django.urls import path
from .views import ProfileView, ProfileUpdateView

urlpatterns = [
    path('profiles/', ProfileView.as_view(), name='profile-list'),
    path('profiles/<int:profile_id>/', ProfileUpdateView.as_view(), name='profile-detail'),
]
