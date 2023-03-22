"""Test the Algorithms class."""

import json

import numpy
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
        data = img.data * self.factor

        # Create output ImageData
        return ImageData(
            data,
            img.mask,
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
