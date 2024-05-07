"""Test Mosaic endpoints."""

import os
from typing import Any, Callable
from unittest.mock import patch

import morecantile
from cogeo_mosaic.backends import FileBackend
from cogeo_mosaic.mosaic import MosaicJSON

from titiler.core.models.mapbox import TileJSON

from ..conftest import DATA_DIR, parse_img, read_json_fixture

MOSAICJSON_FILE = os.path.join(DATA_DIR, "mosaic.json")


def mosaic_read_factory(fname: str) -> Callable:
    """Factory method for patching mosaic reading"""

    def _read(*args: Any, **kwargs: Any) -> MosaicJSON:
        """Match signature of `cogeo_mosaic.backends.BaseBackend._read`"""
        data = read_json_fixture(fname)
        for qk in data["tiles"]:
            data["tiles"][qk] = [
                os.path.join(os.path.dirname(fname), f) for f in data["tiles"][qk]
            ]
        return MosaicJSON(**data)

    return _read


def test_read_mosaic(app):
    """test GET /mosaicjson endpoint"""
    # TODO: Remove
    response = app.get("/mosaicjson", params={"url": MOSAICJSON_FILE})
    assert response.status_code == 200
    MosaicJSON(**response.json())

    response = app.get("/mosaicjson/", params={"url": MOSAICJSON_FILE})
    assert response.status_code == 200
    MosaicJSON(**response.json())


def test_bounds(app):
    """test GET /mosaicjson/bounds endpoint"""
    response = app.get("/mosaicjson/bounds", params={"url": MOSAICJSON_FILE})
    assert response.status_code == 200
    body = response.json()
    assert len(body["bounds"]) == 4
    assert body["bounds"][0] < body["bounds"][2]
    assert body["bounds"][1] < body["bounds"][3]


def test_info(app):
    """test GET /mosaicjson/info endpoint"""
    response = app.get("/mosaicjson/info", params={"url": MOSAICJSON_FILE})
    assert response.status_code == 200
    body = response.json()
    assert body["minzoom"] == 7
    assert body["maxzoom"] == 9
    assert body["name"] == "mosaic"  # mosaic.name is not set
    assert body["quadkeys"] == []

    response = app.get("/mosaicjson/info.geojson", params={"url": MOSAICJSON_FILE})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    body = response.json()
    assert body["geometry"]
    assert body["properties"]["minzoom"] == 7
    assert body["properties"]["maxzoom"] == 9
    assert body["properties"]["name"] == "mosaic"  # mosaic.name is not set
    assert body["properties"]["quadkeys"] == []


def test_tilejson(app):
    """test GET /mosaicjson/WebMercatorQuad/tilejson.json endpoint"""
    mosaicjson = read_json_fixture(MOSAICJSON_FILE)
    response = app.get(
        "/mosaicjson/WebMercatorQuad/tilejson.json", params={"url": MOSAICJSON_FILE}
    )
    assert response.status_code == 200
    body = response.json()
    TileJSON(**body)

    assert (
        "http://testserver/mosaicjson/tiles/WebMercatorQuad/{z}/{x}/{y}@1x?url="
        in body["tiles"][0]
    )
    assert body["minzoom"] == mosaicjson["minzoom"]
    assert body["maxzoom"] == mosaicjson["maxzoom"]
    assert body["bounds"] == mosaicjson["bounds"]
    assert body["center"] == mosaicjson["center"]


def test_point(app):
    """test GET /mosaicjson/point endpoint"""
    mosaicjson = read_json_fixture(MOSAICJSON_FILE)
    center = mosaicjson["center"]
    with patch.object(FileBackend, "_read", mosaic_read_factory(MOSAICJSON_FILE)):
        response = app.get(
            f"/mosaicjson/point/{center[0]},{center[1]}",
            params={"url": MOSAICJSON_FILE},
        )
    assert response.status_code == 200
    body = response.json()
    assert len(body["values"]) == 1
    assert body["values"][0][0].endswith(".tif")
    assert body["values"][0][1] == [9943, 9127, 9603]


