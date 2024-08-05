"""Test the Algorithms class."""

import json

import numpy
from fastapi import Depends, FastAPI
from rio_tiler.models import ImageData
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
