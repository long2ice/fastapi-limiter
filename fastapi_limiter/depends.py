from typing import Callable, Optional

from pydantic import conint
from starlette.requests import Request
from starlette.responses import Response

from fastapi_limiter import FastAPILimiter


class RateLimiter:
    def __init__(
        self,
        times: conint(ge=0) = 1,
        seconds: conint(ge=-1) = 0,
        minutes: conint(ge=-1) = 0,
        hours: conint(ge=-1) = 0,
        identifier: Optional[Callable] = None,
        callback: Optional[Callable] = None,
    ):
        self.times = times
        self.seconds = seconds + 60 * minutes + 3600 * hours
        self.identifier = identifier
        self.callback = callback

    async def __call__(self, request: Request, response: Response):
        if not FastAPILimiter.redis:
            raise Exception("You must call FastAPILimiter.init in startup event of fastapi!")
        # moved here because constructor run before app startup
        identifier = self.identifier or FastAPILimiter.identifier
        callback = self.callback or FastAPILimiter.callback
        redis = FastAPILimiter.redis
        rate_key = await identifier(request)
        key = FastAPILimiter.prefix + ":" + rate_key
        p = redis.pipeline()
        p.incrby(key, 1)
        p.ttl(key)
        num, expire = await p.execute()
        if num == 1:
            await redis.expire(key, self.seconds)
        if num > self.times:
            return await callback(request, expire)
