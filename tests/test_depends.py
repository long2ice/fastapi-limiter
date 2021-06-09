from time import sleep

from starlette.testclient import TestClient

from examples.main import app
from examples.main_disabled import app as app_disabled


def test_limiter():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200

        client.get("/")

        response = client.get("/")
        assert response.status_code == 429
        sleep(5)

        response = client.get("/")
        assert response.status_code == 200

def test_limiter_disabled():
    # Runs the same requests as test_limiter, but with RateLimiter disabled
    with TestClient(app_disabled) as client:
        response = client.get("/")
        assert response.status_code == 200

        client.get("/")

        response = client.get("/")
        assert response.status_code == 200
        sleep(5)

        response = client.get("/")
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

def test_limiter_multiple_disabled():
    # Runs the same requests as test_limiter_multiple, but with RateLimiter disabled
    with TestClient(app_disabled) as client:
        response = client.get("/multiple")
        assert response.status_code == 200

        response = client.get("/multiple")
        assert response.status_code == 200
        sleep(5)

        response = client.get("/multiple")
        assert response.status_code == 200

        response = client.get("/multiple")
        assert response.status_code == 200
        sleep(10)

        response = client.get("/multiple")
        assert response.status_code == 200
