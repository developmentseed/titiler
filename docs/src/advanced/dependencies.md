
If you are new to the concept of **Dependency Injection**, please read this awesome tutorial: https://fastapi.tiangolo.com/tutorial/dependencies/

In titiler `Factories`, we use the dependencies to define the inputs for each endpoint (and thus the OpenAPI documentation).

Example:
```python
# Custom Dependency

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, FastAPI, Query
from titiler.core.dependencies import DefaultDependency

from rio_tiler.io import COGReader

@dataclass
class ImageParams(DefaultDependency):
    """Common Preview/Crop parameters."""

    max_size: Optional[int] = Query(
        1024, description="Maximum image size to read onto."
    )
    height: Optional[int] = Query(None, description="Force output image height.")
    width: Optional[int] = Query(None, description="Force output image width.")

    def __post_init__(self):
        """Post Init."""
        if self.width and self.height:
            self.max_size = None


app = FastAPI()

# Simple preview endpoint
@app.get("/preview.png")
def preview(
    url: str = Query(..., description="data set URL"),
    params: ImageParams = Depends(),
):

    with COGReader(url) as cog:
        img = cog.preview(**params)  # classes built with `DefaultDependency` can be unpacked
        # or
        img = cog.preview(
            max_size=params.max_size,
            height=params.height,
            width=params.width,
        )
    ...
```

!!! important

    In the example above, we create a custom `ImageParams` dependency which will then be injected to the `preview` endpoint to add  **max_size**, **height** and **width** query string parameters.

    Using `titiler.core.dependencies.DefaultDependency`, we can `unpack` the class as if it was a dictionary, which helps with customization.


## Factories Dependencies

The `factories` allow users to set multiple default dependencies. Here is the list of common dependencies and their **default** values.

### BaseTilerFactory

#### path_dependency

Set dataset path (url).

```python
def DatasetPathParams(
    url: str = Query(..., description="Dataset URL")
) -> str:
    """Create dataset path from args"""
    return url
```

#### layer_dependency

Define band indexes or expression

```python
@dataclass
class BidxParams(DefaultDependency):
    """Band Indexes parameters."""

    indexes: Optional[List[int]] = Query(
        None,
        title="Band indexes",
        alias="bidx",
        description="Dataset band indexes",
        examples={"one-band": {"value": [1]}, "multi-bands": {"value": [1, 2, 3]}},
    )

@dataclass
class ExpressionParams(DefaultDependency):
    """Expression parameters."""

    expression: Optional[str] = Query(
        None,
        title="Band Math expression",
        description="rio-tiler's band math expression",
        examples={
            "simple": {"description": "Simple band math.", "value": "b1/b2"},
            "multi-bands": {
                "description": "Semicolon (;) delimited expressions (band1: b1/b2, band2: b2+b3).",
                "value": "b1/b2;b2+b3",
            },
        },
    )

@dataclass
class BidxExprParams(ExpressionParams, BidxParams):
    """Band Indexes and Expression parameters."""

    pass
```

#### dataset_dependency

Overwrite nodata value, apply rescaling or change default resampling.

```python
@dataclass
class DatasetParams(DefaultDependency):
    """Low level WarpedVRT Optional parameters."""

    nodata: Optional[Union[str, int, float]] = Query(
        None, title="Nodata value", description="Overwrite internal Nodata value"
    )
    unscale: Optional[bool] = Query(
        False,
        title="Apply internal Scale/Offset",
        description="Apply internal Scale/Offset",
    )
    resampling_method: ResamplingName = Query(
        ResamplingName.nearest,  # type: ignore
        alias="resampling",
        description="Resampling method.",
    )

    def __post_init__(self):
        """Post Init."""
        if self.nodata is not None:
            self.nodata = numpy.nan if self.nodata == "nan" else float(self.nodata)
        self.resampling_method = self.resampling_method.value  # type: ignore
```

#### render_dependency

Image rendering options.

```python
@dataclass
class ImageRenderingParams(DefaultDependency):
    """Image Rendering options."""

    add_mask: bool = Query(
        True, alias="return_mask", description="Add mask to the output data."
    )
```

#### colormap_dependency

Colormap options.

```python
def ColorMapParams(
    colormap_name: ColorMapName = Query(None, description="Colormap name"),
    colormap: str = Query(None, description="JSON encoded custom Colormap"),
) -> Optional[Union[Dict, Sequence]]:
    """Colormap Dependency."""
    if colormap_name:
        return cmap.get(colormap_name.value)

    if colormap:
        try:
            return json.loads(
                colormap,
                object_hook=lambda x: {int(k): parse_color(v) for k, v in x.items()},
            )
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400, detail="Could not parse the colormap value."
            )

    return None
```

