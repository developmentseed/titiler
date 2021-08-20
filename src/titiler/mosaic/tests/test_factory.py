"""Test TiTiler mosaic Factory."""

import os
import tempfile
from contextlib import contextmanager

from cogeo_mosaic.backends import FileBackend
from cogeo_mosaic.errors import NoAssetFoundError
from cogeo_mosaic.mosaic import MosaicJSON
from pytest import raises

from titiler.core.dependencies import WebMercatorTMSParams
from titiler.core.resources.enums import OptionalHeader
from titiler.mosaic.factory import MosaicTilerFactory
from titiler.mosaic.settings import mosaic_config

from .conftest import DATA_DIR

from fastapi import FastAPI

from starlette.testclient import TestClient

assets = [os.path.join(DATA_DIR, asset) for asset in ["cog1.tif", "cog2.tif"]]


@contextmanager
def tmpmosaic():
    """Create a Temporary MosaicJSON file."""
    fileobj = tempfile.NamedTemporaryFile(suffix=".json.gz", delete=False)
    fileobj.close()
    mosaic_def = MosaicJSON.from_urls(assets)
    with FileBackend(fileobj.name, mosaic_def=mosaic_def) as mosaic:
        mosaic.write(overwrite=True)

    try:
        yield fileobj.name
    finally:
        os.remove(fileobj.name)


