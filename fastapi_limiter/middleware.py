from typing import Coroutine

from pydantic import PositiveInt, conint
from starlette.types import ASGIApp, Receive, Scope, Send

from fastapi_limiter.utils import rate_func


class RateLimtMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        times: PositiveInt = 1,
        seconds: conint(ge=-1) = 0,
        minutes: conint(ge=-1) = 0,
        hours: conint(ge=-1) = 0,
        rate_func: Coroutine = rate_func,
    ) -> None:
        self.app = app
        self.times = times
        self.seconds = seconds + 60 * minutes + 3600 * hours
        self.rate_func = rate_func

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await self.app(scope, receive, send)
