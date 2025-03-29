from time import sleep
from unittest.mock import patch

from starlette.testclient import TestClient
import redis

from examples.main import app


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


def test_limiter_circuit_breaker():
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/circuit-breaker")
        assert response.status_code == 200

        response = client.get("/circuit-breaker")
        assert response.status_code == 429

        with patch("fastapi_limiter.FastAPILimiter.redis.evalsha", autospec=True) as mock_evalsha:
            mock_evalsha.side_effect = redis.exceptions.ConnectionError
            response = client.get("/circuit-breaker")
            assert response.status_code == 500

            # Circuit breaker triggered, rate limiting disabled

            response = client.get("/circuit-breaker")
            assert response.status_code == 200

        response = client.get("/circuit-breaker")
        assert response.status_code == 200

        response = client.get("/circuit-breaker")
        assert response.status_code == 200

        sleep(5)

        # retry after circuit breaker timeout
        response = client.get("/circuit-breaker")
        assert response.status_code == 200

        response = client.get("/circuit-breaker")
        assert response.status_code == 429



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
