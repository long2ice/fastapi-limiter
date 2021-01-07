from time import sleep

from starlette.testclient import TestClient

from examples.main import app


def test_limiter():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"msg": "Hello World"}

        client.get("/")

        response = client.get("/")
        assert response.status_code == 429
        sleep(5)

        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"msg": "Hello World"}
