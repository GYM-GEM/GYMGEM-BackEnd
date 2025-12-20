from .views import SessionAbortView, SessionListView, SessionCancelView, SessionRejectView, SessionRequestView , SessionAcceptView

from django.urls import path

urlpatterns = [
    path('request/', SessionRequestView.as_view(), name='interactive-session-request'),
    path('list/', SessionListView.as_view(), name='interactive-session-list'),
    path('accept/<int:session_id>/', SessionAcceptView.as_view(), name='interactive-session-accept'),
    path('abort/<int:session_id>/', SessionAbortView.as_view(), name='interactive-session-abort'),
    path('cancel/<int:session_id>/', SessionCancelView.as_view(), name='interactive-session-cancel'),
    path('reject/<int:session_id>/', SessionRejectView.as_view(), name='interactive-session-reject'),
]