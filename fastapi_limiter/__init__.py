from typing import Callable

import aioredis
from fastapi import HTTPException
from starlette.requests import Request
from starlette.status import HTTP_403_FORBIDDEN


async def default_identifier(request: Request):
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host


async def default_callback(request: Request):
    raise HTTPException(HTTP_403_FORBIDDEN, "The request is frequent")


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
