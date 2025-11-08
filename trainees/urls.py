from django.urls import path
from .views import TraineeView , TraineeUpdateView

urlpatterns = [
    path('create', TraineeView.as_view(), name='trainee-list'),
    path('update/<int:trainer_id>', TraineeUpdateView.as_view(), name='trainee-detail'),
]

