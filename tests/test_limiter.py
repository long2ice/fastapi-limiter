from time import sleep

import pytest
from fastapi import FastAPI
from pyrate_limiter import Duration, Limiter, Rate
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.testclient import TestClient
from starlette.websockets import WebSocket

from examples.main import app
from examples.middleware import app as middleware_app
from fastapi_limiter.depends import RateLimiter, WebSocketRateLimiter
from fastapi_limiter.middleware import RateLimiterMiddleware


@pytest.fixture(params=["sync", "async", "async_callable", "sync_awaitable"])
def callback(request):
    calls = []

    def sync_callback(*args):
        calls.append(args)
        return JSONResponse(
            {"detail": "Custom limit"},
            status_code=429,
            headers={"X-Callback": "called"},
        )

    async def async_callback(*args):
        return sync_callback(*args)

    class AsyncCallback:
        async def __call__(self, *args):
            return sync_callback(*args)

    def sync_awaitable_callback(*args):
        return async_callback(*args)

    callbacks = {
        "sync": sync_callback,
        "async": async_callback,
        "async_callable": AsyncCallback(),
        "sync_awaitable": sync_awaitable_callback,
    }
    return callbacks[request.param], calls


@pytest.fixture
def limiter():
    rate_limiter = Limiter(Rate(1, Duration.HOUR))
    yield rate_limiter
    rate_limiter.dispose(rate_limiter.buckets()[0])


@pytest.mark.asyncio
async def test_http_callback(callback, limiter):
    custom_callback, calls = callback
    request = Request({"type": "http", "path": "/callback", "headers": []})
    outgoing = Response()
    dependency = RateLimiter(limiter, callback=custom_callback)

    assert await dependency(request, outgoing) is None
    assert calls == []
    response = await dependency(request, outgoing)
    assert response.status_code == 429
    assert response.body == b'{"detail":"Custom limit"}'
    assert response.headers["X-Callback"] == "called"
    assert calls == [(request, outgoing)]


@pytest.mark.asyncio
async def test_websocket_callback(callback, limiter, mocker):
    custom_callback, calls = callback
    websocket = WebSocket(
        {"type": "websocket", "path": "/callback", "headers": []},
        receive=mocker.AsyncMock(),
        send=mocker.AsyncMock(),
    )
    dependency = WebSocketRateLimiter(limiter, callback=custom_callback)

    assert await dependency(websocket) is None
    assert calls == []
    response = await dependency(websocket)
    assert response.status_code == 429
    assert response.body == b'{"detail":"Custom limit"}'
    assert response.headers["X-Callback"] == "called"
    assert calls == [(websocket,)]


def test_middleware_callback(callback, limiter):
    custom_callback, calls = callback
    callback_app = FastAPI()
    handled = []
    callback_app.add_middleware(
        RateLimiterMiddleware, limiter=limiter, callback=custom_callback
    )

    @callback_app.get("/")
    async def index():
        handled.append(True)
        return {"ok": True}

    with TestClient(callback_app) as client:
        assert client.get("/").status_code == 200
        assert calls == []
        response = client.get("/")

    assert response.status_code == 429
    assert response.json() == {"detail": "Custom limit"}
    assert response.headers["X-Callback"] == "called"
    assert len(calls) == 1
    assert len(calls[0]) == 1
    assert isinstance(calls[0][0], Request)
    assert handled == [True]


def test_limiter():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200

        response = client.get("/")
        assert response.status_code == 200

        response = client.get("/")
        assert response.status_code == 429

        response = client.post("/")
        assert response.status_code == 200

        response = client.post("/")
        assert response.status_code == 429
        sleep(5)

        response = client.get("/")
        assert response.status_code == 200

        response = client.post("/")
        assert response.status_code == 200


def test_limiter_multiple():
    with TestClient(app) as client:
        response = client.get("/multiple")
        assert response.status_code == 200

        response = client.get("/multiple")
        assert response.status_code == 429
        sleep(5)

        response = client.get("/multiple")
        assert response.status_code == 200

        response = client.get("/multiple")
        assert response.status_code == 429
        sleep(10)

        response = client.get("/multiple")
        assert response.status_code == 200


def test_limiter_websockets():
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            ws.send_text("Hi")
            data = ws.receive_text()
            assert data == "Hello, world"

            ws.send_text("Hi")
            data = ws.receive_text()
            assert data == "Hello again"

            ws.send_text("Hi 2")
            data = ws.receive_text()
            assert data == "Hello again"
            ws.close()


def test_skip_limiter():
    with TestClient(app) as client:
        for _ in range(5):
            response = client.get("/skip")
            assert response.status_code == 200


def test_middleware():
    with TestClient(middleware_app) as client:
        response = client.get("/")
        assert response.status_code == 200

        response = client.get("/")
        assert response.status_code == 200

        # Global limit of 2 per 5s reached
        response = client.get("/")
        assert response.status_code == 429

        # Different path but same global limiter
        response = client.get("/other")
        assert response.status_code == 429

        sleep(5)

        response = client.get("/")
        assert response.status_code == 200
