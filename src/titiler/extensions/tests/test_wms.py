"""Test TiTiler wms extension."""

import os
import xml.etree.ElementTree as ET

from fastapi import FastAPI
from rasterio.crs import CRS
from starlette.testclient import TestClient

from titiler.core.factory import TilerFactory
from titiler.extensions import wmsExtension

from .conftest import parse_img

cog = os.path.join(os.path.dirname(__file__), "fixtures", "cog.tif")
cog1 = os.path.join(os.path.dirname(__file__), "fixtures", "cog1.tif")
cog2 = os.path.join(os.path.dirname(__file__), "fixtures", "cog2.tif")


def test_wmsExtension_GetCapabilities():
    """Test wmsValidateExtension class."""
    tiler = TilerFactory()
    tiler_plus_wms = TilerFactory(extensions=[wmsExtension()])
    # Check that we added one route (/validate)
    assert len(tiler_plus_wms.router.routes) == len(tiler.router.routes) + 1

    app = FastAPI()
    app.include_router(tiler_plus_wms.router)
    with TestClient(app) as client:
        response = client.get(
            "/wms",
            params={"REQUEST": "GetCapabilities", "SERVICE": "wms", "LAYERS": cog},
        )
        assert response.status_code == 200

        response = client.get(
            "/wms",
            params={"REQUEST": "GetFeatureInfo", "SERVICE": "wms", "LAYERS": cog},
        )
        assert response.status_code == 400

        response = client.get(
            "/wms",
            params={"REQUEST": "GetSomething", "SERVICE": "wms", "LAYERS": cog},
        )
        assert response.status_code == 400

        response = client.get(
            "/wms",
            params={"request": "GetCapabilities", "service": "wms", "LAYERS": cog},
        )
        assert response.status_code == 200

        response = client.get("/wms")
        assert response.status_code == 400
        assert "Missing WMS 'REQUEST' parameter" in response.json()["detail"]

        response = client.get("/wms", params={"request": "GetCapabilities"})
        assert response.status_code == 400
        assert "Missing WMS 'LAYERS' parameter" in response.json()["detail"]

        response = client.get(
            "/wms", params={"request": "GetCapabilities", "LAYERS": cog}
        )
        assert response.status_code == 400
        assert (
            "Missing 'GetCapabilities' parameters: {'service'}"
            in response.json()["detail"]
        )

        response = client.get(
            "/wms",
            params={"request": "GetCapabilities", "service": "wms", "LAYERS": ""},
        )
        assert response.status_code == 400
        assert "Invalid 'LAYERS' parameter: " in response.json()["detail"]

        response = client.get(
            "/wms",
            params={
                "request": "GetCapabilities",
                "service": "somethingelse",
                "LAYERS": cog,
            },
        )
        assert response.status_code == 400
        assert "Invalid 'SERVICE' parameter: somethingelse" in response.json()["detail"]

        response = client.get(
            "/wms",
            params={"REQUEST": "GetCapabilities", "SERVICE": "wms", "LAYERS": cog},
        )
        assert response.status_code == 200
        assert 'Capabilities version="1.3.0">' in response.text

        response = client.get(
            "/wms",
            params={
                "REQUEST": "GetCapabilities",
                "SERVICE": "wms",
                "LAYERS": cog,
                "version": "1.1.1",
            },
        )
        assert response.status_code == 200
        assert 'Capabilities version="1.1.1">' in response.text

        response = client.get(
            "/wms",
            params={
                "REQUEST": "GetCapabilities",
                "SERVICE": "wms",
                "LAYERS": cog,
                "version": "1.0.0",
            },
        )
        assert response.status_code == 200
        assert 'Capabilities version="1.0.0">' in response.text

        response = client.get(
            "/wms",
            params={
                "REQUEST": "GetCapabilities",
                "SERVICE": "wms",
                "LAYERS": cog,
                "version": "4.0.0",
            },
        )
        assert response.status_code == 400
        assert "Invalid 'VERSION' parameter: 4.0.0" in response.json()["detail"]

        response = client.get(
            "/wms",
            params={
                "request": "GetCapabilities",
                "service": "wms",
                "LAYERS": cog,
                "rescale": "0,1000",
            },
        )
        assert response.status_code == 200
        assert "rescale=0%2C1000" in response.text

        response = client.get(
            "/wms",
            params={
                "REQUEST": "GetCapabilities",
                "SERVICE": "wms",
                "LAYERS": f"{cog1},{cog2}",
            },
        )
        assert response.status_code == 200
        root = ET.fromstring(response.text)
        assert len(root.find("Capability").find("Layer").findall("Layer")) == 2
        assert cog1 in response.text
        assert cog2 in response.text


