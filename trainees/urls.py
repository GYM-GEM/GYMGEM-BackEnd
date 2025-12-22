from django.urls import path
from .views import TraineeRecordViewSet, TraineeView , TraineeUpdateView, TraineeDetailView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'records', TraineeRecordViewSet, basename='trainee-record')

urlpatterns = [
    path('create', TraineeView.as_view(), name='trainee-list'),
    path('update', TraineeUpdateView.as_view(), name='trainee-detail'),
    path('detail', TraineeDetailView.as_view(), name='trainee-detail'),
]

urlpatterns += router.urls

