"""test /COG endpoints."""


from typing import Dict

from unittest.mock import patch

from rasterio.io import MemoryFile

from ..conftest import mock_STACreader, mock_reader as mock_COGreader


@patch("titiler.api.endpoints.stac.STACReader")
def test_bounds(stac_reader, app):
    """test /bounds endpoint."""
    stac_reader.side_effect = mock_STACreader

    response = app.get("/stac/bounds?url=https://myurl.com/item.json")
    assert response.status_code == 200
    body = response.json()
    assert len(body["bounds"]) == 4


@patch("stac_tiler.reader.COGReader")
@patch("titiler.api.endpoints.stac.STACReader")
def test_info(stac_reader, cog_reader, app):
    """test /info endpoint."""
    stac_reader.side_effect = mock_STACreader
    cog_reader.side_effect = mock_COGreader

    response = app.get("/stac/info?url=https://myurl.com/item.json")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 17
    cog_reader.assert_not_called()

    response = app.get("/stac/info?url=https://myurl.com/item.json&assets=B01")
    assert response.status_code == 200
    body = response.json()
    assert body["B01"]
    cog_reader.assert_called_once()

    response = app.get("/stac/info?url=https://myurl.com/item.json&assets=B01,B09")
    assert response.status_code == 200
    body = response.json()
    assert body["B01"]
    assert body["B09"]


@patch("stac_tiler.reader.COGReader")
@patch("titiler.api.endpoints.stac.STACReader")
def test_metadata(stac_reader, cog_reader, app):
    """test /metadata endpoint."""
    stac_reader.side_effect = mock_STACreader
    cog_reader.side_effect = mock_COGreader

    response = app.get("/stac/metadata?url=https://myurl.com/item.json&assets=B01")
    assert response.status_code == 200
    body = response.json()
    assert body["B01"]
    cog_reader.assert_called_once()

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


@patch("stac_tiler.reader.COGReader")
@patch("titiler.api.endpoints.stac.STACReader")
def test_tile(stac_reader, cog_reader, app):
    """test tile endpoints."""
    stac_reader.side_effect = mock_STACreader
    cog_reader.side_effect = mock_COGreader

    response = app.get("/stac/tiles/9/289/207?url=https://myurl.com/item.json")
    assert response.status_code == 403

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


@patch("stac_tiler.reader.COGReader")
@patch("titiler.api.endpoints.stac.STACReader")
def test_tilejson(stac_reader, cog_reader, app):
    """test /tilejson endpoint."""
    stac_reader.side_effect = mock_STACreader
    cog_reader.side_effect = mock_COGreader

    response = app.get("/stac/tilejson.json?url=https://myurl.com/item.json")
    assert response.status_code == 403

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


def test_viewer(app):
    """Test STAC Viewer."""
    response = app.get("/stac/viewer")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert response.headers["content-encoding"] == "gzip"
