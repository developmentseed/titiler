"""test /COG endpoints."""

import json
import os
from io import BytesIO
from unittest.mock import patch
from urllib.parse import parse_qsl, urlparse

import numpy
import pytest

from ..conftest import DATA_DIR, mock_rasterio_open, parse_img


@patch("rio_tiler.io.rasterio.rasterio")
def test_bounds(rio, app):
    """test /bounds endpoint."""
    rio.open = mock_rasterio_open

    response = app.get("/cog/bounds?url=https://myurl.com/cog.tif")
    assert response.status_code == 200
    body = response.json()
    assert len(body["bounds"]) == 4
    assert response.headers["Cache-Control"] == "private, max-age=3600"


@patch("rio_tiler.io.rasterio.rasterio")
def test_info(rio, app):
    """test /info endpoint."""
    rio.open = mock_rasterio_open

    response = app.get("/cog/info?url=https://myurl.com/cog.tif")
    assert response.status_code == 200
    body = response.json()
    assert len(body["bounds"]) == 4
    assert body["band_descriptions"] == [["b1", ""]]
    assert body["dtype"] == "uint16"
    assert body["colorinterp"] == ["gray"]
    assert body["nodata_type"] == "None"

    response = app.get("/cog/info.geojson?url=https://myurl.com/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    body = response.json()
    assert body["geometry"]
    assert body["properties"]["band_descriptions"] == [["b1", ""]]
    assert body["properties"]["dtype"] == "uint16"
    assert body["properties"]["colorinterp"] == ["gray"]
    assert body["properties"]["nodata_type"] == "None"


@patch("rio_tiler.io.rasterio.rasterio")
def test_wmts(rio, app):
    """test wmts endpoints."""
    rio.open = mock_rasterio_open

    response = app.get(
        "/cog/WebMercatorQuad/WMTSCapabilities.xml?url=https://myurl.com/cog.tif"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"
    assert response.headers["Cache-Control"] == "private, max-age=3600"
    assert (
        "http://testserver/cog/WebMercatorQuad/WMTSCapabilities.xml?url=https"
        in response.content.decode()
    )
    assert "<ows:Identifier>Dataset</ows:Identifier>" in response.content.decode()
    assert (
        "http://testserver/cog/tiles/WebMercatorQuad/{TileMatrix}/{TileCol}/{TileRow}@1x.png?url=https"
        in response.content.decode()
    )
    assert (
        "<ows:SupportedCRS>http://www.opengis.net/def/crs/EPSG/0/3857</ows:SupportedCRS>"
        in response.content.decode()
    )

    response = app.get(
        "/cog/WebMercatorQuad/WMTSCapabilities.xml?url=https://myurl.com/cog.tif&tile_scale=2&tile_format=jpg"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"
    assert (
        "http://testserver/cog/tiles/WebMercatorQuad/{TileMatrix}/{TileCol}/{TileRow}@2x.jpg?url=https"
        in response.content.decode()
    )

    response = app.get(
        "/cog/WebMercatorQuad/WMTSCapabilities.xml?url=https://myurl.com/cog.tif&use_epsg=true"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"
    assert "<ows:SupportedCRS>EPSG:3857</ows:SupportedCRS>" in response.content.decode()


@patch("rio_tiler.io.rasterio.rasterio")
def test_tile(rio, app):
    """test tile endpoints."""
    rio.open = mock_rasterio_open

    # full tile
    response = app.get(
        "/cog/tiles/WebMercatorQuad/8/87/48?url=https://myurl.com/cog.tif&rescale=0,1000"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert response.headers["Cache-Control"] == "private, max-age=3600"
    meta = parse_img(response.content)
    assert meta["width"] == 256
    assert meta["height"] == 256

    response = app.get(
        "/cog/tiles/WebMercatorQuad/8/87/48@2x?url=https://myurl.com/cog.tif&rescale=0,1000&color_formula=Gamma R 3"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    meta = parse_img(response.content)
    assert meta["width"] == 512
    assert meta["height"] == 512

    response = app.get(
        "/cog/tiles/WebMercatorQuad/8/87/48.jpg?url=https://myurl.com/cog.tif&rescale=0,1000"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpg"

    response = app.get(
        "/cog/tiles/WebMercatorQuad/8/87/48.jpeg?url=https://myurl.com/cog.tif&rescale=0,1000"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    response = app.get(
        "/cog/tiles/WebMercatorQuad/8/87/48@2x.jpg?url=https://myurl.com/cog.tif&rescale=0,1000"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpg"

    response = app.get(
        "/cog/tiles/WebMercatorQuad/8/87/48@2x.tif?url=https://myurl.com/cog.tif&nodata=0&bidx=1"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff; application=geotiff"
    meta = parse_img(response.content)
    assert meta["dtype"] == "uint16"
    assert meta["count"] == 2
    assert meta["width"] == 512
    assert meta["height"] == 512

    response = app.get(
        "/cog/tiles/WebMercatorQuad/8/87/48.npy?url=https://myurl.com/cog.tif&nodata=0"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/x-binary"
    data = numpy.load(BytesIO(response.content))
    assert data.shape == (2, 256, 256)

    response = app.get(
        "/cog/tiles/WebMercatorQuad/8/87/48.npy?url=https://myurl.com/cog.tif&nodata=0&return_mask=false"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/x-binary"
    data = numpy.load(BytesIO(response.content))
    assert data.shape == (1, 256, 256)

    # Test brotli compression
    headers = {"Accept-Encoding": "br"}
    response = app.get(
        "/cog/tiles/WebMercatorQuad/8/87/48.npy?url=https://myurl.com/cog.tif&nodata=0&return_mask=false",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.headers["content-encoding"] == "br"

    # Exclude png from compression middleware
    headers = {"Accept-Encoding": "br"}
    response = app.get(
        "/cog/tiles/WebMercatorQuad/8/87/48.png?url=https://myurl.com/cog.tif&nodata=0&return_mask=false",
        headers=headers,
    )
    assert response.status_code == 200
    assert "content-encoding" not in response.headers

    # Test gzip fallback
    headers = {"Accept-Encoding": "gzip"}
    response = app.get(
        "/cog/tiles/WebMercatorQuad/8/87/48.npy?url=https://myurl.com/cog.tif&nodata=0&return_mask=false",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.headers["content-encoding"] == "gzip"

    # partial
    response = app.get(
        "/cog/tiles/WebMercatorQuad/8/84/47?url=https://myurl.com/cog.tif&rescale=0,1000"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    response = app.get(
        "/cog/tiles/WebMercatorQuad/8/84/47?url=https://myurl.com/cog.tif&nodata=0&rescale=0,1000&colormap_name=viridis"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    # valid colormap
    response = app.get(
        "/cog/tiles/WebMercatorQuad/8/53/50.png",
        params={
            "url": "https://myurl.com/above_cog.tif",
            "bidx": 1,
            "colormap": json.dumps(
                {
                    "1": [58, 102, 24, 255],
                    "2": [100, 177, 41],
                    "3": "#b1b129",
                    "4": "#ddcb9aFF",
                }
            ),
        },
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    # invalid colormap shape
    response = app.get(
        "/cog/tiles/WebMercatorQuad/8/53/50.png",
        params={
            "url": "https://myurl.com/above_cog.tif",
            "bidx": 1,
            "colormap": json.dumps({"1": [58, 102]}),
        },
    )
    assert response.status_code == 400

    # bad resampling
    response = app.get(
        "/cog/tiles/WebMercatorQuad/8/53/50.png?url=https://myurl.com/above_cog.tif&bidx=1&resampling=somethingwrong"
    )
    assert response.status_code == 422

    response = app.get(
        "/cog/tiles/WebMercatorQuad/8/87/48@2x.tif?url=https://myurl.com/cog.tif&nodata=0&bidx=1&return_mask=false"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff; application=geotiff"
    meta = parse_img(response.content)
    assert meta["dtype"] == "uint16"
    assert meta["count"] == 1
    assert meta["width"] == 512
    assert meta["height"] == 512


@patch("rio_tiler.io.rasterio.rasterio")
def test_tilejson(rio, app):
    """test /tilejson endpoint."""
    rio.open = mock_rasterio_open

    response = app.get(
        "/cog/WebMercatorQuad/tilejson.json?url=https://myurl.com/cog.tif"
    )
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
    assert body["maxzoom"] == 9
    assert body["bounds"]
    assert body["center"]

    response = app.get(
        "/cog/WebMercatorQuad/tilejson.json?url=https://myurl.com/cog.tif&tile_format=png&tile_scale=2"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["tiles"][0].startswith(
        "http://testserver/cog/tiles/WebMercatorQuad/{z}/{x}/{y}@2x.png?url=https"
    )

    cmap_dict = {
        "1": [58, 102, 24, 255],
        "2": [100, 177, 41],
        "3": "#b1b129",
        "4": "#ddcb9aFF",
    }
    response = app.get(
        "/cog/WebMercatorQuad/tilejson.json",
        params={
            "url": "https://myurl.com/above_cog.tif",
            "bidx": 1,
            "colormap": json.dumps(cmap_dict),
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["tiles"][0].startswith(
        "http://testserver/cog/tiles/WebMercatorQuad/{z}/{x}/{y}@1x?url=https"
    )
    query = dict(parse_qsl(urlparse(body["tiles"][0]).query))
    assert json.loads(query["colormap"]) == cmap_dict


@patch("rio_tiler.io.rasterio.rasterio")
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
    assert meta["count"] == 2
    assert meta["width"] == 256
    assert meta["height"] == 256
    assert meta["driver"] == "PNG"

    response = app.get(
        "/cog/preview.png?url=https://myurl.com/cog.tif&rescale=0,1000&max_size=256&return_mask=false"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["count"] == 1
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
    data = numpy.load(BytesIO(response.content))
    assert data.shape == (2, 1024, 1021)


@patch("rio_tiler.io.rasterio.rasterio")
def test_part(rio, app):
    """test /bbox endpoint."""
    rio.open = mock_rasterio_open

    response = app.get(
        "/cog/bbox/-56.228,72.715,-54.547,73.188.png?url=https://myurl.com/cog.tif&rescale=0,1000&max_size=256"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["count"] == 2
    assert meta["width"] == 256
    assert meta["height"] == 73
    assert meta["driver"] == "PNG"

    response = app.get(
        "/cog/bbox/-56.228,72.715,-54.547,73.188.jpg?url=https://myurl.com/cog.tif&rescale=0,1000&max_size=256&return_mask=false"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpg"
    meta = parse_img(response.content)
    assert meta["count"] == 1
    assert meta["width"] == 256
    assert meta["height"] == 73
    assert meta["driver"] == "JPEG"

    response = app.get(
        "/cog/bbox/-56.228,72.715,-54.547,73.188/128x128.png?url=https://myurl.com/cog.tif&rescale=0,1000&max_size=256"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["width"] == 128
    assert meta["height"] == 128
    assert meta["driver"] == "PNG"

    response = app.get(
        "/cog/bbox/-56.228,72.715,-54.547,73.188.png?url=https://myurl.com/cog.tif&rescale=0,1000&max_size=256&width=512&height=512"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["width"] == 512
    assert meta["height"] == 512
    assert meta["driver"] == "PNG"

    response = app.get(
        "/cog/bbox/-56.228,72.715,-54.547,73.188.npy?url=https://myurl.com/cog.tif&rescale=0,1000&max_size=256"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/x-binary"
    data = numpy.load(BytesIO(response.content))
    assert data.shape == (2, 73, 256)


@patch("rio_tiler.io.rasterio.rasterio")
def test_point(rio, app):
    """test /point endpoint."""
    rio.open = mock_rasterio_open

    response = app.get("/cog/point/-56.228,72.715?url=https://myurl.com/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    body = response.json()
    assert body["coordinates"] == [-56.228, 72.715]


def test_file_not_found_error(app):
    """raise 404 when file is not found."""
    response = app.get("/cog/info?url=foo.tif")
    assert response.status_code == 500


@patch("rio_tiler.io.rasterio.rasterio")
def test_tile_outside_bounds_error(rio, app):
    """raise 404 when tile is not found."""
    rio.open = mock_rasterio_open

    response = app.get(
        "/cog/tiles/WebMercatorQuad/15/0/0?url=https://myurl.com/cog.tif&rescale=0,1000"
    )
    assert response.status_code == 404
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


@patch("rio_tiler.io.rasterio.rasterio")
def test_json_response_with_nan(rio, app):
    """test /info endpoint."""
    rio.open = mock_rasterio_open

    response = app.get("/cog/info?url=https://myurl.com/cog_with_nan.tif")
    assert response.status_code == 200
    body = response.json()
    assert body["dtype"] == "float32"
    assert body["nodata_type"] == "Nodata"
    assert body["nodata_value"] is None

    response = app.get("/cog/info.geojson?url=https://myurl.com/cog_with_nan.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    body = response.json()
    assert body["geometry"]
    assert body["properties"]["nodata_type"] == "Nodata"
    assert body["properties"]["nodata_value"] is None

    response = app.get(
        "/cog/point/79.80860440702253,21.852217086223234?url=https://myurl.com/cog_with_nan.tif"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["values"][0] is None
