from django.urls import path
from . import views

urlpatterns = [
    path('interactive-sessions/', views.InteractiveSessionView.as_view(), name='interactive-sessions-create'),
    path('interactive-sessions/<int:pk>/', views.InteractiveSessionView.as_view(), name='interactive-sessions-detail'),
]