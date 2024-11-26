"""Test STAC Render extension."""
import os
from urllib.parse import urlencode

from fastapi import FastAPI
from fastapi.testclient import TestClient
from rio_tiler.io import STACReader

from titiler.core.factory import MultiBaseTilerFactory
from titiler.extensions.render import stacRenderExtension

stac_item = os.path.join(os.path.dirname(__file__), "fixtures", "render_item.json")


def test_stacExtension():
    """Test stacExtension class."""

    stac_tiler = MultiBaseTilerFactory(reader=STACReader)

    stac_tiler_plus_stac_render = MultiBaseTilerFactory(
        reader=STACReader, extensions=[stacRenderExtension()]
    )
    # Check that we added two routes (/renders & /renders/{render_id})
    assert (
        len(stac_tiler_plus_stac_render.router.routes)
        == len(stac_tiler.router.routes) + 2
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
            "assets": ["ndvi"],
            "colormap_name": "ylgn",
            "resampling": "average",
            "title": "Normalized Difference Vegetation Index",
        }
        assert body["renders"]["ndvi"]["params"] == expected_params

        links = body["renders"]["ndvi"]["links"]
        assert len(links) == 3

        stac_item_param = urlencode({"url": stac_item})
        hrefs = {link["href"] for link in links}
        expected_hrefs = {
            f"http://testserver/renders/ndvi?{stac_item_param}",
            f"http://testserver/{{tileMatrixSetId}}/WMTSCapabilities.xml?{stac_item_param}&assets=ndvi&resampling_method=average&colormap_name=ylgn",
            f"http://testserver/{{tileMatrixSetId}}/tilejson.json?{stac_item_param}&assets=ndvi&resampling_method=average&colormap_name=ylgn",
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
        hrefs = {link["href"] for link in links}
        assert hrefs == expected_hrefs
        assert body["params"] == expected_params
