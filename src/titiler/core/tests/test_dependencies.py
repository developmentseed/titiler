"""test dependencies."""

import json
from dataclasses import dataclass
from typing import Literal

import pytest
from fastapi import Depends, FastAPI, Path
from morecantile import tms
from rio_tiler.types import ColorMapType
from starlette.testclient import TestClient
from typing_extensions import Annotated

from titiler.core import dependencies, errors
from titiler.core.resources.responses import JSONResponse


def test_tms():
    """Create App."""
    app = FastAPI()

    @app.get("/web/{tileMatrixSetId}")
    def web(
        tileMatrixSetId: Annotated[
            Literal["WebMercatorQuad"],
            Path(),
        ],
    ):
        """return tms id."""
        return tileMatrixSetId

    @app.get("/all/{tileMatrixSetId}")
    def all(tileMatrixSetId: Annotated[Literal[tuple(tms.list())], Path()]):
        """return tms id."""
        return tileMatrixSetId

    client = TestClient(app)
    response = client.get("/web/WebMercatorQuad")
    assert response.json() == "WebMercatorQuad"

    response = client.get("/web/WorldCRS84Quad")
    assert response.status_code == 422
    assert "Input should be 'WebMercatorQuad'" in response.json()["detail"][0]["msg"]

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
    response = client.get("/", params={"colormap": cmap})
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
    response = client.get("/", params={"colormap": cmap})
    assert response.json()[0] == [[1, 2], [0, 0, 0, 255]]
    assert response.json()[1] == [[2, 3], [255, 255, 255, 255]]
    assert response.json()[2] == [[3, 1000], [255, 0, 0, 255]]

    interval_float_cmap = [
        ((0.0, 0.05263157894736842), (247, 252, 240, 255)),
        ((0.05263157894736842, 0.10526315789473684), (238, 248, 231, 255)),
        ((0.10526315789473684, 0.15789473684210525), (228, 245, 223, 255)),
        ((0.15789473684210525, 0.21052631578947367), (219, 241, 213, 255)),
        ((0.21052631578947367, 0.2631578947368421), (211, 238, 204, 255)),
        ((0.2631578947368421, 0.3157894736842105), (200, 234, 195, 255)),
        ((0.3157894736842105, 0.3684210526315789), (186, 228, 189, 255)),
        ((0.3684210526315789, 0.42105263157894735), (170, 222, 182, 255)),
        ((0.42105263157894735, 0.47368421052631576), (152, 215, 186, 255)),
        ((0.47368421052631576, 0.5263157894736842), (132, 207, 193, 255)),
        ((0.5263157894736842, 0.5789473684210527), (114, 199, 199, 255)),
        ((0.5789473684210527, 0.631578947368421), (94, 188, 206, 255)),
        ((0.631578947368421, 0.6842105263157894), (76, 177, 210, 255)),
        ((0.6842105263157894, 0.7368421052631579), (61, 160, 201, 255)),
        ((0.7368421052631579, 0.7894736842105263), (47, 144, 192, 255)),
        ((0.7894736842105263, 0.8421052631578947), (31, 128, 184, 255)),
        ((0.8421052631578947, 0.894736842105263), (17, 113, 177, 255)),
        ((0.894736842105263, 0.9473684210526315), (8, 97, 164, 255)),
        ((0.9473684210526315, 1.0), (8, 80, 147, 255)),
        ((1.0, 1000), (8, 64, 129, 255)),
    ]
    response = client.get("/", params={"colormap": json.dumps(interval_float_cmap)})
    assert response.status_code == 200
    assert response.json()[0][0] == [0.0, 0.05263157894736842]
    assert response.json()[0][1] == [247, 252, 240, 255]

    # Make sure the color is parsed
    interval_float_cmap = [
        ((0.0, 0.05263157894736842), "#f7fcf0ff"),
        ((0.05263157894736842, 0.10526315789473684), "#eef8e7ff"),
        ((0.10526315789473684, 0.15789473684210525), "#e4f5dfff"),
        ((0.15789473684210525, 0.21052631578947367), "#dbf1d5ff"),
        ((0.21052631578947367, 0.2631578947368421), "#d3eeccff"),
        ((0.2631578947368421, 0.3157894736842105), "#c8eac3ff"),
        ((0.3157894736842105, 0.3684210526315789), "#bae4bdff"),
        ((0.3684210526315789, 0.42105263157894735), "#aadeb6ff"),
        ((0.42105263157894735, 0.47368421052631576), "#98d7baff"),
        ((0.47368421052631576, 0.5263157894736842), "#84cfc1ff"),
        ((0.5263157894736842, 0.5789473684210527), "#72c7c7ff"),
        ((0.5789473684210527, 0.631578947368421), "#5ebcceff"),
        ((0.631578947368421, 0.6842105263157894), "#4cb1d2ff"),
        ((0.6842105263157894, 0.7368421052631579), "#3da0c9ff"),
        ((0.7368421052631579, 0.7894736842105263), "#2f90c0ff"),
        ((0.7894736842105263, 0.8421052631578947), "#1f80b8ff"),
        ((0.8421052631578947, 0.894736842105263), "#1171b1ff"),
        ((0.894736842105263, 0.9473684210526315), "#0861a4ff"),
        ((0.9473684210526315, 1.0), "#085093ff"),
        ((1.0, 1000), "#084081ff"),
    ]
    response = client.get("/", params={"colormap": json.dumps(interval_float_cmap)})
    assert response.status_code == 200
    assert response.json()[0][0] == [0.0, 0.05263157894736842]
    assert response.json()[0][1] == [247, 252, 240, 255]


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

    response = client.get("/third?assets=data&assets=image")
    assert response.json()["assets"] == ["data", "image"]

    response = client.get(
        "/third",
        params=(
            ("assets", "data"),
            ("assets", "image"),
        ),
    )
    assert response.json()["assets"] == ["data", "image"]

    response = client.get("/third", params={"assets": ["data", "image"]})
    assert response.json()["assets"] == ["data", "image"]

    response = client.get("/third")
    assert not response.json()["assets"]

    response = client.get(
        "/third?assets=data&assets=image&asset_bidx=data|1,2,3&asset_bidx=image|1"
    )
    assert response.json()["assets"] == ["data", "image"]
    assert response.json()["asset_indexes"] == {"data": [1, 2, 3], "image": [1]}

    response = client.get(
        "/third",
        params=(
            ("assets", "data"),
            ("assets", "image"),
            ("asset_bidx", "data|1,2,3"),
            ("asset_bidx", "image|1"),
        ),
    )

    assert response.json()["assets"] == ["data", "image"]
    assert response.json()["asset_indexes"] == {"data": [1, 2, 3], "image": [1]}

    response = client.get(
        "/third?assets=data&assets=image&asset_expression=data|b1/b2&asset_expression=image|b1*b2"
    )
    assert response.json()["assets"] == ["data", "image"]
    assert response.json()["asset_expression"] == {"data": "b1/b2", "image": "b1*b2"}

    response = client.get(
        "/third",
        params=(
            ("assets", "data"),
            ("assets", "image"),
            ("asset_expression", "data|b1/b2"),
            ("asset_expression", "image|b1*b2"),
        ),
    )
    assert response.json()["assets"] == ["data", "image"]
    assert response.json()["asset_expression"] == {"data": "b1/b2", "image": "b1*b2"}


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


