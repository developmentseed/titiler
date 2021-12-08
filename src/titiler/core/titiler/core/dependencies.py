"""Common dependency."""

import json
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Sequence, Union

import numpy
from morecantile import tms
from morecantile.models import TileMatrixSet
from rasterio.enums import Resampling
from rio_tiler.colormap import cmap, parse_color
from rio_tiler.errors import MissingAssets, MissingBands
from rio_tiler.types import ColorMapType

from fastapi import HTTPException, Query

ColorMapName = Enum(  # type: ignore
    "ColorMapName", [(a, a) for a in sorted(cmap.list())]
)
ResamplingName = Enum(  # type: ignore
    "ResamplingName", [(r.name, r.name) for r in Resampling]
)
WebMercatorTileMatrixSetName = Enum(  # type: ignore
    "WebMercatorTileMatrixSetName", [("WebMercatorQuad", "WebMercatorQuad")]
)
TileMatrixSetName = Enum(  # type: ignore
    "TileMatrixSetName", [(a, a) for a in sorted(tms.list())]
)


def WebMercatorTMSParams(
    TileMatrixSetId: WebMercatorTileMatrixSetName = Query(
        WebMercatorTileMatrixSetName.WebMercatorQuad,  # type: ignore
        description="TileMatrixSet Name (default: 'WebMercatorQuad')",
    )
) -> TileMatrixSet:
    """TileMatrixSet Dependency."""
    return tms.get(TileMatrixSetId.name)


def TMSParams(
    TileMatrixSetId: TileMatrixSetName = Query(
        TileMatrixSetName.WebMercatorQuad,  # type: ignore
        description="TileMatrixSet Name (default: 'WebMercatorQuad')",
    )
) -> TileMatrixSet:
    """TileMatrixSet Dependency."""
    return tms.get(TileMatrixSetId.name)


def ColorMapParams(
    colormap_name: ColorMapName = Query(None, description="Colormap name"),
    colormap: str = Query(None, description="JSON encoded custom Colormap"),
) -> Optional[ColorMapType]:
    """Colormap Dependency."""
    if colormap_name:
        return cmap.get(colormap_name.value)

    if colormap:
        try:
            c = json.loads(
                colormap,
                object_hook=lambda x: {int(k): parse_color(v) for k, v in x.items()},
            )
            # Make sure to match colormap type
            if isinstance(c, Sequence):
                c = [(tuple(inter), parse_color(v)) for (inter, v) in c]
            return c
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400, detail="Could not parse the colormap value."
            )

    return None


def DatasetPathParams(url: str = Query(..., description="Dataset URL")) -> str:
    """Create dataset path from args"""
    return url


@dataclass
class DefaultDependency:
    """Dataclass with dict unpacking"""

    def keys(self):
        """Return Keys."""
        return self.__dict__.keys()

    def __getitem__(self, key):
        """Return value."""
        return self.__dict__[key]


# Dependencies for simple BaseReader (e.g COGReader)
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
                "description": "Coma (,) delimited expressions (band1: b1/b2, band2: b2+b3).",
                "value": "b1/b2,b2+b3",
            },
        },
    )


@dataclass
class BidxExprParams(ExpressionParams, BidxParams):
    """Band Indexes and Expression parameters."""

    pass


# Dependencies for  MultiBaseReader (e.g STACReader)
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


