"""Test titiler.core.middleware.TotalTimeMiddleware."""

from fastapi import FastAPI
from starlette.testclient import TestClient

from titiler.core.middleware import LoggerMiddleware


def test_timing_middleware_exclude(caplog):
    """Create App."""
    app = FastAPI()

    @app.get("/route1")
    async def route1():
        """route1."""
        return "Yo"

    app.add_middleware(LoggerMiddleware, querystrings=True, headers=True)

    with TestClient(app) as client:
        caplog.clear()
        client.get("/route1")
        assert len([rec.message for rec in caplog.records]) == 2

        caplog.clear()
        client.get("/route1", params={"hey": "yo"})
        assert len([rec.message for rec in caplog.records]) == 3

        caplog.clear()
        client.get("/route1", params={"hey": "yo"}, headers={"accept-encoding": "gzip"})
        h = caplog.records[2].message
        assert "'accept-encoding': 'gzip'" in h
