"""test /COG endpoints."""


from io import BytesIO
from unittest.mock import patch

import numpy

from ..conftest import mock_reader, parse_img


@patch("titiler.api.endpoints.cog.COGReader")
def test_bounds(reader, app):
    """test /bounds endpoint."""
    reader.side_effect = mock_reader

    response = app.get("/cog/bounds?url=https://myurl.com/cog.tif")
    assert response.status_code == 200
    body = response.json()
    assert len(body["bounds"]) == 4


@patch("titiler.api.endpoints.cog.COGReader")
def test_info(reader, app):
    """test /info endpoint."""
    reader.side_effect = mock_reader

    response = app.get("/cog/info?url=https://myurl.com/cog.tif")
    assert response.status_code == 200
    body = response.json()
    assert len(body["bounds"]) == 4
    assert body["band_descriptions"] == [[1, "band1"]]
    assert body["dtype"] == "uint16"
    assert body["colorinterp"] == ["gray"]
    assert body["nodata_type"] == "None"


@patch("titiler.api.endpoints.cog.COGReader")
def test_metadata(reader, app):
    """test /metadata endpoint."""
    reader.side_effect = mock_reader

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


@patch("titiler.api.endpoints.cog.COGReader")
def test_wmts(reader, app):
    """test wmts endpoints."""
    reader.side_effect = mock_reader

    response = app.get("/cog/WMTSCapabilities.xml?url=https://myurl.com/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"
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


@patch("titiler.api.endpoints.cog.COGReader")
def test_tile(reader, app):
    """test tile endpoints."""
    reader.side_effect = mock_reader

    # full tile
    response = app.get(
        "/cog/tiles/8/87/48?url=https://myurl.com/cog.tif&rescale=0,1000"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
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


@patch("titiler.api.endpoints.cog.COGReader")
def test_tilejson(reader, app):
    """test /tilejson endpoint."""
    reader.side_effect = mock_reader

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


def test_viewer(app):
    """Test COG Viewer."""
    response = app.get("/cog/viewer")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert response.headers["content-encoding"] == "gzip"


@patch("titiler.api.endpoints.cog.COGReader")
def test_preview(reader, app):
    """test /preview endpoint."""
    reader.side_effect = mock_reader

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


@patch("titiler.api.endpoints.cog.COGReader")
def test_part(reader, app):
    """test /crop endpoint."""
    reader.side_effect = mock_reader

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


@patch("titiler.api.endpoints.cog.COGReader")
def test_point(reader, app):
    """test /point endpoint."""
    reader.side_effect = mock_reader

    response = app.get("/cog/point/-56.228,72.715?url=https://myurl.com/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    body = response.json()
    assert body["coordinates"] == [-56.228, 72.715]


def test_file_not_found_error(app):
    response = app.get("/cog/info?url=foo.tif")
    assert response.status_code == 404


@patch("titiler.api.endpoints.cog.COGReader")
def test_tile_outside_bounds_error(reader, app):
    reader.side_effect = mock_reader
    response = app.get("/cog/tiles/15/0/0?url=https://myurl.com/cog.tif&rescale=0,1000")
    assert response.status_code == 404
