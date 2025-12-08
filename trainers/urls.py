from django.urls import path
from .views import TrainerCalendarSlotView, TrainerCalendarSlotDetailView, TrainerView , TrainerUpdateView , TrainerSpecializationView, TrainerSpecializationUpdateView, TrainerExperienceUpdateView, TrainerExperienceView, TrainerListView

urlpatterns = [
    path('create', TrainerView.as_view(), name='trainer'),
    path('list', TrainerListView.as_view(), name='trainer-list'),
    path('update/<int:trainer_id>', TrainerUpdateView.as_view(), name='trainer-detail'),
    path('specializations', TrainerSpecializationView.as_view(), name='trainer-specializations'),
    path('specializations/<int:specialization_id>', TrainerSpecializationUpdateView.as_view(), name='trainer-specialization-detail'),
    path('experiences', TrainerExperienceView.as_view(), name='trainer-experiences'),
    path('experiences/<int:experience_id>', TrainerExperienceUpdateView.as_view(), name='trainer-experience-detail'),
    path('calendar-slots', TrainerCalendarSlotView.as_view(), name='trainer-calendar-slots'),
    path('calendar-slots/<int:slot_id>', TrainerCalendarSlotDetailView.as_view(), name='trainer-calendar-slot-detail'),
]
