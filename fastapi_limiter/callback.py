from inspect import isawaitable

from fastapi import HTTPException
from starlette.status import HTTP_429_TOO_MANY_REQUESTS


async def _run_callback(callback, *args):
    result = callback(*args)
    if isawaitable(result):
        return await result
    return result


def default_callback(*args, **kwargs):
    raise HTTPException(
        HTTP_429_TOO_MANY_REQUESTS,
        "Too Many Requests",
    )
