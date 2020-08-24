"""test /COG endpoints."""


from typing import Dict
from unittest.mock import patch

from rasterio.io import MemoryFile

from ..conftest import mock_rasterio_open, mock_RequestGet


@patch("rio_tiler.io.stac.requests")
def test_bounds(requests, app):
    """test /bounds endpoint."""
    requests.get = mock_RequestGet

    response = app.get("/stac/bounds?url=https://myurl.com/item.json")
    assert response.status_code == 200
    body = response.json()
    assert len(body["bounds"]) == 4


@patch("rio_tiler.io.cogeo.rasterio")
@patch("rio_tiler.io.stac.requests")
def test_info(requests, rio, app):
    """test /info endpoint."""
    requests.get = mock_RequestGet
    rio.open = mock_rasterio_open

    response = app.get("/stac/info?url=https://myurl.com/item.json")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 17

    response = app.get("/stac/info?url=https://myurl.com/item.json&assets=B01")
    assert response.status_code == 200
    body = response.json()
    assert body["B01"]

    response = app.get("/stac/info?url=https://myurl.com/item.json&assets=B01,B09")
    assert response.status_code == 200
    body = response.json()
    assert body["B01"]
    assert body["B09"]


@patch("rio_tiler.io.cogeo.rasterio")
@patch("rio_tiler.io.stac.requests")
def test_metadata(requests, rio, app):
    """test /metadata endpoint."""
    requests.get = mock_RequestGet
    rio.open = mock_rasterio_open

    response = app.get("/stac/metadata?url=https://myurl.com/item.json&assets=B01")
    assert response.status_code == 200
    body = response.json()
    assert body["B01"]

    response = app.get("/stac/metadata?url=https://myurl.com/item.json&assets=B01,B09")
    assert response.status_code == 200
    body = response.json()
    assert body["B01"]
    assert body["B09"]


def parse_img(content: bytes) -> Dict:
    """Read tile image and return metadata."""
    with MemoryFile(content) as mem:
        with mem.open() as dst:
            return dst.meta


