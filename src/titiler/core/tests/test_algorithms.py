"""Test the Algorithms class."""

import json

import numpy
import pytest
from fastapi import Depends, FastAPI
from rasterio.io import MemoryFile
from rio_tiler.models import ImageData
from starlette.responses import Response
from starlette.testclient import TestClient

from titiler.core.algorithm import BaseAlgorithm
from titiler.core.algorithm import algorithms as default_algorithms


class Multiply(BaseAlgorithm):
    """Custom Dependency."""

    # Parameters
    factor: int

    def __call__(self, img: ImageData) -> ImageData:
        """Apply Multiplication factor."""
        # Multiply image data bcy factor
        data = img.array * self.factor

        # Create output ImageData
        return ImageData(
            data,
            assets=img.assets,
            crs=img.crs,
            bounds=img.bounds,
        )


def test_algo():
    """test algorithm deps."""
    # Add the `Multiply` algorithm to the default ones
    algorithms = default_algorithms.register({"multiply": Multiply})

    app = FastAPI()

    arr = numpy.random.randint(0, 3000, (3, 256, 256))

    @app.get("/")
    def main(algorithm=Depends(algorithms.dependency)):
        """endpoint."""
        img = ImageData(arr)
        if algorithm:
            return algorithm(img).data.max().tolist()

        return img.data.max().tolist()

    client = TestClient(app)
    response = client.get("/")
    assert response.json() == arr.max().tolist()

    # Missing factor input
    response = client.get("/", params={"algorithm": "multiply"})
    assert response.status_code == 400

    response = client.get(
        "/",
        params={"algorithm": "multiply", "algorithm_params": json.dumps({"factor": 3})},
    )
    assert response.json() == arr.max().tolist() * 3


def test_terrain_algo():
    """test terrain algorithm deps."""
    # Add the `Multiply` algorithm to the default ones
    app = FastAPI()

    arr = numpy.random.randint(0, 3000, (1, 256, 256))

    @app.get("/", response_class=Response)
    def main(algorithm=Depends(default_algorithms.dependency)):
        """endpoint."""
        img = ImageData(arr)
        if algorithm:
            img = algorithm(img)

        return Response(img.render(img_format="PNG"), media_type="image/png")

    client = TestClient(app)

    # MAPBOX Terrain RGB
    response = client.get("/", params={"algorithm": "terrainrgb"})
    assert response.status_code == 200
    with MemoryFile(response.content) as mem:
        with mem.open() as dst:
            data = dst.read().astype(numpy.float64)

    # https://docs.mapbox.com/data/tilesets/guides/access-elevation-data/
    elevation = -10000 + (((data[0] * 256 * 256) + (data[1] * 256) + data[2]) * 0.1)
    numpy.testing.assert_array_equal(elevation, arr[0])

    # TILEZEN Terrarium
    response = client.get("/", params={"algorithm": "terrarium"})
    assert response.status_code == 200
    with MemoryFile(response.content) as mem:
        with mem.open() as dst:
            data = dst.read().astype(numpy.float64)

    # https://github.com/tilezen/joerd/blob/master/docs/formats.md#terrarium
    elevation = (data[0] * 256 + data[1] + data[2] / 256) - 32768
    numpy.testing.assert_array_equal(elevation, arr[0])


def test_normalized_index():
    """test ndi."""
    algo = default_algorithms.get("normalizedIndex")()

    arr = numpy.zeros((2, 256, 256), dtype="uint16")
    arr[0, :, :] = 1
    arr[1, :, :] = 2

    img = ImageData(arr)
    out = algo(img)
    assert out.array.shape == (1, 256, 256)
    assert out.array.dtype == "float32"
    assert len(numpy.unique(out.array).tolist()) == 1
    numpy.testing.assert_almost_equal(out.array[0, 0, 0], 0.3333, decimal=3)

    # with mixed 0 and masked
    arr = numpy.ma.MaskedArray(
        numpy.zeros((2, 256, 256), dtype="uint16"),
        mask=numpy.zeros((2, 256, 256), dtype="bool"),
    )
    arr.data[0, :, :] = 1
    arr.data[0, 0:10, 0:10] = 0
    arr.mask[0, 0:5, 0:5] = True

    arr.data[1, :, :] = 2
    arr.data[1, 0:10, 0:10] = 0
    arr.mask[1, 0:5, 0:5] = True

    img = ImageData(arr)
    out = algo(img)
    assert out.array.shape == (1, 256, 256)
    assert out.array.dtype == "float32"
    assert len(numpy.unique(out.array).tolist()) == 2  # 0.33 and None
    assert out.array[0, 0, 0] is numpy.ma.masked
    assert out.array[0, 6, 6] is numpy.ma.masked
    numpy.testing.assert_almost_equal(out.array[0, 10, 10], 0.3333, decimal=3)


