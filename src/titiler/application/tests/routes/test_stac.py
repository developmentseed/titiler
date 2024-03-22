"""test /COG endpoints."""


from typing import Dict
from unittest.mock import patch

from rasterio.io import MemoryFile

from ..conftest import mock_rasterio_open, mock_RequestGet


@patch("rio_tiler.io.stac.httpx")
def test_bounds(httpx, app):
    """test /bounds endpoint."""
    httpx.get = mock_RequestGet

    response = app.get("/stac/bounds?url=https://myurl.com/item.json")
    assert response.status_code == 200
    body = response.json()
    assert len(body["bounds"]) == 4


@patch("rio_tiler.io.rasterio.rasterio")
@patch("rio_tiler.io.stac.httpx")
def test_info(httpx, rio, app):
    """test /info endpoint."""
    httpx.get = mock_RequestGet
    rio.open = mock_rasterio_open

    response = app.get("/stac/assets?url=https://myurl.com/item.json")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2

    response = app.get("/stac/info?url=https://myurl.com/item.json&assets=B01")
    assert response.status_code == 200
    body = response.json()
    assert body["B01"]

    response = app.get("/stac/info?url=https://myurl.com/item.json")
    assert response.status_code == 200
    body = response.json()
    assert body["B01"]
    assert body["B09"]

    response = app.get(
        "/stac/info?url=https://myurl.com/item.json&assets=B01&assets=B09"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["B01"]
    assert body["B09"]

    response = app.get("/stac/info.geojson?url=https://myurl.com/item.json&assets=B01")
    assert response.status_code == 200
    body = response.json()
    assert response.headers["content-type"] == "application/geo+json"
    body = response.json()
    assert body["geometry"]
    assert body["properties"]["B01"]


def parse_img(content: bytes) -> Dict:
    """Read tile image and return metadata."""
    with MemoryFile(content) as mem:
        with mem.open() as dst:
            return dst.meta


@patch("rio_tiler.io.rasterio.rasterio")
@patch("rio_tiler.io.stac.httpx")
def test_tile(httpx, rio, app):
    """test tile endpoints."""
    httpx.get = mock_RequestGet
    rio.open = mock_rasterio_open

    # Missing assets
    response = app.get(
        "/stac/tiles/WebMercatorQuad/9/289/207?url=https://myurl.com/item.json"
    )
    assert response.status_code == 400

    response = app.get(
        "/stac/tiles/WebMercatorQuad/9/289/207?url=https://myurl.com/item.json&assets=B01&rescale=0,1000"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["width"] == 256
    assert meta["height"] == 256

    response = app.get(
        "/stac/tiles/WebMercatorQuad/9/289/207?url=https://myurl.com/item.json&expression=B01_b1&rescale=0,1000"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["width"] == 256
    assert meta["height"] == 256


@patch("rio_tiler.io.rasterio.rasterio")
@patch("rio_tiler.io.stac.httpx")
def test_tilejson(httpx, rio, app):
    """test /tilejson endpoint."""
    httpx.get = mock_RequestGet
    rio.open = mock_rasterio_open

    response = app.get(
        "/stac/WebMercatorQuad/tilejson.json?url=https://myurl.com/item.json"
    )
    assert response.status_code == 400

    response = app.get(
        "/stac/WebMercatorQuad/tilejson.json?url=https://myurl.com/item.json&assets=B01&minzoom=5&maxzoom=10"
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
        "/stac/WebMercatorQuad/tilejson.json?url=https://myurl.com/item.json&assets=B01&tile_format=png&tile_scale=2"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["tiles"][0].startswith(
        "http://testserver/stac/tiles/WebMercatorQuad/{z}/{x}/{y}@2x.png?url="
    )


@patch("rio_tiler.io.rasterio.rasterio")
@patch("rio_tiler.io.stac.httpx")
def test_preview(httpx, rio, app):
    """test preview endpoints."""
    httpx.get = mock_RequestGet
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
        "/stac/preview?url=https://myurl.com/item.json&expression=B01_b1&rescale=0,1000&max_size=64"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["width"] == 64
    assert meta["height"] == 64


@patch("rio_tiler.io.rasterio.rasterio")
@patch("rio_tiler.io.stac.httpx")
def test_part(httpx, rio, app):
    """test crop endpoints."""
    httpx.get = mock_RequestGet
    rio.open = mock_rasterio_open

    # Missing Assets or Expression
    response = app.get(
        "/stac/bbox/23.878,32.063,23.966,32.145.png?url=https://myurl.com/item.json"
    )
    assert response.status_code == 400

    response = app.get(
        "/stac/bbox/23.878,32.063,23.966,32.145.png?url=https://myurl.com/item.json&assets=B01&rescale=0,1000&max_size=64"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["width"] == 15
    assert meta["height"] == 14

    response = app.get(
        "/stac/bbox/23.878,32.063,23.966,32.145.png?url=https://myurl.com/item.json&assets=B01&rescale=0,1000&max_size=64&width=128&height=128"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["width"] == 128
    assert meta["height"] == 128

    response = app.get(
        "/stac/bbox/23.878,32.063,23.966,32.145.png?url=https://myurl.com/item.json&expression=B01_b1&rescale=0,1000&max_size=64"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["width"] == 15
    assert meta["height"] == 14


@patch("rio_tiler.io.rasterio.rasterio")
@patch("rio_tiler.io.stac.httpx")
def test_point(httpx, rio, app):
    """test point endpoints."""
    httpx.get = mock_RequestGet
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
    assert body["values"] == [3565]
    assert body["band_names"] == ["B01_b1"]

    response = app.get(
        "/stac/point/23.878,32.063?url=https://myurl.com/item.json&expression=B01_b1*2"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["coordinates"] == [23.878, 32.063]
    assert body["values"] == [7130]
    assert body["band_names"] == ["B01_b1*2"]

    response = app.get(
        "/stac/point/23.878,32.063?url=https://myurl.com/item.json&expression=B01_b1/B09_b1"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["coordinates"] == [23.878, 32.063]
    assert round(body["values"][0], 2) == 0.49


@patch("rio_tiler.io.rasterio.rasterio")
@patch("rio_tiler.io.stac.httpx")
def test_missing_asset_not_found(httpx, rio, app):
    """test /info endpoint."""
    httpx.get = mock_RequestGet
    rio.open = mock_rasterio_open

    response = app.get(
        "/stac/preview?url=https://myurl.com/item.json&assets=B1111&rescale=0,1000&max_size=64"
    )
    assert response.status_code == 404
