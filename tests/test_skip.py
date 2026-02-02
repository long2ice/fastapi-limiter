from starlette.testclient import TestClient

from examples.main import app


def test_skip_limiter():
    with TestClient(app) as client:
        # Even with RateLimiter(times=1), skip_limiter allows unlimited requests
        for _ in range(5):
            response = client.get("/skip")
            assert response.status_code == 200
