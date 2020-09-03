import json
import os
from typing import Callable
from unittest.mock import patch

import mercantile
from cogeo_mosaic.backends import FileBackend
from cogeo_mosaic.mosaic import MosaicJSON

from titiler.models.mapbox import TileJSON

from ..conftest import DATA_DIR, parse_img, read_json_fixture

MOSAICJSON_FILE = os.path.join(DATA_DIR, "mosaic.json")


def mosaic_read_factory(fname: str) -> Callable:
    """Factory method for patching mosaic reading"""

    def _read(gzip: bool = None) -> MosaicJSON:
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
    response = app.get("/mosaicjson", params={"url": MOSAICJSON_FILE})
    assert response.status_code == 200
    MosaicJSON(**response.json())


def test_update_mosaic(app):
    """test PUT /mosaicjson endpoint"""
    mosaicjson = read_json_fixture("mosaic.json")
    original_qk = json.dumps(mosaicjson["tiles"], sort_keys=True)

    # Remove `cog1.tif` from the mosaic
    for qk in mosaicjson["tiles"]:
        mosaicjson["tiles"][qk].pop(mosaicjson["tiles"][qk].index("cog1.tif"))

    # Save to file to pass to api
    mosaic_file = os.path.join(DATA_DIR, "mosaicjson_temp.json")
    with open(mosaic_file, "w") as f:
        json.dump(mosaicjson, f)

    body = {"files": [os.path.join(DATA_DIR, "cog1.tif")], "url": mosaic_file}
    response = app.put("/mosaicjson", json=body)
    assert response.status_code == 200

    body = response.json()
    # Updating the tilejson adds full path, remove to match the original file
    for qk in body["tiles"]:
        body["tiles"][qk] = [os.path.split(f)[-1] for f in body["tiles"][qk]]

    assert json.dumps(body["tiles"], sort_keys=True) == original_qk

    # Cleanup
    os.remove(mosaic_file)


def test_create_mosaic(app):
    """test POST /mosaicjson endpoint"""
    output_mosaic = os.path.join(DATA_DIR, "test_create_mosaic.json")
    body = {
        "files": [os.path.join(DATA_DIR, fname) for fname in ["cog1.tif", "cog2.tif"]],
        "url": output_mosaic,
    }
    response = app.post("/mosaicjson", json=body)
    assert response.status_code == 200
    assert os.path.exists(output_mosaic)

    # cleanup
    os.remove(output_mosaic)


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
    assert body["quadkeys"] == [
        "0302300",
        "0302301",
        "0302310",
        "0302302",
        "0302303",
        "0302312",
        "0302320",
        "0302321",
        "0302330",
    ]


def test_tilejson(app):
    """test GET /mosaicjson/tilejson.json endpoint"""
    mosaicjson = read_json_fixture(MOSAICJSON_FILE)
    response = app.get("/mosaicjson/tilejson.json", params={"url": MOSAICJSON_FILE})
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
    assert body["values"][0]["values"] == [9943, 9127, 9603]


def test_tile(app):
    """Test GET /mosaicjson/tiles endpoint"""
    mosaicjson = read_json_fixture(MOSAICJSON_FILE)
    bounds = mosaicjson["bounds"]
    tile = mercantile.tile(*mosaicjson["center"])
    partial_tile = mercantile.tile(bounds[0], bounds[1], mosaicjson["minzoom"])

    with patch.object(FileBackend, "_read", mosaic_read_factory(MOSAICJSON_FILE)):
        # full tile
        response = app.get(
            f"/mosaicjson/tiles/{tile.z}/{tile.x}/{tile.y}",
            params={"url": MOSAICJSON_FILE},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert response.headers["X-Assets"]
        meta = parse_img(response.content)
        assert meta["width"] == meta["height"] == 256

        response = app.get(
            f"/mosaicjson/tiles/{tile.z}/{tile.x}/{tile.y}@2x",
            params={"url": MOSAICJSON_FILE},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        meta = parse_img(response.content)
        assert meta["width"] == meta["height"] == 512

        response = app.get(
            f"/mosaicjson/tiles/{tile.z}/{tile.x}/{tile.y}.tif",
            params={"url": MOSAICJSON_FILE},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/tiff"
        meta = parse_img(response.content)
        assert meta["width"] == meta["height"] == 256
        assert meta["crs"] == 3857

        response = app.get(
            f"/mosaicjson/tiles/{tile.z}/{tile.x}/{tile.y}@2x.tif",
            params={"url": MOSAICJSON_FILE, "nodata": 0, "bidx": 1},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/tiff"
        meta = parse_img(response.content)
        assert meta["dtype"] == "uint16"
        assert meta["count"] == 2
        assert meta["width"] == 512
        assert meta["height"] == 512

        response = app.get(
            f"/mosaicjson/tiles/{tile.z}/{tile.x}/{tile.y}@2x.jpg",
            params={
                "url": MOSAICJSON_FILE,
                "rescale": "0,1000",
                "color_map": "viridis",
                "bidx": 1,
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"

        # partial tile
        response = app.get(
            f"/mosaicjson/tiles/{partial_tile.z}/{partial_tile.x}/{partial_tile.y}",
            params={"url": MOSAICJSON_FILE},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

        response = app.get(
            f"/mosaicjson/tiles/{partial_tile.z}/{partial_tile.x}/{partial_tile.y}.tif",
            params={"url": MOSAICJSON_FILE, "resampling_method": "bilinear"},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/tiff"


def test_wmts(app):
    """test GET /mosaicjson/WMTSCapabilities.xml endpoint"""
    with patch.object(FileBackend, "_read", mosaic_read_factory(MOSAICJSON_FILE)):
        response = app.get(
            "/mosaicjson/WMTSCapabilities.xml", params={"url": MOSAICJSON_FILE}
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/xml"
        assert (
            "http://testserver/mosaicjson/tiles/WebMercatorQuad/{TileMatrix}/{TileCol}/{TileRow}@1x.png?url="
            in response.content.decode()
        )

        response = app.get(
            "/mosaicjson/WMTSCapabilities.xml",
            params={"url": MOSAICJSON_FILE, "tile_scale": 2},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/xml"
        assert (
            "http://testserver/mosaicjson/tiles/WebMercatorQuad/{TileMatrix}/{TileCol}/{TileRow}@2x.png?url="
            in response.content.decode()
        )


def test_mosaic_auth_error(app):
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
