"""Test TiTiler Tiler Factories."""

import json
import os
import pathlib
from typing import Dict, Type
from unittest.mock import patch
from urllib.parse import urlencode

import attr
import morecantile
from rio_tiler.io import BaseReader, COGReader, MultiBandReader, STACReader

from titiler.core.dependencies import TMSParams, WebMercatorTMSParams
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.core.factory import (
    MultiBandTilerFactory,
    MultiBaseTilerFactory,
    TilerFactory,
    TMSFactory,
)
from titiler.core.resources.enums import OptionalHeader

from .conftest import DATA_DIR, mock_rasterio_open, parse_img

from fastapi import FastAPI

from starlette.testclient import TestClient


def test_TilerFactory():
    """Test TilerFactory class."""
    cog = TilerFactory()
    assert len(cog.router.routes) == 21
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
    assert len(cog.router.routes) == 17

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
        f"/tiles/8/87/48.tif?url={DATA_DIR}/cog.tif&expression=b1,b1,b1&return_mask=false"
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

    # Bad colormap format
    cmap = urlencode({"colormap": json.dumps({"1": [58, 102]})})
    response = client.get(f"/tiles/8/84/47.png?url={DATA_DIR}/cog.tif&bidx=1&{cmap}")
    assert response.status_code == 400

    # no json encoding
    cmap = urlencode({"colormap": {"1": [58, 102]}})
    response = client.get(f"/tiles/8/84/47.png?url={DATA_DIR}/cog.tif&bidx=1&{cmap}")
    assert response.status_code == 400

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
    assert not response.json().get("minzoom")

    response = client.get(f"/info.geojson?url={DATA_DIR}/cog.tif")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    assert response.json()["type"] == "Feature"

    response = client.get(f"/metadata?url={DATA_DIR}/cog.tif&max_size=256")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["statistics"]
    assert response.json()["band_metadata"]

    response = client.get(
        f"/metadata?url={DATA_DIR}/cog.tif&bounds=-56.228,72.715,-54.547,73.188&max_size=256"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["statistics"]
    assert response.json()["band_metadata"]

    response = client.get(
        f"/metadata?url={DATA_DIR}/cog.tif&bidx=1&histogram_range=0,100"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["statistics"]["1"]["histogram"][0][1] == 0.0

    response = client.get(f"/metadata?url={DATA_DIR}/cog.tif&histogram_bins=4")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert len(response.json()["statistics"]["1"]["histogram"][0]) == 4

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


@patch("rio_tiler.io.cogeo.rasterio")
def test_MultiBaseTilerFactory(rio):
    """test MultiBaseTilerFactory."""
    rio.open = mock_rasterio_open

    stac = MultiBaseTilerFactory(reader=STACReader)
    assert len(stac.router.routes) == 22

    app = FastAPI()
    app.include_router(stac.router)

    add_exception_handlers(app, DEFAULT_STATUS_CODES)

    client = TestClient(app)

    response = client.get(f"/assets?url={DATA_DIR}/item.json")
    assert response.status_code == 200
    assert len(response.json()) == 17

    response = client.get(f"/bounds?url={DATA_DIR}/item.json")
    assert response.status_code == 200
    assert len(response.json()["bounds"]) == 4

    response = client.get(f"/info?url={DATA_DIR}/item.json&assets=B01")
    assert response.status_code == 200
    assert response.json()["B01"]

    response = client.get(f"/info.geojson?url={DATA_DIR}/item.json&assets=B01")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    assert response.json()["type"] == "Feature"

    response = client.get(f"/metadata?url={DATA_DIR}/item.json&assets=B01&bidx=1")
    assert response.status_code == 200
    assert response.json()["B01"]["statistics"]["1"]

    response = client.get(
        f"/preview.tif?url={DATA_DIR}/item.json&assets=B01&bidx=1,1,1&return_mask=false"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff; application=geotiff"
    meta = parse_img(response.content)
    assert meta["dtype"] == "uint16"
    assert meta["count"] == 3

    response = client.get(f"/preview.tif?url={DATA_DIR}/item.json")
    assert response.status_code == 400

    response = client.get(
        f"/preview.tif?url={DATA_DIR}/item.json&expression=B01,B01,B01&return_mask=false"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff; application=geotiff"
    meta = parse_img(response.content)
    assert meta["dtype"] == "int32"
    assert meta["count"] == 3


@attr.s
class BandFileReader(MultiBandReader):
    """Test MultiBand"""

    path: str = attr.ib()
    reader: Type[BaseReader] = attr.ib(default=COGReader)
    reader_options: Dict = attr.ib(factory=dict)
    tms: morecantile.TileMatrixSet = attr.ib(
        default=morecantile.tms.get("WebMercatorQuad")
    )

    def __attrs_post_init__(self):
        """Parse Sceneid and get grid bounds."""
        self.bands = sorted([p.stem for p in pathlib.Path(self.path).glob("B0*.tif")])
        with self.reader(self._get_band_url(self.bands[0])) as cog:
            self.bounds = cog.bounds
            self.minzoom = cog.minzoom
            self.maxzoom = cog.maxzoom

    def _get_band_url(self, band: str) -> str:
        """Validate band's name and return band's url."""
        return os.path.join(self.path, f"{band}.tif")


def test_MultiBandTilerFactory():
    """test MultiBandTilerFactory."""

    bands = MultiBandTilerFactory(reader=BandFileReader)
    assert len(bands.router.routes) == 22

    app = FastAPI()
    app.include_router(bands.router)

    add_exception_handlers(app, DEFAULT_STATUS_CODES)

    client = TestClient(app)

    response = client.get(f"/bands?url={DATA_DIR}")
    assert response.status_code == 200
    assert response.json() == ["B01", "B09"]

    response = client.get(f"/info?url={DATA_DIR}&bands=B01")
    assert response.status_code == 200
    assert response.json()["band_metadata"] == [["B01", {}]]

    response = client.get(f"/info.geojson?url={DATA_DIR}&bands=B01")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"

    response = client.get(f"/metadata?url={DATA_DIR}&bands=B01&bidx=1")
    assert response.status_code == 200
    assert response.json()["statistics"]["B01"]

    response = client.get(f"/preview.tif?url={DATA_DIR}&return_mask=false")
    assert response.status_code == 400

    response = client.get(
        f"/preview.tif?url={DATA_DIR}&bands=B01,B09,B01&return_mask=false"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff; application=geotiff"
    meta = parse_img(response.content)
    assert meta["dtype"] == "uint16"
    assert meta["count"] == 3

    response = client.get(
        f"/preview.tif?url={DATA_DIR}&expression=B01,B09,B01&return_mask=false"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff; application=geotiff"
    meta = parse_img(response.content)
    assert meta["dtype"] == "int32"
    assert meta["count"] == 3


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
    assert len(body["tileMatrixSets"]) == 10  # morecantile has 10 defaults
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
