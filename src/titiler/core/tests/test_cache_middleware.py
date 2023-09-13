"""Test titiler.core.CacheControlMiddleware."""


from fastapi import FastAPI, Path
from starlette.responses import Response
from starlette.testclient import TestClient
from typing_extensions import Annotated

from titiler.core.middleware import CacheControlMiddleware


def test_cachecontrol_middleware_exclude():
    """Create App."""
    app = FastAPI()

    @app.get("/route1")
    async def route1():
        """route1."""
        return "yo"

    @app.get("/route2")
    async def route2():
        """route2."""
        return "yeah"

    @app.get("/route3")
    async def route3():
        """route3."""
        return "yeah"

    @app.get("/tiles/{z}/{x}/{y}")
    async def tiles(
        z: Annotated[int, Path(ge=0, le=30, description="Mercator tiles's zoom level")],
        x: Annotated[int, Path(description="Mercator tiles's column")],
        y: Annotated[int, Path(description="Mercator tiles's row")],
    ):
        """tiles."""
        return "yeah"

    @app.get("/emptytiles/{z}/{x}/{y}")
    async def emptytiles(
        z: Annotated[int, Path(ge=0, le=30, description="Mercator tiles's zoom level")],
        x: Annotated[int, Path(description="Mercator tiles's column")],
        y: Annotated[int, Path(description="Mercator tiles's row")],
    ):
        """tiles."""
        return Response(status_code=404)

    app.add_middleware(
        CacheControlMiddleware,
        cachecontrol="public",
        cachecontrol_max_http_code=400,
        exclude_path={r"/route1", r"/route2", r"/tiles/[0-1]/.+"},
    )

    client = TestClient(app)

    response = client.get("/route1")
    assert not response.headers.get("Cache-Control")

    response = client.get("/route2")
    assert not response.headers.get("Cache-Control")

    response = client.get("/route3")
    assert response.headers["Cache-Control"] == "public"

    response = client.get("/tiles/0/1/1")
    assert not response.headers.get("Cache-Control")

    response = client.get("/tiles/3/1/1")
    assert response.headers["Cache-Control"] == "public"

    response = client.get("/emptytiles/3/1/1")
    assert not response.headers.get("Cache-Control")
