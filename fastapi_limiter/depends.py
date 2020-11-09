from typing import Callable

from pydantic import conint
from starlette.requests import Request

from fastapi_limiter import FastAPILimiter, default_callback, default_identifier


class RateLimiter:
    def __init__(
        self,
        times: conint(ge=0) = 1,
        seconds: conint(ge=-1) = 0,
        minutes: conint(ge=-1) = 0,
        hours: conint(ge=-1) = 0,
        identifier: Callable = default_identifier,
        callback: Callable = default_callback,
    ):
        self.times = times
        self.seconds = seconds + 60 * minutes + 3600 * hours
        self.identifier = identifier or FastAPILimiter.identifier
        self.callback = callback or FastAPILimiter.callback

    async def __call__(self, request: Request):
        if not FastAPILimiter.redis:
            raise Exception("You must call FastAPILimiter.init in startup event of fastapi!")
        redis = FastAPILimiter.redis
        rate_key = await self.identifier(request)
        key = FastAPILimiter.prefix + ":" + rate_key
        num = await redis.incrby(key, 1)
        if num == 1:
            await redis.expire(key, self.seconds)
        if num > self.times:
            return await self.callback(request)
