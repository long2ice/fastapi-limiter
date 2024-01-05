from time import sleep

import pytest
from starlette.testclient import TestClient

from examples.main import app
from fastapi_limiter.depends import RateLimiter


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
            assert data == "Hello, world"
            ws.close()


@pytest.mark.parametrize(
    ("eq_left", "eq_right", "neq_left1", "neq_right1", "neq_left2", "neq_right2"),
    [
        (
            RateLimiter(times=1, milliseconds=5),
            RateLimiter(times=1, milliseconds=5),
            RateLimiter(times=1, milliseconds=5),
            RateLimiter(times=2, milliseconds=5),
            RateLimiter(times=1, milliseconds=5),
            RateLimiter(times=1, milliseconds=10),
        ),
        (
            RateLimiter(times=1, seconds=5),
            RateLimiter(times=1, seconds=5),
            RateLimiter(times=1, seconds=5),
            RateLimiter(times=2, seconds=5),
            RateLimiter(times=1, seconds=5),
            RateLimiter(times=1, seconds=10),
        ),
        (
            RateLimiter(times=1, minutes=5),
            RateLimiter(times=1, minutes=5),
            RateLimiter(times=1, minutes=5),
            RateLimiter(times=2, minutes=5),
            RateLimiter(times=1, minutes=5),
            RateLimiter(times=1, minutes=10),
        ),
        (
            RateLimiter(times=1, hours=5),
            RateLimiter(times=1, hours=5),
            RateLimiter(times=1, hours=5),
            RateLimiter(times=2, hours=5),
            RateLimiter(times=1, hours=5),
            RateLimiter(times=1, hours=10),
        ),
    ],
)
def test_limiter_equality(eq_left, eq_right, neq_left1, neq_right1, neq_left2, neq_right2):
    assert hash(eq_left) == hash(eq_right)
    assert eq_left == eq_right
    assert hash(neq_left1) != hash(neq_right1)
    assert neq_left1 != neq_right1
    assert hash(neq_left2) != hash(neq_right2)
    assert neq_left2 != neq_right2
