from typing import Annotated, Callable, Optional
import time

import redis as pyredis
from pydantic import Field
from starlette.requests import Request
from starlette.responses import Response
from starlette.websockets import WebSocket

from fastapi_limiter import FastAPILimiter


class RateLimiter:
    def __init__(
        self,
        times: Annotated[int, Field(ge=0)] = 1,
        milliseconds: Annotated[int, Field(ge=-1)] = 0,
        seconds: Annotated[int, Field(ge=-1)] = 0,
        minutes: Annotated[int, Field(ge=-1)] = 0,
        hours: Annotated[int, Field(ge=-1)] = 0,
        identifier: Optional[Callable] = None,
        callback: Optional[Callable] = None,
        circuit_breaker: Optional[tuple[int, int]] = None,
    ):
        self.times = times
        self.milliseconds = milliseconds + 1000 * seconds + 60000 * minutes + 3600000 * hours
        self.identifier = identifier
        self.callback = callback
        self.circuit_breaker = circuit_breaker is not None
        self.failure_threshold = circuit_breaker[0] if circuit_breaker else None
        self.recovery_seconds = circuit_breaker[1] if circuit_breaker else None
        self._failure_count = 0
        self._circuitbreaker_timeout = 0


    async def _check(self, key):
        redis = FastAPILimiter.redis
        if time.time() < self._circuitbreaker_timeout:
            return 0
        
        try:
            pexpire = await redis.evalsha(
                FastAPILimiter.lua_sha, 1, key, str(self.times), str(self.milliseconds)
            )
        except pyredis.exceptions.ConnectionError:
            if self.circuit_breaker:
                self._failure_count += 1
                if self._failure_count >= self.failure_threshold:
                    self._circuitbreaker_timeout = time.time() + self.recovery_seconds
                    return 0
            raise
        else:
            self._failure_count = 0
            
        return pexpire

    async def __call__(self, request: Request, response: Response):
        if not FastAPILimiter.redis:
            raise Exception("You must call FastAPILimiter.init in startup event of fastapi!")
        route_index = 0
        dep_index = 0
        for i, route in enumerate(request.app.routes):
            if route.path == request.scope["path"] and request.method in route.methods:
                route_index = i
                for j, dependency in enumerate(route.dependencies):
                    if self is dependency.dependency:
                        dep_index = j
                        break

        # moved here because constructor run before app startup
        identifier = self.identifier or FastAPILimiter.identifier
        callback = self.callback or FastAPILimiter.http_callback
        rate_key = await identifier(request)
        key = f"{FastAPILimiter.prefix}:{rate_key}:{route_index}:{dep_index}"
        try:
            pexpire = await self._check(key)
        except pyredis.exceptions.NoScriptError:
            FastAPILimiter.lua_sha = await FastAPILimiter.redis.script_load(
                FastAPILimiter.lua_script
            )
            pexpire = await self._check(key)
        if pexpire != 0:
            return await callback(request, response, pexpire)


class WebSocketRateLimiter(RateLimiter):
    async def __call__(self, ws: WebSocket, context_key=""):
        if not FastAPILimiter.redis:
            raise Exception("You must call FastAPILimiter.init in startup event of fastapi!")
        identifier = self.identifier or FastAPILimiter.identifier
        rate_key = await identifier(ws)
        key = f"{FastAPILimiter.prefix}:ws:{rate_key}:{context_key}"
        pexpire = await self._check(key)
        callback = self.callback or FastAPILimiter.ws_callback
        if pexpire != 0:
            return await callback(ws, pexpire)
