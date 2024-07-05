
If you are new to the concept of **Dependency Injection**, please read this awesome tutorial: https://fastapi.tiangolo.com/tutorial/dependencies/

In titiler `Factories`, we use the dependencies to define the inputs for each endpoint (and thus the OpenAPI documentation).

Example:
```python
from dataclasses import dataclass
from fastapi import Depends, FastAPI, Query
from titiler.core.dependencies import DefaultDependency
from typing_extensions import Annotated
from rio_tiler.io import Reader

@dataclass
class ImageParams(DefaultDependency):
    max_size: Annotated[
        int, Query(description="Maximum image size to read onto.")
    ] = 1024

app = FastAPI()

# Simple preview endpoint
@app.get("/preview.png")
def preview(
    url: str = Query(..., description="data set URL"),
    params: ImageParams = Depends(),
):
    with Reader(url) as cog:
        img = cog.preview(**params.as_dict())  # we use `DefaultDependency().as_dict()` to pass only non-None parameters
        # or
        img = cog.preview(max_size=params.max_size)
    ...
```

!!! important

    In the example above, we create a custom `ImageParams` dependency which will then be injected to the `preview` endpoint to add  **max_size**, **height** and **width** query string parameters.

    Using `titiler.core.dependencies.DefaultDependency`, we can use `.as_dict(exclude_none=True/False)` method to `unpack` the object parameters. This can be useful if method or reader do not take the same parameters.

#### AssetsParams

Define `assets`.

| Name      | Type      | Required | Default
| ------    | ----------|----------|--------------
| **assets** | Query (str) | No | None

<details>

```python
@dataclass
class AssetsParams(DefaultDependency):
    """Assets parameters."""

    assets: List[str] = Query(
        None,
        title="Asset names",
        description="Asset's names.",
        openapi_examples={
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

</details>


#### AssetsBidxParams

Define `assets` with option of `per-asset` expression with `asset_expression` option.

| Name      | Type      | Required | Default
| ------    | ----------|----------|--------------
| **assets** | Query (str) | No | None
| **asset_indexes** | Query (str) | No | None
| **asset_expression** | Query (str) | No | False

<details>

```python
@dataclass
class AssetsBidxParams(AssetsParams):
    """Assets, Asset's band Indexes and Asset's band Expression parameters."""

    asset_indexes: Annotated[
        Optional[Sequence[str]],
        Query(
            title="Per asset band indexes",
            description="Per asset band indexes",
            alias="asset_bidx",
            openapi_examples={
                "one-asset": {
                    "description": "Return indexes 1,2,3 of asset `data`.",
                    "value": ["data|1;2;3"],
                },
                "multi-assets": {
                    "description": "Return indexes 1,2,3 of asset `data` and indexes 1 of asset `cog`",
                    "value": ["data|1;2;3", "cog|1"],
                },
            },
        ),
    ] = None

    asset_expression: Annotated[
        Optional[Sequence[str]],
        Query(
            title="Per asset band expression",
            description="Per asset band expression",
            openapi_examples={
                "one-asset": {
                    "description": "Return results for expression `b1*b2+b3` of asset `data`.",
                    "value": ["data|b1*b2+b3"],
                },
                "multi-assets": {
                    "description": "Return results for expressions `b1*b2+b3` for asset `data` and `b1+b3` for asset `cog`.",
                    "value": ["data|b1*b2+b3", "cog|b1+b3"],
                },
            },
        ),
    ] = None

    def __post_init__(self):
        """Post Init."""
        if self.asset_indexes:
            self.asset_indexes: Dict[str, Sequence[int]] = {  # type: ignore
                idx.split("|")[0]: list(map(int, idx.split("|")[1].split(",")))
                for idx in self.asset_indexes
            }

        if self.asset_expression:
            self.asset_expression: Dict[str, str] = {  # type: ignore
                idx.split("|")[0]: idx.split("|")[1] for idx in self.asset_expression
            }
