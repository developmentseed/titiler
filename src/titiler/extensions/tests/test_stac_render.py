"""Test STAC Render extension."""

import os
from typing import Annotated
from urllib.parse import unquote, urlparse

from fastapi import FastAPI, Path, Request
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
        reader=STACReader,
        extensions=[stacRenderExtension(), wmtsExtension()],
        get_renders=lambda obj: obj.item.properties.get("renders", {}),
    )
    # Check that we added two routes (/renders & /renders/{render_id}) and `/WMTSCapabilities.xml`
    assert (
        len(stac_tiler_plus_stac_render.router.routes)
        == len(stac_tiler.router.routes) + 3
    )

    app = FastAPI()
    app.include_router(stac_tiler_plus_stac_render.router)
    with TestClient(app, base_url="http://testserver") as client:
        response = client.get("/renders", params={"url": stac_item})
        assert response.status_code == 200
        body = response.json()
        assert body["renders"]
        assert body["links"]
        self_link = next(link for link in body["links"] if link["rel"] == "self")
        link_url = self_link["href"].replace("http://testserver", "")
        r = client.get(link_url)
        assert r.status_code == 200

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

        self_link = next(link for link in body["links"] if link["rel"] == "self")
        link_url = self_link["href"].replace("http://testserver", "")
        r = client.get(link_url)
        assert r.status_code == 200

        response = client.get("/renders/rgb_old", params={"url": stac_item})
        assert response.status_code == 200
        body = response.json()
        assert body["valid"]
        assert body["params"] == {
            "title": "Thumbnail",
            "assets": ["B4|bidx=1", "B3|bidx=1", "B2|bidx=1"],
        }

        response = client.get("/renders/expression_old", params={"url": stac_item})
        assert response.status_code == 200
        body = response.json()
        assert body["valid"]
        assert body["params"] == {
            "title": "expression",
            "assets": ["B02|expression=b1*2"],
        }

        response = client.get("/renders/missing_asset", params={"url": stac_item})
        assert response.status_code == 200
        body = response.json()
        assert not body["valid"]
        assert body["params"] == {"title": "bad_expression", "expression": "b1*2"}


def test_stacExtension_path_params():
    """Test stacExtension class."""

    def FakePathParam(
        request: Request,
        collection_id: Annotated[
            str,
            Path(description="STAC Collection Identifier"),
        ],
        item_id: Annotated[str, Path(description="STAC Item Identifier")],
    ) -> str:
        """Fake path parameter that returns the STAC item URL."""
        return stac_item

    stac_tiler_plus_stac_render = MultiBaseTilerFactory(
        reader=STACReader,
        path_dependency=FakePathParam,
        router_prefix="/collections/{collection_id}/items/{item_id}",
        extensions=[stacRenderExtension(), wmtsExtension()],
        get_renders=lambda obj: obj.item.properties.get("renders", {}),
    )

    app = FastAPI()
    app.include_router(
        stac_tiler_plus_stac_render.router,
        prefix="/collections/{collection_id}/items/{item_id}",
    )
    with TestClient(app, base_url="http://testserver") as client:
        response = client.get(
            "/collections/fake/items/item/renders", params={"url": stac_item}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["renders"]
        assert body["links"]
        self_link = next(link for link in body["links"] if link["rel"] == "self")
        link_url = self_link["href"].replace("http://testserver", "")
        r = client.get(link_url)
        assert r.status_code == 200

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
            "/collections/fake/items/item/renders/ndvi",
            "/collections/fake/items/item/WMTSCapabilities.xml",
            "/collections/fake/items/item/{tileMatrixSetId}/tilejson.json",
        }
        assert hrefs == expected_hrefs

        response = client.get(
            "/collections/fake/items/item/renders/unknown", params={"url": stac_item}
        )
        assert response.status_code == 404
        body = response.json()
        assert body == {"detail": "Render not found"}

        response = client.get(
            "/collections/fake/items/item/renders/ndvi", params={"url": stac_item}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["params"]
        assert body["links"]
        hrefs = {unquote(urlparse(link["href"]).path) for link in links}
        assert hrefs == expected_hrefs
        assert body["params"] == expected_params

        self_link = next(link for link in body["links"] if link["rel"] == "self")
        link_url = self_link["href"].replace("http://testserver", "")
        r = client.get(link_url)
        assert r.status_code == 200

        response = client.get(
            "/collections/fake/items/item/renders/rgb_old", params={"url": stac_item}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["valid"]
        assert body["params"] == {
            "title": "Thumbnail",
            "assets": ["B4|bidx=1", "B3|bidx=1", "B2|bidx=1"],
        }

        response = client.get(
            "/collections/fake/items/item/renders/expression_old",
            params={"url": stac_item},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["valid"]
        assert body["params"] == {
            "title": "expression",
            "assets": ["B02|expression=b1*2"],
        }

        response = client.get(
            "/collections/fake/items/item/renders/missing_asset",
            params={"url": stac_item},
        )
        assert response.status_code == 200
        body = response.json()
        assert not body["valid"]
        assert body["params"] == {"title": "bad_expression", "expression": "b1*2"}
