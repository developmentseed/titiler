"""Test TiTiler cogeo extension."""

import os

from fastapi import FastAPI
from starlette.testclient import TestClient

from titiler.core.factory import TilerFactory
from titiler.extensions import cogValidateExtension

cog = os.path.join(os.path.dirname(__file__), "fixtures", "cog.tif")


def test_cogValidateExtension():
    """Test cogValidateExtension class."""
    tiler = TilerFactory()
    tiler_plus_cog = TilerFactory(extensions=[cogValidateExtension()])
    # Check that we added one route (/validate)
    assert len(tiler_plus_cog.router.routes) == len(tiler.router.routes) + 1

    app = FastAPI()
    app.include_router(tiler_plus_cog.router)
    with TestClient(app) as client:
        response = client.get("/validate", params={"url": cog})
        assert response.status_code == 200
        body = response.json()
        assert body["COG"]