def test_wmsExtension_GetMap():
    """Test wmsValidateExtension class."""
    tiler_plus_wms = TilerFactory(extensions=[wmsExtension()])

    app = FastAPI()
    app.include_router(tiler_plus_wms.router)
    with TestClient(app) as client:
        response = client.get(
            "/wms",
            params={
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": cog,
            },
        )
        assert response.status_code == 400
        assert "Missing 'GetMap' parameters: " in response.text

        response = client.get(
            "/wms",
            params={
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": cog,
                "BBOX": "373185.0,8019284.949381611,639014.9492102272,8286015.0",
                "CRS": "EPSG:32621",
                "WIDTH": 334,
                "HEIGHT": 333,
                "FORMAT": "image/png",
                "TRANSPARENT": False,
            },
        )
        assert response.status_code == 200
        meta = parse_img(response.content)
        assert meta["driver"] == "PNG"
        assert meta["width"] == 334
        assert meta["height"] == 333
        assert meta["count"] == 1

        response = client.get(
            "/wms",
            params={
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": cog,
                "BBOX": "373185.0,8019284.949381611,639014.9492102272,8286015.0",
                "CRS": "EPSG:32621",
                "WIDTH": 334,
                "HEIGHT": 333,
                "FORMAT": "image/png",
                "TRANSPARENT": True,
            },
        )
        assert response.status_code == 200
        meta = parse_img(response.content)
        assert meta["driver"] == "PNG"
        assert meta["width"] == 334
        assert meta["height"] == 333
        assert meta["count"] == 2

        response = client.get(
            "/wms",
            params={
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": cog,
                "BBOX": "373185.0,8019284.949381611,639014.9492102272,8286015.0",
                "SRS": "EPSG:32621",
                "WIDTH": 334,
                "HEIGHT": 333,
                "FORMAT": "image/tiff; application=geotiff",
            },
        )
        assert response.status_code == 200
        meta = parse_img(response.content)
        assert meta["crs"] == CRS.from_epsg(32621)

        response = client.get(
            "/wms",
            params={
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": cog,
                "BBOX": "373185.0,8019284.949381611,639014.9492102272,8286015.0",
                "CRS": "EPSG:32621",
                "WIDTH": 334,
                "HEIGHT": 333,
                "FORMAT": "image/tiff; application=geotiff",
            },
        )
        assert response.status_code == 200
        meta = parse_img(response.content)
        assert meta["driver"] == "GTiff"
        assert meta["width"] == 334
        assert meta["height"] == 333
        assert meta["crs"] == CRS.from_epsg(32621)

        response = client.get(
            "/wms",
            params={
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": cog,
                "BBOX": "373185.0,8019284.949381611,639014.9492102272,8286015.0",
                "CRS": "",
                "WIDTH": 334,
                "HEIGHT": 333,
                "FORMAT": "image/png",
                "TRANSPARENT": True,
            },
        )
        assert response.status_code == 400
        assert "Invalid 'CRS' parameter" in response.text

        response = client.get(
            "/wms",
            params={
                "VERSION": "1.3.1",
                "REQUEST": "GetMap",
                "LAYERS": cog,
                "BBOX": "373185.0,8019284.949381611,639014.9492102272,8286015.0",
                "CRS": "EPSG:32621",
                "WIDTH": 334,
                "HEIGHT": 333,
                "FORMAT": "image/png",
            },
        )
        assert response.status_code == 400
        assert "Invalid 'VERSION' parameter" in response.text

        response = client.get(
            "/wms",
            params={
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": cog,
                "BBOX": "373185.0,8019284.949381611,639014.9492102272,8286015.0",
                "WIDTH": 334,
                "HEIGHT": 333,
                "FORMAT": "image/png",
            },
        )
        assert response.status_code == 400
        assert "Missing 'CRS' or 'SRS parameters." in response.text

        response = client.get(
            "/wms",
            params={
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": cog,
                "BBOX": "373185.0,373185.0,8019284.949381611,639014.9492102272,8286015.0",
                "CRS": "EPSG:32621",
                "WIDTH": 334,
                "HEIGHT": 333,
                "FORMAT": "image/png",
            },
        )
        assert response.status_code == 400
        assert "Invalid 'BBOX' parameters" in response.text

        # 1.3.0 needs inverted X,Y coordinates for EPSG:4326
        response = client.get(
            "/wms",
            params={
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": cog,
                "BBOX": "72.22979795551834,-61.28762442711404,74.66298001264106,-52.301598718454485",
                "CRS": "EPSG:4326",
                "WIDTH": 334,
                "HEIGHT": 333,
                "FORMAT": "image/tiff; application=geotiff",
            },
        )
        assert response.status_code == 200
        meta = parse_img(response.content)
        assert meta["crs"] == CRS.from_epsg(4326)
        assert meta["bounds"] == [
            -61.28762442711404,
            72.22979795551834,
            -52.301598718454485,
            74.66298001264106,
        ]

        response = client.get(
            "/wms",
            params={
                "VERSION": "1.1.1",
                "REQUEST": "GetMap",
                "LAYERS": cog,
                "BBOX": "-61.28762442711404,72.22979795551834,-52.301598718454485,74.66298001264106",
                "CRS": "EPSG:4326",
                "WIDTH": 334,
                "HEIGHT": 333,
                "FORMAT": "image/tiff; application=geotiff",
            },
        )
        assert response.status_code == 200
        meta = parse_img(response.content)
        assert meta["crs"] == CRS.from_epsg(4326)
        assert meta["bounds"] == [
            -61.28762442711404,
            72.22979795551834,
            -52.301598718454485,
            74.66298001264106,
        ]

        response = client.get(
            "/wms",
            params={
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": cog,
                "BBOX": "-61.28762442711404,72.22979795551834,-52.301598718454485,74.66298001264106",
                "CRS": "CRS:84",
                "WIDTH": 334,
                "HEIGHT": 333,
                "FORMAT": "image/tiff; application=geotiff",
            },
        )
        assert response.status_code == 200
        meta = parse_img(response.content)
        assert meta["crs"] == CRS.from_epsg(4326)
        assert meta["bounds"] == [
            -61.28762442711404,
            72.22979795551834,
            -52.301598718454485,
            74.66298001264106,
        ]


