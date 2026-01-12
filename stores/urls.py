from django.urls import path
from .views import (
    StoreListView,
    StoreDetailView,
    StoreItemListView,
    StoreItemDetailView,
    OrderListView,
    OrderDetailView,
    OrderItemListView,
    OrderItemDetailView,
    StoreBranchView,
    PublicStoreBranchView,
    StoreBranchUpdateView,
    MyStoreItemListView,
    ClientOrderListView,
)

urlpatterns = [
    # Store
    path("", StoreListView.as_view(), name="store-list"),
    path("<int:profile_id>", StoreDetailView.as_view(), name="store-detail"),
    # StoreBranch
    path("branches/", StoreBranchView.as_view(), name="store-branches"),
    path(
        "branches/public/",
        PublicStoreBranchView.as_view(),
        name="public-store-branches",
    ),
    path(
        "branches/<int:branch_id>/",
        StoreBranchUpdateView.as_view(),
        name="store-branch-detail",
    ),
    # Store Item
    path("items", StoreItemListView.as_view(), name="store-item-list"),
    path("my-items", MyStoreItemListView.as_view(), name="my-store-item-list"),
    path(
        "items/<int:item_id>", StoreItemDetailView.as_view(), name="store-item-detail"
    ),
    # Order
    path("orders", OrderListView.as_view(), name="order-list"),
    path("my-orders", ClientOrderListView.as_view(), name="client-order-list"),
    path("orders/<int:order_id>", OrderDetailView.as_view(), name="order-detail"),
    path(
        "orders/<int:order_id>/items",
        OrderItemListView.as_view(),
        name="order-item-list",
    ),
    path(
        "orders/items/<int:order_item_id>",
        OrderItemDetailView.as_view(),
        name="order-item-detail",
    ),
]
