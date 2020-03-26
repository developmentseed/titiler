"""Test titiler.main.app."""


def test_health(app):
    """Test /ping endpoint."""
    response = app.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"ping": "pong!"}


def test_index(app):
    """Test /ping endpoint."""
    response = app.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert response.headers["content-encoding"] == "gzip"

    response = app.get("/index.html")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert response.headers["content-encoding"] == "gzip"