def test_wmsExtension_GetFeatureInfo():
    """Test wmsValidateExtension class for GetFeatureInfo request."""
    tiler_plus_wms = TilerFactory(extensions=[wmsExtension()])

    app = FastAPI()
    app.include_router(tiler_plus_wms.router)

    with TestClient(app) as client:
        # Setup the basic GetFeatureInfo request
        params = {
            "VERSION": "1.3.0",
            "REQUEST": "GetFeatureInfo",
            "LAYERS": cog,
            "QUERY_LAYERS": cog,
            "BBOX": "500975.102,8182890.453,501830.647,8183959.884",
            "CRS": "EPSG:32621",
            "WIDTH": 334,
            "HEIGHT": 333,
            "INFO_FORMAT": "text/html",
            "I": "0",
            "J": "0",
        }

        response = client.get("/wms", params=params)

        assert response.status_code == 200
        assert response.content == b"2800"

        params = {
            "VERSION": "1.3.0",
            "REQUEST": "GetFeatureInfo",
            "LAYERS": cog,
            "QUERY_LAYERS": cog,
            "BBOX": "500975.102,8182890.453,501830.647,8183959.884",
            "CRS": "EPSG:32621",
            "WIDTH": 334,
            "HEIGHT": 333,
            "INFO_FORMAT": "text/html",
            "I": "333",
            "J": "332",
        }

        response = client.get("/wms", params=params)

        assert response.status_code == 200
        assert response.content == b"3776"

        # Add additional assertions to check the text response
