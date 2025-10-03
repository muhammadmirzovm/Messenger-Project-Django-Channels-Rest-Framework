# dcrf_messenger/asgi.py
import os

# ✅ 1. Setup settings before importing Django or DRF
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dcrf_messenger.settings")

# ✅ 2. Initialize Django before importing routing / DRF
import django
django.setup()

# ✅ 3. Now safe to import Django/Channels/your routing
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chat.routing

# ✅ 4. Build ASGI app
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(chat.routing.websocket_urlpatterns)
    ),
})
