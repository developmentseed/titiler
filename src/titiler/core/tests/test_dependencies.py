"""test dependencies."""

import json
from dataclasses import dataclass

import pytest
from morecantile import TileMatrixSet
from rio_tiler.types import ColorMapType

from titiler.core import dependencies, errors
from titiler.core.resources.responses import JSONResponse

from fastapi import Depends, FastAPI

from starlette.testclient import TestClient


def test_tms():
    """Create App."""
    app = FastAPI()

    @app.get("/web/{TileMatrixSetId}")
    def web(tms: TileMatrixSet = Depends(dependencies.WebMercatorTMSParams)):
        """return tms id."""
        return tms.identifier

    @app.get("/all/{TileMatrixSetId}")
    def all(tms: TileMatrixSet = Depends(dependencies.TMSParams)):
        """return tms id."""
        return tms.identifier

    client = TestClient(app)
    response = client.get("/web/WebMercatorQuad")
    assert response.json() == "WebMercatorQuad"

    response = client.get("/web/WorldCRS84Quad")
    assert response.status_code == 422
    assert "permitted: 'WebMercatorQuad'" in response.json()["detail"][0]["msg"]

    response = client.get("/all/WebMercatorQuad")
    assert response.json() == "WebMercatorQuad"

    response = client.get("/all/WorldCRS84Quad")
    assert response.json() == "WorldCRS84Quad"


def test_cmap():
    """Create App."""
    app = FastAPI()

    @app.get("/", response_model=ColorMapType)
    def main(cm=Depends(dependencies.ColorMapParams)):
        """return cmap."""
        return cm

    client = TestClient(app)
    response = client.get("/?colormap_name=another_cmap")
    assert response.status_code == 422

    response = client.get("/?colormap_name=viridis")
    assert response.json()["1"] == [68, 2, 85, 255]

    cmap = json.dumps({1: [68, 1, 84, 255]})
    response = client.get(f"/?colormap={cmap}")
    assert response.json()["1"] == [68, 1, 84, 255]

    cmap = json.dumps({0: "#000000", 255: "#ffffff"})
    response = client.get("/", params={"colormap": cmap})
    assert response.json()["0"] == [0, 0, 0, 255]
    assert response.json()["255"] == [255, 255, 255, 255]

    intervals = [
        # ([min, max], [r, g, b, a])
        ([1, 2], [0, 0, 0, 255]),
        ([2, 3], [255, 255, 255, 255]),
        ([3, 1000], [255, 0, 0, 255]),
    ]
    cmap = json.dumps(intervals)
    response = client.get(f"/?colormap={cmap}")
    assert response.json()[0] == [[1, 2], [0, 0, 0, 255]]
    assert response.json()[1] == [[2, 3], [255, 255, 255, 255]]
    assert response.json()[2] == [[3, 1000], [255, 0, 0, 255]]


def test_default():
    """test default dep behavior."""

    @dataclass
    class dep(dependencies.DefaultDependency):

        v: int

    # make sure we can unpack the class
    assert dict(**dep(v=1)) == {"v": 1}
    assert dep(v=1).v == 1


def test_bdix():
    """test bidx deps."""

    app = FastAPI()

    @app.get("/first")
    def _bidx(params=Depends(dependencies.BidxParams)):
        """return indexes."""
        return params.indexes

    @app.get("/second")
    def _bidx_expr(params=Depends(dependencies.BidxExprParams)):
        """return params."""
        return params

    @app.get("/third")
    def _expre(params=Depends(dependencies.ExpressionParams)):
        """return express."""
        return params.expression

    client = TestClient(app)
    response = client.get("/first?bidx=1&bidx=2")
    assert response.json() == [1, 2]

    response = client.get("/first")
    assert not response.json()

    response = client.get("/second?bidx=1&bidx=2")
    assert response.json()["indexes"] == [1, 2]

    response = client.get("/second", params={"expression": "1;2"})
    assert response.json()["expression"] == "1;2"

    response = client.get("/second")
    assert not response.json()["expression"]
    assert not response.json()["indexes"]

    response = client.get("/third", params={"expression": "1;2"})
    assert response.json() == "1;2"

    response = client.get("/third")
    assert not response.json()


