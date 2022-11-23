

Starting with `titiler>=0.8`, we added the possibility to apply complexes operations on Image outputs from `tile`, `crop` or `preview` endpoints.

We added a set of custom algorithms:

- `hillshade`: Create hillshade from elevation dataset
- `contours`: Create contours lines (raster) from elevation dataset
- `terrarium`: Mapzen's format to encode elevation value in RGB values (https://github.com/tilezen/joerd/blob/master/docs/formats.md#terrarium)
- `terrainrgb`: Mapbox's format to encode elevation value in RGB values (https://docs.mapbox.com/data/tilesets/guides/access-elevation-data/)
- `normalizedIndex`: Normalized Difference Index (e.g NDVI)

### Usage

```python
# return a
httpx.get(
    "http://127.0.0.1:8081/cog/tiles/16/34059/23335",
    params={
        "url": "https://data.geo.admin.ch/ch.swisstopo.swissalti3d/swissalti3d_2019_2573-1085/swissalti3d_2019_2573-1085_0.5_2056_5728.tif",
        "buffer": 3,  # By default hillshade will crop the output with a 3pixel buffer, so we need to apply a buffer on the tile
        "algo": "hillshade",
    },
)
```
<img width="300" src="https://user-images.githubusercontent.com/10407788/203507832-f92a87d3-d8d4-4f44-b3d8-e8989f3cc43b.jpeg"/>

```python
# Pass algorithm parameter as a json string
httpx.get(
    "http://127.0.0.1:8081/cog/preview",
    params={
        "url": "https://data.geo.admin.ch/ch.swisstopo.swissalti3d/swissalti3d_2019_2573-1085/swissalti3d_2019_2573-1085_0.5_2056_5728.tif",
        "algo": "contour",
        "algo_params": json.dumps({"minz": 1600, "maxz": 2100}) # algorithm params HAVE TO be provided as a JSON string
    },
)
```
<img width="300" src="https://user-images.githubusercontent.com/10407788/203510073-d9ff329a-d272-4c34-bf94-4841c68529fe.jpeg"/>



### Create your own Algorithm

A titiler'w `Algorithm` must be defined using `titiler.core.algorithm.BaseAlgorithm` base class.

```python
class BaseAlgorithm(BaseModel, metaclass=abc.ABCMeta):
    """Algorithm baseclass.

    Note: attribute starting with `input_` or `output_` are considered as metadata

    """

    # metadata
    input_nbands: int
    output_nbands: int
    output_dtype: str
    output_min: Optional[Sequence]
    output_max: Optional[Sequence]

    @abc.abstractmethod
    def apply(self, img: ImageData) -> ImageData:
        """Apply algorithm"""
        ...

    class Config:
        """Config for model."""

        extra = "allow"
```

This base class defines that algorithm:

- HAVE TO implement an `apply()` method which takes an ImageData as input and return an ImageData
- can have input/output metadata (Those are moslty informative)
- the `extra = "allow"` means we can add more `parameters` to the class

Here is a simple example of a custom Algorithm:

```python
class Multiply(BaseAlgorithm):

    # Parameters
    factor: int

    def apply(self, img: ImageData) -> ImageData:
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
```

### Order of operation

When creating a map tile (or other images), we will fist apply the `algorithm` then the `rescaling` and finally the `color_formula`.

```python
with reader(url as src_dst:
    image = src_dst.tile(
        x,
        y,
        z,
    )
    dst_colormap = getattr(src_dst, "colormap", None)

# Apply algorithm
if post_process:
    image = post_process.apply(image)

# Apply data rescaling
if rescale:
    image.rescale(rescale)

# Apply color-formula
if color_formula:
    image.apply_color_formula(color_formula)

# Determine the format
if not format:
    format = ImageType.jpeg if image.mask.all() else ImageType.png

# Image Rendering
return image.render(
    img_format=format.driver,
    colormap=colormap or dst_colormap,
    **format.profile,
)
```

## Dependency

To be able to use your own algorithm in titiler's endpoint you need to create a `Dependency` to tell the application what algorithm are available.

```python
from typing import Callable
from titiler.core.algorithm import algorithms as default_algorithms
from titiler.core.algorithm import Algorithms
from titiler.core.factory import TilerFactory

# Add the `Multiply` algorithm to the default ones
algorithms: Algorithms = default_algorithms.register({"multiply": Multiply})

# Create a PostProcessParams dependency
PostProcessParams: Callable = algorithms.dependency

endpoints = TilerFactory(process_dependency=PostProcessParams)
```

The `titiler.core.algorithm.Algorithms` class, which acts as the algorithms store, has a `dependency` property which will return a FastAPI dependency to be added to the endpoints.
