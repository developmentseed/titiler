"""Test TiTiler wmts extension."""

import httpx
import pytest
import os
import time
from multiprocessing import Process
import contextlib
import time
import threading
import uvicorn

from titiler.core.factory import TilerFactory
from titiler.extensions import gdalwmtsExtension
import rasterio
from rio_tiler.io import Reader

from .conftest import parse_img

from fastapi import FastAPI

from starlette.testclient import TestClient

cog = os.path.join(os.path.dirname(__file__), "fixtures", "cog.tif")


class Server(uvicorn.Server):
    def install_signal_handlers(self):
        pass

    @contextlib.contextmanager
    def run_in_thread(self):
        thread = threading.Thread(target=self.run)
        thread.start()
        try:
            while not self.started:
                time.sleep(1e-3)
            yield
        finally:
            self.should_exit = True
            thread.join()



@pytest.fixture(scope="session")
def application():
    """Run app in Thread."""
    tiler_plus_wmts = TilerFactory(extensions=[gdalwmtsExtension()])
    app = FastAPI()
    app.include_router(tiler_plus_wmts.router)

    config = uvicorn.Config(app, host="127.0.0.1", port=5000, log_level="info", loop="asyncio")
    server = Server(config=config)
    with server.run_in_thread():
        yield "http://127.0.0.1:5000"


def test_gdalwmtsExtension():
    """Test gdalwmtsExtension class."""
    tiler = TilerFactory()
    tiler_plus_wmts = TilerFactory(extensions=[gdalwmtsExtension()])
    # Check that we added one route (/validate)
    assert len(tiler_plus_wmts.router.routes) == len(tiler.router.routes) + 2

    app = FastAPI()
    app.include_router(tiler_plus_wmts.router)
    with TestClient(app) as client:
        # missing bandscount and datatype
        response = client.get(
            "/wmts.xml",
            params={"url": cog},
        )
        assert response.status_code == 422

        response = client.get(
            "/wmts.xml",
            params={"url": cog, "tile_format": "jpeg", "datatype": "byte", "bandscount": 3},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/xml"


def test_app(application):
    """Test full application."""
    response = httpx.get(
        f"{application}/wmts.xml",
        params={"url": cog, "tile_format": "jpeg", "datatype": "byte", "bandscount": 3},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"

    with rasterio.open(response.text) as src:
        meta = src.meta
        assert meta["driver"] == "WMTS"
        assert meta["count"] == 3
        assert meta["dtype"] == "uint8"

    response = httpx.get(
        f"{application}/wmts.xml",
        params={"url": cog, "tile_format": "tif", "datatype": "uint16", "bandscount": 1},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"

    with rasterio.open(response.text) as src:
        meta = src.meta
        assert meta["driver"] == "WMTS"
        assert meta["count"] == 1
        assert meta["dtype"] == "uint16"

    with Reader(response.text) as src:
        im = src.preview(max_size=128)
        assert im.count == 1
        assert im.width <= 128
        assert im.height <= 128
        assert im.data.dtype == "uint16"

    response = httpx.get(
        f"{application}/wmts.xml",
        params={"url": cog, "tile_format": "tif", "datatype": "byte", "bandscount": 1, "rescale": "0,1000"},
    )
    assert response.status_code == 200

    with Reader(response.text) as src:
        im = src.preview(max_size=128)
        assert im.count == 1
        assert im.width <= 128
        assert im.height <= 128
        assert im.data.dtype == "uint8"

