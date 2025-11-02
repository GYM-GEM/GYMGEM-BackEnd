from django.urls import path
from .views import TrainerView , TrainerUpdateView , TrainerSpecializationView, TrainerSpecializationUpdateView, TrainerExperienceUpdateView, TrainerExperienceView

urlpatterns = [
    path('create', TrainerView.as_view(), name='trainer-list'),
    path('update/<int:trainer_id>', TrainerUpdateView.as_view(), name='trainer-detail'),
    path('specializations', TrainerSpecializationView.as_view(), name='trainer-specializations'),
    path('specializations/<int:specialization_id>', TrainerSpecializationUpdateView.as_view(), name='trainer-specialization-detail'),
    path('experiences', TrainerExperienceView.as_view(), name='trainer-experiences'),
    path('experiences/<int:experience_id>', TrainerExperienceUpdateView.as_view(), name='trainer-experience-detail'),
]
