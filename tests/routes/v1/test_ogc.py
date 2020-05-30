"""test /v1/metadata endpoints."""

# from typing import Dict

from mock import patch

from ...conftest import mock_rio


@patch("titiler.api.api_v1.endpoints.ogc.rasterio")
def test_wmts(rio, app):
    """test wmts endpoints."""
    rio.open = mock_rio

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
