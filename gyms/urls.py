from django.urls import path
from .views import StoreView, GymUpdateView, GymBranchView , GymBranchUpdateView

urlpatterns = [
    path('gyms', StoreView.as_view(), name='gym-list'),     
    path('gyms/<int:gym_id>', GymUpdateView.as_view(), name='gym-detail'),
    path('gym-branches', GymBranchView.as_view(), name='gym-branch-list'),
    path('gym-branches/<int:branch_id>', GymBranchUpdateView.as_view(), name='gym-branch-detail'),
]