"""Test titiler.core.middleware.TotalTimeMiddleware."""

import json
import logging
from logging import config

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
                                    "method",
                                    "referer",
                                    "origin",
                                    "path",
                                    "path_params",
                                    "query_params",
                                    "headers",
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
                "titiler-requests": {
                    "level": "INFO",
                    "handlers": ["console_request"],
                    "propagate": True,
                },
            },
        }
    )

    with TestClient(app) as client:
        with caplog.at_level(logging.INFO, logger="titiler-requests"):
            caplog.clear()
            client.get("/route1")
            log = caplog.records[0]
            assert log.name == "titiler-requests"
            assert log.levelname == "INFO"
            assert log.message == "Request received: /route1 GET"
            assert hasattr(log, "query_params")

            caplog.clear()
            client.get("/route1", params={"hey": "yo"})
            log = caplog.records[0]
            assert log.message == "Request received: /route1 GET"
            assert log.query_params == {"hey": "yo"}

            caplog.clear()
            client.get(
                "/route1", params={"hey": "yo"}, headers={"accept-encoding": "gzip"}
            )
            log = caplog.records[0]
            assert log.message == "Request received: /route1 GET"
            assert log.query_params == {"hey": "yo"}
            assert log.headers["accept-encoding"] == "gzip"
