from django.urls import re_path
from reports.consumers import UpdateNotif

websocket_urlpatterns = [
    re_path(r'^ws/notif_(?P<user_id>\d+)/$', UpdateNotif.as_asgi()),
    # re_path(r'^ws/login/(?P<client_id>\w+)/?$', LoginUser.as_asgi()),
]
