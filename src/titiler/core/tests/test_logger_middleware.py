"""Test titiler.core.middleware.LoggerMiddleware."""

import json
import logging
from logging import config

import pytest
from fastapi import FastAPI, Path
from starlette.testclient import TestClient

from titiler.core.middleware import LoggerMiddleware


def test_logger_middleware(caplog):
    """Create App."""
    app = FastAPI()

    @app.get("/route1")
    async def route1():
        """route1."""
        return "Yo"

    @app.get("/route2/{value}")
    async def route2(value: str = Path()):
        """route2."""
        return value

    @app.get("/route3/{value}")
    async def route3(value: str = Path()):
        """route3."""
        raise Exception("something went wrong")

    app.add_middleware(LoggerMiddleware)

    config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "request": {
                    "format": (
                        "%(asctime)s - %(levelname)s - %(name)s - %(message)s "
                        + json.dumps(
                            {
                                k: f"%({k})s"
                                for k in [
                                    "http.method",
                                    "http.referer",
                                    "http.origin",
                                    "http.route",
                                    "http.path",
                                    "titiler.path_params",
                                    "titiler.query_params",
                                    "http.request.header.",
                                ]
                            }
                        )
                    ),
                },
            },
            "handlers": {
                "console_request": {
                    "class": "logging.StreamHandler",
                    "level": "DEBUG",
                    "formatter": "request",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "titiler.requests": {
                    "level": "INFO",
                    "handlers": ["console_request"],
                    "propagate": True,
                },
            },
        }
    )

    with TestClient(app) as client:
        with caplog.at_level(logging.INFO, logger="titiler.requests"):
            caplog.clear()
            client.get("/route1")
            log = caplog.records[0]
            assert log.name == "titiler.requests"
            assert log.levelname == "INFO"
            assert log.message == "Request received: /route1 GET"
            assert hasattr(log, "titiler.query_params")
            assert getattr(log, "http.route") == "/route1"

            caplog.clear()
            client.get("/route1", params={"hey": "yo"})
            log = caplog.records[0]
            assert log.message == "Request received: /route1 GET"
            assert getattr(log, "titiler.query_params") == {"hey": "yo"}

            caplog.clear()
            client.get(
                "/route1", params={"hey": "yo"}, headers={"accept-encoding": "gzip"}
            )
            log = caplog.records[0]
            assert log.message == "Request received: /route1 GET"
            assert getattr(log, "titiler.query_params") == {"hey": "yo"}
            assert getattr(log, "http.request.header.accept-encoding") == "gzip"

            caplog.clear()
            client.get("/route2/val")
            log = caplog.records[0]
            assert log.name == "titiler.requests"
            assert log.levelname == "INFO"
            assert log.message == "Request received: /route2/val GET"
            assert hasattr(log, "titiler.query_params")
            assert getattr(log, "http.route") == "/route2/{value}"

            caplog.clear()
            with pytest.raises(Exception):  # noqa: B017
                client.get("/route3/val")
                log = caplog.records[0]
                assert log.name == "titiler.requests"
                assert log.levelname == "INFO"
                assert log.message == "Request received: /route3/val GET"
                assert hasattr(log, "titiler.query_params")
                assert log.route == "/route3/{value}"
