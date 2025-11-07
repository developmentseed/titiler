"""test titiler.xarray factory."""

import os

import pytest
from fastapi import FastAPI
from rasterio.io import MemoryFile
from starlette.testclient import TestClient

from titiler.xarray.extensions import DatasetMetadataExtension, VariablesExtension
from titiler.xarray.factory import TilerFactory
from titiler.xarray.io import FsReader, fs_open_dataset

prefix = os.path.join(os.path.dirname(__file__), "fixtures")

dataset_2d_nc = os.path.join(prefix, "dataset_2d.nc")
dataset_3d_nc = os.path.join(prefix, "dataset_3d.nc")
dataset_3d_zarr = os.path.join(prefix, "dataset_3d.zarr")
dataset_4d_nc = os.path.join(prefix, "dataset_4d.nc")
zarr_pyramid = os.path.join(prefix, "pyramid.zarr")


def test_deprecated_extension():
    """Test factory with options."""
    """Test TilerFactory class."""
    with pytest.warns(DeprecationWarning):
        md = TilerFactory(extensions=[VariablesExtension()])
    assert len(md.router.routes) == 20


def test_tiler_factory():
    """Test factory with options."""
    """Test TilerFactory class."""
    md = TilerFactory()
    assert len(md.router.routes) == 19

    with pytest.warns(UserWarning):
        md = TilerFactory(
            # /preview, /preview.{format}, /preview/{width}x{height}.{format}
            add_preview=True,
        )
        assert len(md.router.routes) == 22

    md = TilerFactory(
        router_prefix="/md",
        # /dataset, /dataset/dict, /dataset/keys
        extensions=[DatasetMetadataExtension()],
    )
    assert len(md.router.routes) == 22

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
    md = TilerFactory(
        router_prefix="/md",
        extensions=[
            DatasetMetadataExtension(dataset_opener=fs_open_dataset),
        ],
        reader=FsReader,
    )
    assert len(md.router.routes) == 22

    app = FastAPI()
    app.include_router(md.router, prefix="/md")
    with TestClient(app) as client:
        yield client


@pytest.fixture
def app_zarr():
    """App fixture."""
    md = TilerFactory(
        router_prefix="/md",
        extensions=[
            DatasetMetadataExtension(),
        ],
    )
    assert len(md.router.routes) == 22

    app = FastAPI()
    app.include_router(md.router, prefix="/md")
    with TestClient(app) as client:
        yield client


