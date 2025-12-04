from django.urls import path
from .views import StoreView , StoreUpdateView , StoreBranchView , StoreBranchUpdateView

urlpatterns = [
    path('create', StoreView.as_view(), name='store-list'),
    path('update/<int:store_id>', StoreUpdateView.as_view(), name='store-detail'),
    path('branches', StoreBranchView.as_view(), name='store-branches'),
    path('branches/<int:branch_id>', StoreBranchUpdateView.as_view(), name='store-branch-detail'),
]