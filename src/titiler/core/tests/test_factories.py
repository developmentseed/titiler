"""Test TiTiler Tiler Factories."""

import json
import math
import os
import pathlib
import warnings
from dataclasses import dataclass
from enum import Enum
from io import BytesIO
from typing import Dict, Optional, Sequence, Type
from unittest.mock import patch
from urllib.parse import urlencode

import attr
import httpx
import morecantile
import numpy
import pytest
from attrs import define
from fastapi import Depends, FastAPI, HTTPException, Path, Query, security, status
from morecantile.defaults import TileMatrixSets
from rasterio.crs import CRS
from rasterio.io import MemoryFile
from rio_tiler.colormap import cmap as default_cmap
from rio_tiler.errors import InvalidDatatypeWarning, NoOverviewWarning
from rio_tiler.io import BaseReader, MultiBandReader, Reader, STACReader
from starlette.requests import Request
from starlette.testclient import TestClient
from typing_extensions import Annotated

from titiler.core import dependencies
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.core.factory import (
    AlgorithmFactory,
    BaseFactory,
    ColorMapFactory,
    MultiBaseTilerFactory,
    TilerFactory,
    TMSFactory,
)

from .conftest import DATA_DIR, mock_rasterio_open, parse_img

DEFAULT_TMS = morecantile.tms
NB_DEFAULT_TMS = len(DEFAULT_TMS.list())
WEB_TMS = TileMatrixSets({"WebMercatorQuad": morecantile.tms.get("WebMercatorQuad")})


