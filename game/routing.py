from django.urls import re_path
from django.conf import settings
from . import consumers

if settings.PRODUCTION_WEBSOCKET_URLS:
    websocket_urlpatterns = [
        re_path(r"^so-long-sucker/ws/lobby/$", consumers.LobbyConsumer.as_asgi()),
        re_path(r"^so-long-sucker/ws/game/(?P<game_id>\d+)/$", consumers.GameConsumer.as_asgi()),
    ]
else:
    websocket_urlpatterns = [
        re_path(r"^so-long-sucker/ws/lobby/$", consumers.LobbyConsumer.as_asgi()),
        re_path(r"^so-long-sucker/ws/game/(?P<game_id>\d+)/$", consumers.GameConsumer.as_asgi()),
    ]
