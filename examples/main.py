import redis.asyncio as redis
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, WebSocket

from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter, WebSocketRateLimiter

app = FastAPI()


@app.on_event("startup")
async def startup():
    r = redis.from_url("redis://localhost", encoding="utf8")
    await FastAPILimiter.init(r)


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


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ratelimit = WebSocketRateLimiter(times=1, seconds=5)
    while True:
        try:
            data = await websocket.receive_text()
            await ratelimit(websocket, context_key=data)  # NB: context_key is optional
            await websocket.send_text("Hello, world")
        except HTTPException:
            await websocket.send_text("Hello again")


if __name__ == "__main__":
    uvicorn.run("main:app", debug=True, reload=True)
