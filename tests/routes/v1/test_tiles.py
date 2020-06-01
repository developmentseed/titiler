"""test /v1/tiles endpoints."""

from typing import Dict

from io import BytesIO
from unittest.mock import patch

import numpy

from rasterio.io import MemoryFile

from ...conftest import mock_reader


def parse_img(content: bytes) -> Dict:
    with MemoryFile(content) as mem:
        with mem.open() as dst:
            return dst.meta


@patch("titiler.api.api_v1.endpoints.tiles.COGReader")
def test_tile(reader, app):
    """test tile endpoints."""
    reader.side_effect = mock_reader

    # full tile
    response = app.get(
        "/v1/cog/tiles/8/87/48?url=https://myurl.com/cog.tif&rescale=0,1000"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    meta = parse_img(response.content)
    assert meta["width"] == 256
    assert meta["height"] == 256

    response = app.get(
        "/v1/cog/tiles/8/87/48@2x?url=https://myurl.com/cog.tif&rescale=0,1000&color_formula=Gamma R 3"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    meta = parse_img(response.content)
    assert meta["width"] == 512
    assert meta["height"] == 512

    response = app.get(
        "/v1/cog/tiles/8/87/48.jpg?url=https://myurl.com/cog.tif&rescale=0,1000"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    response = app.get(
        "/v1/cog/tiles/8/87/48@2x.jpg?url=https://myurl.com/cog.tif&rescale=0,1000"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    response = app.get(
        "/v1/cog/tiles/8/87/48@2x.tif?url=https://myurl.com/cog.tif&nodata=0&bidx=1"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff"
    meta = parse_img(response.content)
    assert meta["dtype"] == "uint16"
    assert meta["count"] == 2
    assert meta["width"] == 512
    assert meta["height"] == 512

    response = app.get(
        "/v1/cog/tiles/8/87/48.npy?url=https://myurl.com/cog.tif&nodata=0"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/x-binary"
    t, m = numpy.load(BytesIO(response.content), allow_pickle=True)
    assert t.shape == (1, 256, 256)
    assert m.shape == (256, 256)

    # partial
    response = app.get(
        "/v1/cog/tiles/8/84/47?url=https://myurl.com/cog.tif&rescale=0,1000"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    response = app.get(
        "/v1/cog/tiles/8/84/47?url=https://myurl.com/cog.tif&nodata=0&rescale=0,1000&color_map=viridis"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    response = app.get(
        "/v1/cog/tiles/8/53/50.png?url=https://myurl.com/above_cog.tif&bidx=1&color_map=above"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


@patch("titiler.api.api_v1.endpoints.tiles.COGReader")
def test_tilejson(reader, app):
    """test /tilejson endpoint."""
    reader.side_effect = mock_reader

    response = app.get("/v1/cog/tilejson.json?url=https://myurl.com/cog.tif")
    assert response.status_code == 200
    body = response.json()
    assert body["tilejson"] == "2.2.0"
    assert body["version"] == "1.0.0"
    assert body["scheme"] == "xyz"
    assert len(body["tiles"]) == 1
    assert body["tiles"][0].startswith(
        "http://testserver/v1/cog/tiles/WebMercatorQuad/{z}/{x}/{y}@1x?url=https"
    )
    assert body["minzoom"] == 5
    assert body["maxzoom"] == 8
    assert body["bounds"]
    assert body["center"]

    response = app.get(
        "/v1/cog/tilejson.json?url=https://myurl.com/cog.tif&tile_format=png&tile_scale=2"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["tiles"][0].startswith(
        "http://testserver/v1/cog/tiles/WebMercatorQuad/{z}/{x}/{y}@2x.png?url=https"
    )


def test_tilematrix(app):
    """test /tileMatrixSet endpoint."""
    response = app.get("/v1/tileMatrixSets")
    assert response.status_code == 200
    body = response.json()
    assert len(body["tileMatrixSets"]) == 11  # morecantile has 10 defaults
    tms = list(filter(lambda m: m["id"] == "EPSG3413", body["tileMatrixSets"]))[0]
    assert tms["links"][0]["href"] == "http://testserver/v1/tileMatrixSets/EPSG3413"


def test_tilematrixInfo(app):
    """test /tileMatrixSet endpoint."""
    response = app.get("/v1/tileMatrixSets/EPSG3413")
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "TileMatrixSetType"
    assert body["identifier"] == "EPSG3413"
