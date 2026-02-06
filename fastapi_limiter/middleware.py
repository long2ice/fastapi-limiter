from fastapi import status
from pyrate_limiter import Limiter
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from fastapi_limiter.identifier import default_identifier


async def _default_middleware_callback(request: Request) -> Response:
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Too Many Requests"},
    )


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        limiter: Limiter,
        identifier=default_identifier,
        callback=_default_middleware_callback,
        blocking: bool = False,
        skip=None,
    ):
        super().__init__(app)
        self.limiter = limiter
        self.identifier = identifier
        self.callback = callback
        self.blocking = blocking
        self.skip = skip

    async def dispatch(self, request: Request, call_next):
        if self.skip and await self.skip(request):
            return await call_next(request)
        rate_key = await self.identifier(request)
        success = await self.limiter.try_acquire_async(rate_key, blocking=self.blocking)
        if not success:
            return await self.callback(request)

        return await call_next(request)
