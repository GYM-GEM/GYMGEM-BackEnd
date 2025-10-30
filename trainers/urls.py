from django.urls import path
from .views import TrainerView , TrainerUpdateView 

urlpatterns = [
    path('create', TrainerView.as_view(), name='trainer-list'),
    path('update/<int:trainer_id>', TrainerUpdateView.as_view(), name='trainer-detail'),
]
