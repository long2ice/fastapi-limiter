from pyrate_limiter import Limiter
from starlette.requests import Request
from starlette.responses import Response
from starlette.websockets import WebSocket

from fastapi_limiter.callback import default_callback
from fastapi_limiter.identifier import default_identifier


class _BaseRateLimiter:
    def __init__(
        self,
        limiter: Limiter,
        identifier=default_identifier,
        callback=default_callback,
        blocking: bool = False,
        skip=None,
    ):
        self.limiter = limiter
        self.identifier = identifier
        self.callback = callback
        self.blocking = blocking
        self.skip = skip


class RateLimiter(_BaseRateLimiter):
    async def __call__(self, request: Request, response: Response):
        if self.skip and await self.skip(request):
            return
        rate_key = await self.identifier(request)
        success = await self.limiter.try_acquire_async(rate_key, blocking=self.blocking)
        if not success:
            return await self.callback(request, response)


class WebSocketRateLimiter(_BaseRateLimiter):
    async def __call__(self, ws: WebSocket, context_key: str = ""):
        if self.skip and await self.skip(ws):
            return
        rate_key = await self.identifier(ws)
        key = f"{rate_key}:{context_key}"
        success = await self.limiter.try_acquire_async(key, blocking=self.blocking)
        if not success:
            return await self.callback(ws)
