from typing import Callable, Optional

from pydantic import conint
from starlette.requests import Request
from starlette.responses import Response

from fastapi_limiter import FastAPILimiter


class RateLimiter:
    def __init__(
        self,
        times: conint(ge=0) = 1,
        milliseconds: conint(ge=-1) = 0,
        seconds: conint(ge=-1) = 0,
        minutes: conint(ge=-1) = 0,
        hours: conint(ge=-1) = 0,
        identifier: Optional[Callable] = None,
        callback: Optional[Callable] = None,
    ):
        self.times = times
        self.milliseconds = milliseconds + 1000 * seconds + 60000 * minutes + 3600000 * hours
        self.identifier = identifier
        self.callback = callback

    async def __call__(self, request: Request, response: Response):
        if not FastAPILimiter.redis:
            raise Exception("You must call FastAPILimiter.init in startup event of fastapi!")
        index = 0
        for route in request.app.routes:
            if route.path == request.scope["path"]:
                for idx, dependency in enumerate(route.dependencies):
                    if self is dependency.dependency:
                        index = idx
                        break
        # moved here because constructor run before app startup
        identifier = self.identifier or FastAPILimiter.identifier
        callback = self.callback or FastAPILimiter.callback
        redis = FastAPILimiter.redis
        rate_key = await identifier(request)
        key = f"{FastAPILimiter.prefix}:{rate_key}:{index}"
        pexpire = await redis.evalsha(
            FastAPILimiter.lua_sha, keys=[key], args=[self.times, self.milliseconds]
        )
        if pexpire != 0:
            return await callback(request, response, pexpire)
