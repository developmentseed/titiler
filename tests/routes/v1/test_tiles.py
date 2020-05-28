"""test /v1/tiles endpoints."""

from typing import Dict

from io import BytesIO
from mock import patch

import numpy

from rasterio.io import MemoryFile

from ...conftest import mock_rio


def parse_img(content: bytes) -> Dict:
    with MemoryFile(content) as mem:
        with mem.open() as dst:
            return dst.meta


@patch("titiler.api.api_v1.endpoints.tiles.cogeo.rasterio")
def test_tile(rio, app):
    """test tile endpoints."""
    rio.open = mock_rio

    # full tile
    response = app.get("/v1/8/87/48?url=https://myurl.com/cog.tif&rescale=0,1000")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpg"
    meta = parse_img(response.content)
    assert meta["width"] == 256
    assert meta["height"] == 256

    response = app.get(
        "/v1/8/87/48@2x?url=https://myurl.com/cog.tif&rescale=0,1000&color_formula=Gamma R 3"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpg"
    meta = parse_img(response.content)
    assert meta["width"] == 512
    assert meta["height"] == 512

    response = app.get("/v1/8/87/48.jpg?url=https://myurl.com/cog.tif&rescale=0,1000")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpg"

    response = app.get(
        "/v1/8/87/48@2x.jpg?url=https://myurl.com/cog.tif&rescale=0,1000"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpg"

    response = app.get(
        "/v1/8/87/48@2x.tif?url=https://myurl.com/cog.tif&nodata=0&bidx=1"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff"
    meta = parse_img(response.content)
    assert meta["dtype"] == "uint16"
    assert meta["count"] == 2
    assert meta["width"] == 512
    assert meta["height"] == 512

    response = app.get("/v1/8/87/48.npy?url=https://myurl.com/cog.tif&nodata=0")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/x-binary"
    t, m = numpy.load(BytesIO(response.content), allow_pickle=True)
    assert t.shape == (1, 256, 256)
    assert m.shape == (256, 256)

    # partial
    response = app.get("/v1/8/84/47?url=https://myurl.com/cog.tif&rescale=0,1000")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    response = app.get(
        "/v1/8/84/47?url=https://myurl.com/cog.tif&nodata=0&rescale=0,1000&color_map=viridis"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    response = app.get(
        "/v1/8/53/50.png?url=https://myurl.com/above_cog.tif&bidx=1&color_map=above"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
