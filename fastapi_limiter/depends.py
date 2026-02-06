from typing import Callable

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
        identifier: Callable = default_identifier,
        callback: Callable = default_callback,
        blocking: bool = False,
    ):
        self.limiter = limiter
        self.identifier = identifier
        self.callback = callback
        self.blocking = blocking


class RateLimiter(_BaseRateLimiter):
    async def __call__(self, request: Request, response: Response):
        route_index = 0
        dep_index = 0
        for i, route in enumerate(request.app.routes):
            if (
                route.path == request.scope["path"]
                and hasattr(route, "methods")
                and request.method in route.methods
            ):
                route_index = i
                # Check if the route endpoint has _skip_limiter attribute
                if hasattr(route, "endpoint") and getattr(
                    route.endpoint, "_skip_limiter", False
                ):
                    return
                for j, dependency in enumerate(route.dependencies):
                    if self is dependency.dependency:
                        dep_index = j
                        break

        rate_key = await self.identifier(request)
        key = f"{rate_key}:{route_index}:{dep_index}"
        success = await self.limiter.try_acquire_async(key, blocking=self.blocking)
        if not success:
            return await self.callback(request, response)


class WebSocketRateLimiter(_BaseRateLimiter):
    async def __call__(self, ws: WebSocket, context_key: str = ""):
        rate_key = await self.identifier(ws)
        key = f"{rate_key}:{context_key}"
        success = await self.limiter.try_acquire_async(key, blocking=self.blocking)
        if not success:
            return await self.callback(ws)
