
**Goal**: add custom Algorithm to a tiler

**requirements**: titiler.core


1 - Create a custom algorithm and register it to the list of available algorithms

```python
"""algos.

app/algorithms.py

"""
from titiler.core.algorithm import BaseAlgorithm
from titiler.core.algorithm import algorithms as default_algorithms

from rio_tiler.models import ImageData


class Multiply(BaseAlgorithm):

    # Parameters
    factor: int # There is no default, which means calls to this algorithm without any parameter will fail

    # We don't set any metadata for this Algorithm

    def __call__(self, img: ImageData) -> ImageData:
        # Multiply image data bcy factor
        data = img.data * self.factor

        # Create output ImageData
        return ImageData(
            data,
            assets=img.assets,
            crs=img.crs,
            bounds=img.bounds,
        )

# default_algorithms is a `titiler.core.algorithm.Algorithms` Object
algorithms = default_algorithms.register(
    {
        "multiply": Multiply,
    }
)

```

2 - Create application and register endpoints

```python
"""application.

app/app.py

"""
from fastapi import FastAPI
from titiler.core.factory import TilerFactory

from .algorithms import algorithms


app = FastAPI(title="My simple app with custom Algorithm")

# The Algorithms class (titiler.core.algorithm.algorithms) as a `dependency` property which return a process_dependency.
tiler = TilerFactory(process_dependency=algorithms.dependency)
app.include_router(tiler.router)
```
