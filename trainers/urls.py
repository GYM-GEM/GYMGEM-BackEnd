from django.urls import path
from .views import MyTrainerView, TrainerCalendarSlotView, TrainerCalendarSlotDetailView, TrainerView , TrainerUpdateView , TrainerSpecializationView, TrainerSpecializationUpdateView, TrainerExperienceUpdateView, TrainerExperienceView, TrainerListView, TrainerCalendarSlotDeleteView, TrainerRecordView
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'records', TrainerRecordView, basename='trainer-records')

urlpatterns = [
    path('create', TrainerView.as_view(), name='trainer'),
    path('list', TrainerListView.as_view(), name='trainer-list'),
    path('update', TrainerUpdateView.as_view(), name='trainer-detail'),
    path('specializations', TrainerSpecializationView.as_view(), name='trainer-specializations'),
    path('specializations/<int:specialization_id>', TrainerSpecializationUpdateView.as_view(), name='trainer-specialization-detail'),
    path('experiences', TrainerExperienceView.as_view(), name='trainer-experiences'),
    path('experiences/<int:experience_id>', TrainerExperienceUpdateView.as_view(), name='trainer-experience-detail'),
    path('calendar-slots/', TrainerCalendarSlotView.as_view(), name='trainer-calendar-slots'),
    path('calendar-slots/<int:slot_id>/', TrainerCalendarSlotDeleteView.as_view(), name='trainer-calendar-slot-detail'),
    path('calendar-slots/<int:profile_id>/detail/', TrainerCalendarSlotDetailView.as_view(), name='trainer-calendar-slot-detail-view'),
    path('my-records/', MyTrainerView.as_view(), name='trainer-my-records'),
]

urlpatterns += router.urls