"""test /COG endpoints."""
import os
from io import BytesIO
from unittest.mock import patch

import numpy
import pytest

from ..conftest import DATA_DIR, mock_rasterio_open, parse_img


@patch("rio_tiler.io.cogeo.rasterio")
def test_bounds(rio, app):
    """test /bounds endpoint."""
    rio.open = mock_rasterio_open

    response = app.get("/cog/bounds?url=https://myurl.com/cog.tif")
    assert response.status_code == 200
    body = response.json()
    assert len(body["bounds"]) == 4
    assert response.headers["Cache-Control"] == "private, max-age=3600"


@patch("rio_tiler.io.cogeo.rasterio")
def test_info(rio, app):
    """test /info endpoint."""
    rio.open = mock_rasterio_open

    response = app.get("/cog/info?url=https://myurl.com/cog.tif")
    assert response.status_code == 200
    body = response.json()
    assert len(body["bounds"]) == 4
    assert body["band_descriptions"] == [[1, "band1"]]
    assert body["dtype"] == "uint16"
    assert body["colorinterp"] == ["gray"]
    assert body["nodata_type"] == "None"


@patch("rio_tiler.io.cogeo.rasterio")
def test_metadata(rio, app):
    """test /metadata endpoint."""
    rio.open = mock_rasterio_open

    response = app.get("/cog/metadata?url=https://myurl.com/cog.tif")
    assert response.status_code == 200
    body = response.json()
    assert len(body["bounds"]) == 4
    assert body["statistics"]
    assert len(body["statistics"]["1"]["histogram"][0]) == 10
    assert body["band_descriptions"] == [[1, "band1"]]
    assert body["dtype"] == "uint16"
    assert body["colorinterp"] == ["gray"]
    assert body["nodata_type"] == "None"

    response = app.get(
        "/cog/metadata?url=https://myurl.com/cog.tif&resampling_method=bilinear"
    )
    assert response.status_code == 200
    body2 = response.json()
    assert body2["statistics"] != body["statistics"]

    response = app.get(
        "/cog/metadata?url=https://myurl.com/cog.tif&bounds=-56.228,72.715,-54.547,73.188"
    )
    assert response.status_code == 200
    body2 = response.json()
    assert body2["statistics"] != body["statistics"]

    response = app.get(
        "/cog/metadata?url=https://myurl.com/cog.tif&histogram_bins=5&histogram_range=1,1000&nodata=0"
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["statistics"]["1"]["histogram"][0]) == 5