def test_TilerFactory():
    """Test TilerFactory class."""
    cog = TilerFactory()
    assert len(cog.router.routes) == 19
    assert len(cog.supported_tms.list()) == NB_DEFAULT_TMS

    cog = TilerFactory(router_prefix="something", supported_tms=WEB_TMS)
    assert len(cog.supported_tms.list()) == 1

    app = FastAPI()
    app.include_router(cog.router, prefix="/something")
    client = TestClient(app)

    response = client.get("/openapi.json")
    assert response.status_code == 200

    response = client.get("/docs")
    assert response.status_code == 200

    response = client.get(
        f"/something/WebMercatorQuad/tilejson.json?url={DATA_DIR}/cog.tif"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["tilejson"]

    response = client.get(f"/something/NZTM2000/tilejson.json?url={DATA_DIR}/cog.tif")
    assert response.status_code == 422

    cog = TilerFactory(add_preview=False, add_part=False, add_viewer=False)
    assert len(cog.router.routes) == 10

    app = FastAPI()
    cog = TilerFactory()
    app.include_router(cog.router)

    add_exception_handlers(app, DEFAULT_STATUS_CODES)

    client = TestClient(app)

    response = client.get(
        f"/tiles/WebMercatorQuad/8/87/48?url={DATA_DIR}/cog.tif&rescale=0,1000"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    response = client.get(
        f"/tiles/WebMercatorQuad/8/87/48?url={DATA_DIR}/cog.tif&rescale=-3.4028235e+38,3.4028235e+38"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    response = client.get(
        f"/tiles/WebMercatorQuad/8/87/48.tif?url={DATA_DIR}/cog.tif&bidx=1&bidx=1&bidx=1&return_mask=false"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff; application=geotiff"
    meta = parse_img(response.content)
    assert meta["dtype"] == "uint16"
    assert meta["count"] == 3
    assert meta["width"] == 256
    assert meta["height"] == 256

    response = client.get(
        "/tiles/WebMercatorQuad/8/87/48.tif",
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
        f"/tiles/WebMercatorQuad/8/84/47?url={DATA_DIR}/cog.tif&bidx=1&rescale=0,1000&colormap_name=viridis"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    # Dict
    response = client.get(
        "/tiles/WebMercatorQuad/8/84/47.png",
        params={
            "url": f"{DATA_DIR}/cog.tif",
            "bidx": 1,
            "colormap": json.dumps(
                {
                    "1": [58, 102, 24, 255],
                    "2": [100, 177, 41],
                    "3": "#b1b129",
                    "4": "#ddcb9aFF",
                }
            ),
        },
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    # Intervals
    response = client.get(
        "/tiles/WebMercatorQuad/8/84/47.png",
        params={
            "url": f"{DATA_DIR}/cog.tif",
            "bidx": 1,
            "colormap": json.dumps(
                [
                    # ([min, max], [r, g, b, a])
                    ([1, 2], [0, 0, 0, 255]),
                    ([2, 3], [255, 255, 255, 255]),
                    ([3, 1000], [255, 0, 0, 255]),
                ]
            ),
        },
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    # Bad colormap format
    cmap = urlencode({"colormap": json.dumps({"1": [58, 102]})})
    response = client.get(
        f"/tiles/WebMercatorQuad/8/84/47.png?url={DATA_DIR}/cog.tif&bidx=1&{cmap}"
    )
    assert response.status_code == 400

    # no json encoding
    cmap = urlencode({"colormap": {"1": [58, 102]}})
    response = client.get(
        f"/tiles/WebMercatorQuad/8/84/47.png?url={DATA_DIR}/cog.tif&bidx=1&{cmap}"
    )
    assert response.status_code == 400

    # Test NumpyTile
    response = client.get(f"/tiles/WebMercatorQuad/8/87/48.npy?url={DATA_DIR}/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/x-binary"
    npy_tile = numpy.load(BytesIO(response.content))
    assert npy_tile.shape == (2, 256, 256)  # mask + data

    # Test Buffer
    response = client.get(
        f"/tiles/WebMercatorQuad/8/87/48.npy?url={DATA_DIR}/cog.tif&buffer=10"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/x-binary"
    npy_tile = numpy.load(BytesIO(response.content))
    assert npy_tile.shape == (2, 276, 276)  # mask + data

    response = client.get(
        f"/tiles/WebMercatorQuad/8/87/48.png?url={DATA_DIR}/cog.tif&tilesize=512"
    )
    assert response.status_code == 200
    meta = parse_img(response.content)
    assert meta["width"] == 512
    assert meta["height"] == 512

    response = client.get(
        f"/preview?url={DATA_DIR}/cog.tif&rescale=0,1000&max_size=256"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    response = client.get(
        f"/bbox/-56.228,72.715,-54.547,73.188.png?url={DATA_DIR}/cog.tif&rescale=0,1000&max_size=256"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    response = client.get(
        f"/bbox/-56.228,72.715,-54.547,73.188/100x100.png?url={DATA_DIR}/cog.tif&rescale=0,1000"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["driver"] == "PNG"
    assert meta["count"] == 2
    assert meta["width"] == 100
    assert meta["height"] == 100

    response = client.get(f"/point/-56.228,72.715?url={DATA_DIR}/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert len(response.json()["values"]) == 1
    assert response.json()["band_names"] == ["b1"]

    # Masked values
    response = client.get(f"/point/-59.337,73.9898?url={DATA_DIR}/cog.tif&nodata=1")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["values"] == [None]
    assert response.json()["band_names"] == ["b1"]

    response = client.get(
        f"/point/-6259272.328324187,12015838.020930404?url={DATA_DIR}/cog.tif&coord_crs=EPSG:3857"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert len(response.json()["values"]) == 1
    assert response.json()["band_names"] == ["b1"]

    response = client.get(f"/point/-56.228,72.715?url={DATA_DIR}/cog.tif&bidx=1&bidx=1")
    assert len(response.json()["values"]) == 2
    assert response.json()["band_names"] == ["b1", "b2"]
    assert response.json()["band_descriptions"] == ["b1", "b1"]

    response = client.get(
        f"/point/-56.228,72.715?url={DATA_DIR}/cog.tif&expression=b1*2"
    )
    assert len(response.json()["values"]) == 1
    assert response.json()["band_descriptions"] == ["b1*2"]

    # NOTE: tilejson tilesize default to 512x512
    # because Mapbox and Maplibre expect tiles to be 512x512
    response = client.get(f"/WebMercatorQuad/tilejson.json?url={DATA_DIR}/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["tilejson"]
    assert "tilesize=512" in response.json()["tiles"][0]

    response = client.get(
        f"/WebMercatorQuad/tilejson.json?url={DATA_DIR}/cog.tif&tilesize=256"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["tilejson"]
    assert "tilesize=256" in response.json()["tiles"][0]

    response = client.get(f"/WorldCRS84Quad/tilejson.json?url={DATA_DIR}/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["tilejson"]

    response = client.get(
        f"/WebMercatorQuad/tilejson.json?url={DATA_DIR}/cog.tif&tile_format=png"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["tilejson"]
    assert "png" in response.json()["tiles"][0]

    response = client.get(
        f"/WebMercatorQuad/tilejson.json?url={DATA_DIR}/cog.tif&minzoom=5&maxzoom=12"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["tilejson"]
    assert response.json()["minzoom"] == 5
    assert response.json()["maxzoom"] == 12

    response = client.get(f"/info?url={DATA_DIR}/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["band_metadata"]

    response = client.get(f"/info.geojson?url={DATA_DIR}/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    assert response.json()["type"] == "Feature"
    assert "bbox" in response.json()
    assert response.json()["geometry"]["type"] == "Polygon"

    # BBOX crossing the Antimeridian
    with pytest.warns(UserWarning):
        response = client.get(f"/info.geojson?url={DATA_DIR}/cog_dateline.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    assert response.json()["type"] == "Feature"
    assert "bbox" in response.json()
    assert response.json()["geometry"]["type"] == "MultiPolygon"

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

    response = client.get(f"/preview/512x512.png?url={DATA_DIR}/cog.tif&rescale=0,1000")
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

    response = client.post(f"/feature?url={DATA_DIR}/cog.tif", json=feature)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    response = client.post(
        f"/feature/100x100.png?url={DATA_DIR}/cog.tif&rescale=0,1000", json=feature
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["driver"] == "PNG"
    assert meta["width"] == 100
    assert meta["height"] == 100

    response = client.post(f"/feature.tif?url={DATA_DIR}/cog.tif", json=feature)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff; application=geotiff"
    meta = parse_img(response.content)
    assert meta["dtype"] == "uint16"
    assert meta["count"] == 2

    with pytest.warns(InvalidDatatypeWarning):
        response = client.post(
            f"/feature/100x100.jpeg?url={DATA_DIR}/cog.tif", json=feature
        )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    meta = parse_img(response.content)
    assert meta["width"] == 100
    assert meta["height"] == 100

    # GET - statistics
    stats_keys = [
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
        "description",
    ]

    response = client.get(f"/statistics?url={DATA_DIR}/cog.tif&bidx=1&bidx=1&bidx=1")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert len(resp) == 3
    assert set(resp["b1"].keys()) == {
        *stats_keys,
        "percentile_2",
        "percentile_98",
    }
    assert len(resp["b1"]["histogram"][0]) == 10
    assert resp["b1"]["description"] == "b1"

    response = client.get(f"/statistics?url={DATA_DIR}/cog.tif&expression=b1*2")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert len(resp) == 1
    assert set(resp["b1"].keys()) == {
        *stats_keys,
        "percentile_2",
        "percentile_98",
    }
    assert resp["b1"]["description"] == "b1*2"

    response = client.get(
        f"/statistics?url={DATA_DIR}/cog.tif&bidx=1&bidx=1&bidx=1&p=4&p=5"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert len(resp) == 3
    assert set(resp["b1"].keys()) == {
        *stats_keys,
        "percentile_4",
        "percentile_5",
    }
    assert resp["b1"]["description"] == "b1"

    response = client.get(f"/statistics?url={DATA_DIR}/cog.tif&categorical=true")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert len(resp) == 1
    assert set(resp["b1"].keys()) == {
        *stats_keys,
        "percentile_2",
        "percentile_98",
    }
    # categories are stored in the histogram
    assert len(resp["b1"]["histogram"][1]) == 15

    response = client.get(
        f"/statistics?url={DATA_DIR}/cog.tif&categorical=true&c=1&c=2&c=3&c=4"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert len(resp) == 1
    assert set(resp["b1"].keys()) == {
        *stats_keys,
        "percentile_2",
        "percentile_98",
    }
    assert resp["b1"]["histogram"][1] == [1.0, 2.0, 3.0, 4.0]  # categories
    assert resp["b1"]["histogram"][0][3] == 0  # 4.0 is not present in the array

    response = client.get(f"/statistics?url={DATA_DIR}/cog.tif&bidx=1&histogram_bins=3")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert len(resp) == 1
    assert len(resp["b1"]["histogram"][0]) == 3

    response = client.get(
        f"/statistics?url={DATA_DIR}/cog.tif&bidx=1&histogram_range=5,10"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert len(resp) == 1
    assert min(resp["b1"]["histogram"][1]) == 5.0
    assert max(resp["b1"]["histogram"][1]) == 10.0

    # Stats with Algorithm
    response = client.get(
        f"/statistics?url={DATA_DIR}/cog.tif&bidx=1&bidx=1&algorithm=normalizedIndex"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert len(resp) == 1
    assert resp["b1"]["description"] == "(b1 - b1) / (b1 + b1)"

    # POST - statistics
    response = client.post(
        f"/statistics?url={DATA_DIR}/cog.tif&bidx=1&bidx=1&bidx=1", json=feature
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    resp = response.json()
    assert resp["type"] == "Feature"
    assert len(resp["properties"]["statistics"]) == 3
    assert set(resp["properties"]["statistics"]["b1"].keys()) == {
        *stats_keys,
        "percentile_2",
        "percentile_98",
    }
    assert resp["properties"]["statistics"]["b1"]["description"] == "b1"
    assert resp["properties"]["statistics"]["b2"]["description"] == "b1"

    response = client.post(
        f"/statistics?url={DATA_DIR}/cog.tif&bidx=1&bidx=1&bidx=1",
        json=feature_collection,
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    resp = response.json()
    assert resp["type"] == "FeatureCollection"
    assert len(resp["features"][0]["properties"]["statistics"]) == 3
    assert set(resp["features"][0]["properties"]["statistics"]["b1"].keys()) == {
        *stats_keys,
        "percentile_2",
        "percentile_98",
    }
    assert resp["features"][0]["properties"]["statistics"]["b1"]["description"] == "b1"
    assert resp["features"][0]["properties"]["statistics"]["b2"]["description"] == "b1"

    response = client.post(
        "/statistics",
        json=feature,
        params={"categorical": True, "max_size": 1024, "url": f"{DATA_DIR}/cog.tif"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    resp = response.json()
    assert resp["type"] == "Feature"
    assert len(resp["properties"]["statistics"]) == 1
    assert set(resp["properties"]["statistics"]["b1"].keys()) == {
        *stats_keys,
        "percentile_2",
        "percentile_98",
    }
    assert len(resp["properties"]["statistics"]["b1"]["histogram"][1]) == 13
    assert resp["properties"]["statistics"]["b1"]["description"] == "b1"

    response = client.post(
        "/statistics",
        json=feature,
        params=(
            ("categorical", True),
            ("c", 1),
            ("c", 2),
            ("c", 3),
            ("c", 4),
            ("max_size", 1024),
            ("url", f"{DATA_DIR}/cog.tif"),
        ),
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    resp = response.json()
    assert resp["type"] == "Feature"
    assert len(resp["properties"]["statistics"]) == 1
    assert set(resp["properties"]["statistics"]["b1"].keys()) == {
        *stats_keys,
        "percentile_2",
        "percentile_98",
    }
    assert len(resp["properties"]["statistics"]["b1"]["histogram"][0]) == 4
    assert resp["properties"]["statistics"]["b1"]["histogram"][0][3] == 0

    # Stats with Algorithm
    response = client.post(
        f"/statistics?url={DATA_DIR}/cog.tif&bidx=1&bidx=1&algorithm=normalizedIndex",
        json=feature,
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    resp = response.json()
    assert resp["type"] == "Feature"
    assert len(resp["properties"]["statistics"]) == 1
    assert (
        resp["properties"]["statistics"]["b1"]["description"] == "(b1 - b1) / (b1 + b1)"
    )

    # Test with Algorithm
    response = client.get(f"/preview.tif?url={DATA_DIR}/dem.tif&return_mask=False")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff; application=geotiff"
    meta = parse_img(response.content)
    assert meta["dtype"] == "float32"
    assert meta["count"] == 1

    response = client.get(
        f"/preview.tif?url={DATA_DIR}/dem.tif&return_mask=False&algorithm=terrarium"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff; application=geotiff"
    meta = parse_img(response.content)
    assert meta["dtype"] == "uint8"
    assert meta["count"] == 3

    # OGC Tileset
    response = client.get(f"/tiles?url={DATA_DIR}/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert len(resp["tilesets"]) == NB_DEFAULT_TMS

    first_tms = resp["tilesets"][0]
    first_id = DEFAULT_TMS.list()[0]
    assert first_id in first_tms["title"]
    assert len(first_tms["links"]) == 2  # no link to the tms definition

    response = client.get(f"/tiles/WebMercatorQuad?url={DATA_DIR}/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    # covers only 5 zoom levels
    assert len(resp["tileMatrixSetLimits"]) == 5


@patch("rio_tiler.io.rasterio.rasterio")
def test_MultiBaseTilerFactory(rio):
    """test MultiBaseTilerFactory."""
    rio.open = mock_rasterio_open

    stac = MultiBaseTilerFactory(reader=STACReader)
    assert len(stac.router.routes) == 21

    app = FastAPI()
    app.include_router(stac.router)

    add_exception_handlers(app, DEFAULT_STATUS_CODES)

    client = TestClient(app)

    response = client.get("/openapi.json")
    assert response.status_code == 200

    response = client.get("/docs")
    assert response.status_code == 200

    response = client.get(f"/assets?url={DATA_DIR}/item.json")
    assert response.status_code == 200
    assert len(response.json()) == 2

    # no assets
    with pytest.warns(UserWarning):
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
            "assets": "B01|indexes=1,1,1",
            "return_mask": False,
        },
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
            "expression": "b1;b1;b1",
            "return_mask": False,
        },
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff; application=geotiff"
    meta = parse_img(response.content)
    assert meta["dtype"] == "int32"
    assert meta["count"] == 3

    response = client.get(
        "/preview.tif",
        params={
            "url": f"{DATA_DIR}/item.json",
            "assets": "B01|expression=b1;b1;b1",
            "return_mask": False,
        },
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff; application=geotiff"
    meta = parse_img(response.content)
    assert meta["dtype"] == "int32"
    assert meta["count"] == 3

    # Use asset_as_band option
    response = client.get(
        "/preview.tif",
        params={
            "url": f"{DATA_DIR}/item.json",
            "assets": "B01",
            "asset_as_band": True,
            "return_mask": False,
        },
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff; application=geotiff"
    meta = parse_img(response.content)
    assert meta["dtype"] == "uint16"
    assert meta["count"] == 1

    # GET - statistics
    stats_keys = [
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
        "description",
    ]

    response = client.get(
        f"/asset_statistics?url={DATA_DIR}/item.json&assets=B01&assets=B09"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert len(resp) == 2
    assert set(resp["B01"]["b1"].keys()) == {
        *stats_keys,
        "percentile_2",
        "percentile_98",
    }
    assert resp["B09"]["b1"]["description"] == "b1"

    response = client.get(
        f"/asset_statistics?url={DATA_DIR}/item.json&assets=B09|indexes=1,1"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert len(resp) == 1
    assert resp["B09|indexes=1,1"]["b1"]
    assert resp["B09|indexes=1,1"]["b2"]
    assert resp["B09|indexes=1,1"]["b1"]["description"] == "b1"
    assert resp["B09|indexes=1,1"]["b2"]["description"] == "b1"

    # default to all assets
    response = client.get(f"/statistics?url={DATA_DIR}/item.json")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert len(resp) == 2

    response = client.get(f"/statistics?url={DATA_DIR}/item.json&assets=B01&assets=B09")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert list(resp) == ["b1", "b2"]
    assert set(resp["b1"].keys()) == {
        *stats_keys,
        "percentile_2",
        "percentile_98",
    }
    assert resp["b1"]["description"] == "B01_b1"
    assert resp["b2"]["description"] == "B09_b1"

    response = client.get(f"/statistics?url={DATA_DIR}/item.json&assets=B01&assets=B09")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert len(resp) == 2
    assert resp["b1"]["description"] == "B01_b1"
    assert resp["b2"]["description"] == "B09_b1"

    response = client.get(
        f"/statistics?url={DATA_DIR}/item.json&assets=B01&assets=B09&asset_as_band=True"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert len(resp) == 2
    assert resp["b1"]["description"] == "B01"
    assert resp["b2"]["description"] == "B09"

    # with Algorithm
    response = client.get(
        f"/statistics?url={DATA_DIR}/item.json&assets=B01&assets=B09&algorithm=normalizedIndex&asset_as_band=True"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert resp["b1"]["description"] == "(B09 - B01) / (B09 + B01)"

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
    assert set(props["b1"].keys()) == {
        *stats_keys,
        "percentile_2",
        "percentile_98",
    }
    assert props["b1"]["description"] == "B01_b1"
    assert props["b2"]["description"] == "B09_b1"

    # default to all assets
    response = client.post(
        f"/statistics?url={DATA_DIR}/item.json",
        json=stac_feature["features"][0],
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    resp = response.json()
    assert len(resp["properties"]["statistics"]) == 2

    response = client.post(
        f"/statistics?url={DATA_DIR}/item.json&assets=B01&assets=B09", json=stac_feature
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    resp = response.json()
    props = resp["features"][0]["properties"]["statistics"]
    assert len(props) == 2
    assert set(props["b1"].keys()) == {
        *stats_keys,
        "percentile_2",
        "percentile_98",
    }
    assert props["b1"]["description"] == "B01_b1"

    response = client.post(
        f"/statistics?url={DATA_DIR}/item.json&assets=B01&assets=B09&asset_as_band=True",
        json=stac_feature["features"][0],
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    resp = response.json()
    props = resp["properties"]["statistics"]
    assert len(props) == 2
    assert set(props["b1"].keys()) == {
        *stats_keys,
        "percentile_2",
        "percentile_98",
    }
    assert props["b1"]["description"] == "B01"
    assert props["b2"]["description"] == "B09"

    response = client.post(
        f"/statistics?url={DATA_DIR}/item.json&assets=B01&assets=B09&expression=b1/b2&asset_as_band=True",
        json=stac_feature["features"][0],
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    resp = response.json()
    props = resp["properties"]["statistics"]
    assert len(props) == 1
    assert set(props["b1"].keys()) == {
        *stats_keys,
        "percentile_2",
        "percentile_98",
    }
    assert props["b1"]["description"] == "B01/B09"

    # with Algorithm
    response = client.post(
        f"/statistics?url={DATA_DIR}/item.json&assets=B01&assets=B09&algorithm=normalizedIndex&asset_as_band=True",
        json=stac_feature["features"][0],
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    resp = response.json()
    props = resp["properties"]["statistics"]
    assert len(props) == 1
    assert props["b1"]["description"] == "(B09 - B01) / (B09 + B01)"

    # OGC Tileset
    response = client.get(f"/tiles?url={DATA_DIR}/item.json")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    assert len(resp["tilesets"]) == NB_DEFAULT_TMS

    first_tms = resp["tilesets"][0]
    first_id = DEFAULT_TMS.list()[0]
    assert first_id in first_tms["title"]
    assert len(first_tms["links"]) == 2  # no link to the tms definition

    response = client.get(f"/tiles/WebMercatorQuad?url={DATA_DIR}/item.json")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    resp = response.json()
    # default minzoom/maxzoom are 0->24
    assert len(resp["tileMatrixSetLimits"]) == 25


@attr.s
class BandFileReader(MultiBandReader):
    """Test MultiBand"""

    input: str = attr.ib()
    tms: morecantile.TileMatrixSet = attr.ib(
        default=morecantile.tms.get("WebMercatorQuad")
    )

    reader: Type[BaseReader] = attr.ib(default=Reader)
    reader_options: Dict = attr.ib(factory=dict)

    bands: Sequence[str] = attr.ib(init=False)
    default_bands: Optional[Sequence[str]] = attr.ib(init=False, default=None)

    minzoom: int = attr.ib(init=False)
    maxzoom: int = attr.ib(init=False)

    def __attrs_post_init__(self):
        """Parse Sceneid and get grid bounds."""
        self.bands = sorted([p.stem for p in pathlib.Path(self.input).glob("B0*.tif")])
        with self.reader(self._get_band_url(self.bands[0])) as cog:
            self.bounds = cog.bounds
            self.crs = cog.crs
            self.minzoom = cog.minzoom
            self.maxzoom = cog.maxzoom
            self.width = cog.width
            self.height = cog.height
            self.transform = cog.transform

    def _get_band_url(self, band: str) -> str:
        """Validate band's name and return band's url."""
        return os.path.join(self.input, f"{band}.tif")


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
    assert body["id"] == "WebMercatorQuad"

    response = client.get("/tms/tileMatrixSets/WebMercatorQua")
    assert response.status_code == 422

    app = FastAPI()
    tms_endpoints = TMSFactory(supported_tms=WEB_TMS)
    app.include_router(
        tms_endpoints.router,
    )

    client = TestClient(app)

    response = client.get("/tileMatrixSets")
    assert response.status_code == 200
    body = response.json()
    assert len(body["tileMatrixSets"]) == 1

    response = client.get("/tileMatrixSets/WebMercatorQuad")
    assert response.status_code == 200

    response = client.get("/tileMatrixSets/LINZAntarticaMapTilegrid")
    assert response.status_code == 422


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
                    {"path": "/info", "method": "GET"},
                    {"path": "/tiles/{tileMatrixSetId}/{z}/{x}/{y}", "method": "GET"},
                ],
                [Depends(must_be_bob)],
            ),
        ],
        router_prefix="something",
    )
    assert len(cog.router.routes) == 19

    app = FastAPI()
    app.include_router(cog.router, prefix="/something")
    client = TestClient(app)

    auth_bob = httpx.BasicAuth(username="bob", password="ILoveSponge")
    auth_notbob = httpx.BasicAuth(username="notbob", password="IHateSponge")

    response = client.get(
        f"/something/WebMercatorQuad/tilejson.json?url={DATA_DIR}/cog.tif"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["tilejson"]

    response = client.get(f"/something/info?url={DATA_DIR}/cog.tif", auth=auth_bob)
    assert response.status_code == 200

    response = client.get(f"/something/info?url={DATA_DIR}/cog.tif", auth=auth_notbob)
    assert response.status_code == 401
    assert response.json()["detail"] == "You're not Bob"

    response = client.get(
        f"/something/tiles/WebMercatorQuad/8/87/48?url={DATA_DIR}/cog.tif&rescale=0,1000",
        auth=auth_bob,
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    response = client.get(
        f"/something/tiles/WebMercatorQuad/8/87/48?url={DATA_DIR}/cog.tif&rescale=0,1000",
        auth=auth_notbob,
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "You're not Bob"

    response = client.get(
        f"/something/tiles/WebMercatorQuad/8/87/48.jpeg?url={DATA_DIR}/cog.tif&rescale=0,1000"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    cog = TilerFactory(router_prefix="something")
    cog.add_route_dependencies(
        scopes=[{"path": "/info", "method": "GET"}],
        dependencies=[Depends(must_be_bob)],
    )

    app = FastAPI()
    app.include_router(cog.router, prefix="/something")
    client = TestClient(app)

    response = client.get(
        f"/something/WebMercatorQuad/tilejson.json?url={DATA_DIR}/cog.tif"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["tilejson"]

    response = client.get(f"/something/info?url={DATA_DIR}/cog.tif", auth=auth_bob)
    assert response.status_code == 200

    response = client.get(f"/something/info?url={DATA_DIR}/cog.tif", auth=auth_notbob)
    assert response.status_code == 401
    assert response.json()["detail"] == "You're not Bob"


def test_TilerFactory_WithGdalEnv():
    """test environment_dependency option."""

    router = TilerFactory(
        environment_dependency=lambda: {"GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR"}
    ).router
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    with pytest.warns(NoOverviewWarning):
        response = client.get(f"/info?url={DATA_DIR}/non_cog.tif")
    assert not response.json()["overviews"]

    router = TilerFactory(
        environment_dependency=lambda: {"GDAL_DISABLE_READDIR_ON_OPEN": "FALSE"}
    ).router
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    response = client.get(f"/info?url={DATA_DIR}/non_cog.tif")
    assert response.json()["overviews"]

    class ReaddirType(str, Enum):
        false = "false"
        true = "true"
        empty_dir = "empty_dir"

    def gdal_env(disable_read: ReaddirType = Query(ReaddirType.false)):
        return {"GDAL_DISABLE_READDIR_ON_OPEN": disable_read.value.upper()}

    router = TilerFactory(environment_dependency=gdal_env).router
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        response = client.get(f"/info?url={DATA_DIR}/non_cog.tif")
        assert response.json()["overviews"]

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        response = client.get(f"/info?url={DATA_DIR}/non_cog.tif&disable_read=false")
        assert response.json()["overviews"]

    with pytest.warns(NoOverviewWarning):
        response = client.get(
            f"/info?url={DATA_DIR}/non_cog.tif&disable_read=empty_dir"
        )
        assert not response.json()["overviews"]


def test_algorithm():
    """Test Algorithms endpoint."""
    algorithm = AlgorithmFactory()

    app = FastAPI()
    app.include_router(algorithm.router)
    client = TestClient(app)

    response = client.get("/algorithms")
    assert response.status_code == 200
    algo_ids = [algo["id"] for algo in response.json()["algorithms"]]
    assert "hillshade" in algo_ids

    response = client.get("/algorithms", params={"f": "html"})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

    response = client.get("/algorithms", headers={"Accept": "text/html"})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

    response = client.get("/algorithms/hillshade")
    assert response.status_code == 200

    response = client.get("/algorithms/hillshade", params={"f": "html"})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

    response = client.get("/algorithms/hillshade", headers={"Accept": "text/html"})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_path_param_in_prefix():
    """Test path params in prefix."""

    @define
    class EndpointFactory(BaseFactory):
        def register_routes(self):
            """register endpoints."""

            @self.router.get("/{param2}.json")
            def route2(
                request: Request, param1: int = Path(...), param2: str = Path(...)
            ):
                """return url."""
                return {"url": self.url_for(request, "route1", param2=param2)}

            @self.router.get("/{param2}")
            def route1(param1: int = Path(...), param2: str = Path(...)):
                """return param."""
                return {"value": param2}

    app = FastAPI()
    endpoints = EndpointFactory(router_prefix="/prefixed/{param1}")
    app.include_router(endpoints.router, prefix="/prefixed/{param1}")
    client = TestClient(app)

    response = client.get("/p")
    assert response.status_code == 404

    response = client.get("/prefixed/100/value")
    assert response.json()["value"] == "value"

    response = client.get("/prefixed/100/value.json")
    assert response.json()["url"] == "http://testserver/prefixed/100/value"


def test_AutoFormat_Colormap():
    """Make sure we take both alpha/mask into account."""
    app = FastAPI()
    cog = TilerFactory()
    app.include_router(cog.router)

    with TestClient(app) as client:
        response = client.get(
            "/preview",
            params={
                "url": f"{DATA_DIR}/cog.tif",
                "bidx": 1,
                "colormap": json.dumps(
                    [
                        # ([min, max], [r, g, b, a])
                        ([0, 1], [255, 255, 255, 0]),  # should be masked
                        ([2, 6000], [255, 0, 0, 255]),
                        ([6001, 300000], [0, 255, 0, 255]),
                    ]
                ),
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        with MemoryFile(response.content) as mem:
            with mem.open() as dst:
                img = dst.read()
                assert img[:, 0, 0].tolist() == [
                    0,
                    0,
                    0,
                    0,
                ]  # when creating a PNG, GDAL will set masked value to 0
                assert img[:, 500, 500].tolist() == [255, 0, 0, 255]


def test_rescale_dependency():
    """Ensure that we can set default rescale values via the rescale_dependency"""

    @dataclass
    class ImageRenderingParams(dependencies.ImageRenderingParams):
        """Custom ImageParams."""

        def __post_init__(self):
            if self.rescale:
                rescale_array = []
                for r in self.rescale:
                    parsed = tuple(
                        map(
                            float,
                            r.replace(" ", "")
                            .replace("[", "")
                            .replace("]", "")
                            .split(","),
                        )
                    )
                    assert (
                        len(parsed) == 2
                    ), f"Invalid rescale values: {self.rescale}, should be of form ['min,max', 'min,max'] or [[min,max], [min, max]]"
                    rescale_array.append(parsed)

                self.rescale = rescale_array  # Noqa
            else:
                self.rescale = [(0, 100)]

    cog = TilerFactory()
    cog_custom_range = TilerFactory(render_dependency=ImageRenderingParams)

    app = FastAPI()
    app.include_router(cog.router, prefix="/cog")
    app.include_router(cog_custom_range.router, prefix="/cog_custom")

    with TestClient(app) as client:
        response = client.get(
            f"/cog/tiles/WebMercatorQuad/8/87/48.npy?url={DATA_DIR}/cog.tif&rescale=0,1000"
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/x-binary"
        npy_tile = numpy.load(BytesIO(response.content))
        assert npy_tile.shape == (2, 256, 256)  # mask + data

        response = client.get(
            f"/cog_custom/tiles/WebMercatorQuad/8/87/48.npy?url={DATA_DIR}/cog.tif&rescale=0,1000"
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/x-binary"
        numpy.load(BytesIO(response.content))
        assert npy_tile.shape == (2, 256, 256)  # mask + data


def test_dst_crs_option():
    """test dst_crs parameter."""
    app = FastAPI()
    app.include_router(TilerFactory().router)

    with TestClient(app) as client:
        # preview endpoints
        response = client.get(f"/preview.tif?url={DATA_DIR}/cog.tif")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/tiff; application=geotiff"
        meta = parse_img(response.content)
        assert meta["crs"] == CRS.from_epsg(
            32621
        )  # return the image in the original CRS

        response = client.get(f"/preview.tif?url={DATA_DIR}/cog.tif&dst_crs=epsg:4326")
        meta = parse_img(response.content)
        assert meta["crs"] == CRS.from_epsg(4326)
        assert not meta["crs"] == CRS.from_epsg(32621)

        # /bbox endpoints
        response = client.get(
            f"/bbox/-56.228,72.715,-54.547,73.188.tif?url={DATA_DIR}/cog.tif"
        )
        meta = parse_img(response.content)
        assert meta["crs"] == CRS.from_epsg(
            4326
        )  # default is to return image in the bounds-crs
        assert not meta["crs"] == CRS.from_epsg(32621)

        # Force output in epsg:32621
        response = client.get(
            f"/bbox/-56.228,72.715,-54.547,73.188.tif?url={DATA_DIR}/cog.tif&dst_crs=epsg:32621"
        )
        meta = parse_img(response.content)
        assert meta["crs"] == CRS.from_epsg(32621)

        # coord_crs + dst_crs
        response = client.get(
            f"/bbox/-6259272.328324187,12015838.020930404,-6072144.264300693,12195445.265479913.tif?url={DATA_DIR}/cog.tif&coord_crs=epsg:3857"
        )
        meta = parse_img(response.content)
        assert meta["crs"] == CRS.from_epsg(3857)

        response = client.get(
            f"/bbox/-6259272.328324187,12015838.020930404,-6072144.264300693,12195445.265479913.tif?url={DATA_DIR}/cog.tif&coord_crs=epsg:3857&dst_crs=epsg:32621"
        )
        meta = parse_img(response.content)
        assert meta["crs"] == CRS.from_epsg(32621)


def test_color_formula_dependency():
    """Ensure that we can set default color formulae via the color_formula_dependency"""

    @dataclass
    class ImageRenderingParams(dependencies.ImageRenderingParams):
        """Custom ImageParams."""

        color_formula: Annotated[
            Optional[str],
            Query(
                title="Color Formula",
                description="rio-color formula (info: https://github.com/mapbox/rio-color)",
            ),
        ] = "sigmoidal R 7 0.4"

    cog = TilerFactory()
    cog_custom_color_formula = TilerFactory(render_dependency=ImageRenderingParams)

    app = FastAPI()
    app.include_router(cog.router, prefix="/cog")
    app.include_router(cog_custom_color_formula.router, prefix="/cog_custom")

    with TestClient(app) as client:
        response = client.get(
            f"/cog/tiles/WebMercatorQuad/8/87/48.npy?url={DATA_DIR}/cog.tif&color_formula=sigmoidal R 10 0.1"
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/x-binary"
        npy_tile = numpy.load(BytesIO(response.content))
        assert npy_tile.shape == (2, 256, 256)  # mask + data

        response = client.get(
            f"/cog_custom/tiles/WebMercatorQuad/8/87/48.npy?url={DATA_DIR}/cog.tif"
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/x-binary"
        numpy.load(BytesIO(response.content))
        assert npy_tile.shape == (2, 256, 256)  # mask + data


def test_colormap_factory():
    """Test ColorMapFactory endpoint."""
    # Register custom colormaps
    cmaps = default_cmap.register(
        {
            "cust": {0: (0, 0, 0, 255), 1: (255, 0, 0, 255), 255: (255, 255, 0, 255)},
            "negative": {
                -100: (0, 0, 0, 255),
                1: (255, 0, 0, 255),
                255: (255, 255, 0, 255),
            },
            "seq": [
                ((1, 2), (255, 0, 0, 255)),
                ((2, 3), (255, 240, 255, 255)),
            ],
        }
    )

    cmaps = ColorMapFactory(supported_colormaps=cmaps)

    app = FastAPI()
    app.include_router(cmaps.router)
    client = TestClient(app)

    response = client.get("/colorMaps")
    assert response.status_code == 200
    cmap_ids = [cm["id"] for cm in response.json()["colormaps"]]
    assert "cust" in cmap_ids
    assert "negative" in cmap_ids
    assert "seq" in cmap_ids
    assert "viridis" in cmap_ids

    response = client.get("/colorMaps", headers={"Accept": "text/html"})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

    response = client.get("/colorMaps/viridis")
    assert response.status_code == 200

    response = client.get("/colorMaps/viridis", headers={"Accept": "text/html"})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

    response = client.get("/colorMaps/cust")
    assert response.status_code == 200

    response = client.get("/colorMaps/negative")
    assert response.status_code == 200

    response = client.get("/colorMaps/seq")
    assert response.status_code == 200

    response = client.get("/colorMaps/yo")
    assert response.status_code == 422

    response = client.get("/colorMaps/viridis", params={"f": "png"})
    assert response.status_code == 200
    meta = parse_img(response.content)
    assert meta["dtype"] == "uint8"
    assert meta["count"] == 4
    assert meta["width"] == 256
    assert meta["height"] == 20

    response = client.get(
        "/colorMaps/viridis", params={"f": "png", "orientation": "vertical"}
    )
    assert response.status_code == 200
    meta = parse_img(response.content)
    assert meta["dtype"] == "uint8"
    assert meta["count"] == 4
    assert meta["width"] == 20
    assert meta["height"] == 256

    response = client.get(
        "/colorMaps/viridis", params={"f": "png", "width": 1000, "height": 100}
    )
    assert response.status_code == 200
    meta = parse_img(response.content)
    assert meta["dtype"] == "uint8"
    assert meta["count"] == 4
    assert meta["width"] == 1000
    assert meta["height"] == 100

    response = client.get("/colorMaps/cust", params={"f": "png"})
    assert response.status_code == 200
    meta = parse_img(response.content)
    assert meta["dtype"] == "uint8"
    assert meta["count"] == 4
    assert meta["width"] == 256
    assert meta["height"] == 20

    response = client.get(
        "/colorMaps/cust", params={"f": "png", "orientation": "vertical"}
    )
    assert response.status_code == 200
    meta = parse_img(response.content)
    assert meta["dtype"] == "uint8"
    assert meta["count"] == 4
    assert meta["width"] == 20
    assert meta["height"] == 256

    response = client.get("/colorMaps/negative", params={"f": "png"})
    assert response.status_code == 200
    meta = parse_img(response.content)
    assert meta["dtype"] == "uint8"
    assert meta["count"] == 4
    assert meta["width"] == 256
    assert meta["height"] == 20

    response = client.get(
        "/colorMaps/negative", params={"f": "png", "orientation": "vertical"}
    )
    assert response.status_code == 200
    meta = parse_img(response.content)
    assert meta["dtype"] == "uint8"
    assert meta["count"] == 4
    assert meta["width"] == 20
    assert meta["height"] == 256

    response = client.get("/colorMaps/seq", params={"f": "png"})
    assert response.status_code == 200
    meta = parse_img(response.content)
    assert meta["dtype"] == "uint8"
    assert meta["count"] == 4
    assert meta["width"] == 256
    assert meta["height"] == 20

    response = client.get(
        "/colorMaps/seq", params={"f": "png", "orientation": "vertical"}
    )
    assert response.status_code == 200
    meta = parse_img(response.content)
    assert meta["dtype"] == "uint8"
    assert meta["count"] == 4
    assert meta["width"] == 20
    assert meta["height"] == 256


def test_ogc_maps_cog():
    """Test TilerFactory class."""
    cog_path = f"{DATA_DIR}/cog.tif"

    cog = TilerFactory(add_ogc_maps=True)
    assert len(cog.router.routes) == 20

    assert "https://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/core" in cog.conforms_to

    app = FastAPI()
    app.include_router(cog.router)
    with TestClient(app) as client:
        # Conformance Class “Core”
        response = client.get(
            "/map",
            params={
                "url": cog_path,
            },
        )
        assert response.status_code == 200
        headers = response.headers
        assert (
            headers["Content-Bbox"]
            == "373185.0,8019284.949381611,639014.9492102272,8286015.0"
        )
        assert headers["Content-Crs"] == "<http://www.opengis.net/def/crs/EPSG/0/32621>"
        assert headers["content-type"] == "image/png"
        meta = parse_img(response.content)
        assert meta["width"] == 1021
        assert meta["height"] == 1024  # default max size

        response = client.get(
            "/map",
            params={
                "url": cog_path,
            },
            headers={"Accept": "image/jpeg"},
        )
        assert response.status_code == 200
        headers = response.headers
        assert "Content-Bbox" in headers
        assert "Content-Crs" in headers
        assert headers["content-type"] == "image/jpeg"
        meta = parse_img(response.content)
        assert not meta["crs"]

        response = client.get("/map", params={"url": cog_path, "f": "tif"})
        assert response.status_code == 200
        headers = response.headers
        assert "Content-Bbox" in headers
        assert "Content-Crs" in headers
        assert headers["content-type"] == "image/tiff; application=geotiff"
        meta = parse_img(response.content)
        assert meta["crs"]

        response = client.get("/map", params={"url": cog_path, "f": "tiff"})
        assert response.status_code == 200
        headers = response.headers
        assert "Content-Bbox" in headers
        assert "Content-Crs" in headers
        assert headers["content-type"] == "image/tiff; application=geotiff"
        meta = parse_img(response.content)
        assert meta["crs"]

        # Conformance Class “Scaling”
        # /req/scaling/width-definition
        response = client.get(
            "/map",
            params={
                "url": cog_path,
                "width": 256,
            },
        )
        assert response.status_code == 200
        meta = parse_img(response.content)
        assert meta["width"] == 256
        assert meta["height"] == 257

        response = client.get(
            "/map",
            params={
                "url": cog_path,
                "width": -256,
            },
        )
        assert response.status_code == 422

        # /req/scaling/height-definition
        response = client.get(
            "/map",
            params={
                "url": cog_path,
                "height": 256,
            },
        )
        assert response.status_code == 200
        meta = parse_img(response.content)
        assert meta["height"] == 256

        response = client.get(
            "/map",
            params={
                "url": cog_path,
                "height": -256,
            },
        )
        assert response.status_code == 422

        # Conformance Class “Spatial Subsetting”
        # /conf/spatial-subsetting/bbox-crs
        response = client.get(
            "/map",
            params={
                "url": cog_path,
                "bbox": "-56.228,72.715,-54.547,73.188",
            },
        )
        headers = response.headers
        assert headers["Content-Crs"] == "<http://www.opengis.net/def/crs/EPSG/0/32621>"
        bbox = list(map(float, headers["Content-Bbox"].split(",")))
        assert all(
            math.isclose(a, b, rel_tol=1e-5)
            for a, b in zip(
                bbox,
                [
                    524922.2217886819,
                    8068852.367048624,
                    581330.6416587981,
                    8123074.564952523,
                ],
            )
        )

        assert headers["content-type"] == "image/png"
        meta = parse_img(response.content)

        response = client.get(
            "/map",
            params={
                "url": cog_path,
                "bbox": "-56.228,72.715,-54.547,73.188",
                "bbox-crs": "http://www.opengis.net/def/crs/OGC/0/CRS84",
            },
        )
        headers = response.headers
        assert headers["Content-Crs"] == "<http://www.opengis.net/def/crs/EPSG/0/32621>"
        bbox = list(map(float, headers["Content-Bbox"].split(",")))
        assert all(
            math.isclose(a, b, rel_tol=1e-5)
            for a, b in zip(
                bbox,
                [
                    524922.2217886819,
                    8068852.367048624,
                    581330.6416587981,
                    8123074.564952523,
                ],
            )
        )
        assert headers["content-type"] == "image/png"

        response = client.get(
            "/map",
            params={
                "url": cog_path,
                "bbox": "-6259272.328324187,12015838.020930404,-6072144.264300693,12195445.265479913",
                "bbox-crs": "[EPSG:3857]",
            },
        )
        assert response.status_code == 200
        headers = response.headers
        assert headers["Content-Crs"] == "<http://www.opengis.net/def/crs/EPSG/0/32621>"
        bbox = list(map(float, headers["Content-Bbox"].split(",")))
        assert all(
            math.isclose(a, b, rel_tol=1e-5)
            for a, b in zip(
                bbox,
                [
                    524922.2217886819,
                    8068852.367048624,
                    581330.6416587981,
                    8123074.564952523,
                ],
            )
        )
        assert headers["content-type"] == "image/png"

        # Abstract Test for Requirement crs parameter definition
        response = client.get(
            "/map",
            params={
                "url": cog_path,
                "bbox": "-6259272.328324187,12015838.020930404,-6072144.264300693,12195445.265479913",
                "bbox-crs": "[EPSG:3857]",
                "crs": "[EPSG:4326]",
            },
        )
        assert response.status_code == 200
        headers = response.headers
        assert headers["Content-Crs"] == "<http://www.opengis.net/def/crs/EPSG/0/4326>"
        assert headers["Content-Bbox"] == "-56.228,72.715,-54.54699999999999,73.188"
        assert headers["content-type"] == "image/png"