def test_MosaicTilerFactory():
    """Test MosaicTilerFactory class."""
    mosaic = MosaicTilerFactory(
        optional_headers=[OptionalHeader.server_timing, OptionalHeader.x_assets],
        router_prefix="mosaic",
    )
    assert len(mosaic.router.routes) == 33
    assert mosaic.tms_dependency == WebMercatorTMSParams

    app = FastAPI()
    app.include_router(mosaic.router, prefix="/mosaic")
    client = TestClient(app)

    with tmpmosaic() as mosaic_file:
        response = client.get("/mosaic/", params={"url": mosaic_file},)
        assert response.status_code == 200
        assert response.json()["mosaicjson"]

        response = client.get("/mosaic", params={"url": mosaic_file},)
        assert response.status_code == 200
        assert response.json()["mosaicjson"]

        response = client.get("/mosaic/bounds", params={"url": mosaic_file},)
        assert response.status_code == 200
        assert response.json()["bounds"]

        response = client.get("/mosaic/info", params={"url": mosaic_file},)
        assert response.status_code == 200
        assert response.json()["bounds"]

        response = client.get("/mosaic/info.geojson", params={"url": mosaic_file},)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/geo+json"
        assert response.json()["type"] == "Feature"

        response = client.get(
            "/mosaic/point/-74.53125,45.9956935", params={"url": mosaic_file},
        )
        assert response.status_code == 200
        timing = response.headers["server-timing"]
        assert "mosaicread;dur" in timing
        assert "dataread;dur" in timing

        response = client.get("/mosaic/tiles/7/37/45", params={"url": mosaic_file})
        assert response.status_code == 200

        assert response.headers["X-Assets"]
        timing = response.headers["server-timing"]
        assert "mosaicread;dur" in timing
        assert "dataread;dur" in timing
        assert "postprocess;dur" in timing
        assert "format;dur" in timing

        response = client.get(
            "/mosaic/tilejson.json",
            params={
                "url": mosaic_file,
                "tile_format": "png",
                "minzoom": 6,
                "maxzoom": 9,
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert (
            "http://testserver/mosaic/tiles/WebMercatorQuad/{z}/{x}/{y}@1x.png?url="
            in body["tiles"][0]
        )
        assert body["minzoom"] == 6
        assert body["maxzoom"] == 9

        response = client.get(
            "/mosaic/tilejson.json",
            params={
                "url": mosaic_file,
                "tile_format": "png",
                "minzoom": 6,
                "maxzoom": 9,
                "TileMatrixSetId": "WebMercatorQuad",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert (
            "http://testserver/mosaic/tiles/WebMercatorQuad/{z}/{x}/{y}@1x.png?url="
            in body["tiles"][0]
        )
        assert body["minzoom"] == 6
        assert body["maxzoom"] == 9
        assert "TileMatrixSetId" not in body["tiles"][0]

        response = client.get(
            "/mosaic/WMTSCapabilities.xml",
            params={
                "url": mosaic_file,
                "tile_format": "png",
                "minzoom": 6,
                "maxzoom": 9,
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/xml"

        response = client.post(
            "/mosaic/validate", json=MosaicJSON.from_urls(assets).dict(),
        )
        assert response.status_code == 200

        response = client.get("/mosaic/7/36/45/assets", params={"url": mosaic_file},)
        assert response.status_code == 200
        assert all(
            filepath.split("/")[-1] in ["cog1.tif"] for filepath in response.json()
        )

        response = client.get("/mosaic/-71,46/assets", params={"url": mosaic_file})
        assert response.status_code == 200
        assert all(
            filepath.split("/")[-1] in ["cog1.tif", "cog2.tif"]
            for filepath in response.json()
        )

        response = client.get(
            "/mosaic/-75.9375,43.06888777416962,-73.125,45.089035564831015/assets",
            params={"url": mosaic_file},
        )
        assert response.status_code == 200
        assert all(
            filepath.split("/")[-1] in ["cog1.tif", "cog2.tif"]
            for filepath in response.json()
        )

        response = client.get(
            "/mosaic/10,10,11,11/assets", params={"url": mosaic_file},
        )
        assert response.status_code == 200
        assert response.json() == []


root = "http://testserver/mosaic"


def _get_link_by_rel(response_body: dict, rel: str) -> str:
    return next((x["href"] for x in response_body["links"] if x["rel"] == rel), "")


def test_mosaics_basic(set_env, client):
    """Test mosaicjson functionality."""

    # Create a new MosaicJSON
    mosaicjson_data = MosaicJSON.from_urls(assets)
    mosaicjson_data.name = "my mosaic"
    mosaicjson_data.description = "this is a great mosaic"
    mosaicjson_data.attribution = "some attribution"

    r = client.post(
        url="/mosaic/mosaics",
        headers={"Content-Type": "application/vnd.titiler.mosaicjson+json"},
        json=mosaicjson_data.dict(exclude_none=True),
    )
    assert r.status_code == 201
    mosaic_id = r.json()["id"]
    assert mosaic_id

    location_header_url = r.headers["location"]
    assert location_header_url == f"{root}/mosaics/{mosaic_id}"

    assert location_header_url == _get_link_by_rel(r.json(), "self")

    # GET
    r = client.get(url=location_header_url)
    assert r.json()["id"] == mosaic_id

    self_link = _get_link_by_rel(r.json(), "self")
    assert self_link == f"{root}/mosaics/{mosaic_id}"

    mosaicjson_link = _get_link_by_rel(r.json(), "mosaicjson")
    assert mosaicjson_link == f"{root}/mosaics/{mosaic_id}/mosaicjson"

    tilejson_link = _get_link_by_rel(r.json(), "tilejson")
    assert tilejson_link == f"{root}/mosaics/{mosaic_id}/tilejson.json"

    tiles_link = _get_link_by_rel(r.json(), "tiles")
    assert tiles_link == f"{root}/mosaics/{mosaic_id}/tiles/{{z}}/{{x}}/{{y}}"

    wmts_link = _get_link_by_rel(r.json(), "wmts")
    assert wmts_link == f"{root}/mosaics/{mosaic_id}/WMTSCapabilities.xml"

    # /mosaicjson
    r = client.get(url=mosaicjson_link)
    assert MosaicJSON(**r.json()) == mosaicjson_data

    # /tilejson.json
    r = client.get(url=tilejson_link)
    assert r.json()["name"] == mosaic_id
    assert (
        r.json()["tiles"][0]
        == f"{root}/mosaics/{mosaic_id}/tiles/{{z}}/{{x}}/{{y}}@1x?"
    )

    # tilejson with arguments
    r = client.get(url=f"{tilejson_link}?tile_format=jpg")
    assert r.json()["name"] == mosaic_id
    assert (
        r.json()["tiles"][0]
        == f"{root}/mosaics/{mosaic_id}/tiles/{{z}}/{{x}}/{{y}}@1x.jpg?"
    )

    r = client.get(url=f"{tilejson_link}?tile_scale=2")
    assert r.json()["name"] == mosaic_id
    assert (
        r.json()["tiles"][0]
        == f"{root}/mosaics/{mosaic_id}/tiles/{{z}}/{{x}}/{{y}}@2x?"
    )

    # /tiles

    single_tile_link = (
        tiles_link.replace("{z}", "7").replace("{x}", "37").replace("{y}", "45")
    )
    r = client.get(url=single_tile_link)
    assert r.status_code == 200

    with raises(NoAssetFoundError):
        bad_single_tile_link = (
            tiles_link.replace("{z}", "10").replace("{x}", "10").replace("{y}", "10")
        )
        r = client.get(url=bad_single_tile_link)
        assert r.status_code == 404

    # WMTS
    r = client.get(url=wmts_link)
    assert r.text

    # PUT update

    mosaicjson_data.name = "updated mosaicjson"

    r = client.put(
        url=self_link,
        headers={"Content-Type": "application/vnd.titiler.mosaicjson+json"},
        json=mosaicjson_data.dict(exclude_none=True),
    )
    assert r.status_code == 204

    r = client.get(url=mosaicjson_link)
    # note: in cogeo-mosaic, the cache is not flushed on update, so the old entry still exists for 5 min
    assert r.json()["name"] == "my mosaic"

    r = client.delete(url=self_link)
    assert (
        r.status_code == 405
    )  # because we're using the in-memory db instead of dynamodb

    # note: in cogeo-mosaic, the cache is not flushed on delete, so the old entry still exists for 5 min


def test_mosaics_errors_not_found(set_env, client):
    """Test mosaicjson functionality."""

    # Create a new MosaicJSON
    mosaicjson_data = MosaicJSON.from_urls(assets)
    mosaicjson_data.name = "my mosaic"
    mosaicjson_data.description = "this is a great mosaic"
    mosaicjson_data.attribution = "some attribution"

    r = client.get(url="/mosaic/mosaics/ABC")
    assert r.status_code == 404

    r = client.put(
        url="/mosaic/mosaics/ABC",
        headers={"Content-Type": "application/vnd.titiler.mosaicjson+json"},
        json={},
    )
    assert r.status_code == 404

    r = client.delete(url="/mosaic/mosaics/ABC")
    assert r.status_code == 404


def test_mosaics_create(set_env, client):
    """Test mosaicjson functionality."""

    # Create a new MosaicJSON
    mosaicjson_data = MosaicJSON.from_urls(assets)
    mosaicjson_data.name = "my mosaic"
    mosaicjson_data.description = "this is a great mosaic"
    mosaicjson_data.attribution = "some attribution"

    r = client.post(
        url="/mosaic/mosaics",
        headers={"Content-Type": ""},
        json=mosaicjson_data.dict(exclude_none=True),
    )
    assert r.status_code == 201

    r = client.post(
        url="/mosaic/mosaics",
        headers={"Content-Type": "application/json"},
        json=mosaicjson_data.dict(exclude_none=True),
    )
    assert r.status_code == 201

    r = client.post(
        url="/mosaic/mosaics",
        headers={"Content-Type": "application/json; charset=utf-8"},
        json=mosaicjson_data.dict(exclude_none=True),
    )
    assert r.status_code == 201

    r = client.post(
        url="/mosaic/mosaics",
        headers={"Content-Type": "application/vnd.titiler.mosaicjson+json"},
        json=mosaicjson_data.dict(exclude_none=True),
    )
    assert r.status_code == 201

    r = client.post(
        url="/mosaic/mosaics",
        headers={"Content-Type": "application/vnd.titiler.urls+json"},
        json={"urls": assets},
    )
    assert r.status_code == 201

    r = client.post(
        url="/mosaic/mosaics",
        headers={"Content-Type": "application/vnd.titiler.stac-api-query+json"},
        json={
            "stac_api_root": "https://earth-search.aws.element84.com/v0",
            "name": "foo",
            "description": "bar",
            "attribution": "shmattribution",
            "asset_name": "visual",
            "collections": ["sentinel-s2-l2a-cogs"],
            "datetime": "2021-04-20T00:00:00Z/2021-04-21T02:00:00Z",
            "bbox": [20, 20, 21, 21],
        },
    )
    assert r.status_code == 201

    def test_mosaics_create_errors(set_env):
        """Test mosaicjson functionality."""

        mosaic_config.backend = "file://"
        mosaic_config.host = "/tmp"

        mosaic = MosaicTilerFactory(
            optional_headers=[OptionalHeader.server_timing, OptionalHeader.x_assets],
            router_prefix="mosaic",
        )

        app = FastAPI()
        app.include_router(mosaic.router, prefix="/mosaic")
        client = TestClient(app)

        # invalid MosaicJSON
        r = client.post(
            url="/mosaic/mosaics",
            headers={"Content-Type": "application/json"},
            json={},
        )
        assert r.status_code == 400

        # too many urls
        r = client.post(
            url="/mosaic/mosaics",
            headers={"Content-Type": "application/vnd.titiler.urls+json"},
            json={"urls": [{str(x): str(x)} for x in range(101)]},
        )
        assert r.status_code == 400

        # too many results from STAC query
        r = client.post(
            url="/mosaic/mosaics",
            headers={"Content-Type": "application/vnd.titiler.stac-api-query+json"},
            json={
                "stac_api_root": "https://earth-search.aws.element84.com/v0",
                "collections": ["sentinel-s2-l2a-cogs"],
            },
        )
        assert r.status_code == 400
