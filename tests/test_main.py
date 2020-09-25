"""Test titiler.main.app."""


def test_health(app):
    """Test /ping endpoint."""
    response = app.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"ping": "pong!"}
    assert response.headers["server-timing"]
