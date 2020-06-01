"""test /v1/metadata endpoints."""

from unittest.mock import patch

from ...conftest import mock_reader


@patch("titiler.api.api_v1.endpoints.ogc.COGReader")
def test_wmts(reader, app):
    """test wmts endpoints."""
    reader.side_effect = mock_reader

    response = app.get("/v1/cogs/WMTSCapabilities.xml?url=https://myurl.com/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"
    assert (
        "http://testserver/v1/cogs/WebMercatorQuad/{TileMatrix}/{TileCol}/{TileRow}@1x.png?url=https"
        in response.content.decode()
    )

    response = app.get(
        "/v1/cogs/WMTSCapabilities.xml?url=https://myurl.com/cog.tif&tile_scale=2&tile_format=jpg"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"
    assert (
        "http://testserver/v1/cogs/WebMercatorQuad/{TileMatrix}/{TileCol}/{TileRow}@2x.jpg?url=https"
        in response.content.decode()
    )
