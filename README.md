# fastapi-limiter

[![pypi](https://img.shields.io/pypi/v/fastapi-limiter.svg?style=flat)](https://pypi.python.org/pypi/fastapi-limiter)
[![license](https://img.shields.io/github/license/long2ice/fastapi-limiter)](https://github.com/long2ice/fastapi-limiter/blob/master/LICENCE)
[![workflows](https://github.com/long2ice/fastapi-limiter/workflows/pypi/badge.svg)](https://github.com/long2ice/fastapi-limiter/actions?query=workflow:pypi)
[![workflows](https://github.com/long2ice/fastapi-limiter/workflows/ci/badge.svg)](https://github.com/long2ice/fastapi-limiter/actions?query=workflow:ci)

## Introduction

FastAPI-Limiter is a rate limiting tool for [fastapi](https://github.com/tiangolo/fastapi) routes, powered by [pyrate-limiter](https://github.com/vutran1710/PyrateLimiter).

## Install

Just install from pypi

```shell script
> pip install fastapi-limiter
```

## Quick Start

FastAPI-Limiter is simple to use, which just provides a dependency `RateLimiter`. The following example allows `2` requests per `5` seconds on route `/`.

```py
import uvicorn
from fastapi import Depends, FastAPI
from pyrate_limiter import Duration, Limiter, Rate

from fastapi_limiter.depends import RateLimiter

app = FastAPI()

@app.get(
    "/",
    dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(2, Duration.SECOND * 5))))],
)
async def index():
    return {"msg": "Hello World"}


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
```

## Usage

### RateLimiter

`RateLimiter` accepts the following parameters:

- `limiter`: A `pyrate_limiter.Limiter` instance that defines the rate limiting rules.
- `identifier`: A callable to identify the request source, default is by IP + path.
- `callback`: A callable invoked when the rate limit is exceeded, default raises `HTTPException` with `429` status code.
- `blocking`: Whether to block the request when the rate limit is exceeded, default is `False`.

### identifier

Identifier of route limit, default is `ip + path`, you can override it such as `userid` and so on.

```py
async def default_identifier(request: Union[Request, WebSocket]):
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0]
    elif request.client:
        ip = request.client.host
    else:
        ip = "127.0.0.1"
    return ip + ":" + request.scope["path"]
```

### callback

Callback when rate limit is exceeded, default raises `HTTPException` with `429` status code.

```py
def default_callback(*args, **kwargs):
    raise HTTPException(
        HTTP_429_TOO_MANY_REQUESTS,
        "Too Many Requests",
    )
```

## Multiple limiters

You can use multiple limiters in one route.

```py
@app.get(
    "/multiple",
    dependencies=[
        Depends(RateLimiter(limiter=Limiter(Rate(1, Duration.SECOND * 5)))),
        Depends(RateLimiter(limiter=Limiter(Rate(2, Duration.SECOND * 15)))),
    ],
)
async def multiple():
    return {"msg": "Hello World"}
```

Note that you should keep the stricter limiter (lower `seconds/times` ratio) first.

## Skip rate limiting

You can use the `skip_limiter` decorator to skip rate limiting for a specific route.

```py
from fastapi_limiter.decorators import skip_limiter

@app.get(
    "/skip",
    dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(1, Duration.SECOND * 5))))],
)
@skip_limiter
async def skip_route():
    return {"msg": "This route skips rate limiting"}
```

## Rate limiting within a websocket

While the above examples work with REST requests, FastAPI also allows easy usage
of websockets, which require a slightly different approach.

Because websockets are likely to be long lived, you may want to rate limit in
response to data sent over the socket.

You can do this by rate limiting within the body of the websocket handler:

```py
from fastapi_limiter.depends import WebSocketRateLimiter

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ratelimit = WebSocketRateLimiter(limiter=Limiter(Rate(1, Duration.SECOND * 5)))
    while True:
        try:
            data = await websocket.receive_text()
            await ratelimit(websocket, context_key=data)  # NB: context_key is optional
            await websocket.send_text("Hello, world")
        except HTTPException:
            await websocket.send_text("Hello again")
```

## License

This project is licensed under the
[Apache-2.0](https://github.com/long2ice/fastapi-limiter/blob/master/LICENCE) License.
