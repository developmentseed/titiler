"""Test TiTiler Tiler Factories."""

import os
import tempfile
from contextlib import contextmanager

from cogeo_mosaic.backends import FileBackend
from cogeo_mosaic.mosaic import MosaicJSON

from titiler.core.dependencies import WebMercatorTMSParams
from titiler.core.resources.enums import OptionalHeader
from titiler.mosaic.factory import MosaicTilerFactory

from .conftest import DATA_DIR

from fastapi import FastAPI

from starlette.testclient import TestClient

assets = [os.path.join(DATA_DIR, asset) for asset in ["cog1.tif", "cog2.tif"]]


@contextmanager
def tmpmosaic():
    """Create a Temporary MosaicJSON file."""
    fileobj = tempfile.NamedTemporaryFile(suffix=".json.gz", delete=False)
    fileobj.close()
    mosaic_def = MosaicJSON.from_urls(assets)
    with FileBackend(fileobj.name, mosaic_def=mosaic_def) as mosaic:
        mosaic.write(overwrite=True)

    try:
        yield fileobj.name
    finally:
        os.remove(fileobj.name)


def test_MosaicTilerFactory():
    """Test MosaicTilerFactory class."""
    mosaic = MosaicTilerFactory(
        optional_headers=[OptionalHeader.server_timing, OptionalHeader.x_assets],
        router_prefix="mosaic",
    )
    assert len(mosaic.router.routes) == 19
    assert mosaic.tms_dependency == WebMercatorTMSParams

    app = FastAPI()
    app.include_router(mosaic.router, prefix="/mosaic")
    client = TestClient(app)

    with tmpmosaic() as mosaic_file:
        response = client.get(
            "/mosaic/point/-74.53125,45.9956935", params={"url": mosaic_file},
        )
        assert response.status_code == 200
        timing = response.headers["server-timing"]
        assert "mosaicread;dur" in timing
        assert "dataread;dur" in timing

        response = client.get("/mosaic/tiles/7/37/45", params={"url": mosaic_file})
        assert response.status_code == 200

        assert response.headers["X-Assets"]
        timing = response.headers["server-timing"]
        assert "mosaicread;dur" in timing
        assert "dataread;dur" in timing
        assert "postprocess;dur" in timing
        assert "format;dur" in timing