def test_tile(app):
    """Test GET /mosaicjson/tiles endpoint"""
    mosaicjson = read_json_fixture(MOSAICJSON_FILE)
    bounds = mosaicjson["bounds"]
    tms = morecantile.tms.get("WebMercatorQuad")
    tile = tms.tile(*mosaicjson["center"])
    partial_tile = tms.tile(bounds[0], bounds[1], mosaicjson["minzoom"])

    with patch.object(FileBackend, "_read", mosaic_read_factory(MOSAICJSON_FILE)):
        # full tile
        response = app.get(
            f"/mosaicjson/tiles/WebMercatorQuad/{tile.z}/{tile.x}/{tile.y}",
            params={"url": MOSAICJSON_FILE},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        meta = parse_img(response.content)
        assert meta["width"] == meta["height"] == 256

        response = app.get(
            f"/mosaicjson/tiles/WebMercatorQuad/{tile.z}/{tile.x}/{tile.y}@2x",
            params={"url": MOSAICJSON_FILE},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        meta = parse_img(response.content)
        assert meta["width"] == meta["height"] == 512

        response = app.get(
            f"/mosaicjson/tiles/WebMercatorQuad/{tile.z}/{tile.x}/{tile.y}.tif",
            params={"url": MOSAICJSON_FILE},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/tiff; application=geotiff"
        meta = parse_img(response.content)
        assert meta["width"] == meta["height"] == 256
        assert meta["crs"] == 3857

        response = app.get(
            f"/mosaicjson/tiles/WebMercatorQuad/{tile.z}/{tile.x}/{tile.y}@2x.tif",
            params={"url": MOSAICJSON_FILE, "nodata": 0, "bidx": 1},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/tiff; application=geotiff"
        meta = parse_img(response.content)
        assert meta["dtype"] == "uint16"
        assert meta["count"] == 2
        assert meta["width"] == 512
        assert meta["height"] == 512

        response = app.get(
            f"/mosaicjson/tiles/WebMercatorQuad/{tile.z}/{tile.x}/{tile.y}@2x.jpg",
            params={
                "url": MOSAICJSON_FILE,
                "rescale": "0,1000",
                "colormap_name": "viridis",
                "bidx": 1,
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpg"

        # partial tile
        response = app.get(
            f"/mosaicjson/tiles/WebMercatorQuad/{partial_tile.z}/{partial_tile.x}/{partial_tile.y}",
            params={"url": MOSAICJSON_FILE},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

        response = app.get(
            f"/mosaicjson/tiles/WebMercatorQuad/{partial_tile.z}/{partial_tile.x}/{partial_tile.y}.tif",
            params={"url": MOSAICJSON_FILE, "resampling": "bilinear"},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/tiff; application=geotiff"


def test_wmts(app):
    """test GET /mosaicjson/WebMercatorQuad/WMTSCapabilities.xml endpoint"""
    with patch.object(FileBackend, "_read", mosaic_read_factory(MOSAICJSON_FILE)):
        response = app.get(
            "/mosaicjson/WebMercatorQuad/WMTSCapabilities.xml",
            params={"url": MOSAICJSON_FILE},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/xml"
        assert (
            "http://testserver/mosaicjson/tiles/WebMercatorQuad/{TileMatrix}/{TileCol}/{TileRow}@1x.png?url="
            in response.content.decode()
        )

        response = app.get(
            "/mosaicjson/WebMercatorQuad/WMTSCapabilities.xml",
            params={"url": MOSAICJSON_FILE, "tile_scale": 2},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/xml"
        assert (
            "http://testserver/mosaicjson/tiles/WebMercatorQuad/{TileMatrix}/{TileCol}/{TileRow}@2x.png?url="
            in response.content.decode()
        )


def test_mosaic_auth_error(app):
    """Raise auth error 401."""
    response = app.get("/mosaicjson", params={"url": "s3://bucket/mosaic.json"})
    assert response.status_code == 401


def test_mosaic_not_found_error(app):
    """
    This should probably return a 404 but currently returns a 424 because cogeo_mosaic incorrectly raises a MosaicError
    instead of MosaicNotFoundError.
    """
    response = app.get("/mosaicjson", params={"url": "mosaic.json"})
    assert response.status_code == 424


def test_validate(app):
    """test POST /mosaicjson/validate endpoint"""
    body = read_json_fixture("mosaic.json")
    response = app.post("/mosaicjson/validate", json=body)
    assert response.status_code == 200

    response = app.post("/mosaicjson/validate", json={"nope": "oups"})
    assert response.status_code == 422
