import os
import django
# from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import app.routing
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")
django.setup()

application = ProtocolTypeRouter({
    # "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        URLRouter(
            app.routing.websocket_urlpatterns
        )
    ),
})
