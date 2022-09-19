"""``pytest`` configuration."""

import json
import os
from importlib import reload
from typing import Any, Dict

import pytest
import rasterio
from rasterio.io import MemoryFile

import titiler.application.main as main

from starlette.testclient import TestClient

DATA_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def set_env(monkeypatch, request):
    """Set Env variables."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "jqt")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "rde")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-west-2")
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    monkeypatch.setenv("AWS_CONFIG_FILE", "/tmp/noconfigheere")
    monkeypatch.setenv("TITILER_API_CACHECONTROL", "private, max-age=3600")

    # Support additional env vars via parametrization:
    additional_env_vars = getattr(request, "param", {})
    for key, value in additional_env_vars.items():
        monkeypatch.setenv(key, value)


@pytest.fixture(autouse=True)
def app(set_env) -> TestClient:
    """Create App."""
    # Reload to consume latest environment variables:
    reload(main)

    return TestClient(main.app)


def mock_RequestGet(src_path):
    """Mock Requests."""
    # HTTP
    class MockResponse:
        def __init__(self, data):
            self.data = data

        def json(self):
            return json.loads(self.data)

        def raise_for_status(self):
            return True

    assert src_path.startswith("https://myurl.com/")
    stac_path = os.path.basename(src_path)
    with open(os.path.join(DATA_DIR, stac_path), "r") as f:
        return MockResponse(f.read())


def mock_rasterio_open(asset):
    """Mock rasterio Open."""
    assert asset.startswith("https://myurl.com/")
    asset = asset.replace("https://myurl.com", DATA_DIR)
    return rasterio.open(asset)


def read_json_fixture(fname: str) -> Dict[Any, Any]:
    """Read json from test directory."""
    with open(os.path.join(DATA_DIR, fname)) as f:
        return json.load(f)


def parse_img(content: bytes) -> Dict[Any, Any]:
    """Read tile image and return metadata."""
    with MemoryFile(content) as mem:
        with mem.open() as dst:
            return dst.profile
