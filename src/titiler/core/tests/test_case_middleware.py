"""Test titiler.core.middleware.LowerCaseQueryStringMiddleware."""


from titiler.core.middleware import LowerCaseQueryStringMiddleware

from fastapi import FastAPI, Query

from starlette.testclient import TestClient


def test_lowercase_middleware():
    """Make sure upper and lower case QS are accepted."""
    app = FastAPI()

    @app.get("/route1")
    async def route1(value: str = Query(...)):
        """route1."""
        return {"value": value}

    app.add_middleware(LowerCaseQueryStringMiddleware)

    client = TestClient(app)

    response = client.get("/route1?value=lorenzori")
    assert response.json() == {"value": "lorenzori"}

    response = client.get("/route1?VALUE=lorenzori")
    assert response.json() == {"value": "lorenzori"}
