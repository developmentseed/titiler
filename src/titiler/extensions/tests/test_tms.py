"""Test TiTiler stac extension."""

import os

from fastapi import FastAPI
from morecantile import TileMatrixSet
from starlette.testclient import TestClient

from titiler.core.factory import TilerFactory
from titiler.extensions import tmsExtension

cog = os.path.join(os.path.dirname(__file__), "fixtures", "cog.tif")


def test_tmsExtension():
    """Test stacExtension class."""
    tiler = TilerFactory()
    tiler_plus_tms = TilerFactory(extensions=[tmsExtension()])
    # Check that we added one route (/tms)
    assert len(tiler_plus_tms.router.routes) == len(tiler.router.routes) + 1

    app = FastAPI()
    app.include_router(tiler_plus_tms.router)
    with TestClient(app) as client:
        response = client.get("/tms", params={"url": cog, "f": "html"})
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

        response = client.get(
            "/tms", params={"url": cog}, headers={"Accept": "text/html"}
        )
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

        response = client.get("/tms", params={"url": cog})
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        body = response.json()
        tms = TileMatrixSet.model_validate(body)
        assert tms.description
        assert tms.boundingBox
        assert tms.crs
        assert len(tms.tileMatrices) == 5
