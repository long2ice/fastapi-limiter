from math import ceil
from typing import Callable

import aioredis
from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_429_TOO_MANY_REQUESTS


async def default_identifier(request: Request):
#This code allows any requester to override the ratekey by sending the header X-Forwarded-For with any data and just use a random generator to never trip the ratelimiter
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
#################################################################
    return request.client.host + ":" + request.scope["path"]


async def default_callback(request: Request, response: Response, pexpire: int):
    """
    default callback when too many requests
    :param request:
    :param pexpire: The remaining milliseconds
    :param response:
    :return:
    """
    expire = ceil(pexpire / 1000)

    raise HTTPException(
        HTTP_429_TOO_MANY_REQUESTS, "Too Many Requests", headers={"Retry-After": str(expire)}
    )


class FastAPILimiter:
    redis: aioredis.Redis = None
    prefix: str = None
    identifier: Callable = None
    callback: Callable = None

    @classmethod
    def init(
        cls,
        redis: aioredis.Redis,
        prefix: str = "fastapi-limiter",
        identifier: Callable = default_identifier,
        callback: Callable = default_callback,
    ):
        cls.redis = redis
        cls.prefix = prefix
        cls.identifier = identifier
        cls.callback = callback
