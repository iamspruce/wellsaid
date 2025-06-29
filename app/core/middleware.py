from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
import os

def get_rate_limit():
    return os.getenv("RATE_LIMIT", "100/minute")

limiter = Limiter(key_func=get_remote_address, headers_enabled=True, default_limits=[get_rate_limit()])

def setup_middlewares(app: FastAPI):
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logging.exception(f"Unhandled exception from {request.client.host}")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
