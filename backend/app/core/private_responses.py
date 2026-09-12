"""Prevent intermediary and browser caches from retaining account API responses."""
from starlette.datastructures import MutableHeaders


class PrivateApiResponses:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope["path"].startswith(("/api/", "/sse/")):
            return await self.app(scope, receive, send)

        async def private_send(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["Cache-Control"] = "private, no-store"
                headers.add_vary_header("Authorization")
            await send(message)

        await self.app(scope, receive, private_send)
