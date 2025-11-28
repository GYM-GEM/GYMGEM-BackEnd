from django.urls import path
from .views import AccountsListView, AccountsDetailView, CurrentAccountView, AccountsCreateView

urlpatterns = [
    path('list', AccountsListView.as_view(), name='accounts-list'),

    #get , put , patch , delete account by id
    path('<int:account_id>/', AccountsDetailView.as_view(), name='accounts-detail'),
    path('current', CurrentAccountView.as_view(), name='current-account'),
    path('create', AccountsCreateView.as_view(), name='accounts-create'),
]
