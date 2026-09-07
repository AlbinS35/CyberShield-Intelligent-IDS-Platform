"""
WebSocket URL routing for CyberShield Django Channels.
Provides real-time alert streaming per tenant group.
"""

from django.urls import re_path
from detection.consumers import AlertConsumer

websocket_urlpatterns = [
    # Live alert feed: ws://host/ws/alerts/?token=<JWT>
    re_path(r"ws/alerts/$", AlertConsumer.as_asgi()),
]
