"""Test OGC Maps Extension."""

from fastapi import FastAPI
from starlette.testclient import TestClient

from titiler.core.factory import TilerFactory
from titiler.extensions.ogcmaps import OGCMapsExtension


def test_ogcmaps_extension():
    """Test OGCMapsExtension."""
    app = FastAPI()
    cog = TilerFactory(extensions=[OGCMapsExtension()])
    app.include_router(cog.router)
    client = TestClient(app)

    response = client.get("/maps")
    assert response.status_code == 200
    resp = response.json()
    assert len(resp["maps"]) == 1
    assert resp["maps"][0]["id"] == "default"

    map_id = resp["maps"][0]["id"]
    response = client.get(f"/maps/{map_id}")
    assert response.status_code == 200
    resp = response.json()
    assert resp["id"] == map_id
    assert "links" in resp

    response = client.get(f"/maps/{map_id}/styles")
    assert response.status_code == 200
    resp = response.json()
    assert len(resp) == 1
    assert resp[0]["id"] == "default"

    response = client.get(
        f"/maps/{map_id}/map?url={DATA_DIR}/cog.tif"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png" 