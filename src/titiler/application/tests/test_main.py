"""Test titiler.application.main.app."""


def test_health(app):
    """Test /healthz endpoint."""
    response = app.get("/healthz")
    assert response.status_code == 200
    assert set(response["versions"].keys()) == {
        "titiler",
        "gdal",
        "geos",
        "proj",
        "rasterio",
    }

    response = app.get("/api")
    assert response.status_code == 200

    response = app.get("/api.html")
    assert response.status_code == 200
