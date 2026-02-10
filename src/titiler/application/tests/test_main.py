"""Test titiler.application.main.app."""


def test_health(app):
    """Test /healthz endpoint."""
    response = app.get("/healthz")
    assert response.status_code == 200
    resp = response.json()
    assert set(resp["versions"].keys()) == {
        "titiler",
        "gdal",
        "geos",
        "proj",
        "rasterio",
        "zarr",
        "xarray",
    }

    response = app.get("/api")
    assert response.status_code == 200

    response = app.get("/api.html")
    assert response.status_code == 200
