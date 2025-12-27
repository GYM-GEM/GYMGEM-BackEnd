from django.urls import re_path
from .consumers import InteractiveSessionConsumer

websocket_urlpatterns = [
    re_path(r"ws/interactive_sessions/(?P<session_id>\d+)/$", InteractiveSessionConsumer.as_asgi()),
]