```

</details>

#### AssetsBidxExprParams

Define `assets`.

| Name      | Type      | Required | Default
| ------    | ----------|----------|--------------
| **assets** | Query (str) | No\* | None
| **expression** | Query (str) | No\* | None
| **asset_indexes** | Query (str) | No | None
| **asset_as_band** | Query (bool) | No | False

\* `assets` or `expression` is required.

<details>

```python
@dataclass
class AssetsBidxExprParams(AssetsParams):
    """Assets, Expression and Asset's band Indexes parameters."""

    expression: Annotated[
        Optional[str],
        Query(
            title="Band Math expression",
            description="Band math expression between assets",
            openapi_examples={
                "simple": {
                    "description": "Return results of expression between assets.",
                    "value": "asset1_b1 + asset2_b1 / asset3_b1",
                },
            },
        ),
    ] = None

    asset_indexes: Annotated[
        Optional[Sequence[str]],
        Query(
            title="Per asset band indexes",
            description="Per asset band indexes (coma separated indexes)",
            alias="asset_bidx",
            openapi_examples={
                "one-asset": {
                    "description": "Return indexes 1,2,3 of asset `data`.",
                    "value": ["data|1,2,3"],
                },
                "multi-assets": {
                    "description": "Return indexes 1,2,3 of asset `data` and indexes 1 of asset `cog`",
                    "value": ["data|1,2,3", "cog|1"],
                },
            },
        ),
    ] = None

    asset_as_band: Annotated[
        Optional[bool],
        Query(
            title="Consider asset as a 1 band dataset",
            description="Asset as Band",
        ),
    ] = None

    def __post_init__(self):
        """Post Init."""
        if not self.assets and not self.expression:
            raise MissingAssets(
                "assets must be defined either via expression or assets options."
            )

        if self.asset_indexes:
            self.asset_indexes: Dict[str, Sequence[int]] = {  # type: ignore
                idx.split("|")[0]: list(map(int, idx.split("|")[1].split(",")))
                for idx in self.asset_indexes
            }
```

</details>

#### AssetsBidxExprParamsOptional

Define `assets`. Without requirement on assets nor expression.

| Name      | Type      | Required | Default
| ------    | ----------|----------|--------------
| **assets** | Query (str) | No | None
| **expression** | Query (str) | No | None
| **asset_indexes** | Query (str) | No | None
| **asset_as_band** | Query (bool) | No | False

<details>

```python
@dataclass
class AssetsBidxExprParamsOptional(AssetsBidxExprParams):
    """Assets, Expression and Asset's band Indexes parameters but with no requirement."""

    def __post_init__(self):
        """Post Init."""
        if self.asset_indexes:
            self.asset_indexes: Dict[str, Sequence[int]] = {  # type: ignore
                idx.split("|")[0]: list(map(int, idx.split("|")[1].split(",")))
                for idx in self.asset_indexes
            }
