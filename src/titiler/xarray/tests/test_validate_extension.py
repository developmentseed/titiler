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
zarr_coord = os.path.join(prefix, "zarr_invalid_coord.zarr")
zarr_coord_name = os.path.join(prefix, "zarr_invalid_coord_name.zarr")
zarr_5d = os.path.join(prefix, "zarr_5d.zarr")


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

    resp = app_zarr.get(
        "/md/validate",
        params={"url": zarr_coord},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    val = resp.json()
    assert list(val) == ["dataset"]
    assert not val["dataset"]["compatible_with_titiler"]
    assert val["dataset"]["errors"] == [
        "Dataset bounds are not valid, must be in [-180, 180] and [-90, 90]"
    ]

    resp = app_zarr.get(
        "/md/validate",
        params={"url": zarr_coord},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    val = resp.json()
    assert list(val) == ["dataset"]
    assert not val["dataset"]["compatible_with_titiler"]
    assert val["dataset"]["errors"] == [
        "Dataset bounds are not valid, must be in [-180, 180] and [-90, 90]"
    ]

    resp = app_zarr.get(
        "/md/validate",
        params={"url": zarr_5d},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    val = resp.json()
    assert list(val) == ["dataset"]
    assert val["dataset"]["compatible_with_titiler"]
    assert val["dataset"]["warnings"] == [
        "DataArray has too many dimension (5) for titiler.xarray, dimensions reduction (sel) will be required."
    ]
