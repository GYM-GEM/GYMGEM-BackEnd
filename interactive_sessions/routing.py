from .consumers import InteractiveSessionConsumer
from django.urls import path

websocket_urlpatterns = [
    path("ws/interactive_sessions/<int:session_id>/", InteractiveSessionConsumer.as_asgi()),
]