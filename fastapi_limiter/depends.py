from typing import Coroutine

from pydantic import PositiveInt, conint
from starlette.requests import Request

from fastapi_limiter.utils import rate_func


class RateLimter:
    rate_limit = "fastapi-limiter:{rate_key}"

    def __init__(
        self,
        times: PositiveInt = 1,
        seconds: conint(ge=-1) = 0,
        minutes: conint(ge=-1) = 0,
        hours: conint(ge=-1) = 0,
        rate_func: Coroutine = rate_func,
    ):
        self.times = times
        self.seconds = seconds + 60 * minutes + 3600 * hours
        self.rate_func = rate_func

    async def __call__(self, request: Request):
        rate_key = await self.rate_func(request)
        key = self.rate_limit.format(rate_key=rate_key)
