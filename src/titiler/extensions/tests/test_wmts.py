"""test WMTS extension."""

import io
import os

import rasterio
from fastapi import FastAPI
from owslib.wmts import WebMapTileService
from starlette.testclient import TestClient

from titiler.core.factory import TilerFactory
from titiler.extensions import wmtsExtension

from .conftest import parse_img

DATA_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def test_wmtsExtension():
    """Test wmtsExtension class."""
    tiler = TilerFactory()
    tiler_plus_wmts = TilerFactory(extensions=[wmtsExtension()])
    assert len(tiler_plus_wmts.router.routes) == len(tiler.router.routes) + 1

    app = FastAPI()
    app.include_router(tiler_plus_wmts.router)
    with TestClient(app) as client:
        response = client.get(f"/WMTSCapabilities.xml?url={DATA_DIR}/cog.tif")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/xml"
        meta = parse_img(response.content)
        assert meta["driver"] == "WMTS"

        wmts = WebMapTileService(
            f"/WMTSCapabilities.xml?url={DATA_DIR}/cog.tif", xml=response.content
        )
        assert wmts.version == "1.0.0"
        assert len(wmts.contents) == 13  # 1 render x 13 TMS
        assert f"{DATA_DIR}/cog.tif_WebMercatorQuad_default" in wmts.contents
        assert f"{DATA_DIR}/cog.tif_WorldCRS84Quad_default" in wmts.contents

        layer = wmts.contents[f"{DATA_DIR}/cog.tif_WebMercatorQuad_default"]
        assert ["5", "6", "7", "8", "9"] == list(
            layer.tilematrixsetlinks["WebMercatorQuad"].tilematrixlimits
        )

        assert "WebMercatorQuad" in wmts.tilematrixsets
        assert "WorldCRS84Quad" in wmts.tilematrixsets

        assert wmts.provider.name == "TiTiler"
        assert wmts.provider.url == "https://developmentseed.org/titiler/"

        # Validate it's a good WMTS
        with rasterio.open(io.BytesIO(response.content)) as src:
            assert not src.crs
            assert src.profile["driver"] == "WMTS"
            assert len(src.subdatasets) == 13
            sds_names = [s.split(",layer=")[1] for s in src.subdatasets]
            assert f"{DATA_DIR}/cog.tif_WebMercatorQuad_default" in sds_names

        with rasterio.open(
            io.BytesIO(response.content),
            layer=f"{DATA_DIR}/cog.tif_WebMercatorQuad_default",
        ) as sds:
            assert sds.crs == "epsg:3857"


def test_wmtsExtension_with_renders():
    """Test wmtsExtension class with Renders."""
    tiler_plus_wmts = TilerFactory(
        extensions=[
            wmtsExtension(
                get_renders=lambda obj: {
                    "one_band_limit": {
                        "tilematrixsets": {
                            "WebMercatorQuad": [0, 1],
                        },
                        "spatial_extent": (-180, -90, 180, 90),
                        "bidx": [1, 2, 3],
                        "rescale": [[0, 10000], [0, 5000], [0, 1000]],
                    },
                    "one_band": {
                        "bidx": [1],
                        "rescale": ["0,10000"],
                    },
                },
            )
        ],
    )

    app = FastAPI()
    app.include_router(tiler_plus_wmts.router)
    with TestClient(app) as client:
        response = client.get(f"/WMTSCapabilities.xml?url={DATA_DIR}/cog.tif")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/xml"
        meta = parse_img(response.content)
        assert meta["driver"] == "WMTS"

        wmts = WebMapTileService(
            f"/WMTSCapabilities.xml?url={DATA_DIR}/cog.tif", xml=response.content
        )
        assert wmts.version == "1.0.0"
        assert len(wmts.contents) == 39  # (2 renders + default) x 13 TMS

        assert f"{DATA_DIR}/cog.tif_WebMercatorQuad_default" in wmts.contents
        assert f"{DATA_DIR}/cog.tif_WorldCRS84Quad_default" in wmts.contents

        layer = wmts.contents[f"{DATA_DIR}/cog.tif_WebMercatorQuad_default"]
        assert ["5", "6", "7", "8", "9"] == list(
            layer.tilematrixsetlinks["WebMercatorQuad"].tilematrixlimits
        )

        assert f"{DATA_DIR}/cog.tif_WebMercatorQuad_one_band_limit" in wmts.contents
        assert f"{DATA_DIR}/cog.tif_WorldCRS84Quad_one_band_limit" in wmts.contents

        layer = wmts.contents[f"{DATA_DIR}/cog.tif_WebMercatorQuad_one_band_limit"]
        assert ["0", "1"] == list(
            layer.tilematrixsetlinks["WebMercatorQuad"].tilematrixlimits
        )
        assert (
            layer.tilematrixsetlinks["WebMercatorQuad"].tilematrixlimits["0"].mintilerow
            == 0
        )

        assert f"{DATA_DIR}/cog.tif_WebMercatorQuad_one_band" in wmts.contents
        assert f"{DATA_DIR}/cog.tif_WorldCRS84Quad_one_band" in wmts.contents

        assert "WebMercatorQuad" in wmts.tilematrixsets
        assert "WorldCRS84Quad" in wmts.tilematrixsets

        assert wmts.provider.name == "TiTiler"
        assert wmts.provider.url == "https://developmentseed.org/titiler/"
