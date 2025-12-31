from django.urls import path
from .views import ProfileView, ProfileUpdateView, ProfileBalanceView, ProfileAdminView,ProfileBalanceAdminView,ProfileHideToggleView,ProfilesAdminListView,CashoutReportAdminView,CashoutReportAdminDetailView

urlpatterns = [
    path('create', ProfileView.as_view(), name='profile-list'),
    path('update/<int:profile_id>', ProfileUpdateView.as_view(), name='profile-detail'),
    path('balance', ProfileBalanceView.as_view(), name='profile-balance'),
    path('admin/<int:profile_id>', ProfileAdminView.as_view(), name='profile-admin-detail'),
    path('admin/balance/<int:profile_id>', ProfileBalanceAdminView.as_view(), name='profile-admin-balance'),
    path('admin/toggle-hide/<int:profile_id>', ProfileHideToggleView.as_view(), name='profile-admin-toggle-hide'),
    path('admin/list', ProfilesAdminListView.as_view(), name='profiles-admin-list'),
    path('admin/cashout-reports', CashoutReportAdminView.as_view(), name='cashout-reports-admin-list'),
    path('admin/cashout-reports/<int:report_id>', CashoutReportAdminDetailView.as_view(), name='cashout-report-admin-detail'),
]   
