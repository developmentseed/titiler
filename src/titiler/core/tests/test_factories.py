"""Test TiTiler Tiler Factories."""

import json
import os
import pathlib
from dataclasses import dataclass
from io import BytesIO
from typing import Dict, Type
from unittest.mock import patch
from urllib.parse import urlencode

import attr
import morecantile
import numpy
from requests.auth import HTTPBasicAuth
from rio_tiler.io import BaseReader, COGReader, MultiBandReader, STACReader

from titiler.core.dependencies import DefaultDependency, TMSParams, WebMercatorTMSParams
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.core.factory import (
    MultiBandTilerFactory,
    MultiBaseTilerFactory,
    TilerFactory,
    TMSFactory,
)
from titiler.core.resources.enums import OptionalHeader

from .conftest import DATA_DIR, mock_rasterio_open, parse_img

from fastapi import Depends, FastAPI, HTTPException, Query, security, status

from starlette.testclient import TestClient

NB_DEFAULT_TMS = len(morecantile.tms.list())


def test_TilerFactory():
    """Test TilerFactory class."""
    cog = TilerFactory()
    assert len(cog.router.routes) == 25
    assert cog.tms_dependency == TMSParams

    cog = TilerFactory(router_prefix="something", tms_dependency=WebMercatorTMSParams)
    app = FastAPI()
    app.include_router(cog.router, prefix="/something")
    client = TestClient(app)

    response = client.get(f"/something/tilejson.json?url={DATA_DIR}/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["tilejson"]

    response = client.get(f"/something/NZTM2000/tilejson.json?url={DATA_DIR}/cog.tif")
    assert response.status_code == 422

    cog = TilerFactory(add_preview=False, add_part=False)
    assert len(cog.router.routes) == 18

    app = FastAPI()
    cog = TilerFactory(optional_headers=[OptionalHeader.server_timing])
    app.include_router(cog.router)

    add_exception_handlers(app, DEFAULT_STATUS_CODES)

    client = TestClient(app)

    response = client.get(f"/tiles/8/87/48?url={DATA_DIR}/cog.tif&rescale=0,1000")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    timing = response.headers["server-timing"]
    assert "dataread;dur" in timing
    assert "postprocess;dur" in timing
    assert "format;dur" in timing

    response = client.get(
        f"/tiles/8/87/48?url={DATA_DIR}/cog.tif&rescale=-3.4028235e+38,3.4028235e+38"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    timing = response.headers["server-timing"]
    assert "dataread;dur" in timing
    assert "postprocess;dur" in timing
    assert "format;dur" in timing

    response = client.get(
        f"/tiles/8/87/48.tif?url={DATA_DIR}/cog.tif&bidx=1&bidx=1&bidx=1&return_mask=false"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff; application=geotiff"
    meta = parse_img(response.content)
    assert meta["dtype"] == "uint16"
    assert meta["count"] == 3
    assert meta["width"] == 256
    assert meta["height"] == 256

    response = client.get(
        "/tiles/8/87/48.tif",
        params={
            "url": f"{DATA_DIR}/cog.tif",
            "expression": "b1;b1;b1",
            "return_mask": False,
        },
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff; application=geotiff"
    meta = parse_img(response.content)
    assert meta["dtype"] == "int32"
    assert meta["count"] == 3
    assert meta["width"] == 256
    assert meta["height"] == 256

    response = client.get(
        f"/tiles/8/84/47?url={DATA_DIR}/cog.tif&bidx=1&rescale=0,1000&colormap_name=viridis"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    # Dict
    cmap = urlencode(
        {
            "colormap": json.dumps(
                {
                    "1": [58, 102, 24, 255],
                    "2": [100, 177, 41],
                    "3": "#b1b129",
                    "4": "#ddcb9aFF",
                }
            )
        }
    )
    response = client.get(f"/tiles/8/84/47.png?url={DATA_DIR}/cog.tif&bidx=1&{cmap}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    # Intervals
    cmap = urlencode(
        {
            "colormap": json.dumps(
                [
                    # ([min, max], [r, g, b, a])
                    ([1, 2], [0, 0, 0, 255]),
                    ([2, 3], [255, 255, 255, 255]),
                    ([3, 1000], [255, 0, 0, 255]),
                ]
            )
        }
    )
    response = client.get(f"/tiles/8/84/47.png?url={DATA_DIR}/cog.tif&bidx=1&{cmap}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    # Bad colormap format
    cmap = urlencode({"colormap": json.dumps({"1": [58, 102]})})
    response = client.get(f"/tiles/8/84/47.png?url={DATA_DIR}/cog.tif&bidx=1&{cmap}")
    assert response.status_code == 400

    # no json encoding
    cmap = urlencode({"colormap": {"1": [58, 102]}})
    response = client.get(f"/tiles/8/84/47.png?url={DATA_DIR}/cog.tif&bidx=1&{cmap}")
    assert response.status_code == 400

    # Test NumpyTile
    response = client.get(f"/tiles/8/87/48.npy?url={DATA_DIR}/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/x-binary"
    npy_tile = numpy.load(BytesIO(response.content))
    assert npy_tile.shape == (2, 256, 256)  # mask + data

    # Test Buffer
    response = client.get(f"/tiles/8/87/48.npy?url={DATA_DIR}/cog.tif&buffer=10")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/x-binary"
    npy_tile = numpy.load(BytesIO(response.content))
    assert npy_tile.shape == (2, 276, 276)  # mask + data

    response = client.get(
        f"/preview?url={DATA_DIR}/cog.tif&rescale=0,1000&max_size=256"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    timing = response.headers["server-timing"]
    assert "dataread;dur" in timing
    assert "postprocess;dur" in timing
    assert "format;dur" in timing

    response = client.get(
        f"/crop/-56.228,72.715,-54.547,73.188.png?url={DATA_DIR}/cog.tif&rescale=0,1000&max_size=256"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    timing = response.headers["server-timing"]
    assert "dataread;dur" in timing
    assert "postprocess;dur" in timing
    assert "format;dur" in timing

    response = client.get(f"/point/-56.228,72.715?url={DATA_DIR}/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    timing = response.headers["server-timing"]
    assert "dataread;dur" in timing

    response = client.get(f"/tilejson.json?url={DATA_DIR}/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["tilejson"]

    response = client.get(f"/WorldCRS84Quad/tilejson.json?url={DATA_DIR}/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["tilejson"]

    response_qs = client.get(
        f"/tilejson.json?url={DATA_DIR}/cog.tif&TileMatrixSetId=WorldCRS84Quad"
    )
    assert response.json()["tiles"] == response_qs.json()["tiles"]

    response = client.get(f"/tilejson.json?url={DATA_DIR}/cog.tif&tile_format=png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["tilejson"]
    assert "png" in response.json()["tiles"][0]

    response = client.get(f"/tilejson.json?url={DATA_DIR}/cog.tif&minzoom=5&maxzoom=12")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["tilejson"]
    assert response.json()["minzoom"] == 5
    assert response.json()["maxzoom"] == 12

    response = client.get(
        f"/WMTSCapabilities.xml?url={DATA_DIR}/cog.tif&minzoom=5&maxzoom=12"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"

    response = client.get(f"/bounds?url={DATA_DIR}/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["bounds"]

    response = client.get(f"/info?url={DATA_DIR}/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["band_metadata"]

    response = client.get(f"/info.geojson?url={DATA_DIR}/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    assert response.json()["type"] == "Feature"

    response = client.get(
        f"/preview.png?url={DATA_DIR}/cog.tif&rescale=0,1000&max_size=256"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert 256 in (meta["width"], meta["height"])

    response = client.get(
        f"/preview.png?url={DATA_DIR}/cog.tif&rescale=0,1000&max_size=256&height=512&width=512"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["width"] == 512
    assert meta["height"] == 512

    response = client.get(
        f"/preview.png?url={DATA_DIR}/cog.tif&rescale=0,1000&max_size=0&nodata=0"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["width"] == 2658
    assert meta["height"] == 2667

    response = client.get(
        f"/preview.png?url={DATA_DIR}/cog.tif&rescale=0,1000&max_size=0&nodata=0"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["width"] == 2658
    assert meta["height"] == 2667

    response = client.get(
        f"/preview.tif?url={DATA_DIR}/cog_scale.tif&unscale=True&return_mask=false"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff; application=geotiff"
    meta = parse_img(response.content)
    assert meta["dtype"] == "float32"
    assert meta["count"] == 1

    response = client.get(
        f"/preview.tif?url={DATA_DIR}/cog_scale.tif&return_mask=false"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff; application=geotiff"
    meta = parse_img(response.content)
    assert meta["dtype"] == "int16"
    assert meta["count"] == 1

    feature = {
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [-59.23828124999999, 74.16408546675687],
                    [-59.83154296874999, 73.15680773175981],
                    [-58.73291015624999, 72.88087095711504],
                    [-56.62353515625, 73.06104462497655],
                    [-55.17333984375, 73.41588526207096],
                    [-55.2392578125, 74.09799577518739],
                    [-56.88720703125, 74.2895142503942],
                    [-57.23876953124999, 74.30735341486248],
                    [-59.23828124999999, 74.16408546675687],
                ]
            ],
        },
    }

    feature_collection = {"type": "FeatureCollection", "features": [feature]}

    response = client.post(f"/crop?url={DATA_DIR}/cog.tif", json=feature)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    response = client.post(f"/crop.tif?url={DATA_DIR}/cog.tif", json=feature)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff; application=geotiff"
    meta = parse_img(response.content)
    assert meta["dtype"] == "uint16"
    assert meta["count"] == 2

    response = client.post(f"/crop/100x100.jpeg?url={DATA_DIR}/cog.tif", json=feature)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    meta = parse_img(response.content)
    assert meta["width"] == 100
    assert meta["height"] == 100

    # GET - statistics
    response = client.get(f"/statistics?url={DATA_DIR}/cog.tif&bidx=1&bidx=1&bidx=1")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert len(resp) == 1
    assert set(resp["1"].keys()) == {
        "min",
        "max",
        "mean",
        "count",
        "sum",
        "std",
        "median",
        "majority",
        "minority",
        "unique",
        "histogram",
        "valid_percent",
        "masked_pixels",
        "valid_pixels",
        "percentile_2",
        "percentile_98",
    }
    assert len(resp["1"]["histogram"][0]) == 10

    response = client.get(f"/statistics?url={DATA_DIR}/cog.tif&expression=b1*2")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert len(resp) == 1
    assert set(resp["b1*2"].keys()) == {
        "min",
        "max",
        "mean",
        "count",
        "sum",
        "std",
        "median",
        "majority",
        "minority",
        "unique",
        "histogram",
        "valid_percent",
        "masked_pixels",
        "valid_pixels",
        "percentile_2",
        "percentile_98",
    }

    response = client.get(
        f"/statistics?url={DATA_DIR}/cog.tif&bidx=1&bidx=1&bidx=1&p=4&p=5"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert len(resp) == 1
    assert set(resp["1"].keys()) == {
        "min",
        "max",
        "mean",
        "count",
        "sum",
        "std",
        "median",
        "majority",
        "minority",
        "unique",
        "histogram",
        "valid_percent",
        "masked_pixels",
        "valid_pixels",
        "percentile_4",
        "percentile_5",
    }

    response = client.get(f"/statistics?url={DATA_DIR}/cog.tif&categorical=true")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert len(resp) == 1
    assert set(resp["1"].keys()) == {
        "min",
        "max",
        "mean",
        "count",
        "sum",
        "std",
        "median",
        "majority",
        "minority",
        "unique",
        "histogram",
        "valid_percent",
        "masked_pixels",
        "valid_pixels",
        "percentile_2",
        "percentile_98",
    }
    # categories are stored in the histogram
    assert len(resp["1"]["histogram"][1]) == 15

    response = client.get(
        f"/statistics?url={DATA_DIR}/cog.tif&categorical=true&c=1&c=2&c=3&c=4"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert len(resp) == 1
    assert set(resp["1"].keys()) == {
        "min",
        "max",
        "mean",
        "count",
        "sum",
        "std",
        "median",
        "majority",
        "minority",
        "unique",
        "histogram",
        "valid_percent",
        "masked_pixels",
        "valid_pixels",
        "percentile_2",
        "percentile_98",
    }
    assert resp["1"]["histogram"][1] == [1.0, 2.0, 3.0, 4.0]  # categories
    assert resp["1"]["histogram"][0][3] == 0  # 4.0 is not present in the array

    response = client.get(f"/statistics?url={DATA_DIR}/cog.tif&bidx=1&histogram_bins=3")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert len(resp) == 1
    assert len(resp["1"]["histogram"][0]) == 3

    response = client.get(
        f"/statistics?url={DATA_DIR}/cog.tif&bidx=1&histogram_range=5,10"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert len(resp) == 1
    assert min(resp["1"]["histogram"][1]) == 5.0
    assert max(resp["1"]["histogram"][1]) == 10.0

    # POST - statistics
    response = client.post(
        f"/statistics?url={DATA_DIR}/cog.tif&bidx=1&bidx=1&bidx=1", json=feature
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    resp = response.json()
    assert resp["type"] == "Feature"
    assert len(resp["properties"]["statistics"]) == 1
    assert set(resp["properties"]["statistics"]["1"].keys()) == {
        "min",
        "max",
        "mean",
        "count",
        "sum",
        "std",
        "median",
        "majority",
        "minority",
        "unique",
        "histogram",
        "percentile_2",
        "percentile_98",
        "valid_pixels",
        "masked_pixels",
        "valid_percent",
    }

    response = client.post(
        f"/statistics?url={DATA_DIR}/cog.tif&bidx=1&bidx=1&bidx=1",
        json=feature_collection,
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    resp = response.json()
    assert resp["type"] == "FeatureCollection"
    assert len(resp["features"][0]["properties"]["statistics"]) == 1
    assert set(resp["features"][0]["properties"]["statistics"]["1"].keys()) == {
        "min",
        "max",
        "mean",
        "count",
        "sum",
        "std",
        "median",
        "majority",
        "minority",
        "unique",
        "histogram",
        "percentile_2",
        "percentile_98",
        "valid_pixels",
        "masked_pixels",
        "valid_percent",
    }

    response = client.post(
        f"/statistics?url={DATA_DIR}/cog.tif&categorical=true", json=feature
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    resp = response.json()
    assert resp["type"] == "Feature"
    assert len(resp["properties"]["statistics"]) == 1
    assert set(resp["properties"]["statistics"]["1"].keys()) == {
        "min",
        "max",
        "mean",
        "count",
        "sum",
        "std",
        "median",
        "majority",
        "minority",
        "unique",
        "histogram",
        "percentile_2",
        "percentile_98",
        "valid_pixels",
        "masked_pixels",
        "valid_percent",
    }
    assert len(resp["properties"]["statistics"]["1"]["histogram"][1]) == 12

    response = client.post(
        f"/statistics?url={DATA_DIR}/cog.tif&categorical=true&c=1&c=2&c=3&c=4",
        json=feature,
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    resp = response.json()
    assert resp["type"] == "Feature"
    assert len(resp["properties"]["statistics"]) == 1
    assert set(resp["properties"]["statistics"]["1"].keys()) == {
        "min",
        "max",
        "mean",
        "count",
        "sum",
        "std",
        "median",
        "majority",
        "minority",
        "unique",
        "histogram",
        "percentile_2",
        "percentile_98",
        "valid_pixels",
        "masked_pixels",
        "valid_percent",
    }
    assert len(resp["properties"]["statistics"]["1"]["histogram"][0]) == 4
    assert resp["properties"]["statistics"]["1"]["histogram"][0][3] == 0


@dataclass
class ReaderParams(DefaultDependency):
    """Reader options to overwrite min/max zoom."""

    minzoom: int = 4
    maxzoom: int = 8


def test_TilerFactory_ReaderParams():
    """Test TilerFactory factory with Reader dependency."""
    cog = TilerFactory(reader_dependency=ReaderParams)
    app = FastAPI()
    app.include_router(cog.router)
    client = TestClient(app)

    response = client.get(f"/tilejson.json?url={DATA_DIR}/cog.tif")
    tj = response.json()
    assert tj["minzoom"] == 4
    assert tj["maxzoom"] == 8


@patch("rio_tiler.io.cogeo.rasterio")
def test_MultiBaseTilerFactory(rio):
    """test MultiBaseTilerFactory."""
    rio.open = mock_rasterio_open

    stac = MultiBaseTilerFactory(reader=STACReader)
    assert len(stac.router.routes) == 27

    app = FastAPI()
    app.include_router(stac.router)

    add_exception_handlers(app, DEFAULT_STATUS_CODES)

    client = TestClient(app)

    response = client.get(f"/assets?url={DATA_DIR}/item.json")
    assert response.status_code == 200
    assert len(response.json()) == 2

    response = client.get(f"/bounds?url={DATA_DIR}/item.json")
    assert response.status_code == 200
    assert len(response.json()["bounds"]) == 4

    response = client.get(f"/info?url={DATA_DIR}/item.json")
    assert response.status_code == 200
    assert len(response.json()) == 2

    response = client.get(f"/info?url={DATA_DIR}/item.json&assets=B01&assets=B09")
    assert response.status_code == 200
    assert response.json()["B01"]
    assert response.json()["B09"]

    response = client.get(f"/info.geojson?url={DATA_DIR}/item.json&assets=B01")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    assert response.json()["type"] == "Feature"

    response = client.get(f"/preview.tif?url={DATA_DIR}/item.json")
    assert response.status_code == 400

    response = client.get(
        f"/preview.tif?url={DATA_DIR}/item.json&assets=B01&assets=B09&return_mask=false"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff; application=geotiff"
    meta = parse_img(response.content)
    assert meta["dtype"] == "uint16"
    assert meta["count"] == 2

    response = client.get(
        "/preview.tif",
        params={
            "url": f"{DATA_DIR}/item.json",
            "expression": "B01;B01;B01",
            "return_mask": False,
        },
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff; application=geotiff"
    meta = parse_img(response.content)
    assert meta["dtype"] == "int32"
    assert meta["count"] == 3

    response = client.get(
        f"/preview.tif?url={DATA_DIR}/item.json&assets=B01&asset_bidx=B01|1,1,1&return_mask=false"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff; application=geotiff"
    meta = parse_img(response.content)
    assert meta["dtype"] == "uint16"
    assert meta["count"] == 3

    response = client.get(
        "/preview.tif",
        params={
            "url": f"{DATA_DIR}/item.json",
            "assets": "B01",
            "asset_expression": "B01|b1;b1;b1",
            "return_mask": False,
        },
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff; application=geotiff"
    meta = parse_img(response.content)
    assert meta["dtype"] == "int32"
    assert meta["count"] == 3

    # GET - statistics
    response = client.get(
        f"/asset_statistics?url={DATA_DIR}/item.json&assets=B01&assets=B09"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert len(resp) == 2
    assert set(resp["B01"]["1"].keys()) == {
        "min",
        "max",
        "mean",
        "count",
        "sum",
        "std",
        "median",
        "majority",
        "minority",
        "unique",
        "histogram",
        "valid_percent",
        "masked_pixels",
        "valid_pixels",
        "percentile_2",
        "percentile_98",
    }
    response = client.get(
        f"/asset_statistics?url={DATA_DIR}/item.json&assets=B01&assets=B09&asset_bidx=B01|1&asset_bidx=B09|1"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert len(resp) == 2
    assert resp["B01"]["1"]
    assert resp["B09"]["1"]

    response = client.get(f"/statistics?url={DATA_DIR}/item.json&assets=B01&assets=B09")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert list(resp) == ["B01_1", "B09_1"]
    assert set(resp["B01_1"].keys()) == {
        "min",
        "max",
        "mean",
        "count",
        "sum",
        "std",
        "median",
        "majority",
        "minority",
        "unique",
        "histogram",
        "valid_percent",
        "masked_pixels",
        "valid_pixels",
        "percentile_2",
        "percentile_98",
    }

    response = client.get(
        f"/statistics?url={DATA_DIR}/item.json&assets=B01&assets=B09&asset_bidx=B01|1&asset_bidx=B09|1"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert len(resp) == 2
    assert resp["B01_1"]
    assert resp["B09_1"]

    stac_feature = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [23.62060546875, 31.834399275715842],
                            [23.838958740234375, 31.834399275715842],
                            [23.838958740234375, 32.072101858328686],
                            [23.62060546875, 32.072101858328686],
                            [23.62060546875, 31.834399275715842],
                        ]
                    ],
                },
            }
        ],
    }

    # POST - statistics
    response = client.post(
        f"/statistics?url={DATA_DIR}/item.json&assets=B01&assets=B09",
        json=stac_feature["features"][0],
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    resp = response.json()
    props = resp["properties"]["statistics"]
    assert len(props) == 2
    assert set(props["B01_1"].keys()) == {
        "min",
        "max",
        "mean",
        "count",
        "sum",
        "std",
        "median",
        "majority",
        "minority",
        "unique",
        "histogram",
        "valid_percent",
        "masked_pixels",
        "valid_pixels",
        "percentile_2",
        "percentile_98",
    }
    assert props["B09_1"]

    response = client.post(
        f"/statistics?url={DATA_DIR}/item.json&assets=B01&assets=B09", json=stac_feature
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    resp = response.json()
    props = resp["features"][0]["properties"]["statistics"]
    assert len(props) == 2
    assert set(props["B01_1"].keys()) == {
        "min",
        "max",
        "mean",
        "count",
        "sum",
        "std",
        "median",
        "majority",
        "minority",
        "unique",
        "histogram",
        "valid_percent",
        "masked_pixels",
        "valid_pixels",
        "percentile_2",
        "percentile_98",
    }
    assert props["B09_1"]

    response = client.post(
        f"/statistics?url={DATA_DIR}/item.json&assets=B01&assets=B09&asset_bidx=B01|1&asset_bidx=B09|1",
        json=stac_feature["features"][0],
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    resp = response.json()
    props = resp["properties"]["statistics"]
    assert len(props) == 2
    assert set(props["B01_1"].keys()) == {
        "min",
        "max",
        "mean",
        "count",
        "sum",
        "std",
        "median",
        "majority",
        "minority",
        "unique",
        "histogram",
        "valid_percent",
        "masked_pixels",
        "valid_pixels",
        "percentile_2",
        "percentile_98",
    }
    assert props["B09_1"]


@attr.s
class BandFileReader(MultiBandReader):
    """Test MultiBand"""

    input: str = attr.ib()
    tms: morecantile.TileMatrixSet = attr.ib(
        default=morecantile.tms.get("WebMercatorQuad")
    )
    reader_options: Dict = attr.ib(factory=dict)

    reader: Type[BaseReader] = attr.ib(default=COGReader)

    def __attrs_post_init__(self):
        """Parse Sceneid and get grid bounds."""
        self.bands = sorted([p.stem for p in pathlib.Path(self.input).glob("B0*.tif")])
        with self.reader(self._get_band_url(self.bands[0])) as cog:
            self.bounds = cog.bounds
            self.crs = cog.crs
            self.minzoom = cog.minzoom
            self.maxzoom = cog.maxzoom

    def _get_band_url(self, band: str) -> str:
        """Validate band's name and return band's url."""
        return os.path.join(self.input, f"{band}.tif")


def CustomPathParams(directory: str = Query(..., description="Give me a url.")) -> str:
    """Custom path Dependency."""
    return directory


def test_MultiBandTilerFactory():
    """test MultiBandTilerFactory."""

    bands = MultiBandTilerFactory(
        reader=BandFileReader, path_dependency=CustomPathParams
    )
    assert len(bands.router.routes) == 26

    app = FastAPI()
    app.include_router(bands.router)

    add_exception_handlers(app, DEFAULT_STATUS_CODES)

    client = TestClient(app)

    response = client.get(f"/bands?directory={DATA_DIR}")
    assert response.status_code == 200
    assert response.json() == ["B01", "B09"]

    # default bands
    response = client.get(f"/info?directory={DATA_DIR}")
    assert response.json()["band_metadata"] == [["B01", {}], ["B09", {}]]

    response = client.get(f"/info?directory={DATA_DIR}&bands=B01")
    assert response.status_code == 200
    assert response.json()["band_metadata"] == [["B01", {}]]

    response = client.get(f"/info.geojson?directory={DATA_DIR}&bands=B01")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    assert response.json()["properties"]["band_metadata"] == [["B01", {}]]

    # need bands or expression
    response = client.get(f"/preview.tif?directory={DATA_DIR}&return_mask=false")
    assert response.status_code == 400

    response = client.get(
        f"/preview.tif?directory={DATA_DIR}&bands=B01&bands=B09&bands=B01&return_mask=false"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff; application=geotiff"
    meta = parse_img(response.content)
    assert meta["dtype"] == "uint16"
    assert meta["count"] == 3

    response = client.get(
        "/preview.tif",
        params={
            "directory": DATA_DIR,
            "expression": "B01;B09;B01",
            "return_mask": False,
        },
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff; application=geotiff"
    meta = parse_img(response.content)
    assert (
        meta["dtype"] == "int32"
    )  # when using expression, numexpr will change the datatype
    assert meta["count"] == 3

    # GET - statistics
    response = client.get(f"/statistics?directory={DATA_DIR}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert len(resp) == 2
    assert resp["B01"]
    assert resp["B09"]

    response = client.get(f"/statistics?directory={DATA_DIR}&bands=B01&bands=B09")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert len(resp) == 2
    assert set(resp["B01"].keys()) == {
        "min",
        "max",
        "mean",
        "count",
        "sum",
        "std",
        "median",
        "majority",
        "minority",
        "unique",
        "histogram",
        "valid_percent",
        "masked_pixels",
        "valid_pixels",
        "percentile_2",
        "percentile_98",
    }
    assert resp["B09"]

    response = client.get(f"/statistics?directory={DATA_DIR}&expression=B01/B09")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert len(resp) == 1
    assert set(resp["B01/B09"].keys()) == {
        "min",
        "max",
        "mean",
        "count",
        "sum",
        "std",
        "median",
        "majority",
        "minority",
        "unique",
        "histogram",
        "valid_percent",
        "masked_pixels",
        "valid_pixels",
        "percentile_2",
        "percentile_98",
    }

    # POST - statistics
    band_feature = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [23.62060546875, 31.834399275715842],
                            [23.838958740234375, 31.834399275715842],
                            [23.838958740234375, 32.072101858328686],
                            [23.62060546875, 32.072101858328686],
                            [23.62060546875, 31.834399275715842],
                        ]
                    ],
                },
            }
        ],
    }

    response = client.post(
        f"/statistics?directory={DATA_DIR}&bands=B01&bands=B09",
        json=band_feature["features"][0],
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    resp = response.json()
    props = resp["properties"]["statistics"]
    assert len(props) == 2
    assert set(props["B01"].keys()) == {
        "min",
        "max",
        "mean",
        "count",
        "sum",
        "std",
        "median",
        "majority",
        "minority",
        "unique",
        "histogram",
        "valid_percent",
        "masked_pixels",
        "valid_pixels",
        "percentile_2",
        "percentile_98",
    }
    assert props["B09"]

    response = client.post(
        f"/statistics?directory={DATA_DIR}&expression=B01/B09",
        json=band_feature["features"][0],
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    resp = response.json()
    props = resp["properties"]["statistics"]
    assert len(props) == 1
    assert set(props["B01/B09"].keys()) == {
        "min",
        "max",
        "mean",
        "count",
        "sum",
        "std",
        "median",
        "majority",
        "minority",
        "unique",
        "histogram",
        "valid_percent",
        "masked_pixels",
        "valid_pixels",
        "percentile_2",
        "percentile_98",
    }

    response = client.post(
        f"/statistics?directory={DATA_DIR}&bands=B01&bands=B09", json=band_feature
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    resp = response.json()
    props = resp["features"][0]["properties"]["statistics"]
    assert len(props) == 2
    assert set(props["B01"].keys()) == {
        "min",
        "max",
        "mean",
        "count",
        "sum",
        "std",
        "median",
        "majority",
        "minority",
        "unique",
        "histogram",
        "valid_percent",
        "masked_pixels",
        "valid_pixels",
        "percentile_2",
        "percentile_98",
    }
    assert props["B09"]

    response = client.post(
        f"/statistics?directory={DATA_DIR}&expression=B01/B09", json=band_feature
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    resp = response.json()
    props = resp["features"][0]["properties"]["statistics"]
    assert len(props) == 1
    assert set(props["B01/B09"].keys()) == {
        "min",
        "max",
        "mean",
        "count",
        "sum",
        "std",
        "median",
        "majority",
        "minority",
        "unique",
        "histogram",
        "valid_percent",
        "masked_pixels",
        "valid_pixels",
        "percentile_2",
        "percentile_98",
    }

    # default bands
    response = client.post(f"/statistics?directory={DATA_DIR}", json=band_feature)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    resp = response.json()
    props = resp["features"][0]["properties"]["statistics"]
    assert props["B01"]
    assert props["B09"]

    response = client.post(
        f"/statistics?directory={DATA_DIR}",
        json=band_feature["features"][0],
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    resp = response.json()
    props = resp["properties"]["statistics"]
    assert props["B01"]
    assert props["B09"]


def test_TMSFactory():
    """test TMSFactory."""

    tms_endpoints = TMSFactory(router_prefix="tms")
    assert len(tms_endpoints.router.routes) == 2

    app = FastAPI()
    app.include_router(tms_endpoints.router, prefix="/tms")

    client = TestClient(app)

    response = client.get("/tms/tileMatrixSets")
    assert response.status_code == 200
    body = response.json()
    assert len(body["tileMatrixSets"]) == NB_DEFAULT_TMS
    tms = list(filter(lambda m: m["id"] == "WebMercatorQuad", body["tileMatrixSets"]))[
        0
    ]
    assert (
        tms["links"][0]["href"]
        == "http://testserver/tms/tileMatrixSets/WebMercatorQuad"
    )

    response = client.get("/tms/tileMatrixSets/WebMercatorQuad")
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "TileMatrixSetType"
    assert body["identifier"] == "WebMercatorQuad"


def test_TilerFactory_WithDependencies():
    """Test TilerFactory class."""

    http_basic = security.HTTPBasic()

    def must_be_bob(credentials: security.HTTPBasicCredentials = Depends(http_basic)):
        if credentials.username == "bob":
            return True
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You're not Bob",
            headers={"WWW-Authenticate": "Basic"},
        )

    cog = TilerFactory(
        route_dependencies=[
            (
                [
                    {"path": "/bounds", "method": "GET"},
                    {"path": "/tiles/{z}/{x}/{y}", "method": "GET"},
                ],
                [Depends(must_be_bob)],
            ),
        ],
        router_prefix="something",
    )
    assert len(cog.router.routes) == 25
    assert cog.tms_dependency == TMSParams

    app = FastAPI()
    app.include_router(cog.router, prefix="/something")
    client = TestClient(app)

    auth_bob = HTTPBasicAuth(username="bob", password="ILoveSponge")
    auth_notbob = HTTPBasicAuth(username="notbob", password="IHateSponge")

    response = client.get(f"/something/tilejson.json?url={DATA_DIR}/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["tilejson"]

    response = client.get(
        f"/something/bounds?url={DATA_DIR}/cog.tif&rescale=0,1000", auth=auth_bob
    )
    assert response.status_code == 200

    response = client.get(
        f"/something/bounds?url={DATA_DIR}/cog.tif&rescale=0,1000", auth=auth_notbob
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "You're not Bob"

    response = client.get(
        f"/something/tiles/8/87/48?url={DATA_DIR}/cog.tif&rescale=0,1000", auth=auth_bob
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    response = client.get(
        f"/something/tiles/8/87/48?url={DATA_DIR}/cog.tif&rescale=0,1000",
        auth=auth_notbob,
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "You're not Bob"

    response = client.get(
        f"/something/tiles/8/87/48.jpeg?url={DATA_DIR}/cog.tif&rescale=0,1000"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    cog = TilerFactory(router_prefix="something")
    cog.add_route_dependencies(
        scopes=[{"path": "/bounds", "method": "GET"}],
        dependencies=[Depends(must_be_bob)],
    )

    app = FastAPI()
    app.include_router(cog.router, prefix="/something")
    client = TestClient(app)

    response = client.get(f"/something/tilejson.json?url={DATA_DIR}/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["tilejson"]

    response = client.get(
        f"/something/bounds?url={DATA_DIR}/cog.tif&rescale=0,1000", auth=auth_bob
    )
    assert response.status_code == 200

    response = client.get(
        f"/something/bounds?url={DATA_DIR}/cog.tif&rescale=0,1000", auth=auth_notbob
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "You're not Bob"