#### reader_dependency

Additional reader options. Defaults to `DefaultDependency` (empty).


#### Other Attributes

##### Supported TMS

The TMS dependency sets the available TMS for a tile endpoint.

```python
# Allow all morecantile TMS
from morecantile import tms as default_tms

tiler = TilerFactory(supported_tms=default_tms)


# Restrict the TMS to `WebMercatorQuad` only
from morecantile import tms
from morecantile.defaults import TileMatrixSets

# Construct a TileMatrixSets object with only the `WebMercatorQuad` tms
default_tms = TileMatrixSets({"WebMercatorQuad": tms.get("WebMercatorQuad")})
tiler = TilerFactory(supported_tms=default_tms)
```

##### Default TMS

Set the default's TMS Identifier (default to `WebMercatorQuad`).

```python
# Create a Tile with it's default TMS being `WGS1984Quad`
tiler = TilerFactory(default_tms="WGS1984Quad")
```

### TilerFactory

The `TilerFactory` inherits dependency from `BaseTilerFactory`.

#### metadata_dependency

`rio_tiler.io.BaseReader.metadata()` methods options.

```python
@dataclass
class MetadataParams(DefaultDependency):
    """Common Metadada parameters."""

    # Required params
    pmin: float = Query(2.0, description="Minimum percentile")
    pmax: float = Query(98.0, description="Maximum percentile")

    # Optional params
    max_size: Optional[int] = Query(
        None, description="Maximum image size to read onto."
    )
    histogram_bins: Optional[int] = Query(None, description="Histogram bins.")
    histogram_range: Optional[str] = Query(
        None, description="comma (',') delimited Min,Max histogram bounds"
    )
    bounds: Optional[str] = Query(
        None,
        descriptions="comma (',') delimited Bounding box coordinates from which to calculate image statistics.",
    )

    def __post_init__(self):
        """Post Init."""
        if self.max_size is not None:
            self.kwargs["max_size"] = self.max_size

        if self.bounds:
            self.kwargs["bounds"] = tuple(map(float, self.bounds.split(",")))

        hist_options = {}
        if self.histogram_bins:
            hist_options.update(dict(bins=self.histogram_bins))
        if self.histogram_range:
            hist_options.update(
                dict(range=list(map(float, self.histogram_range.split(","))))
            )
        if hist_options:
            self.kwargs["hist_options"] = hist_options
```

#### img_dependency

Used in Crop/Preview to define size of the output image.

```python
@dataclass
class ImageParams(DefaultDependency):
    """Common Preview/Crop parameters."""

    max_size: Optional[int] = Query(
        1024, description="Maximum image size to read onto."
    )
    height: Optional[int] = Query(None, description="Force output image height.")
    width: Optional[int] = Query(None, description="Force output image width.")

    def __post_init__(self):
        """Post Init."""
        if self.width and self.height:
            self.max_size = None
```

### MultiBaseTilerFactory

The `MultiBaseTilerFactory` inherits dependency from `TilerFactory` and `BaseTilerFactory`.

#### assets_dependency

Define `assets`.

```python
@dataclass
class AssetsParams(DefaultDependency):
    """Assets parameters."""

    assets: List[str] = Query(
        None,
        title="Asset names",
        description="Asset's names.",
        examples={
            "one-asset": {
                "description": "Return results for asset `data`.",
                "value": ["data"],
            },
            "multi-assets": {
                "description": "Return results for assets `data` and `cog`.",
                "value": ["data", "cog"],
            },
        },
    )
```

### MultiBandTilerFactory

The `MultiBaseTilerFactory` inherits dependency from `TilerFactory` and `BaseTilerFactory`.

#### bands_dependency

Define `bands`.

```python
@dataclass
class BandsParams(DefaultDependency):
    """Band names parameters."""

    bands: List[str] = Query(
        None,
        title="Band names",
        description="Band's names.",
        examples={
            "one-band": {
                "description": "Return results for band `B01`.",
                "value": ["B01"],
            },
            "multi-bands": {
                "description": "Return results for bands `B01` and `B02`.",
                "value": ["B01", "B02"],
            },
        },
    )
```

### MosaicTilerFactory

The `MultiBaseTilerFactory` inherits dependency from `BaseTilerFactory`.

#### backend_dependency

Additional backend options. Defaults to `DefaultDependency` (empty).