def test_preview_part_params():
    """test preview/part deps."""

    app = FastAPI()

    @app.get("/preview")
    def _endpoint(params=Depends(dependencies.PreviewParams)):
        """return params."""
        return params

    @app.get("/part")
    def _endpoint(params=Depends(dependencies.PartFeatureParams)):
        """return params."""
        return params

    client = TestClient(app)
    response = client.get("/preview")
    assert response.json()["max_size"] == 1024
    assert not response.json()["height"]
    assert not response.json()["width"]

    response = client.get("/preview?max_size=2048")
    assert response.json()["max_size"] == 2048
    assert not response.json()["height"]
    assert not response.json()["width"]

    response = client.get("/preview?width=128")
    assert response.json()["max_size"] == 1024
    assert not response.json()["height"]
    assert response.json()["width"] == 128

    response = client.get("/preview?width=128&height=128")
    assert not response.json()["max_size"]
    assert response.json()["height"] == 128
    assert response.json()["width"] == 128

    response = client.get("/part")
    assert not response.json()["max_size"]
    assert not response.json()["height"]
    assert not response.json()["width"]

    response = client.get("/part?max_size=2048")
    assert response.json()["max_size"] == 2048
    assert not response.json()["height"]
    assert not response.json()["width"]

    response = client.get("/part?width=128")
    assert not response.json()["max_size"]
    assert not response.json()["height"]
    assert response.json()["width"] == 128

    response = client.get("/part?width=128&height=128")
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
    assert not response.json()["resampling_method"]

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
    assert not response.json()["add_mask"]

    response = client.get("/?return_mask=False")
    assert response.json()["add_mask"] is False

    response = client.get("/?return_mask=True")
    assert response.json()["add_mask"] is True


