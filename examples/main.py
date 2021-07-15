import aioredis
import uvicorn
from fastapi import Depends, FastAPI

from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

app = FastAPI()


@app.on_event("startup")
async def startup():
    redis = await aioredis.from_url("redis://localhost", encoding="utf8")
    await FastAPILimiter.init(redis)


@app.on_event("shutdown")
async def shutdown():
    await FastAPILimiter.close()


@app.get("/", dependencies=[Depends(RateLimiter(times=2, seconds=5))])
async def index():
    return {"msg": "Hello World"}


@app.get(
    "/multiple",
    dependencies=[
        Depends(RateLimiter(times=1, seconds=5)),
        Depends(RateLimiter(times=2, seconds=15)),
    ],
)
async def multiple():
    return {"msg": "Hello World"}


if __name__ == "__main__":
    uvicorn.run("main:app", debug=True, reload=True)
