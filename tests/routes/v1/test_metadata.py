"""test /v1/metadata endpoints."""

from unittest.mock import patch

from ...conftest import mock_reader


@patch("titiler.api.api_v1.endpoints.metadata.COGReader")
def test_bounds(reader, app):
    """test /bounds endpoint."""
    reader.side_effect = mock_reader

    response = app.get("/v1/cog/bounds?url=https://myurl.com/cog.tif")
    assert response.status_code == 200
    body = response.json()
    assert len(body["bounds"]) == 4


@patch("titiler.api.api_v1.endpoints.metadata.COGReader")
def test_metadata(reader, app):
    """test /metadata endpoint."""
    reader.side_effect = mock_reader

    response = app.get("/v1/cog/metadata?url=https://myurl.com/cog.tif")
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
        "/v1/cog/metadata?url=https://myurl.com/cog.tif&histogram_bins=5&histogram_range=1,1000&nodata=0"
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["statistics"]["1"]["histogram"][0]) == 5
