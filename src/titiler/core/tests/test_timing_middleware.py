"""Test titiler.core.middleware.TotalTimeMiddleware."""

import time

from fastapi import FastAPI
from starlette.responses import Response
from starlette.testclient import TestClient

from titiler.core.middleware import TotalTimeMiddleware


def test_timing_middleware_exclude():
    """Create App."""
    app = FastAPI()

    @app.get("/route1")
    async def route1():
        """route1."""
        return "I am tired"

    @app.get("/route2")
    async def route2():
        """route2."""
        time.sleep(1)
        return "I slept fine"

    @app.get("/route3")
    async def route3(response: Response):
        """route3."""
        time.sleep(1)
        response.headers["Server-Timing"] = "atime;dur=2000"
        return "I slept fine"

    app.add_middleware(TotalTimeMiddleware)

    with TestClient(app) as client:
        response = client.get("/route1")
        tim = response.headers.get("Server-Timing")
        assert "total;dur=" in tim

        response = client.get("/route2")
        tim = response.headers.get("Server-Timing")
        assert "total;dur=" in tim
        assert float(tim.split("=")[1]) > 1000

        response = client.get("/route3")
        tim = response.headers.get("Server-Timing")
        assert "atime;dur=2000, total" in tim
