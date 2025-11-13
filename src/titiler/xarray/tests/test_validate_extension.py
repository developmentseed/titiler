"""test titiler.xarray factory."""

import os

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from titiler.xarray.extensions import ValidateExtension
from titiler.xarray.factory import TilerFactory

prefix = os.path.join(os.path.dirname(__file__), "fixtures")
dataset_3d_zarr = os.path.join(prefix, "dataset_3d.zarr")
zarr_pyramid = os.path.join(prefix, "pyramid.zarr")


@pytest.fixture
def app_zarr():
    """App fixture."""
    md = TilerFactory(
        router_prefix="/md",
        extensions=[
            ValidateExtension(),
        ],
    )
    assert len(md.router.routes) == 19

    app = FastAPI()
    app.include_router(md.router, prefix="/md")
    with TestClient(app) as client:
        yield client


def test_validate_extension(app_zarr):
    """Test /dataset endpoints."""
    resp = app_zarr.get("/md/validate", params={"url": dataset_3d_zarr})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    assert list(resp.json()) == ["dataset"]
    assert resp.json()["dataset"]["compatible_with_titiler"]

    resp = app_zarr.get(
        "/md/validate", params={"url": dataset_3d_zarr, "variables": "dataset"}
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    assert list(resp.json()) == ["dataset"]
    assert resp.json()["dataset"]["compatible_with_titiler"]

    resp = app_zarr.get("/md/validate", params={"url": zarr_pyramid, "group": "0"})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    assert list(resp.json()) == ["dataset"]
    assert resp.json()["dataset"]["compatible_with_titiler"]

    resp = app_zarr.get(
        "/md/validate",
        params={"url": zarr_pyramid, "group": "0", "variables": "dataset"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    assert list(resp.json()) == ["dataset"]
    assert resp.json()["dataset"]["compatible_with_titiler"]
