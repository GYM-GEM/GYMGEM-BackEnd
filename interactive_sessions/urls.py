from .views import (
    SessionAbortView,
    SessionListView,
    SessionCancelView,
    SessionRejectView,
    SessionRequestView,
    SessionAcceptView,
    SessionStartView,
    SessionCompleteView,
    SessionDetailView
)

from django.urls import path

urlpatterns = [
    path('request/', SessionRequestView.as_view(), name='interactive-session-request'),
    path('list/', SessionListView.as_view(), name='interactive-session-list'),
    path('accept/<int:session_id>/', SessionAcceptView.as_view(), name='interactive-session-accept'),
    path('start/<int:session_id>/', SessionStartView.as_view(), name='interactive-session-start'),
    path('complete/<int:session_id>/', SessionCompleteView.as_view(), name='interactive-session-complete'),
    path('abort/<int:session_id>/', SessionAbortView.as_view(), name='interactive-session-abort'),
    path('cancel/<int:session_id>/', SessionCancelView.as_view(), name='interactive-session-cancel'),
    path('reject/<int:session_id>/', SessionRejectView.as_view(), name='interactive-session-reject'),
    path('detail/<int:session_id>/', SessionDetailView.as_view(), name='interactive-session-detail'),
]