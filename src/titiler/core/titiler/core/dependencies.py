"""Common dependency."""

import json
import warnings
from dataclasses import dataclass
from typing import Callable, Dict, List, Literal, Optional, Sequence, Tuple, Union

import numpy
from fastapi import HTTPException, Query
from rasterio.crs import CRS
from rio_tiler.colormap import ColorMaps
from rio_tiler.colormap import cmap as default_cmap
from rio_tiler.colormap import parse_color
from rio_tiler.errors import MissingAssets, MissingBands
from rio_tiler.types import RIOResampling, WarpResampling
from typing_extensions import Annotated


def create_colormap_dependency(cmap: ColorMaps) -> Callable:
    """Create Colormap Dependency."""

    def deps(
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

    return deps


ColorMapParams = create_colormap_dependency(default_cmap)


def DatasetPathParams(url: Annotated[str, Query(description="Dataset URL")]) -> str:
    """Create dataset path from args"""
    return url


@dataclass
class DefaultDependency:
    """Dataclass with dict unpacking"""

    def keys(self):
        """Return Keys."""
        warnings.warn(
            "Dict unpacking will be removed for `DefaultDependency` in titiler 0.19.0",
            DeprecationWarning,
        )
        return self.__dict__.keys()

    def __getitem__(self, key):
        """Return value."""
        return self.__dict__[key]

    def as_dict(self, exclude_none: bool = True) -> Dict:
        """Transform dataclass to dict."""
        if exclude_none:
            return {k: v for k, v in self.__dict__.items() if v is not None}

        return dict(self.__dict__.items())


# Dependencies for simple BaseReader (e.g COGReader)
@dataclass
class BidxParams(DefaultDependency):
    """Band Indexes parameters."""

    indexes: Annotated[
        Optional[List[int]],
        Query(
            title="Band indexes",
            alias="bidx",
            description="Dataset band indexes",
            openapi_examples={
                "one-band": {"value": [1]},
                "multi-bands": {"value": [1, 2, 3]},
            },
        ),
    ] = None


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


@dataclass
class BidxExprParams(ExpressionParams, BidxParams):
    """Band Indexes and Expression parameters."""

    pass


# Dependencies for  MultiBaseReader (e.g STACReader)
@dataclass
class AssetsParams(DefaultDependency):
    """Assets parameters."""

    assets: Annotated[
        Optional[List[str]],
        Query(
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
        ),
    ] = None


def parse_asset_indexes(
    asset_indexes: Union[Sequence[str], Dict[str, Sequence[int]]],
) -> Dict[str, Sequence[int]]:
    """parse asset indexes parameters."""
    return {
        idx.split("|")[0]: list(map(int, idx.split("|")[1].split(",")))
        for idx in asset_indexes
    }


def parse_asset_expression(
    asset_expression: Union[Sequence[str], Dict[str, str]],
) -> Dict[str, str]:
    """parse asset expression parameters."""
    return {idx.split("|")[0]: idx.split("|")[1] for idx in asset_expression}


@dataclass
class AssetsBidxExprParams(AssetsParams, BidxParams):
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
            self.asset_indexes = parse_asset_indexes(self.asset_indexes)

        if self.asset_indexes and self.indexes:
            warnings.warn(
                "Both `asset_bidx` and `bidx` passed; only `asset_bidx` will be considered.",
                UserWarning,
            )


@dataclass
class AssetsBidxExprParamsOptional(AssetsBidxExprParams):
    """Assets, Expression and Asset's band Indexes parameters but with no requirement."""

    def __post_init__(self):
        """Post Init."""
        if self.asset_indexes:
            self.asset_indexes = parse_asset_indexes(self.asset_indexes)

        if self.asset_indexes and self.indexes:
            warnings.warn(
                "Both `asset_bidx` and `bidx` passed; only `asset_bidx` will be considered.",
                UserWarning,
            )


@dataclass
class AssetsBidxParams(AssetsParams, BidxParams):
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
            self.asset_indexes = parse_asset_indexes(self.asset_indexes)

        if self.asset_expression:
            self.asset_expression = parse_asset_expression(self.asset_expression)

        if self.asset_indexes and self.indexes:
            warnings.warn(
                "Both `asset_bidx` and `bidx` passed; only `asset_bidx` will be considered.",
                UserWarning,
            )


# Dependencies for  MultiBandReader
@dataclass
class BandsParams(DefaultDependency):
    """Band names parameters."""

    bands: Annotated[
        Optional[List[str]],
        Query(
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
        ),
    ] = None


@dataclass
class BandsExprParamsOptional(ExpressionParams, BandsParams):
    """Optional Band names and Expression parameters."""

    pass


@dataclass
class BandsExprParams(ExpressionParams, BandsParams):
    """Band names and Expression parameters (Band or Expression required)."""

    def __post_init__(self):
        """Post Init."""
        if not self.bands and not self.expression:
            raise MissingBands(
                "bands must be defined either via expression or bands options."
            )


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
        Optional[bool],
        Query(
            title="Apply internal Scale/Offset",
            description="Apply internal Scale/Offset. Defaults to `False`.",
        ),
    ] = None
    resampling_method: Annotated[
        Optional[RIOResampling],
        Query(
            alias="resampling",
            description="RasterIO resampling algorithm. Defaults to `nearest`.",
        ),
    ] = None
    reproject_method: Annotated[
        Optional[WarpResampling],
        Query(
            alias="reproject",
            description="WarpKernel resampling algorithm (only used when doing re-projection). Defaults to `nearest`.",
        ),
    ] = None

    def __post_init__(self):
        """Post Init."""
        if self.nodata is not None:
            self.nodata = numpy.nan if self.nodata == "nan" else float(self.nodata)

        if self.unscale is not None:
            self.unscale = bool(self.unscale)


@dataclass
class ImageRenderingParams(DefaultDependency):
    """Image Rendering options."""

    add_mask: Annotated[
        Optional[bool],
        Query(
            alias="return_mask",
            description="Add mask to the output data. Defaults to `True`",
        ),
    ] = None


RescaleType = List[Tuple[float, ...]]


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
        rescale_array = []
        for r in rescale:
            parsed = tuple(
                map(
                    float,
                    r.replace(" ", "").replace("[", "").replace("]", "").split(","),
                )
            )
            assert (
                len(parsed) == 2
            ), f"Invalid rescale values: {rescale}, should be of form ['min,max', 'min,max'] or [[min,max], [min, max]]"
            rescale_array.append(parsed)

        return rescale_array

    return None


@dataclass
class StatisticsParams(DefaultDependency):
    """Statistics options."""

    categorical: Annotated[
        Optional[bool],
        Query(
            description="Return statistics for categorical dataset. Defaults to `False`"
        ),
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
            parsed = list(map(float, self.range.split(",")))
            assert (
                len(parsed) == 2
            ), f"Invalid histogram_range values: {self.range}, should be of form 'min,max'"

            self.range = parsed  # type: ignore


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


def BufferParams(
    buffer: Annotated[
        Optional[float],
        Query(
            gt=0,
            title="Tile buffer.",
            description="Buffer on each side of the given tile. It must be a multiple of `0.5`. Output **tilesize** will be expanded to `tilesize + 2 * buffer` (e.g 0.5 = 257x257, 1.0 = 258x258).",
        ),
    ] = None,
) -> Optional[float]:
    """Tile buffer Parameter."""
    return buffer


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