def test_hillshade():
    """test hillshade."""
    algo = default_algorithms.get("hillshade")()

    arr = numpy.random.randint(0, 5000, (1, 262, 262), dtype="uint16")
    img = ImageData(arr)
    out = algo(img)
    assert out.array.shape == (1, 256, 256)
    assert out.array.dtype == "uint8"

    arr = numpy.ma.MaskedArray(
        numpy.random.randint(0, 5000, (1, 262, 262), dtype="uint16"),
        mask=numpy.zeros((1, 262, 262), dtype="bool"),
    )
    arr.mask[0, 0:100, 0:100] = True

    img = ImageData(arr)
    out = algo(img)
    assert out.array.shape == (1, 256, 256)
    assert out.array.dtype == "uint8"
    assert out.array[0, 0, 0] is numpy.ma.masked


def test_slope():
    """test slope."""
    algo = default_algorithms.get("slope")()

    arr = numpy.random.randint(0, 5000, (1, 262, 262), dtype="uint16")
    img = ImageData(arr)
    out = algo(img)
    assert out.array.shape == (1, 256, 256)
    assert out.array.dtype == "float32"

    arr = numpy.ma.MaskedArray(
        numpy.random.randint(0, 5000, (1, 262, 262), dtype="uint16"),
        mask=numpy.zeros((1, 262, 262), dtype="bool"),
    )
    arr.mask[0, 0:100, 0:100] = True

    img = ImageData(arr)
    out = algo(img)
    assert out.array.shape == (1, 256, 256)
    assert out.array.dtype == "float32"
    assert out.array[0, 0, 0] is numpy.ma.masked


def test_contours():
    """test contours."""
    algo = default_algorithms.get("contours")()

    arr = numpy.random.randint(0, 5000, (1, 256, 256), dtype="uint16")
    img = ImageData(arr)
    out = algo(img)
    assert out.array.shape == (3, 256, 256)
    assert out.array.dtype == "uint8"

    arr = numpy.ma.MaskedArray(
        numpy.random.randint(0, 5000, (1, 256, 256), dtype="uint16"),
        mask=numpy.zeros((1, 256, 256), dtype="bool"),
    )
    arr.mask[0, 0:100, 0:100] = True

    img = ImageData(arr)
    out = algo(img)
    assert out.array.shape == (3, 256, 256)
    assert out.array.dtype == "uint8"
    assert out.array[0, 0, 0] is numpy.ma.masked


def test_terrarium():
    """test terrarium."""
    algo = default_algorithms.get("terrarium")()

    arr = numpy.random.randint(0, 5000, (1, 256, 256), dtype="uint16")
    img = ImageData(arr)
    out = algo(img)
    assert out.array.shape == (3, 256, 256)
    assert out.array.dtype == "uint8"

    arr = numpy.ma.MaskedArray(
        numpy.random.randint(0, 5000, (1, 256, 256), dtype="uint16"),
        mask=numpy.zeros((1, 256, 256), dtype="bool"),
    )
    arr.mask[0, 0:100, 0:100] = True

    img = ImageData(arr)
    out = algo(img)
    assert out.array.shape == (3, 256, 256)
    assert out.array.dtype == "uint8"
    assert out.array[0, 0, 0] is numpy.ma.masked

    # works on the above masked array img, with algo which was passed nodata_height
    nodata_height = 10.0
    algo = default_algorithms.get("terrarium")(nodata_height=nodata_height)
    out = algo(img)
    masked = out.array[:, arr.mask[0, :, :]]
    masked_height = (masked[0] * 256 + masked[1] + masked[2] / 256) - 32768
    numpy.testing.assert_array_equal(
        masked_height, nodata_height * numpy.ones((100 * 100), dtype="bool")
    )


