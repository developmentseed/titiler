"""test titiler.xarray factory."""
import os

import pytest
from fastapi import FastAPI
from rasterio.io import MemoryFile
from starlette.testclient import TestClient

from titiler.xarray.extensions import VariablesExtension
from titiler.xarray.factory import TilerFactory

prefix = os.path.join(os.path.dirname(__file__), "fixtures")

dataset_2d_nc = os.path.join(prefix, "dataset_2d.nc")
dataset_3d_nc = os.path.join(prefix, "dataset_3d.nc")
dataset_3d_zarr = os.path.join(prefix, "dataset_3d.zarr")
dataset_4d_nc = os.path.join(prefix, "dataset_4d.nc")
zarr_pyramid = os.path.join(prefix, "pyramid.zarr")


def test_tiler_factory():
    """Test factory with options."""
    """Test TilerFactory class."""
    md = TilerFactory(
        add_viewer=False, add_part=False, extensions=[VariablesExtension()]
    )
    assert len(md.router.routes) == 14

    md = TilerFactory(router_prefix="/md", extensions=[VariablesExtension()])
    assert len(md.router.routes) == 20

    app = FastAPI()
    app.include_router(md.router, prefix="/md")
    client = TestClient(app)

    response = client.get("/openapi.json")
    assert response.status_code == 200

    response = client.get("/docs")
    assert response.status_code == 200


@pytest.fixture
def app():
    """App fixture."""
    md = TilerFactory(router_prefix="/md", extensions=[VariablesExtension()])
    assert len(md.router.routes) == 20

    app = FastAPI()
    app.include_router(md.router, prefix="/md")
    client = TestClient(app)

    with TestClient(app) as client:
        yield client


@pytest.mark.parametrize(
    "filename",
    [dataset_2d_nc, dataset_3d_nc, dataset_3d_zarr],
)
def test_variable(filename, app):
    """Test /variables endpoint."""
    resp = app.get("/md/variables", params={"url": filename})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    assert resp.json() == ["dataset"]


@pytest.mark.parametrize(
    "filename",
    [dataset_2d_nc, dataset_3d_nc, dataset_3d_zarr],
)
def test_bounds(filename, app):
    """Test /bounds endpoint."""
    # missing variable parameter
    resp = app.get("/md/bounds", params={"url": filename})
    assert resp.status_code == 422

    resp = app.get("/md/bounds", params={"url": filename, "variable": "dataset"})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"


