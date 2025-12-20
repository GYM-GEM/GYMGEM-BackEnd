from django.urls import path
from .views import (
    StoreListView, StoreDetailView, StoreItemListView, StoreItemDetailView,
    OrderListView, OrderDetailView, OrderItemListView, OrderItemDetailView,
    StoreBranchView, StoreBranchUpdateView
)

urlpatterns = [
    # Store endpoints
    path('', StoreListView.as_view(), name='store-list'),
    path('<int:store_id>', StoreDetailView.as_view(), name='store-detail'),
    
    # StoreBranch endpoints
    path('branches', StoreBranchView.as_view(), name='store-branches'),
    path('branches/<int:branch_id>', StoreBranchUpdateView.as_view(), name='store-branch-detail'),
    
    # Store Item endpoints
    path('items', StoreItemListView.as_view(), name='store-item-list'),
    path('items/<int:item_id>', StoreItemDetailView.as_view(), name='store-item-detail'),
    
    # Order endpoints
    path('orders', OrderListView.as_view(), name='order-list'),
    path('orders/<int:order_id>', OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:order_id>/items', OrderItemListView.as_view(), name='order-item-list'),
    path('orders/items/<int:order_item_id>', OrderItemDetailView.as_view(), name='order-item-detail'),
    
]

