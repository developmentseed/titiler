"""test /v1/metadata endpoints."""

# from typing import Dict

from mock import patch

from ...conftest import mock_rio


@patch("titiler.api.api_v1.endpoints.metadata.cogeo.rasterio")
def test_tilejson(rio, app):
    """test /tilejson endpoint."""
    rio.open = mock_rio

    response = app.get("/v1/tilejson.json?url=https://myurl.com/cog.tif")
    assert response.status_code == 200
    body = response.json()
    assert body["tilejson"] == "2.2.0"
    assert body["version"] == "1.0.0"
    assert body["scheme"] == "xyz"
    assert len(body["tiles"]) == 1
    assert body["tiles"][0].startswith("http://testserver/v1/{z}/{x}/{y}@1x?url=https")
    assert body["minzoom"] == 5
    assert body["maxzoom"] == 8
    assert body["bounds"]
    assert body["center"]

    response = app.get(
        "/v1/tilejson.json?url=https://myurl.com/cog.tif&tile_format=png&tile_scale=2"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["tiles"][0].startswith(
        "http://testserver/v1/{z}/{x}/{y}@2x.png?url=https"
    )


@patch("titiler.api.api_v1.endpoints.metadata.cogeo.rasterio")
def test_bounds(rio, app):
    """test /bounds endpoint."""
    rio.open = mock_rio

    response = app.get("/v1/bounds?url=https://myurl.com/cog.tif")
    assert response.status_code == 200
    body = response.json()
    assert body["address"] == "https://myurl.com/cog.tif"
    assert len(body["bounds"]) == 4


@patch("titiler.api.api_v1.endpoints.metadata.cogeo.rasterio")
def test_metadata(rio, app):
    """test /metadata endpoint."""
    rio.open = mock_rio

    response = app.get("/v1/metadata?url=https://myurl.com/cog.tif")
    assert response.status_code == 200
    body = response.json()
    assert body["address"] == "https://myurl.com/cog.tif"
    assert len(body["bounds"]) == 4
    assert body["statistics"]
    assert len(body["statistics"]["1"]["histogram"][0]) == 20
    assert body["band_descriptions"] == [[1, "band1"]]
    assert body["dtype"] == "uint16"
    assert body["colorinterp"] == ["gray"]
    assert body["nodata_type"] == "None"

    response = app.get(
        "/v1/metadata?url=https://myurl.com/cog.tif&histogram_bins=5&histogram_range=1,1000&nodata=0"
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["statistics"]["1"]["histogram"][0]) == 5
