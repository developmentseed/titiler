"""test /COG endpoints."""

import os

from ..conftest import DATA_DIR

dataset_3d_zarr = os.path.join(DATA_DIR, "dataset_3d.zarr")


def test_zarr_endpoints(app):
    """test zarr endpoint."""
    resp = app.get("/zarr/validate", params={"url": dataset_3d_zarr})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    assert list(resp.json()) == ["dataset"]
    assert resp.json()["dataset"]["compatible_with_titiler"]

    resp = app.get("/zarr/dataset/keys", params={"url": dataset_3d_zarr})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    assert resp.json() == ["dataset"]

    resp = app.get("/zarr/info", params={"url": dataset_3d_zarr, "variable": "dataset"})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"

    resp = app.get(
        "/zarr/tiles/WebMercatorQuad/0/0/0",
        params={
            "url": dataset_3d_zarr,
            "variable": "dataset",
            "rescale": "0,500",
            "bidx": 1,
        },
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