```

</details>


#### BandsParams

Define `bands`.

| Name      | Type      | Required | Default
| ------    | ----------|----------|--------------
| **bands** | Query (str) | No | None

<details>

```python
@dataclass
class BandsParams(DefaultDependency):
    """Band names parameters."""

    bands: List[str] = Query(
        None,
        title="Band names",
        description="Band's names.",
        openapi_examples={
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

</details>


#### BandsExprParams

Define `bands`.

| Name      | Type      | Required | Default
| ------    | ----------|----------|--------------
| **bands** | Query (str) | No\* | None
| **expression** | Query (str) | No\* | None

\* `bands` or `expression` is required.

<details>

```python
@dataclass
class BandsExprParamsOptional(ExpressionParams, BandsParams):
    """Optional Band names and Expression parameters."""

    pass
```

</details>

#### BandsExprParamsOptional

Define `bands`.

| Name      | Type      | Required | Default
| ------    | ----------|----------|--------------
| **bands** | Query (str) | No | None
| **expression** | Query (str) | No | None

<details>

```python
@dataclass
class BandsExprParamsOptional(ExpressionParams, BandsParams):
    """Optional Band names and Expression parameters."""

    pass
```

</details>

#### `BidxParams`

Define band indexes.

| Name      | Type      | Required | Default
| ------    | ----------|----------|--------------
| **bidx**  | Query (int)    | No       | None

<details>

```python
@dataclass
class BidxParams(DefaultDependency):
    """Band Indexes parameters."""

    indexes: Annotated[
        Optional[List[int]],
        Query(
            title="Band indexes",
            alias="bidx",
            description="Dataset band indexes",
            openapi_examples={"one-band": {"value": [1]}, "multi-bands": {"value": [1, 2, 3]}},
        ),
    ] = None
```

</details>

#### `ExpressionParams`

Define band expression.

| Name      | Type      | Required | Default
| ------    | ----------|----------|--------------
| **expression** | Query (str)    | No       | None


<details>

```python
@dataclass
class ExpressionParams(DefaultDependency):
    """Expression parameters."""

    expression: Annotated[
        Optional[str],
        Query(
            title="Band Math expression",
            description="rio-tiler's band math expression",
            openapi_examples={
                "simple": {"description": "Simple band math.", "value": "b1/b2"},
                "multi-bands": {
                    "description": "Semicolon (;) delimited expressions (band1: b1/b2, band2: b2+b3).",
                    "value": "b1/b2;b2+b3",
                },
            },
        ),
    ] = None
```

</details>

#### `BidxExprParams`

Define band indexes or expression.

| Name      | Type      | Required | Default
| ------    | ----------|----------|--------------
| **bidx**  | Query (int)    | No       | None
| **expression** | Query (str)    | No       | None

<details>

```python
@dataclass
class BidxExprParams(ExpressionParams, BidxParams):
    """Band Indexes and Expression parameters."""

    pass
```

</details>

#### `ColorFormulaParams`

Color Formula option (see https://github.com/vincentsarago/color-operations).

| Name      | Type      | Required | Default
| ------    | ----------|----------|--------------
| **color_formula**  | Query (str)     | No       | None

<details>

```python
def ColorFormulaParams(
    color_formula: Annotated[
        Optional[str],
        Query(
            title="Color Formula",
            description="rio-color formula (info: https://github.com/mapbox/rio-color)",
        ),
    ] = None,
) -> Optional[str]:
    """ColorFormula Parameter."""
    return color_formula
```

</details>

#### `ColorMapParams`

Colormap options. See [titiler.core.dependencies](https://github.com/developmentseed/titiler/blob/e46c35c8927b207f08443a274544901eb9ef3914/src/titiler/core/titiler/core/dependencies.py#L18-L54).

| Name      | Type      | Required | Default
| ------    | ----------|----------|--------------
| **colormap_name**  | Query (str)     | No       | None
| **colormap**  | Query (encoded json)    | No       | None

<details>

```python
cmap = {}

def ColorMapParams(
    colormap_name: Annotated[  # type: ignore
        Literal[tuple(cmap.list())],
        Query(description="Colormap name"),
    ] = None,
    colormap: Annotated[
        Optional[str], Query(description="JSON encoded custom Colormap")
    ] = None,
):
    if colormap_name:
        return cmap.get(colormap_name)

    if colormap:
        try:
            c = json.loads(
                colormap,
                object_hook=lambda x: {
                    int(k): parse_color(v) for k, v in x.items()
                },
            )

            # Make sure to match colormap type
            if isinstance(c, Sequence):
                c = [(tuple(inter), parse_color(v)) for (inter, v) in c]

            return c
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400, detail="Could not parse the colormap value."
            ) from e

    return None
```

</details>

#### CoordCRSParams

Define input Coordinate Reference System.

| Name      | Type      | Required | Default
| ------    | ----------|----------|--------------
| **crs** | Query (str) | No | None


<details>

```python
def CoordCRSParams(
    crs: Annotated[
        Optional[str],
        Query(
            alias="coord_crs",
            description="Coordinate Reference System of the input coords. Default to `epsg:4326`.",
        ),
    ] = None,
) -> Optional[CRS]:
    """Coordinate Reference System Coordinates Param."""
    if crs:
        return CRS.from_user_input(crs)

    return None
```

</details>

#### `DatasetParams`

Overwrite `nodata` value, apply `rescaling` and change the `I/O` or `Warp` resamplings.

| Name      | Type      | Required | Default
| ------    | ----------|----------|--------------
| **nodata**  | Query (str, int, float)    | No       | None
| **unscale** | Query (bool)    | No       | False
| **resampling** | Query (str) | No        | 'nearest'
| **reproject** | Query (str) | No        | 'nearest'

<details>

```python
@dataclass
class DatasetParams(DefaultDependency):
    """Low level WarpedVRT Optional parameters."""

    nodata: Annotated[
        Optional[Union[str, int, float]],
        Query(
            title="Nodata value",
            description="Overwrite internal Nodata value",
        ),
    ] = None
    unscale: Annotated[
        bool,
        Query(
            title="Apply internal Scale/Offset",
            description="Apply internal Scale/Offset. Defaults to `False` in rio-tiler.",
        ),
    ] = False
    resampling_method: Annotated[
        Optional[RIOResampling],
        Query(
            alias="resampling",
            description="RasterIO resampling algorithm. Defaults to `nearest` in rio-tiler.",
        ),
    ] = None
    reproject_method: Annotated[
        Optional[WarpResampling],
        Query(
            alias="reproject",
            description="WarpKernel resampling algorithm (only used when doing re-projection). Defaults to `nearest` in rio-tiler.",
        ),
    ] = None

    def __post_init__(self):
        """Post Init."""
        if self.nodata is not None:
            self.nodata = numpy.nan if self.nodata == "nan" else float(self.nodata)

        if self.unscale is not None:
            self.unscale = bool(self.unscale)
```

</details>

#### `DatasetPathParams`

Set dataset path.

| Name   | Type      | Required             | Default
| ------ | ----------|--------------------- |--------------
| **url**  | Query (str)  | :warning: **Yes**  :warning:  | -


<details>

```python
def DatasetPathParams(
    url: Annotated[str, Query(description="Dataset URL")]
) -> str:
    """Create dataset path from args"""
    return url
```

</details>


#### DstCRSParams

Define output Coordinate Reference System.

| Name      | Type      | Required | Default
| ------    | ----------|----------|--------------
| **crs** | Query (str) | No | None


<details>

```python
def DstCRSParams(
    crs: Annotated[
        Optional[str],
        Query(
            alias="dst_crs",
            description="Output Coordinate Reference System.",
        ),
    ] = None,
) -> Optional[CRS]:
    """Coordinate Reference System Coordinates Param."""
    if crs:
        return CRS.from_user_input(crs)

    return None
```

</details>

#### HistogramParams

Define *numpy*'s histogram options.

| Name      | Type      | Required | Default
| ------    | ----------|----------|--------------
| **histogram_bins** | Query (encoded list of Number) | No | 10
| **histogram_range** | Query (encoded list of Number) | No | None

<details>

```python
@dataclass
class HistogramParams(DefaultDependency):
    """Numpy Histogram options."""

    bins: Annotated[
        Optional[str],
        Query(
            alias="histogram_bins",
            title="Histogram bins.",
            description="""
Defines the number of equal-width bins in the given range (10, by default).

If bins is a sequence (comma `,` delimited values), it defines a monotonically increasing array of bin edges, including the rightmost edge, allowing for non-uniform bin widths.

link: https://numpy.org/doc/stable/reference/generated/numpy.histogram.html
            """,
            openapi_examples={
                "simple": {
                    "description": "Defines the number of equal-width bins",
                    "value": 8,
                },
                "array": {
                    "description": "Defines custom bin edges (comma `,` delimited values)",
                    "value": "0,100,200,300",
                },
            },
        ),
    ] = None

    range: Annotated[
        Optional[str],
        Query(
            alias="histogram_range",
            title="Histogram range",
            description="""
Comma `,` delimited range of the bins.

The lower and upper range of the bins. If not provided, range is simply (a.min(), a.max()).

Values outside the range are ignored. The first element of the range must be less than or equal to the second.
range affects the automatic bin computation as well.

link: https://numpy.org/doc/stable/reference/generated/numpy.histogram.html
            """,
            examples="0,1000",
        ),
    ] = None

    def __post_init__(self):
        """Post Init."""
        if self.bins:
            bins = self.bins.split(",")
            if len(bins) == 1:
                self.bins = int(bins[0])  # type: ignore
            else:
                self.bins = list(map(float, bins))  # type: ignore
        else:
            self.bins = 10

        if self.range:
            self.range = list(map(float, self.range.split(",")))  # type: ignore
```

</details>

#### `ImageRenderingParams`

Control output image rendering options.

| Name      | Type      | Required | Default
| ------    | ----------|----------|--------------
| **return_mask**  | Query (bool)     | No       | False

<details>

```python
@dataclass
class ImageRenderingParams(DefaultDependency):
    """Image Rendering options."""

    add_mask: Annotated[
        Optional[bool],
        Query(
            alias="return_mask",
            description="Add mask to the output data. Defaults to `True` in rio-tiler",
        ),
    ] = None
```

</details>

#### PartFeatureParams

Same as `PreviewParams` but without default `max_size`.

| Name      | Type      | Required | Default
| ------    | ----------|----------|--------------
| **max_size** | Query (int) | No | None
| **height** | Query (int) | No | None
| **width** | Query (int) | No | None

<details>

```python
@dataclass
class PartFeatureParams(DefaultDependency):
    """Common parameters for bbox and feature."""

    max_size: Annotated[Optional[int], "Maximum image size to read onto."] = None
    height: Annotated[Optional[int], "Force output image height."] = None
    width: Annotated[Optional[int], "Force output image width."] = None

    def __post_init__(self):
        """Post Init."""
        if self.width and self.height:
            self.max_size = None
```

</details>

#### PixelSelectionParams

In `titiler.mosaic`, define pixel-selection method to apply.

| Name      | Type      | Required | Default
| ------    | ----------|----------|--------------
| **pixel_selection** | Query (str) | No | 'first'


<details>

```python
def PixelSelectionParams(
    pixel_selection: Annotated[  # type: ignore
        Literal[tuple([e.name for e in PixelSelectionMethod])],
        Query(description="Pixel selection method."),
    ] = "first",
) -> MosaicMethodBase:
    """
    Returns the mosaic method used to combine datasets together.
    """
    return PixelSelectionMethod[pixel_selection].value()
```

</details>

#### PreviewParams

Define image output size.

| Name      | Type      | Required | Default
| ------    | ----------|----------|--------------
| **max_size** | Query (int) | No | 1024
| **height** | Query (int) | No | None
| **width** | Query (int) | No | None

<details>

```python
@dataclass
class PreviewParams(DefaultDependency):
    """Common Preview parameters."""

    max_size: Annotated[int, "Maximum image size to read onto."] = 1024
    height: Annotated[Optional[int], "Force output image height."] = None
    width: Annotated[Optional[int], "Force output image width."] = None

    def __post_init__(self):
        """Post Init."""
        if self.width and self.height:
            self.max_size = None
```

</details>

#### `RescalingParams`

Set Min/Max values to rescale from, to 0 -> 255.

| Name      | Type      | Required | Default
| ------    | ----------|----------|--------------
| **rescale**  | Query (str, comma delimited Numer)     | No       | None

<details>

```python
def RescalingParams(
    rescale: Annotated[
        Optional[List[str]],
        Query(
            title="Min/Max data Rescaling",
            description="comma (',') delimited Min,Max range. Can set multiple time for multiple bands.",
            examples=["0,2000", "0,1000", "0,10000"],  # band 1  # band 2  # band 3
        ),
    ] = None,
) -> Optional[RescaleType]:
    """Min/Max data Rescaling"""
    if rescale:
        return [tuple(map(float, r.replace(" ", "").split(","))) for r in rescale]

    return None
```

</details>

#### StatisticsParams

Define options for *rio-tiler*'s statistics method.

| Name      | Type      | Required | Default
| ------    | ----------|----------|--------------
| **categorical**  | Query (bool)     | No       | False
| **categories** | Query (list of Number) | No | None
| **p** | Query (list of Number) | No | [2, 98]

<details>

```python
@dataclass
class StatisticsParams(DefaultDependency):
    """Statistics options."""

    categorical: Annotated[
        Optional[bool],
        Query(description="Return statistics for categorical dataset. Defaults to `False` in rio-tiler"),
    ] = None
    categories: Annotated[
        Optional[List[Union[float, int]]],
        Query(
            alias="c",
            title="Pixels values for categories.",
            description="List of values for which to report counts.",
            examples=[1, 2, 3],
        ),
    ] = None
    percentiles: Annotated[
        Optional[List[int]],
        Query(
            alias="p",
            title="Percentile values",
            description="List of percentile values (default to [2, 98]).",
            examples=[2, 5, 95, 98],
        ),
    ] = None

    def __post_init__(self):
        """Set percentiles default."""
        if not self.percentiles:
            self.percentiles = [2, 98]
```

</details>

#### TileParams

Defile `buffer` and `padding` to apply at tile creation.

| Name      | Type      | Required | Default
| ------    | ----------|----------|--------------
| **buffer** | Query (float) | No | None
| **padding** | Query (int) | No | None

<details>

```python
@dataclass
class TileParams(DefaultDependency):
    """Tile options."""

    buffer: Annotated[
        Optional[float],
        Query(
            gt=0,
            title="Tile buffer.",
            description="Buffer on each side of the given tile. It must be a multiple of `0.5`. Output **tilesize** will be expanded to `tilesize + 2 * buffer` (e.g 0.5 = 257x257, 1.0 = 258x258).",
        ),
    ] = None

    padding: Annotated[
        Optional[int],
        Query(
            gt=0,
            title="Tile padding.",
            description="Padding to apply to each tile edge. Helps reduce resampling artefacts along edges. Defaults to `0`.",
        ),
    ] = None
```

</details>

#### `algorithm.dependency`

Control which `algorithm` to apply to the data.

See [titiler.core.algorithm](https://github.com/developmentseed/titiler/blob/e46c35c8927b207f08443a274544901eb9ef3914/src/titiler/core/titiler/core/algorithm/__init__.py#L54-L79).

| Name      | Type      | Required | Default
| ------    | ----------|----------|--------------
| **algorithm**  | Query (str)    | No       | None
| **algorithm_params** | Query (encoded json)     | No       | None

<details>

```python
algorithms = {}

def post_process(
    algorithm: Annotated[
        Literal[tuple(algorithms.keys())],
        Query(description="Algorithm name"),
    ] = None,
    algorithm_params: Annotated[
        Optional[str],
        Query(description="Algorithm parameter"),
    ] = None,
) -> Optional[BaseAlgorithm]:
    """Data Post-Processing options."""
    kwargs = json.loads(algorithm_params) if algorithm_params else {}
    if algorithm:
        try:
            return algorithms.get(algorithm)(**kwargs)

        except ValidationError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    return None
```

</details>

