"""Test TiTiler wms extension."""

import os

from titiler.core.factory import TilerFactory
from titiler.extensions import wmsExtension

from fastapi import FastAPI

from starlette.testclient import TestClient

cog = os.path.join(os.path.dirname(__file__), "fixtures", "cog.tif")


def test_wmsExtension():
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
