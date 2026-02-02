from functools import wraps
from typing import Callable


def skip_limiter(func: Callable) -> Callable:
    """
    Decorator to skip rate limiting for a specific route.

    Usage:
        @app.get("/health")
        @skip_limiter
        async def health():
            return {"status": "ok"}
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)

    wrapper._skip_limiter = True  # type: ignore
    return wrapper
