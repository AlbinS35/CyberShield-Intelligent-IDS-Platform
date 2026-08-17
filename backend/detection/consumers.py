"""
Django Channels WebSocket Consumer
Streams real-time alerts to authenticated analyst dashboards.
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger("cybershield.consumers")


class AlertConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for live alert streaming.

    Connection: ws://host/ws/alerts/?token=<JWT_ACCESS_TOKEN>
    Each tenant gets its own broadcast group: alerts_<tenant_id>

    Events:
        alert.new   → new Alert created (broadcast to group)
        ping        → keepalive (echoes pong)
    """

    async def connect(self):
        """Authenticate JWT token and join tenant broadcast group."""
        user = await self._get_authenticated_user()
        if not user or not user.is_authenticated or not user.tenant_id:
            await self.close(code=4001)
            return

        self.user = user
        self.tenant_id = str(user.tenant_id)
        self.group_name = f"alerts_{self.tenant_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        logger.info(f"WS connected: {user.email} → group {self.group_name}")
        await self.send(text_data=json.dumps({
            "type": "connection_established",
            "message": f"Connected to live alert feed for tenant {self.tenant_id}",
        }))

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            logger.info(f"WS disconnected: group {self.group_name}")

    async def receive(self, text_data):
        """Handle client-side messages (keepalive ping)."""
        try:
            data = json.loads(text_data)
            if data.get("type") == "ping":
                await self.send(text_data=json.dumps({"type": "pong"}))
        except json.JSONDecodeError:
            pass

    async def alert_new(self, event):
        """Handler for alert.new group message — broadcast to WebSocket client."""
        await self.send(text_data=json.dumps({
            "type": "alert.new",
            "alert": event["alert"],
        }))

    @database_sync_to_async
    def _get_authenticated_user(self):
        """Extract and validate JWT token from query string or cookies."""
        from urllib.parse import parse_qs
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.exceptions import TokenError
        from authentication.models import User
        from django.http import SimpleCookie

        query_string = self.scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        token_list = params.get("token", [])
        token_str = token_list[0] if token_list else None

        # Fallback to cookie
        if not token_str or token_str == "null" or token_str == "undefined":
            headers = dict(self.scope.get("headers", []))
            cookie_header = headers.get(b"cookie", b"").decode()
            if cookie_header:
                cookie = SimpleCookie()
                cookie.load(cookie_header)
                if "access_token" in cookie:
                    token_str = cookie["access_token"].value

        if not token_str or token_str == "null" or token_str == "undefined":
            return None
        try:
            token = AccessToken(token_str)
            user_id = token.get("user_id")
            return User.objects.select_related("tenant").get(id=user_id, is_active=True)
        except (TokenError, User.DoesNotExist, Exception):
            return None
