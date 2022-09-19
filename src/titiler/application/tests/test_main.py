"""Test titiler.application.main.app."""

import pytest


def test_health(app):
    """Test /healthz endpoint."""
    response = app.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"ping": "pong!"}


@pytest.mark.parametrize(
    "set_env", [{"TITILER_API_PATH_PREFIX": "/foo"}], indirect=True
)
def test_path_prefix(app):
    """Test /foo/healthz endpoint."""
    response = app.get("/foo/healthz")
    assert response.status_code == 200
    assert response.json() == {"ping": "pong!"}