def test_terrainrgb():
    """test terrainrgb."""
    algo = default_algorithms.get("terrainrgb")()

    arr = numpy.random.randint(0, 5000, (1, 256, 256), dtype="uint16")
    img = ImageData(arr)
    out = algo(img)
    assert out.array.shape == (3, 256, 256)
    assert out.array.dtype == "uint8"

    arr = numpy.ma.MaskedArray(
        numpy.random.randint(0, 5000, (1, 256, 256), dtype="uint16"),
        mask=numpy.zeros((1, 256, 256), dtype="bool"),
    )
    arr.mask[0, 0:100, 0:100] = True

    img = ImageData(arr)
    out = algo(img)
    assert out.array.shape == (3, 256, 256)
    assert out.array.dtype == "uint8"
    assert out.array[0, 0, 0] is numpy.ma.masked

    # works on the above masked array img, with algo which was passed nodata_height
    nodata_height = 10.0
    algo = default_algorithms.get("terrainrgb")(nodata_height=nodata_height)
    out = algo(img)
    masked = out.array[:, arr.mask[0, :, :]]
    masked_height = -10000 + (
        ((masked[0] * 256 * 256) + (masked[1] * 256) + masked[2]) * 0.1
    )
    numpy.testing.assert_array_equal(
        masked_height, nodata_height * numpy.ones((100 * 100), dtype="bool")
    )


def test_ops():
    """test ops: cast, ceil and floor."""
    arr = numpy.ma.MaskedArray(
        numpy.random.randint(0, 5000, (1, 256, 256)).astype("float32"),
        mask=numpy.zeros((1, 256, 256), dtype="bool"),
    )
    arr.data[0, 0, 0] = 1.6
    arr.mask[0, 1:100, 1:100] = True

    img = ImageData(arr)
    assert img.array.dtype == numpy.float32

    algo = default_algorithms.get("cast")()
    out = algo(img)
    assert out.array.shape == (1, 256, 256)
    assert out.array.dtype == "uint8"
    assert out.array[0, 0, 0] == 1
    assert out.array[0, 1, 1] is numpy.ma.masked

    assert img.array.dtype == numpy.float32
    algo = default_algorithms.get("floor")()
    out = algo(img)
    assert out.array.shape == (1, 256, 256)
    assert out.array.dtype == "uint8"
    assert out.array[0, 0, 0] == 1
    assert out.array[0, 1, 1] is numpy.ma.masked

    assert img.array.dtype == numpy.float32
    algo = default_algorithms.get("ceil")()
    out = algo(img)
    assert out.array.shape == (1, 256, 256)
    assert out.array.dtype == "uint8"
    assert out.array[0, 0, 0] == 2
    assert out.array[0, 1, 1] is numpy.ma.masked


@pytest.mark.parametrize(
    "name,numpy_method,options",
    [
        ("min", numpy.ma.min, {}),
        ("max", numpy.ma.max, {}),
        ("median", numpy.ma.median, {}),
        ("mean", numpy.ma.mean, {}),
        ("std", numpy.ma.std, {"ddof": 1}),
        ("var", numpy.ma.var, {"ddof": 1}),
        ("sum", numpy.ma.sum, {}),
    ],
)
def test_math_algorithm(name, numpy_method, options):
    """test math algos."""
    arr = numpy.ma.MaskedArray(
        numpy.random.randint(0, 5000, (1, 256, 256)).astype("float32"),
        mask=numpy.zeros((1, 256, 256), dtype="bool"),
    )
    arr.data[0, 0, 0] = 1.6
    arr.mask[0, 1:100, 1:100] = True

    img = ImageData(arr)
    assert img.array.dtype == numpy.float32

    algo = default_algorithms.get(name)()
    out = algo(img)

    numpy.testing.assert_array_equal(
        out.array, numpy_method(img.array, axis=0, keepdims=True, **options)
    )
    assert out.array[0, 1, 1] is numpy.ma.masked
