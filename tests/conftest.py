"""``pytest`` configuration."""

import os
import pytest

from starlette.testclient import TestClient

import rasterio
from rasterio.io import DatasetReader


@pytest.fixture(autouse=True)
def app(monkeypatch) -> TestClient:
    """Make sure we use monkeypatch env."""
    monkeypatch.setenv("DISABLE_CACHE", "YESPLEASE")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "jqt")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "rde")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-west-2")
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    monkeypatch.setenv("AWS_CONFIG_FILE", "/tmp/noconfigheere")

    from titiler.main import app

    return TestClient(app)


def mock_rio(src_path: str) -> DatasetReader:
    """Mock rasterio.open."""
    prefix = os.path.join(os.path.dirname(__file__), "fixtures")
    assert src_path.startswith("https://myurl.com/")
    cog_path = os.path.basename(src_path)
    return rasterio.open(os.path.join(prefix, cog_path))