@patch("rio_tiler.io.cogeo.rasterio")
@patch("rio_tiler.io.stac.requests")
def test_tile(requests, rio, app):
    """test tile endpoints."""
    requests.get = mock_RequestGet
    rio.open = mock_rasterio_open

    # Missing assets
    response = app.get("/stac/tiles/9/289/207?url=https://myurl.com/item.json")
    assert response.status_code == 400

    response = app.get(
        "/stac/tiles/9/289/207?url=https://myurl.com/item.json&assets=B01&rescale=0,1000"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["width"] == 256
    assert meta["height"] == 256

    response = app.get(
        "/stac/tiles/9/289/207?url=https://myurl.com/item.json&expression=B01&rescale=0,1000"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["width"] == 256
    assert meta["height"] == 256


@patch("rio_tiler.io.cogeo.rasterio")
@patch("rio_tiler.io.stac.requests")
def test_tilejson(requests, rio, app):
    """test /tilejson endpoint."""
    requests.get = mock_RequestGet
    rio.open = mock_rasterio_open

    # calling tilejson without args work but tiles will fail because of missing expression or assets
    response = app.get("/stac/tilejson.json?url=https://myurl.com/item.json")
    assert response.status_code == 200

    response = app.get(
        "/stac/tilejson.json?url=https://myurl.com/item.json&assets=B01&minzoom=5&maxzoom=10"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["tilejson"] == "2.2.0"
    assert body["version"] == "1.0.0"
    assert body["scheme"] == "xyz"
    assert len(body["tiles"]) == 1
    assert body["tiles"][0].startswith(
        "http://testserver/stac/tiles/WebMercatorQuad/{z}/{x}/{y}@1x?url="
    )
    assert body["minzoom"] == 5
    assert body["maxzoom"] == 10
    assert body["bounds"]
    assert body["center"]

    response = app.get(
        "/stac/tilejson.json?url=https://myurl.com/item.json&assets=B01&tile_format=png&tile_scale=2"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["tiles"][0].startswith(
        "http://testserver/stac/tiles/WebMercatorQuad/{z}/{x}/{y}@2x.png?url="
    )


@patch("rio_tiler.io.cogeo.rasterio")
@patch("rio_tiler.io.stac.requests")
def test_preview(requests, rio, app):
    """test preview endpoints."""
    requests.get = mock_RequestGet
    rio.open = mock_rasterio_open

    # Missing Assets or Expression
    response = app.get("/stac/preview?url=https://myurl.com/item.json")
    assert response.status_code == 400

    response = app.get(
        "/stac/preview?url=https://myurl.com/item.json&assets=B01&rescale=0,1000&max_size=64"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["width"] == 64
    assert meta["height"] == 64

    response = app.get(
        "/stac/preview?url=https://myurl.com/item.json&assets=B01&rescale=0,1000&max_size=64&width=128&height=128"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["width"] == 128
    assert meta["height"] == 128

    response = app.get(
        "/stac/preview?url=https://myurl.com/item.json&expression=B01&rescale=0,1000&max_size=64"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["width"] == 64
    assert meta["height"] == 64


@patch("rio_tiler.io.cogeo.rasterio")
@patch("rio_tiler.io.stac.requests")
def test_part(requests, rio, app):
    """test crop endpoints."""
    requests.get = mock_RequestGet
    rio.open = mock_rasterio_open

    # Missing Assets or Expression
    response = app.get(
        "/stac/crop/23.878,32.063,23.966,32.145.png?url=https://myurl.com/item.json"
    )
    assert response.status_code == 400

    response = app.get(
        "/stac/crop/23.878,32.063,23.966,32.145.png?url=https://myurl.com/item.json&assets=B01&rescale=0,1000&max_size=64"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["width"] == 15
    assert meta["height"] == 14

    response = app.get(
        "/stac/crop/23.878,32.063,23.966,32.145.png?url=https://myurl.com/item.json&assets=B01&rescale=0,1000&max_size=64&width=128&height=128"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["width"] == 128
    assert meta["height"] == 128

    response = app.get(
        "/stac/crop/23.878,32.063,23.966,32.145.png?url=https://myurl.com/item.json&expression=B01&rescale=0,1000&max_size=64"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["width"] == 15
    assert meta["height"] == 14


@patch("rio_tiler.io.cogeo.rasterio")
@patch("rio_tiler.io.stac.requests")
def test_point(requests, rio, app):
    """test crop endpoints."""
    requests.get = mock_RequestGet
    rio.open = mock_rasterio_open

    # Missing Assets or Expression
    response = app.get("/stac/point/23.878,32.063?url=https://myurl.com/item.json")
    assert response.status_code == 400

    response = app.get(
        "/stac/point/23.878,32.063?url=https://myurl.com/item.json&assets=B01"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["coordinates"] == [23.878, 32.063]
    assert body["values"] == [[3565]]

    # response = app.get(
    #     "/stac/point/23.878,32.063?url=https://myurl.com/item.json&assets=B01&asset_expression=b1*2"
    # )
    # assert response.status_code == 200
    # body = response.json()
    # assert body["coordinates"] == [23.878, 32.063]
    # assert body["values"] == [[7130]]

    response = app.get(
        "/stac/point/23.878,32.063?url=https://myurl.com/item.json&expression=B01/B09"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["coordinates"] == [23.878, 32.063]
    assert round(body["values"][0][0], 2) == 0.49


@patch("rio_tiler.io.cogeo.rasterio")
@patch("rio_tiler.io.stac.requests")
def test_missing_asset_not_found(requests, rio, app):
    """test /info endpoint."""
    requests.get = mock_RequestGet
    rio.open = mock_rasterio_open

    response = app.get(
        "/stac/preview?url=https://myurl.com/item.json&assets=B1111&rescale=0,1000&max_size=64"
    )
    assert response.status_code == 404