def test_assets():
    """test assets deps."""

    app = FastAPI()

    @app.get("/first")
    def _assets(params=Depends(dependencies.AssetsParams)):
        """return assets."""
        return params.assets

    @app.get("/second")
    def _assets_expr(params=Depends(dependencies.AssetsBidxExprParams)):
        """return params."""
        return params

    @app.get("/third")
    def _assets_bidx(params=Depends(dependencies.AssetsBidxParams)):
        """return params."""
        return params

    client = TestClient(app)
    response = client.get("/first?assets=data&assets=image")
    assert response.json() == ["data", "image"]

    response = client.get("/first")
    assert not response.json()

    response = client.get("/second?assets=data&assets=image")
    assert response.json()["assets"] == ["data", "image"]
    assert not response.json()["expression"]

    response = client.get("/second?expression=data*image")
    assert response.json()["expression"] == "data*image"
    assert not response.json()["assets"]

    with pytest.raises(errors.MissingAssets):
        response = client.get("/second")

    response = client.get(
        "/second?assets=data&assets=image&asset_bidx=data|1,2,3&asset_bidx=image|1"
    )
    assert response.json()["assets"] == ["data", "image"]
    assert response.json()["asset_indexes"] == {"data": [1, 2, 3], "image": [1]}

    response = client.get(
        "/second?assets=data&assets=image&asset_expression=data|b1\b2&asset_expression=image|b1*b2"
    )
    assert response.json()["assets"] == ["data", "image"]
    assert response.json()["asset_expression"] == {"data": "b1\b2", "image": "b1*b2"}

    response = client.get("/third?assets=data&assets=image")
    assert response.json()["assets"] == ["data", "image"]

    response = client.get("/third")
    assert not response.json()["assets"]

    response = client.get(
        "/third?assets=data&assets=image&asset_bidx=data|1,2,3&asset_bidx=image|1"
    )
    assert response.json()["assets"] == ["data", "image"]
    assert response.json()["asset_indexes"] == {"data": [1, 2, 3], "image": [1]}

    response = client.get(
        "/third?assets=data&assets=image&asset_expression=data|b1\b2&asset_expression=image|b1*b2"
    )
    assert response.json()["assets"] == ["data", "image"]
    assert response.json()["asset_expression"] == {"data": "b1\b2", "image": "b1*b2"}


def test_bands():
    """test bands deps."""

    app = FastAPI()

    @app.get("/first")
    def _bands(params=Depends(dependencies.BandsParams)):
        """return bands."""
        return params.bands

    @app.get("/second")
    def _bands_expr(params=Depends(dependencies.BandsExprParams)):
        """return params."""
        return params

    @app.get("/third")
    def _bands_expr_opt(params=Depends(dependencies.BandsExprParamsOptional)):
        """return params."""
        return params

    client = TestClient(app)
    response = client.get("/first?bands=b1&bands=b2")
    assert response.json() == ["b1", "b2"]

    response = client.get("/first")
    assert not response.json()

    response = client.get("/second?bands=b1&bands=b2")
    assert response.json()["bands"] == ["b1", "b2"]

    response = client.get("/second", params={"expression": "b1;b2"})
    assert response.json()["expression"] == "b1;b2"

    with pytest.raises(errors.MissingBands):
        response = client.get("/second")

    response = client.get("/third?bands=b1&bands=b2")
    assert response.json()["bands"] == ["b1", "b2"]

    response = client.get("/third", params={"expression": "b1;b2"})
    assert response.json()["expression"] == "b1;b2"

    response = client.get("/third")
    assert not response.json()["bands"]


def test_image():
    """test image deps."""

    app = FastAPI()

    @app.get("/")
    def _endpoint(params=Depends(dependencies.ImageParams)):
        """return params."""
        return params

    client = TestClient(app)
    response = client.get("/")
    assert response.json()["max_size"] == 1024
    assert not response.json()["height"]
    assert not response.json()["width"]

    response = client.get("/?max_size=2048")
    assert response.json()["max_size"] == 2048
    assert not response.json()["height"]
    assert not response.json()["width"]

    response = client.get("/?width=128")
    assert response.json()["max_size"] == 1024
    assert not response.json()["height"]
    assert response.json()["width"] == 128

    response = client.get("/?width=128&height=128")
    assert not response.json()["max_size"]
    assert response.json()["height"] == 128
    assert response.json()["width"] == 128


def test_dataset():
    """test dataset deps."""

    app = FastAPI()

    @app.get("/", response_class=JSONResponse)
    def _endpoint(params=Depends(dependencies.DatasetParams)):
        """return params."""
        return params

    @app.get("/nan", response_class=JSONResponse)
    def is_nan(params=Depends(dependencies.DatasetParams)):
        """return params."""
        return str(params.nodata)

    client = TestClient(app)
    response = client.get("/")
    assert not response.json()["nodata"]
    assert not response.json()["unscale"]
    assert response.json()["resampling_method"] == "nearest"

    response = client.get("/?resampling=cubic")
    assert not response.json()["nodata"]
    assert not response.json()["unscale"]
    assert response.json()["resampling_method"] == "cubic"

    response = client.get("/?nodata=10")
    assert response.json()["nodata"] == 10.0

    response = client.get("/nan?nodata=nan")
    assert response.json() == "nan"


def test_render():
    """test render deps."""

    app = FastAPI()

    @app.get("/")
    def _endpoint(params=Depends(dependencies.ImageRenderingParams)):
        """return params."""
        return params

    client = TestClient(app)
    response = client.get("/")
    assert response.json()["add_mask"] is True

    response = client.get("/?return_mask=False")
    assert response.json()["add_mask"] is False

    response = client.get("/?return_mask=True")
    assert response.json()["add_mask"] is True


def test_postprocess():
    """test postprocess deps."""

    app = FastAPI()

    @app.get("/")
    def _endpoint(params=Depends(dependencies.PostProcessParams)):
        """return params."""
        return params

    client = TestClient(app)
    response = client.get("/")
    assert not response.json()["in_range"]
    assert not response.json()["color_formula"]

    response = client.get("/?rescale=0,1000")
    assert response.json()["in_range"] == [[0, 1000]]

    response = client.get("/?rescale=0,1000&rescale=0,255")
    assert response.json()["in_range"] == [[0, 1000], [0, 255]]

    response = client.get("/?color_formula=gamma RGB 3")
    assert response.json()["color_formula"] == "gamma RGB 3"