@dataclass
class AssetsBidxExprParams(DefaultDependency):
    """Assets, Band Indexes and Expression parameters."""

    assets: Optional[List[str]] = Query(
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
    expression: Optional[str] = Query(
        None,
        title="Band Math expression",
        description="Band math expression between assets",
        examples={
            "simple": {
                "description": "Return results of expression between assets.",
                "value": "asset1 + asset2 / asset3",
            },
        },
    )

    asset_indexes: Optional[Sequence[str]] = Query(
        None,
        title="Per asset band indexes",
        description="Per asset band indexes",
        alias="asset_bidx",
        examples={
            "one-asset": {
                "description": "Return indexes 1,2,3 of asset `data`.",
                "value": ["data|1,2,3"],
            },
            "multi-assets": {
                "description": "Return indexes 1,2,3 of asset `data` and indexes 1 of asset `cog`",
                "value": ["data|1,2,3", "cog|1"],
            },
        },
    )

    asset_expression: Optional[Sequence[str]] = Query(
        None,
        title="Per asset band expression",
        description="Per asset band expression",
        examples={
            "one-asset": {
                "description": "Return results for expression `b1*b2+b3` of asset `data`.",
                "value": ["data|b1*b2+b3"],
            },
            "multi-assets": {
                "description": "Return results for expressions `b1*b2+b3` for asset `data` and `b1+b3` for asset `cog`.",
                "value": ["data|b1*b2+b3", "cog|b1+b3"],
            },
        },
    )

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

        if self.asset_expression:
            self.asset_expression: Dict[str, str] = {  # type: ignore
                idx.split("|")[0]: idx.split("|")[1] for idx in self.asset_expression
            }


@dataclass
class AssetsBidxParams(AssetsParams):
    """asset and extra."""

    asset_indexes: Optional[Sequence[str]] = Query(
        None,
        title="Per asset band indexes",
        description="Per asset band indexes",
        alias="asset_bidx",
        examples={
            "one-asset": {
                "description": "Return indexes 1,2,3 of asset `data`.",
                "value": ["data|1,2,3"],
            },
            "multi-assets": {
                "description": "Return indexes 1,2,3 of asset `data` and indexes 1 of asset `cog`",
                "value": ["data|1,2,3", "cog|1"],
            },
        },
    )

    asset_expression: Optional[Sequence[str]] = Query(
        None,
        title="Per asset band expression",
        description="Per asset band expression",
        examples={
            "one-asset": {
                "description": "Return results for expression `b1*b2+b3` of asset `data`.",
                "value": ["data|b1*b2+b3"],
            },
            "multi-assets": {
                "description": "Return results for expressions `b1*b2+b3` for asset `data` and `b1+b3` for asset `cog`.",
                "value": ["data|b1*b2+b3", "cog|b1+b3"],
            },
        },
    )

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


# Dependencies for  MultiBandReader
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


@dataclass
class ImageRenderingParams(DefaultDependency):
    """Image Rendering options."""

    add_mask: bool = Query(
        True, alias="return_mask", description="Add mask to the output data."
    )


@dataclass
class PostProcessParams(DefaultDependency):
    """Data Post-Processing options."""

    in_range: Optional[List[str]] = Query(
        None,
        alias="rescale",
        title="Min/Max data Rescaling",
        description="comma (',') delimited Min,Max range. Can set multiple time for multiple bands.",
        example=["0,2000", "0,1000", "0,10000"],  # band 1  # band 2  # band 3
    )
    color_formula: Optional[str] = Query(
        None,
        title="Color Formula",
        description="rio-color formula (info: https://github.com/mapbox/rio-color)",
    )

    def __post_init__(self):
        """Post Init."""
        if self.in_range:
            self.in_range = [  # type: ignore
                tuple(map(float, r.replace(" ", "").split(","))) for r in self.in_range
            ]


@dataclass
class StatisticsParams(DefaultDependency):
    """Statistics options."""

    categorical: bool = Query(
        False, description="Return statistics for categorical dataset."
    )
    categories: List[Union[float, int]] = Query(
        None,
        alias="c",
        title="Pixels values for categories.",
        description="List of values for which to report counts.",
        example=[1, 2, 3],
    )
    percentiles: List[int] = Query(
        [2, 98],
        alias="p",
        title="Percentile values",
        description="List of percentile values.",
        example=[2, 5, 95, 98],
    )


@dataclass
class HistogramParams(DefaultDependency):
    """Numpy Histogram options."""

    bins: Optional[str] = Query(
        None,
        alias="histogram_bins",
        title="Histogram bins.",
        description="""
Defines the number of equal-width bins in the given range (10, by default).

If bins is a sequence (comma `,` delimited values), it defines a monotonically increasing array of bin edges, including the rightmost edge, allowing for non-uniform bin widths.

link: https://numpy.org/doc/stable/reference/generated/numpy.histogram.html
        """,
        examples={
            "simple": {
                "description": "Defines the number of equal-width bins",
                "value": 8,
            },
            "array": {
                "description": "Defines custom bin edges (comma `,` delimited values)",
                "value": "0,100,200,300",
            },
        },
    )

    range: Optional[str] = Query(
        None,
        alias="histogram_range",
        title="Histogram range",
        description="""
Comma `,` delimited range of the bins.

The lower and upper range of the bins. If not provided, range is simply (a.min(), a.max()).

Values outside the range are ignored. The first element of the range must be less than or equal to the second.
range affects the automatic bin computation as well.

link: https://numpy.org/doc/stable/reference/generated/numpy.histogram.html
        """,
        example="0,1000",
    )

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
