"""Test titiler.core.middleware.TotalTimeMiddleware."""

import json
import logging

from fastapi import FastAPI
from starlette.testclient import TestClient

from titiler.core.middleware import LoggerMiddleware


def test_timing_middleware(caplog):
    """Create App."""
    app = FastAPI()

    @app.get("/route1")
    async def route1():
        """route1."""
        return "Yo"

    app.add_middleware(LoggerMiddleware)

    with TestClient(app) as client:
        caplog.clear()
        client.get("/route1")
        log = caplog.records[0]
        assert log.name == "titiler"
        assert log.levelname == "INFO"
        req = json.loads(log.message.split("Request: ")[1])
        assert req["path"] == "/route1"

        caplog.clear()
        client.get("/route1", params={"hey": "yo"})
        log = caplog.records[0]
        req = json.loads(log.message.split("Request: ")[1])
        assert req["path"] == "/route1"
        assert req["query_params"] == {"hey": "yo"}

        caplog.clear()
        client.get("/route1", params={"hey": "yo"}, headers={"accept-encoding": "gzip"})
        log = caplog.records[0]
        req = json.loads(log.message.split("Request: ")[1])
        assert req["headers"]["accept-encoding"] == "gzip"


def test_timing_middleware_option(caplog):
    """Create App."""
    app = FastAPI()

    @app.get("/route1")
    async def route1():
        """route1."""
        return "Yo"

    logger = logging.getLogger("custom")
    logger.setLevel(logging.INFO)

    app.add_middleware(LoggerMiddleware, logger=logger, log_data=["path"])

    with TestClient(app) as client:
        caplog.clear()
        client.get("/route1")
        log = caplog.records[0]
        assert log.name == "custom"
        assert log.levelname == "INFO"
        req = json.loads(log.message.split("Request: ")[1])
        assert req["path"] == "/route1"

        caplog.clear()
        client.get("/route1", params={"hey": "yo"})
        log = caplog.records[0]
        req = json.loads(log.message.split("Request: ")[1])
        assert req["path"] == "/route1"
        assert "query_params" not in req

        caplog.clear()
        client.get("/route1", params={"hey": "yo"}, headers={"accept-encoding": "gzip"})
        log = caplog.records[0]
        req = json.loads(log.message.split("Request: ")[1])
        assert "headers" not in req
