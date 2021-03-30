"""Test TiTiler Custom Render Params."""

from dataclasses import dataclass
from typing import Optional, Union

import numpy

from titiler.core.dependencies import RenderParams
from titiler.core.factory import TilerFactory

from .conftest import DATA_DIR, parse_img

from fastapi import FastAPI, Query

from starlette.testclient import TestClient


@dataclass
class CustomRenderParams(RenderParams):
    """Custom renderparams class."""

    output_nodata: Optional[Union[str, int, float]] = Query(
        None, title="Tiff Ouptut Nodata value",
    )
    output_compression: Optional[str] = Query(
        None, title="Tiff compression schema",
    )

    def __post_init__(self):
        """post init."""
        super().__post_init__()
        if self.output_nodata is not None:
            self.kwargs["nodata"] = (
                numpy.nan if self.output_nodata == "nan" else float(self.output_nodata)
            )
        if self.output_compression is not None:
            self.kwargs["compress"] = self.output_compression


def test_CustomRender():
    """Test Custom Render Params dependency."""
    app = FastAPI()
    cog = TilerFactory(render_dependency=CustomRenderParams)
    app.include_router(cog.router)
    client = TestClient(app)

    response = client.get(f"/tiles/8/87/48.tif?url={DATA_DIR}/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff; application=geotiff"
    meta = parse_img(response.content)
    assert meta["driver"] == "GTiff"
    assert meta["nodata"] is None
    assert meta["count"] == 2
    assert not meta.get("compress")

    response = client.get(
        f"/tiles/8/87/48.tif?url={DATA_DIR}/cog.tif&return_mask=false&output_nodata=0&output_compression=deflate"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff; application=geotiff"
    meta = parse_img(response.content)
    assert meta["driver"] == "GTiff"
    assert meta["nodata"] == 0
    assert meta["count"] == 1
    assert meta["compress"] == "deflate"