@patch("rio_tiler.io.cogeo.rasterio")
def test_wmts(rio, app):
    """test wmts endpoints."""
    rio.open = mock_rasterio_open

    response = app.get("/cog/WMTSCapabilities.xml?url=https://myurl.com/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"
    assert response.headers["Cache-Control"] == "private, max-age=3600"
    assert (
        "http://testserver/cog/WMTSCapabilities.xml?url=https://myurl.com/cog.tif"
        in response.content.decode()
    )
    assert "<ows:Identifier>cogeo</ows:Identifier>" in response.content.decode()
    assert (
        "http://testserver/cog/tiles/WebMercatorQuad/{TileMatrix}/{TileCol}/{TileRow}@1x.png?url=https"
        in response.content.decode()
    )

    response = app.get(
        "/cog/WMTSCapabilities.xml?url=https://myurl.com/cog.tif&tile_scale=2&tile_format=jpg"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"
    assert (
        "http://testserver/cog/tiles/WebMercatorQuad/{TileMatrix}/{TileCol}/{TileRow}@2x.jpg?url=https"
        in response.content.decode()
    )


@patch("rio_tiler.io.cogeo.rasterio")
def test_tile(rio, app):
    """test tile endpoints."""
    rio.open = mock_rasterio_open

    # full tile
    response = app.get(
        "/cog/tiles/8/87/48?url=https://myurl.com/cog.tif&rescale=0,1000"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert response.headers["Cache-Control"] == "private, max-age=3600"
    meta = parse_img(response.content)
    assert meta["width"] == 256
    assert meta["height"] == 256

    response = app.get(
        "/cog/tiles/8/87/48@2x?url=https://myurl.com/cog.tif&rescale=0,1000&color_formula=Gamma R 3"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    meta = parse_img(response.content)
    assert meta["width"] == 512
    assert meta["height"] == 512

    response = app.get(
        "/cog/tiles/8/87/48.jpg?url=https://myurl.com/cog.tif&rescale=0,1000"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    response = app.get(
        "/cog/tiles/8/87/48@2x.jpg?url=https://myurl.com/cog.tif&rescale=0,1000"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    response = app.get(
        "/cog/tiles/8/87/48@2x.tif?url=https://myurl.com/cog.tif&nodata=0&bidx=1"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff"
    meta = parse_img(response.content)
    assert meta["dtype"] == "uint16"
    assert meta["count"] == 2
    assert meta["width"] == 512
    assert meta["height"] == 512

    response = app.get("/cog/tiles/8/87/48.npy?url=https://myurl.com/cog.tif&nodata=0")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/x-binary"
    t, m = numpy.load(BytesIO(response.content), allow_pickle=True)
    assert t.shape == (1, 256, 256)
    assert m.shape == (256, 256)

    # partial
    response = app.get(
        "/cog/tiles/8/84/47?url=https://myurl.com/cog.tif&rescale=0,1000"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    response = app.get(
        "/cog/tiles/8/84/47?url=https://myurl.com/cog.tif&nodata=0&rescale=0,1000&color_map=viridis"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    response = app.get(
        "/cog/tiles/8/53/50.png?url=https://myurl.com/above_cog.tif&bidx=1&color_map=above"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    response = app.get(
        "/cog/tiles/8/53/50.png?url=https://myurl.com/above_cog.tif&bidx=1&color_map=above&resampling_method=somethingwrong"
    )
    assert response.status_code == 422


@patch("rio_tiler.io.cogeo.rasterio")
def test_tilejson(rio, app):
    """test /tilejson endpoint."""
    rio.open = mock_rasterio_open

    response = app.get("/cog/tilejson.json?url=https://myurl.com/cog.tif")
    assert response.status_code == 200
    body = response.json()
    assert body["tilejson"] == "2.2.0"
    assert body["version"] == "1.0.0"
    assert body["scheme"] == "xyz"
    assert len(body["tiles"]) == 1
    assert body["tiles"][0].startswith(
        "http://testserver/cog/tiles/WebMercatorQuad/{z}/{x}/{y}@1x?url=https"
    )
    assert body["minzoom"] == 5
    assert body["maxzoom"] == 8
    assert body["bounds"]
    assert body["center"]

    response = app.get(
        "/cog/tilejson.json?url=https://myurl.com/cog.tif&tile_format=png&tile_scale=2"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["tiles"][0].startswith(
        "http://testserver/cog/tiles/WebMercatorQuad/{z}/{x}/{y}@2x.png?url=https"
    )


@patch("rio_tiler.io.cogeo.rasterio")
def test_preview(rio, app):
    """test /preview endpoint."""
    rio.open = mock_rasterio_open

    response = app.get(
        "/cog/preview?url=https://myurl.com/cog.tif&rescale=0,1000&max_size=256"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    meta = parse_img(response.content)
    assert meta["width"] == 256
    assert meta["height"] == 256
    assert meta["driver"] == "JPEG"

    response = app.get(
        "/cog/preview.png?url=https://myurl.com/cog.tif&rescale=0,1000&max_size=256"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["width"] == 256
    assert meta["height"] == 256
    assert meta["driver"] == "PNG"

    response = app.get(
        "/cog/preview.png?url=https://myurl.com/cog.tif&rescale=0,1000&max_size=128&width=512&height=512"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["width"] == 512
    assert meta["height"] == 512
    assert meta["driver"] == "PNG"

    response = app.get(
        "/cog/preview.npy?url=https://myurl.com/cog.tif&rescale=0,1000&max_size=1024"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/x-binary"
    t, m = numpy.load(BytesIO(response.content), allow_pickle=True)
    assert t.shape == (1, 1024, 1021)
    assert m.shape == (1024, 1021)


@patch("rio_tiler.io.cogeo.rasterio")
def test_part(rio, app):
    """test /crop endpoint."""
    rio.open = mock_rasterio_open

    response = app.get(
        "/cog/crop/-56.228,72.715,-54.547,73.188.png?url=https://myurl.com/cog.tif&rescale=0,1000&max_size=256"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["width"] == 256
    assert meta["height"] == 73
    assert meta["driver"] == "PNG"

    # response = app.get(
    #     "/cog/crop/-56.228,72.715,-54.547,73.188?url=https://myurl.com/cog.tif&rescale=0,1000&max_size=256"
    # )
    # assert response.status_code == 200
    # assert response.headers["content-type"] == "image/png"
    # meta = parse_img(response.content)
    # assert meta["width"] == 256
    # assert meta["height"] == 73
    # assert meta["driver"] == "PNG"

    response = app.get(
        "/cog/crop/-56.228,72.715,-54.547,73.188.png?url=https://myurl.com/cog.tif&rescale=0,1000&max_size=256&width=512&height=512"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["width"] == 512
    assert meta["height"] == 512
    assert meta["driver"] == "PNG"

    response = app.get(
        "/cog/crop/-56.228,72.715,-54.547,73.188.npy?url=https://myurl.com/cog.tif&rescale=0,1000&max_size=256"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/x-binary"
    t, m = numpy.load(BytesIO(response.content), allow_pickle=True)
    assert t.shape == (1, 73, 256)
    assert m.shape == (73, 256)


@patch("rio_tiler.io.cogeo.rasterio")
def test_point(rio, app):
    """test /point endpoint."""
    rio.open = mock_rasterio_open

    response = app.get("/cog/point/-56.228,72.715?url=https://myurl.com/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    body = response.json()
    assert body["coordinates"] == [-56.228, 72.715]


def test_file_not_found_error(app):
    response = app.get("/cog/info?url=foo.tif")
    assert response.status_code == 404


@patch("rio_tiler.io.cogeo.rasterio")
def test_tile_outside_bounds_error(rio, app):
    rio.open = mock_rasterio_open

    response = app.get("/cog/tiles/15/0/0?url=https://myurl.com/cog.tif&rescale=0,1000")
    assert response.status_code == 404
    # NOT THIS MIGHT CHANGE
    assert response.headers["Cache-Control"] == "private, max-age=3600"


@pytest.mark.parametrize(
    "url",
    [os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR) if f.endswith(".tif")],
)
def test_validate_cog(app, url):
    """test /validate endpoint"""
    response = app.get(f"/cog/validate?url={os.path.join(DATA_DIR, 'cog.tif')}")
    assert response.status_code == 200
    assert response.json()["COG"]
