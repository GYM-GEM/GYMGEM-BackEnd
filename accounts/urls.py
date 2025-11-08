from django.urls import path
from .views import AccountsView

urlpatterns = [
    path('', AccountsView.as_view(), name='accounts-list'),
    path('<int:account_id>/', AccountsView.as_view(), name='accounts-detail'),
]