@pytest.mark.parametrize(
    "filename",
    [dataset_2d_nc, dataset_3d_nc, dataset_3d_zarr],
)
def test_dataset_extension(filename, app):
    """Test /dataset endpoints."""
    resp = app.get("/md/dataset/keys", params={"url": filename})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    assert resp.json() == ["dataset"]

    resp = app.get("/md/dataset/dict", params={"url": filename})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    assert resp.json()["data_vars"]["dataset"]

    resp = app.get("/md/dataset/", params={"url": filename})
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


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
        params={"url": dataset_4d_nc, "variable": "dataset", "sel": "time=2023-01-01"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    body = resp.json()
    assert body["band_descriptions"] == [["b1", "0"]]

    resp = app.get(
        "/md/info",
        params={"url": dataset_4d_nc, "variable": "dataset", "sel": "z=0"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    body = resp.json()
    assert body["band_descriptions"] == [
        ["b1", "2022-01-01T00:00:00.000000000"],
        ["b2", "2023-01-01T00:00:00.000000000"],
    ]

    resp = app.get(
        "/md/info",
        params={
            "url": dataset_4d_nc,
            "variable": "dataset",
            "sel": "z=1",
            "sel_method": "nearest",
        },
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    body = resp.json()
    assert body["band_descriptions"] == [
        ["b1", "2022-01-01T00:00:00.000000000"],
        ["b2", "2023-01-01T00:00:00.000000000"],
    ]

    resp = app.get(
        "/md/info",
        params={
            "url": dataset_3d_nc,
            "variable": "dataset",
            "sel": "time=2023-01-01",
            "decode_times": True,
        },
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    body = resp.json()
    assert body["band_descriptions"] == [["b1", "2023-01-01T00:00:00.000000000"]]


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
        params={"url": filename, "variable": "dataset", "rescale": "0,500", "bidx": 1},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"

    resp = app.get(
        "/md/tiles/WebMercatorQuad/0/0/0.jpeg",
        params={"url": filename, "variable": "dataset", "rescale": "0,500", "bidx": 1},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/jpeg"

    resp = app.get(
        "/md/WebMercatorQuad/tilejson.json",
        params={"url": filename, "variable": "dataset", "rescale": "0,500", "bidx": 1},
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
        params={"url": filename, "variable": "dataset", "rescale": "0,500", "bidx": 1},
        json=feat,
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/jpeg"

    resp = app.post(
        "/md/feature.png",
        params={"url": filename, "variable": "dataset", "rescale": "0,500", "bidx": 1},
        json=feat,
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"

    resp = app.post(
        "/md/feature/100x100.png",
        params={"url": filename, "variable": "dataset", "rescale": "0,500", "bidx": 1},
        json=feat,
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"

    resp = app.get(
        "/md/bbox/-100,-25,40,60.jpeg",
        params={"url": filename, "variable": "dataset", "rescale": "0,500", "bidx": 1},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/jpeg"

    resp = app.get(
        "/md/bbox/-100,-25,40,60/100x100.png",
        params={"url": filename, "variable": "dataset", "rescale": "0,500", "bidx": 1},
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
        params={"url": zarr_pyramid, "variable": "dataset", "group": str(group)},
    )
    assert resp.status_code == 200
    # see src/titiler/xarray/tests/fixtures/generate_fixtures.ipynb
    # for structure of zarr pyramid
    with MemoryFile(resp.content) as mem:
        with mem.open() as dst:
            arr = dst.read(1)
            assert arr.max() == group * 2 + 1

    resp = app.get(
        "/md/point/0,0",
        params={"url": zarr_pyramid, "variable": "dataset", "group": str(group)},
    )
    assert resp.json()["values"] == [group * 2 + 1]


@pytest.mark.parametrize(
    "filename",
    [dataset_2d_nc, dataset_3d_nc, dataset_3d_zarr],
)
def test_preview(filename):
    """App fixture."""
    with pytest.warns(UserWarning):
        md = TilerFactory(add_preview=True, reader=FsReader)

    app = FastAPI()
    app.include_router(md.router)
    with TestClient(app) as client:
        resp = client.get(
            "/preview",
            params={
                "url": filename,
                "variable": "dataset",
                "rescale": "0,500",
                "bidx": 1,
            },
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/jpeg"

        resp = client.get(
            "/preview.png",
            params={
                "url": filename,
                "variable": "dataset",
                "rescale": "0,500",
                "bidx": 1,
            },
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"

        resp = client.get(
            "/preview/1024x1024.png",
            params={
                "url": filename,
                "variable": "dataset",
                "rescale": "0,500",
                "bidx": 1,
            },
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"
        with MemoryFile(resp.content) as mem:
            with mem.open() as dst:
                assert dst.width == 1024
                assert dst.height == 1024


@pytest.mark.parametrize(
    "filename",
    [dataset_3d_zarr],
)
def test_app_zarr(filename, app_zarr):
    """Test endpoints with Zarr Reader."""
    resp = app_zarr.get("/md/dataset/keys", params={"url": filename})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    assert resp.json() == ["dataset"]

    resp = app_zarr.get("/md/dataset/dict", params={"url": filename})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    assert resp.json()["data_vars"]["dataset"]

    resp = app_zarr.get("/md/dataset/", params={"url": filename})
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]

    resp = app_zarr.get("/md/info", params={"url": filename, "variable": "dataset"})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"

    resp = app_zarr.get(
        "/md/tiles/WebMercatorQuad/0/0/0",
        params={"url": filename, "variable": "dataset", "rescale": "0,500", "bidx": 1},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"

    resp = app_zarr.get(
        "/md/WebMercatorQuad/tilejson.json",
        params={"url": filename, "variable": "dataset", "rescale": "0,500", "bidx": 1},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"

    resp = app_zarr.get(
        "/md/point/0,0", params={"url": filename, "variable": "dataset"}
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"

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

    resp = app_zarr.post(
        "/md/statistics", params={"url": filename, "variable": "dataset"}, json=feat
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/geo+json"

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

    resp = app_zarr.post(
        "/md/feature",
        params={"url": filename, "variable": "dataset", "rescale": "0,500", "bidx": 1},
        json=feat,
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/jpeg"


@pytest.mark.parametrize(
    "group",
    [0, 1, 2],
)
def test_group_open_zarr(group, app_zarr):
    """Test /tiles endpoints."""
    resp = app_zarr.get(
        f"/md/tiles/WebMercatorQuad/{group}/0/0.tif",
        params={"url": zarr_pyramid, "variable": "dataset", "group": str(group)},
    )
    assert resp.status_code == 200
    # see src/titiler/xarray/tests/fixtures/generate_fixtures.ipynb
    # for structure of zarr pyramid
    with MemoryFile(resp.content) as mem:
        with mem.open() as dst:
            arr = dst.read(1)
            assert arr.max() == group * 2 + 1

    resp = app_zarr.get(
        "/md/point/0,0",
        params={"url": zarr_pyramid, "variable": "dataset", "group": str(group)},
    )
    assert resp.json()["values"] == [group * 2 + 1]
