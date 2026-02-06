import uvicorn
from fastapi import Depends, FastAPI, HTTPException, WebSocket
from pyrate_limiter import Duration, Limiter, Rate
from starlette.websockets import WebSocketDisconnect

from fastapi_limiter.decorators import skip_limiter
from fastapi_limiter.depends import RateLimiter, WebSocketRateLimiter

app = FastAPI()


@app.get(
    "/",
    dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(2, Duration.SECOND * 5))))],
)
async def index_get():
    return {"msg": "Hello World"}


@app.post(
    "/",
    dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(1, Duration.SECOND * 5))))],
)
async def index_post():
    return {"msg": "Hello World"}


@app.get(
    "/multiple",
    dependencies=[
        Depends(RateLimiter(limiter=Limiter(Rate(1, Duration.SECOND * 5)))),
        Depends(RateLimiter(limiter=Limiter(Rate(2, Duration.SECOND * 15)))),
    ],
)
async def multiple():
    return {"msg": "Hello World"}


@app.get(
    "/skip",
    dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(1, Duration.SECOND * 5))))],
)
@skip_limiter
async def skip_route():
    return {"msg": "This route skips rate limiting"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ratelimit = WebSocketRateLimiter(limiter=Limiter(Rate(1, Duration.SECOND * 5)))
    while True:
        try:
            data = await websocket.receive_text()
            await ratelimit(websocket, context_key=data)  # NB: context_key is optional
            await websocket.send_text("Hello, world")
        except WebSocketDisconnect:
            break
        except HTTPException:
            await websocket.send_text("Hello again")


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
