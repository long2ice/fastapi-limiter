# fastapi-limiter

[![pypi](https://img.shields.io/pypi/v/fastapi-limiter.svg?style=flat)](https://pypi.python.org/pypi/fastapi-limiter)
[![license](https://img.shields.io/github/license/long2ice/fastapi-limiter)](https://github.com/long2ice/fastapi-limiter/blob/master/LICENCE)
[![workflows](https://github.com/long2ice/fastapi-limiter/workflows/pypi/badge.svg)](https://github.com/long2ice/fastapi-limiter/actions?query=workflow:pypi)
[![workflows](https://github.com/long2ice/fastapi-limiter/workflows/ci/badge.svg)](https://github.com/long2ice/fastapi-limiter/actions?query=workflow:ci)

## Introduction

FastAPI-Limiter is a rate limiting tool for [fastapi](https://github.com/tiangolo/fastapi) routes with lua script.

## Requirements

- [redis](https://redis.io/)

## Install

Just install from pypi

```shell script
> pip install fastapi-limiter
```

## Quick Start

FastAPI-Limiter is simple to use, which just provide a dependency `RateLimiter`, the following example allow `2` times
request per `5` seconds in route `/`.

```py
import redis.asyncio as redis
import uvicorn
from fastapi import Depends, FastAPI

from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

app = FastAPI()


@app.on_event("startup")
async def startup():
    redis_connection = redis.from_url("redis://localhost", encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis_connection)


@app.get("/", dependencies=[Depends(RateLimiter(times=2, seconds=5))])
async def index():
    return {"msg": "Hello World"}


if __name__ == "__main__":
    uvicorn.run("main:app", debug=True, reload=True)
```

## Usage

There are some config in `FastAPILimiter.init`.

### redis

The `redis` instance of `aioredis`.

### prefix

Prefix of redis key.

### identifier

Identifier of route limit, default is `ip`, you can override it such as `userid` and so on.

```py
async def default_identifier(request: Request):
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host + ":" + request.scope["path"]
```

### callback

Callback when access is forbidden, default is raise `HTTPException` with `429` status code.

```py
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
```

## Multiple limiters

You can use multiple limiters in one route.

```py
@app.get(
    "/multiple",
    dependencies=[
        Depends(RateLimiter(times=1, seconds=5)),
        Depends(RateLimiter(times=2, seconds=15)),
    ],
)
async def multiple():
    return {"msg": "Hello World"}
```

Not that you should note the dependencies orders, keep lower of result of `seconds/times` at the first.

## Rate limiting within a websocket.

While the above examples work with rest requests, FastAPI also allows easy usage
of websockets, which require a slightly different approach.

Because websockets are likely to be long lived, you may want to rate limit in
response to data sent over the socket.

You can do this by rate limiting within the body of the websocket handler:

```py
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ratelimit = WebSocketRateLimiter(times=1, seconds=5)
    while True:
        try:
            data = await websocket.receive_text()
            await ratelimit(websocket, context_key=data)  # NB: context_key is optional
            await websocket.send_text(f"Hello, world")
        except WebSocketRateLimitException:  # Thrown when rate limit exceeded.
            await websocket.send_text(f"Hello again")
```

## Lua script

The lua script used.

```lua
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local expire_time = ARGV[2]

local current = tonumber(redis.call('get', key) or "0")
if current > 0 then
    if current + 1 > limit then
        return redis.call("PTTL", key)
    else
        redis.call("INCR", key)
        return 0
    end
else
    redis.call("SET", key, 1, "px", expire_time)
    return 0
end
```

## License

This project is licensed under the
[Apache-2.0](https://github.com/long2ice/fastapi-limiter/blob/master/LICENCE) License.
