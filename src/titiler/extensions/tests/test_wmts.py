"""test WMTS extension."""

import os

from fastapi import FastAPI
from owslib.wmts import WebMapTileService
from starlette.testclient import TestClient

from titiler.core.factory import TilerFactory
from titiler.extensions import wmtsExtension

from .conftest import parse_img

DATA_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def test_wmtsExtension():
    """Test wmtsExtension class."""
    tiler = TilerFactory()
    tiler_plus_wmts = TilerFactory(extensions=[wmtsExtension()])
    assert len(tiler_plus_wmts.router.routes) == len(tiler.router.routes) + 1

    app = FastAPI()
    app.include_router(tiler_plus_wmts.router)
    with TestClient(app) as client:
        response = client.get(f"/WMTSCapabilities.xml?url={DATA_DIR}/cog.tif")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/xml"
        meta = parse_img(response.content)
        assert meta["driver"] == "WMTS"

        wmts = WebMapTileService(
            f"/WMTSCapabilities.xml?url={DATA_DIR}/cog.tif", xml=response.content
        )
        assert wmts.version == "1.0.0"
        assert "WebMercatorQuad" in wmts.contents
        assert "WorldCRS84Quad" in wmts.contents
        assert "WebMercatorQuad" in wmts.tilematrixsets
        assert "WorldCRS84Quad" in wmts.tilematrixsets

        assert wmts.provider.name == "TiTiler"
        assert wmts.provider.url == "https://developmentseed.org/titiler/"
