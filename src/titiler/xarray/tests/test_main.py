"""test titiler.xarray application."""

import os

import pytest
from starlette.testclient import TestClient

from titiler.xarray.main import app

prefix = os.path.join(os.path.dirname(__file__), "fixtures")
dataset_3d_zarr = os.path.join(prefix, "dataset_3d.zarr")
zarr_5d = os.path.join(prefix, "zarr_5d.zarr")

client = TestClient(app)
base_params = {"url": dataset_3d_zarr, "variable": "dataset", "rescale": "0,1"}
t0 = "2022-01-01T00:00:00.000000000"


@pytest.mark.parametrize(
    "path",
    ["/tiles/WebMercatorQuad/0/0/0.png", "/info", "/WebMercatorQuad/tilejson.json"],
)
@pytest.mark.parametrize(
    "name,value",
    [
        ("datetime", t0),
        ("drop_dim", "time=2022-01-01"),
    ],
)
def test_removed_params_rejected(path, name, value):
    """Query-parameters removed in titiler.xarray 0.22 return 400 instead of being ignored."""
    response = client.get(path, params={**base_params, name: value})
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert name in detail
    assert "sel=" in detail


@pytest.mark.parametrize(
    "params",
    [
        {"datetime": t0},
        {"drop_dim": "time=2022-01-01"},
    ],
)
def test_removed_params_rejected_when_sel_skips_their_dimension(params):
    """`sel` on other dimensions leaves `time` unselected, so the request is still rejected."""
    response = client.get(
        "/tiles/WebMercatorQuad/0/0/0.png",
        params={
            "url": zarr_5d,
            "variable": "dataset",
            "rescale": "0,1",
            "sel": ["universe=somewhere", "z=0"],
            **params,
        },
    )
    assert response.status_code == 400


@pytest.mark.parametrize(
    "path,media_type",
    [
        ("/tiles/WebMercatorQuad/0/0/0.png", "image/png"),
        ("/WebMercatorQuad/tilejson.json", "application/json"),
    ],
)
@pytest.mark.parametrize(
    "params",
    [
        {},
        {"datetime": t0},
        {"drop_dim": "time=2022-01-01"},
    ],
)
def test_sel_still_works(path, media_type, params):
    """`sel` selection works, also next to a removed parameter on the same dimension."""
    response = client.get(path, params={**base_params, **params, "sel": f"time={t0}"})
    assert response.status_code == 200
    assert response.headers["content-type"] == media_type
