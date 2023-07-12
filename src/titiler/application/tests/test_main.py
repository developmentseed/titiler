"""Test titiler.application.main.app."""


def test_health(app):
    """Test /healthz endpoint."""
    response = app.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"ping": "pong!"}

    response = app.get("/openapi.json")
    assert response.status_code == 200

    response = app.get("/docs")
    assert response.status_code == 200