@pytest.mark.parametrize(
    "filename",
    [dataset_2d_nc, dataset_3d_nc, dataset_3d_zarr],
)
def test_info(filename, app):
    """Test /info endpoints."""
    # missing variable parameter
    resp = app.get("/md/info", params={"url": filename})
    assert resp.status_code == 422

    resp = app.get("/md/info", params={"url": filename, "variable": "dataset"})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"

    resp = app.get(
        "/md/info", params={"url": filename, "variable": "dataset", "show_times": True}
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"

    resp = app.get("/md/info.geojson", params={"url": filename, "variable": "dataset"})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/geo+json"

    resp = app.get(
        "/md/info.geojson",
        params={"url": filename, "variable": "dataset", "show_times": True},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/geo+json"


def test_info_da_options(app):
    """Test /info endpoints with Dataarray options."""
    resp = app.get(
        "/md/info",
        params={"url": dataset_4d_nc, "variable": "dataset", "drop_dims": "z=0"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"

    resp = app.get(
        "/md/info",
        params={
            "url": dataset_3d_nc,
            "variable": "dataset",
            "datetime": "2023-01-01",
            "decode_times": True,
        },
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"


@pytest.mark.parametrize(
    "filename",
    [dataset_2d_nc, dataset_3d_nc, dataset_3d_zarr],
)
def test_tiles(filename, app):
    """Test /tiles endpoints."""
    # missing variable parameter
    resp = app.get("/md/tiles/WebMercatorQuad/0/0/0", params={"url": filename})
    assert resp.status_code == 422

    resp = app.get(
        "/md/tiles/WebMercatorQuad/0/0/0",
        params={"url": filename, "variable": "dataset", "rescale": "0,500"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"

    resp = app.get(
        "/md/tiles/WebMercatorQuad/0/0/0.jpeg",
        params={"url": filename, "variable": "dataset", "rescale": "0,500"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/jpeg"

    resp = app.get(
        "/md/WebMercatorQuad/tilejson.json",
        params={"url": filename, "variable": "dataset", "rescale": "0,500"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"


@pytest.mark.parametrize(
    "filename",
    [dataset_2d_nc, dataset_3d_nc, dataset_3d_zarr],
)
def test_point(filename, app):
    """Test /point endpoint."""
    # missing variable parameter
    resp = app.get("/md/point/0,0", params={"url": filename})
    assert resp.status_code == 422

    resp = app.get("/md/point/0,0", params={"url": filename, "variable": "dataset"})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"


@pytest.mark.parametrize(
    "filename",
    [dataset_2d_nc, dataset_3d_nc, dataset_3d_zarr],
)
def test_statistics(filename, app):
    """Test /statistics endpoint."""
    feat = {
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    (-100.0, -25.0),
                    (40.0, -25.0),
                    (40.0, 60.0),
                    (-100.0, 60.0),
                    (-100.0, -25.0),
                ]
            ],
        },
    }

    # missing variable parameter
    resp = app.post("/md/statistics", params={"url": filename}, json=feat)
    assert resp.status_code == 422

    resp = app.post(
        "/md/statistics", params={"url": filename, "variable": "dataset"}, json=feat
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/geo+json"

    resp = app.post(
        "/md/statistics",
        params={
            "url": filename,
            "variable": "dataset",
            "max_size": 100,
            "resampling_method": "bilinear",
        },
        json=feat,
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/geo+json"

    resp = app.post(
        "/md/statistics",
        params={"url": filename, "variable": "dataset", "height": 100, "width": 100},
        json=feat,
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/geo+json"


@pytest.mark.parametrize(
    "filename",
    [dataset_2d_nc, dataset_3d_nc, dataset_3d_zarr],
)
def test_part(filename, app):
    """Test /feature and /bbox endpoints."""
    feat = {
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    (-100.0, -25.0),
                    (40.0, -25.0),
                    (40.0, 60.0),
                    (-100.0, 60.0),
                    (-100.0, -25.0),
                ]
            ],
        },
    }

    # missing variable parameter
    resp = app.post("/md/feature", params={"url": filename}, json=feat)
    assert resp.status_code == 422

    resp = app.post(
        "/md/feature",
        params={"url": filename, "variable": "dataset", "rescale": "0,500"},
        json=feat,
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/jpeg"

    resp = app.post(
        "/md/feature.png",
        params={"url": filename, "variable": "dataset", "rescale": "0,500"},
        json=feat,
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"

    resp = app.post(
        "/md/feature/100x100.png",
        params={"url": filename, "variable": "dataset", "rescale": "0,500"},
        json=feat,
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"

    resp = app.get(
        "/md/bbox/-100,-25,40,60.jpeg",
        params={"url": filename, "variable": "dataset", "rescale": "0,500"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/jpeg"

    resp = app.get(
        "/md/bbox/-100,-25,40,60/100x100.png",
        params={"url": filename, "variable": "dataset", "rescale": "0,500"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"


@pytest.mark.parametrize(
    "group",
    [0, 1, 2],
)
def test_zarr_group(group, app):
    """Test /tiles endpoints."""
    resp = app.get(
        f"/md/tiles/WebMercatorQuad/{group}/0/0.tif",
        params={"url": zarr_pyramid, "variable": "dataset", "group": group},
    )
    assert resp.status_code == 200
    # see src/titiler/xarray/tests/fixtures/generate_fixtures.ipynb
    # for structure of zarr pyramid
    with MemoryFile(resp.content) as mem:
        with mem.open() as dst:
            arr = dst.read(1)
            assert arr.max() == group * 2

    resp = app.get(
        "/md/point/0,0",
        params={"url": zarr_pyramid, "variable": "dataset", "group": group},
    )
    assert resp.json()["values"] == [group * 2]
