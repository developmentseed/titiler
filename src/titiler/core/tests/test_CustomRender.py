"""Test TiTiler Custom Render Params."""

from dataclasses import dataclass
from typing import Optional, Union

import numpy
from fastapi import FastAPI, Query
from starlette.testclient import TestClient

from titiler.core.dependencies import ImageRenderingParams
from titiler.core.factory import TilerFactory

from .conftest import DATA_DIR, parse_img


@dataclass
class CustomRenderParams(ImageRenderingParams):
    """Custom renderparams class."""

    nodata: Optional[Union[str, int, float]] = Query(
        None,
        title="Tiff Ouptut Nodata value",
        alias="output_nodata",
    )
    compress: Optional[str] = Query(
        None,
        title="Tiff compression schema",
        alias="output_compression",
    )

    def __post_init__(self):
        """post init."""
        if self.nodata is not None:
            self.nodata = numpy.nan if self.nodata == "nan" else float(self.nodata)


def test_CustomRender():
    """Test Custom Render Params dependency."""
    app = FastAPI()
    cog = TilerFactory(render_dependency=CustomRenderParams)
    app.include_router(cog.router)
    client = TestClient(app)

    response = client.get(f"/tiles/WebMercatorQuad/8/87/48.tif?url={DATA_DIR}/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff; application=geotiff"
    meta = parse_img(response.content)
    assert meta["driver"] == "GTiff"
    assert meta["nodata"] is None
    assert meta["count"] == 2
    assert not meta.get("compress")

    response = client.get(
        f"/tiles/WebMercatorQuad/8/87/48.tif?url={DATA_DIR}/cog.tif&return_mask=false&output_nodata=0&output_compression=deflate"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff; application=geotiff"
    meta = parse_img(response.content)
    assert meta["driver"] == "GTiff"
    assert meta["nodata"] == 0
    assert meta["count"] == 1
    assert meta["compress"] == "deflate"

    response = client.get(
        f"/tiles/WebMercatorQuad/9/289/207?url={DATA_DIR}/TCI.tif&rescale=0,1000&rescale=0,2000&rescale=0,3000"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["width"] == 256
    assert meta["height"] == 256
