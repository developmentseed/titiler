"""Test TiTiler Tiler Factories."""

import os
import tempfile
from contextlib import contextmanager

from cogeo_mosaic.backends import FileBackend
from cogeo_mosaic.mosaic import MosaicJSON

from titiler.core.dependencies import TMSParams
from titiler.core.factory import TilerFactory
from titiler.core.resources.enums import OptionalHeader

from .conftest import DATA_DIR

from fastapi import FastAPI

from starlette.testclient import TestClient

assets = [os.path.join(DATA_DIR, asset) for asset in ["cog1.tif", "cog2.tif"]]


def test_TilerFactory():
    """Test TilerFactory class."""
    cog = TilerFactory()
    assert len(cog.router.routes) == 21
    assert cog.tms_dependency == TMSParams

    cog = TilerFactory(add_preview=False, add_part=False)
    assert len(cog.router.routes) == 17

    app = FastAPI()
    cog = TilerFactory(optional_headers=[OptionalHeader.server_timing])
    app.include_router(cog.router)
    client = TestClient(app)

    response = client.get(f"/tiles/8/87/48?url={DATA_DIR}/cog.tif&rescale=0,1000")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    timing = response.headers["server-timing"]
    assert "dataread;dur" in timing
    assert "postprocess;dur" in timing
    assert "format;dur" in timing

    response = client.get(
        f"/preview?url={DATA_DIR}/cog.tif&rescale=0,1000&max_size=256"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    timing = response.headers["server-timing"]
    assert "dataread;dur" in timing
    assert "postprocess;dur" in timing
    assert "format;dur" in timing

    response = client.get(
        f"/crop/-56.228,72.715,-54.547,73.188.png?url={DATA_DIR}/cog.tif&rescale=0,1000&max_size=256"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    timing = response.headers["server-timing"]
    assert "dataread;dur" in timing
    assert "postprocess;dur" in timing
    assert "format;dur" in timing

    response = client.get(f"/point/-56.228,72.715?url={DATA_DIR}/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    timing = response.headers["server-timing"]
    assert "dataread;dur" in timing


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
