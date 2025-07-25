"""Common dependency."""

import json
import warnings
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Literal, Optional, Sequence, Tuple, Union

import numpy
from fastapi import HTTPException, Query
from pydantic import Field
from rasterio.crs import CRS
from rio_tiler.colormap import ColorMaps
from rio_tiler.colormap import cmap as default_cmap
from rio_tiler.colormap import parse_color
from rio_tiler.errors import MissingAssets, MissingBands
from rio_tiler.types import RIOResampling, WarpResampling
from starlette.requests import Request
from typing_extensions import Annotated

from titiler.core.resources.enums import ImageType, MediaType
from titiler.core.utils import accept_media_type


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
                "user-provided": {"value": None},
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
                "user-provided": {"value": None},
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
                "user-provided": {"value": None},
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
                "user-provided": {"value": None},
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
                "user-provided": {"value": None},
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
                stacklevel=1,
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
                stacklevel=1,
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
                "user-provided": {"value": None},
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
                "user-provided": {"value": None},
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
                stacklevel=1,
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
                "user-provided": {"value": None},
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

    # NOTE: sizes dependency can either be a Query or a Path Parameter
    max_size: Annotated[int, Field(description="Maximum image size to read onto.")] = (
        1024
    )
    height: Annotated[
        Optional[int], Field(description="Force output image height.")
    ] = None
    width: Annotated[Optional[int], Field(description="Force output image width.")] = (
        None
    )

    def __post_init__(self):
        """Post Init."""
        if self.width or self.height:
            self.max_size = None


@dataclass
class PartFeatureParams(DefaultDependency):
    """Common parameters for bbox and feature."""

    # NOTE: the part sizes dependency can either be a Query or a Path Parameter
    max_size: Annotated[
        Optional[int], Field(description="Maximum image size to read onto.")
    ] = None
    height: Annotated[
        Optional[int], Field(description="Force output image height.")
    ] = None
    width: Annotated[Optional[int], Field(description="Force output image width.")] = (
        None
    )

    def __post_init__(self):
        """Post Init."""
        if self.width or self.height:
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


RescaleType = List[Tuple[float, float]]


@dataclass
class RenderingParams(DefaultDependency):
    """Image Rendering options."""

    rescale: Annotated[
        Optional[List[str]],
        Query(
            title="Min/Max data Rescaling",
            description="comma (',') delimited Min,Max range. Can set multiple time for multiple bands.",
            examples=["0,2000", "0,1000", "0,10000"],  # band 1  # band 2  # band 3
        ),
    ] = None

    color_formula: Annotated[
        Optional[str],
        Query(
            title="Color Formula",
            description="rio-color formula (info: https://github.com/mapbox/rio-color)",
        ),
    ] = None

    def __post_init__(self) -> None:
        """Post Init."""
        if self.rescale:
            rescale_array = []
            for r in self.rescale:
                parsed = tuple(
                    map(
                        float,
                        r.replace(" ", "").replace("[", "").replace("]", "").split(","),
                    )
                )
                assert (
                    len(parsed) == 2
                ), f"Invalid rescale values: {self.rescale}, should be of form ['min,max', 'min,max'] or [[min,max], [min, max]]"
                rescale_array.append(parsed)

            self.rescale: RescaleType = rescale_array  # type: ignore


@dataclass
class ImageRenderingParams(RenderingParams):
    """Image Rendering options."""

    add_mask: Annotated[
        Optional[bool],
        Query(
            alias="return_mask",
            description="Add mask to the output data. Defaults to `True`",
        ),
    ] = None


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
                "user-provided": {"value": None},
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


def CRSParams(
    crs: Annotated[
        Optional[str],
        Query(
            description="Coordinate Reference System.",
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


@dataclass
class OGCMapsParams(DefaultDependency):
    """OGC Maps options."""

    request: Request

    bbox: Annotated[
        Optional[str],
        Query(
            description="Bounding box of the rendered map. The bounding box is provided as four or six coordinates.",
        ),
    ] = None

    crs: Annotated[
        Optional[str],
        Query(
            description="Reproject the output to the given crs.",
        ),
    ] = None

    bbox_crs: Annotated[
        Optional[str],
        Query(
            description="crs for the specified bbox.",
            alias="bbox-crs",
        ),
    ] = None

    height: Annotated[
        Optional[int],
        Query(
            description="Height of the map in pixels. If omitted and `width` is specified, defaults to the `height` maintaining a 1:1 aspect ratio. If both `width` and `height` are omitted, the server will select default dimensions.",
            gt=0,
        ),
    ] = None

    width: Annotated[
        Optional[int],
        Query(
            description="Width of the map in pixels. If omitted and `height` is specified, defaults to the `width` maintaining a 1:1 aspect ratio. If both `width` and `height` are omitted, the server will select default dimensions.",
            gt=0,
        ),
    ] = None

    f: Annotated[
        Optional[ImageType],
        Query(description="The format of the map response (e.g. png)."),
    ] = None

    max_size: Optional[int] = field(init=False, default=None)

    format: Optional[ImageType] = field(init=False, default=ImageType.png)

    def __post_init__(self):  # noqa: C901
        """Parse and validate."""
        if self.crs:
            if self.crs.startswith("[") and self.crs.endswith("]"):
                self.crs = self.crs[1:-1]
            self.crs = CRS.from_user_input(self.crs)  # type: ignore

        if self.bbox_crs:
            if self.bbox_crs.startswith("[") and self.bbox_crs.endswith("]"):
                self.bbox_crs = self.bbox_crs[1:-1]
            self.bbox_crs = CRS.from_user_input(self.bbox_crs)  # type: ignore

        if not self.height and not self.width:
            self.max_size = 1024

        if self.bbox:
            bounds = list(map(float, self.bbox.split(",")))
            if len(bounds) == 6:
                bounds = [bounds[0], bounds[1], bounds[3], bounds[4]]

            self.bbox = bounds  # type: ignore

        if self.f:
            self.format = ImageType[self.f]

        else:
            if media := accept_media_type(
                self.request.headers.get("accept", ""),
                [MediaType[e] for e in ImageType],
            ):
                self.format = ImageType[media.name]
