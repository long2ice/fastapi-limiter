from math import ceil
from typing import Callable, Optional, Union

from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
from starlette.websockets import WebSocket

try:
    from importlib.metadata import version as get_version
except ImportError:
    from importlib_metadata import version as get_version


async def default_identifier(request: Union[Request, WebSocket]):
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0]
    else:
        ip = request.client.host
    return ip + ":" + request.scope["path"]


async def http_default_callback(request: Request, response: Response, pexpire: int):
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


async def ws_default_callback(ws: WebSocket, pexpire: int):
    """
    default callback when too many requests
    :param ws:
    :param pexpire: The remaining milliseconds
    :return:
    """
    expire = ceil(pexpire / 1000)
    raise HTTPException(
        HTTP_429_TOO_MANY_REQUESTS, "Too Many Requests", headers={"Retry-After": str(expire)}
    )


class FastAPILimiter:
    redis = None
    prefix: Optional[str] = None
    lua_sha: Optional[str] = None
    identifier: Optional[Callable] = None
    http_callback: Optional[Callable] = None
    ws_callback: Optional[Callable] = None
    lua_script = """local key = KEYS[1]
local limit = tonumber(ARGV[1])
local expire_time = ARGV[2]

local current = tonumber(redis.call('get', key) or "0")
if current > 0 then
 if current + 1 > limit then
 return redis.call("PTTL",key)
 else
        redis.call("INCR", key)
 return 0
 end
else
    redis.call("SET", key, 1,"px",expire_time)
 return 0
end"""

    @classmethod
    def _add_driver_info(cls, redis) -> None:
        """Add driver identification to Redis connection.

        Uses DriverInfo class if available, or falls back to
        lib_name/lib_version for older versions.
        """
        from typing import Any

        # Get fastapi-limiter version
        try:
            limiter_version = get_version("fastapi-limiter")
        except Exception:
            limiter_version = "unknown"

        # Get connection pool from the redis client
        connection_pool: Any = getattr(redis, "connection_pool", None)
        if connection_pool is None:
            return

        # Try to use DriverInfo class
        try:
            from redis import DriverInfo

            driver_info = DriverInfo().add_upstream_driver("fastapi-limiter", limiter_version)
            connection_pool.connection_kwargs["driver_info"] = driver_info
        except (ImportError, AttributeError):
            # Fallback: use lib_name/lib_version
            # Format: lib_name='redis-py(fastapi-limiter_v{version})'
            connection_pool.connection_kwargs["lib_name"] = (
                f"redis-py(fastapi-limiter_v{limiter_version})"
            )
            # lib_version should be the redis client version
            try:
                import redis

                redis_version = redis.__version__
            except (ImportError, AttributeError):
                redis_version = "unknown"
            connection_pool.connection_kwargs["lib_version"] = redis_version

    @classmethod
    async def init(
        cls,
        redis,
        prefix: str = "fastapi-limiter",
        identifier: Callable = default_identifier,
        http_callback: Callable = http_default_callback,
        ws_callback: Callable = ws_default_callback,
    ) -> None:
        cls.redis = redis
        cls.prefix = prefix
        cls.identifier = identifier
        cls.http_callback = http_callback
        cls.ws_callback = ws_callback
        cls._add_driver_info(redis)
        cls.lua_sha = await redis.script_load(cls.lua_script)

    @classmethod
    async def close(cls) -> None:
        await cls.redis.close()
