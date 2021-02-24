# fastapi-limiter

[![pypi](https://img.shields.io/pypi/v/fastapi-limiter.svg?style=flat)](https://pypi.python.org/pypi/fastapi-limiter)
[![license](https://img.shields.io/github/license/long2ice/fastapi-limiter)](https://github.com/long2ice/fastapi-limiter/blob/master/LICENCE)
[![workflows](https://github.com/long2ice/fastapi-limiter/workflows/pypi/badge.svg)](https://github.com/long2ice/fastapi-limiter/actions?query=workflow:pypi)
[![workflows](https://github.com/long2ice/fastapi-limiter/workflows/ci/badge.svg)](https://github.com/long2ice/fastapi-limiter/actions?query=workflow:ci)

## Introduction

FastAPI-Limiter is a rate limiting tool for [fastapi](https://github.com/tiangolo/fastapi) routes.

## Requirements

- [redis](https://redis.io/)

## Install

Just install from pypi

```shell script
> pip install fastapi-limiter
```

## Quick Start

FastAPI-Limiter is simple to use, which just provide a dependency `RateLimiter`, the following example allow `2` times request per `5` seconds in route `/`.

```py
import aioredis
import uvicorn
from fastapi import Depends, FastAPI

from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

app = FastAPI()


@app.on_event("startup")
async def startup():
    redis = await aioredis.create_redis_pool("redis://localhost")
    FastAPILimiter.init(redis)


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
    return request.client.host
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

## License

This project is licensed under the
[Apache-2.0](https://github.com/long2ice/fastapi-limiter/blob/master/LICENCE) License.
