# chat/routing.py
from django.urls import re_path
from .consumers import ChatConsumer, PresenceConsumer, RoomPresenceConsumer

websocket_urlpatterns = [
    # your DCRF chat endpoint (as used in your templates)
    re_path(r"^ws/chat/room/$", ChatConsumer.as_asgi()),

    # NEW presence endpoints
    re_path(r"^ws/presence/$", PresenceConsumer.as_asgi()),
    re_path(r"^ws/room/(?P<room_id>\d+)/presence/$", RoomPresenceConsumer.as_asgi()),
]
