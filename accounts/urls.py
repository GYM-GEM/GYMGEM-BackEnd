from django.urls import path
from .views import (
    AccountsListView,
    AccountsDetailView,
    AccountsVerifyView,
    CurrentAccountView,
    AccountsCreateView,
    AccountsPasswordChangeView,
    AccountsManageStatusView,
)

urlpatterns = [
    path('list', AccountsListView.as_view(), name='accounts-list'),

    #get , put , patch , delete account by id
    path('detail/<int:account_id>', AccountsDetailView.as_view(), name='accounts-detail'),
    path('current', CurrentAccountView.as_view(), name='current-account'),
    path('create', AccountsCreateView.as_view(), name='accounts-create'),
    path('change-password', AccountsPasswordChangeView.as_view(), name='accounts-change-password'),
    path('verify', AccountsVerifyView.as_view(), name='accounts-verify'),
    path('manage-status/<int:account_id>', AccountsManageStatusView.as_view(), name='accounts-manage-status'),
]
