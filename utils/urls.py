from django.urls import path
from .views import CategoryListView, SpecializationListView, SendComplaint, ComplaintStatusView, ComplaintUpdateView,CompaintAdminListView

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="categories-list"),
    path("specializations/", SpecializationListView.as_view(), name="specializations-list"),
    path("complaints/", SendComplaint.as_view(), name="complaint-create"),
    path("complaints/", ComplaintStatusView.as_view(), name="complaint-status"),
    path("complaints/<int:complaint_id>/update/", ComplaintUpdateView.as_view(), name="complaint-update"),
    path("admin/complaints/", CompaintAdminListView.as_view(), name="admin-complaint-list"),
]
