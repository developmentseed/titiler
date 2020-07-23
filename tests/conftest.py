"""``pytest`` configuration."""

import json
import os
from typing import Any, Dict

import pytest
import rasterio
from rasterio.io import MemoryFile
from rio_tiler_crs import COGReader, STACReader

from starlette.testclient import TestClient

DATA_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


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
    monkeypatch.setenv("DEFAULT_MOSAIC_BACKEND", "file://")
    monkeypatch.setenv("DEFAULT_MOSAIC_HOST", DATA_DIR)

    from titiler.main import app

    return TestClient(app)


def mock_reader(src_path: str, *args, **kwargs) -> COGReader:
    """Mock rasterio.open."""
    assert src_path.startswith("https://myurl.com/")
    cog_path = os.path.basename(src_path)
    return COGReader(os.path.join(DATA_DIR, cog_path), *args, **kwargs)


def mock_STACreader(src_path: str, *args, **kwargs) -> COGReader:
    """Mock rasterio.open."""
    assert src_path.startswith("https://myurl.com/")
    stac_path = os.path.basename(src_path)
    return STACReader(os.path.join(DATA_DIR, stac_path), *args, **kwargs)


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
            return dst.meta
