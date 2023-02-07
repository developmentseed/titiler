"""Test TiTiler stac extension."""

import os

import pystac
from fastapi import FastAPI
from starlette.testclient import TestClient

from titiler.core.factory import TilerFactory
from titiler.extensions import stacExtension

cog = os.path.join(os.path.dirname(__file__), "fixtures", "cog.tif")


def test_stacExtension():
    """Test stacExtension class."""
    tiler = TilerFactory()
    tiler_plus_stac = TilerFactory(extensions=[stacExtension()])
    # Check that we added one route (/stac)
    assert len(tiler_plus_stac.router.routes) == len(tiler.router.routes) + 1

    app = FastAPI()
    app.include_router(tiler_plus_stac.router)
    with TestClient(app) as client:
        response = client.get("/stac", params={"url": cog})
        assert response.status_code == 200
        body = response.json()
        assert pystac.Item.from_dict(body).validate()
        assert body["id"] == "cog.tif"
        assert body["assets"]["data"]["type"] == "image/tiff; application=geotiff"

        response = client.get("/stac", params={"url": cog, "id": "cog"})
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == "cog"
        assert pystac.Item.from_dict(body).validate()

        response = client.get("/stac", params={"url": cog, "datetime": "2010-01-01"})
        assert response.status_code == 200
        body = response.json()
        assert body["properties"]["datetime"] == "2010-01-01T00:00:00Z"
        assert pystac.Item.from_dict(body).validate()

        response = client.get(
            "/stac", params={"url": cog, "datetime": "2010-01-01/2010-01-02"}
        )
        assert response.status_code == 200
        body = response.json()
        assert "datetime" in body["properties"]
        assert not body["properties"]["datetime"]
        assert body["properties"]["start_datetime"] == "2010-01-01T00:00:00Z"
        assert body["properties"]["end_datetime"] == "2010-01-02T00:00:00Z"
        assert pystac.Item.from_dict(body).validate()

        response = client.get(
            "/stac",
            params={
                "url": cog,
                "asset_media_type": "image/tiff; application=geotiff; profile=cloud-optimized",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert (
            body["assets"]["data"]["type"]
            == "image/tiff; application=geotiff; profile=cloud-optimized"
        )
        assert pystac.Item.from_dict(body).validate()
