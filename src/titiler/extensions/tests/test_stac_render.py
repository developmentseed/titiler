"""Test STAC Render extension."""

import os
from urllib.parse import unquote, urlparse

from fastapi import FastAPI
from fastapi.testclient import TestClient
from rio_tiler.io import STACReader

from titiler.core.factory import MultiBaseTilerFactory
from titiler.extensions.render import stacRenderExtension
from titiler.extensions.wmts import wmtsExtension

stac_item = os.path.join(os.path.dirname(__file__), "fixtures", "render_item.json")


def test_stacExtension():
    """Test stacExtension class."""

    stac_tiler = MultiBaseTilerFactory(reader=STACReader)

    stac_tiler_plus_stac_render = MultiBaseTilerFactory(
        reader=STACReader, extensions=[stacRenderExtension(), wmtsExtension()]
    )
    # Check that we added two routes (/renders & /renders/{render_id}) and `/WMTSCapabilities.xml`
    assert (
        len(stac_tiler_plus_stac_render.router.routes)
        == len(stac_tiler.router.routes) + 3
    )

    app = FastAPI()
    app.include_router(stac_tiler_plus_stac_render.router)
    with TestClient(app) as client:
        response = client.get("/renders", params={"url": stac_item})
        assert response.status_code == 200
        body = response.json()
        assert body["renders"]
        assert body["links"]

        self_link = body["links"][0]
        assert self_link["href"] == response.url
        assert self_link["rel"] == "self"

        assert "ndvi" in body["renders"]
        assert "thumbnail" in body["renders"]

        expected_params = {
            "title": "Normalized Difference Vegetation Index",
            "assets": ["ndvi"],
            "resampling": "average",
            "colormap_name": "ylgn",
            "extra_param": "that titiler does not know",
        }
        assert body["renders"]["ndvi"]["params"] == expected_params

        links = body["renders"]["ndvi"]["links"]
        assert len(links) == 3

        hrefs = {unquote(urlparse(link["href"]).path) for link in links}
        expected_hrefs = {
            "/renders/ndvi",
            "/WMTSCapabilities.xml",
            "/{tileMatrixSetId}/tilejson.json",
        }
        assert hrefs == expected_hrefs

        response = client.get("/renders/unknown", params={"url": stac_item})
        assert response.status_code == 404
        body = response.json()
        assert body == {"detail": "Render not found"}

        response = client.get("/renders/ndvi", params={"url": stac_item})
        assert response.status_code == 200
        body = response.json()
        assert body["params"]
        assert body["links"]
        hrefs = {unquote(urlparse(link["href"]).path) for link in links}
        assert hrefs == expected_hrefs
        assert body["params"] == expected_params