def test_algo():
    """test algorithm deps."""

    from titiler.core.algorithm import algorithms as default_algorithms

    PostProcessParams = default_algorithms.dependency

    app = FastAPI()

    @app.get("/")
    def _endpoint(algorithm=Depends(PostProcessParams)):
        """return params."""
        if algorithm:
            return algorithm.model_dump()
        return {}

    client = TestClient(app)
    response = client.get("/")
    assert not response.json()

    response = client.get("/?algorithm=hillshad")
    assert response.status_code == 422

    response = client.get("/?algorithm=hillshade")
    assert response.json()["azimuth"] == 90
    assert response.json()["buffer"] == 3
    assert response.json()["input_nbands"] == 1

    response = client.get(
        "/",
        params={
            "algorithm": "hillshade",
            "algorithm_params": json.dumps({"azimuth": 30, "buffer": 4}),
        },
    )
    assert response.json()["azimuth"] == 30
    assert response.json()["buffer"] == 4
    assert response.json()["input_nbands"] == 1


def test_rescale_params():
    """test RescalingParams dependency."""
    app = FastAPI()

    @app.get("/")
    def main(rescale=Depends(dependencies.RescalingParams)):
        """return rescale."""
        return rescale

    client = TestClient(app)

    response = client.get("/", params={"rescale": "0,1"})
    assert response.status_code == 200
    assert response.json() == [[0, 1]]

    response = client.get("/?rescale=0,1")
    assert response.status_code == 200
    assert response.json() == [[0, 1]]

    response = client.get("/?rescale=0,1&rescale=2,3")
    assert response.status_code == 200
    assert response.json() == [[0, 1], [2, 3]]

    with pytest.raises(AssertionError):
        client.get("/", params={"rescale": [0, 1]})

    response = client.get("/", params={"rescale": [[0, 1]]})
    assert response.status_code == 200
    assert response.json() == [[0, 1]]

    response = client.get(
        "/",
        params=(
            ("rescale", [0, 1]),
            ("rescale", [0, 1]),
        ),
    )
    assert response.status_code == 200
    assert response.json() == [[0, 1], [0, 1]]

    response = client.get(
        "/",
        params=(
            ("rescale", "0,1"),
            ("rescale", "0,1"),
        ),
    )
    assert response.status_code == 200
    assert response.json() == [[0, 1], [0, 1]]

    response = client.get("/", params={"rescale": [[0, 1], [2, 3]]})
    assert response.status_code == 200
    assert response.json() == [[0, 1], [2, 3]]


def test_histogram_params():
    """Test HistogramParams dependency."""
    app = FastAPI()

    @app.get("/")
    def main(params=Depends(dependencies.HistogramParams)):
        """return rescale."""
        return params

    client = TestClient(app)

    response = client.get(
        "/",
        params={"histogram_bins": "8"},
    )
    assert response.status_code == 200
    assert response.json()["bins"] == 8

    response = client.get(
        "/",
        params={"histogram_bins": "8,9"},
    )
    assert response.status_code == 200
    assert response.json()["bins"] == [8.0, 9.0]

    response = client.get(
        "/",
    )
    assert response.status_code == 200
    assert response.json()["bins"] == 10

    response = client.get(
        "/",
        params={"histogram_range": "8,9"},
    )
    assert response.status_code == 200
    assert response.json()["range"] == [8.0, 9.0]

    with pytest.raises(AssertionError):
        client.get(
            "/",
            params={"histogram_range": "8"},
        )
