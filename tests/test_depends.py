from time import sleep

from starlette.testclient import TestClient

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


def test_limiter_sliding_window():
    with TestClient(app) as client:
        def req(sleep_times, assert_code):
            nonlocal client
            response = client.get("/test_sliding_window")
            assert response.status_code == assert_code
            sleep(sleep_times)
        
        req(4, 200) # 0s
        req(1, 200) # 4s
        req(1, 200) # 5s
        req(1, 429) # 6s
        req(1, 429) # 7s
        req(1, 429) # 8s
        req(1, 200) # 9s