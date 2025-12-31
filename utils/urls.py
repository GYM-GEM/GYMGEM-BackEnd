from django.urls import path
from .views import CategoryListView, SpecializationListView, SendComplaint, ComplaintStatusView, ComplaintUpdateView

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="categories-list"),
    path("specializations/", SpecializationListView.as_view(), name="specializations-list"),
    path("complaints/", SendComplaint.as_view(), name="complaint-create"),
    path("complaints/<int:complaint_id>/", ComplaintStatusView.as_view(), name="complaint-status"),
    path("complaints/<int:complaint_id>/update/", ComplaintUpdateView.as_view(), name="complaint-update"),
    
]
