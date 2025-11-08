from django.urls import path
from .views import AccountsListView, AccountsDetailView

urlpatterns = [
    path('', AccountsListView.as_view(), name='accounts-list'),
    path('<int:account_id>/', AccountsDetailView.as_view(), name='accounts-detail'),
]