from fastapi import HTTPException
from starlette.status import HTTP_429_TOO_MANY_REQUESTS


def default_callback(*args, **kwargs):
    raise HTTPException(
        HTTP_429_TOO_MANY_REQUESTS,
        "Too Many Requests",
    )
