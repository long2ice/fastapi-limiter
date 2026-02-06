from time import sleep

from starlette.testclient import TestClient

from examples.main import app
from examples.middleware import app as middleware_app


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
