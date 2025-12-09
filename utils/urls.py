from django.urls import path
from .views import CategoryListView, SpecializationListView

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="categories-list"),
    path("specializations/", SpecializationListView.as_view(), name="specializations-list"),
]
