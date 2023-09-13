"""Test titiler.core.middleware.LowerCaseQueryStringMiddleware."""

from typing import List

from fastapi import FastAPI, Query
from starlette.testclient import TestClient
from typing_extensions import Annotated

from titiler.core.middleware import LowerCaseQueryStringMiddleware


def test_lowercase_middleware():
    """Make sure upper and lower case QS are accepted."""
    app = FastAPI()

    @app.get("/route1")
    async def route1(value: Annotated[str, Query()]):
        """route1."""
        return {"value": value}

    app.add_middleware(LowerCaseQueryStringMiddleware)

    client = TestClient(app)

    response = client.get("/route1?value=lorenzori")
    assert response.json() == {"value": "lorenzori"}

    response = client.get("/route1?VALUE=lorenzori")
    assert response.json() == {"value": "lorenzori"}


def test_lowercase_middleware_multiple_values():
    """Make sure all values are available for lists."""
    app = FastAPI()

    @app.get("/route1")
    async def route1(value: Annotated[List[str], Query()]):
        """route1."""
        return {"value": value}

    app.add_middleware(LowerCaseQueryStringMiddleware)

    client = TestClient(app)

    response = client.get("/route1?value=lorenzori&value=dogs")
    assert response.json() == {"value": ["lorenzori", "dogs"]}

    response = client.get("/route1?VALUE=lorenzori&VALUE=dogs&value=trucks")
    assert response.json() == {"value": ["lorenzori", "dogs", "trucks"]}


def test_lowercase_middleware_url_with_query_parameters():
    """Make sure all query parameters return."""
    app = FastAPI()

    @app.get("/route1")
    async def route1(url: List[str] = Query(...)):
        """route1."""
        return {"url": url}

    app.add_middleware(LowerCaseQueryStringMiddleware)

    client = TestClient(app)

    url = "https://developmentseed.org?solutions=geospatial&planet=better"
    url_encoded = (
        "https%3A%2F%2Fdevelopmentseed.org%3Fsolutions%3Dgeospatial%26planet%3Dbetter"
    )

    response = client.get(f"/route1?url={url_encoded}")

    assert response.json() == {"url": [url]}
