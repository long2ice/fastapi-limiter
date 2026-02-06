import uvicorn
from fastapi import FastAPI
from fastapi.requests import Request
from pyrate_limiter import Duration, Limiter, Rate

from fastapi_limiter.middleware import RateLimiterMiddleware

app = FastAPI()


async def skip(request: Request):
    return request.scope["path"] == "/skip"


app.add_middleware(
    RateLimiterMiddleware,
    limiter=Limiter(Rate(2, Duration.SECOND * 5)),
    skip=skip,
)


@app.get("/")
async def index():
    return {"msg": "Hello World"}


@app.get("/other")
async def other():
    return {"msg": "Other"}


@app.get("/skip")
async def skip_route():
    return {"msg": "This route skips rate limiting"}


if __name__ == "__main__":
    uvicorn.run("middleware:app", reload=True)
