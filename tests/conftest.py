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

    from titiler.main import app

    return TestClient(app)


def mock_rio(src_path: str) -> DatasetReader:
    """Mock rasterio.open."""
    prefix = os.path.join(os.path.dirname(__file__), "fixtures")
    assert src_path.startswith("https://myurl.com/")
    return rasterio.open(os.path.join(prefix, "cog.tif"))
