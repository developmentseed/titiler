"""Common dependency."""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

import numpy
from morecantile import tms
from morecantile.models import TileMatrixSet
from rasterio.enums import Resampling
from rio_tiler.colormap import cmap

from .custom import cmap as custom_colormap
from .custom import tms as custom_tms
from .utils import get_hash

from fastapi import Query

from starlette.requests import Request

################################################################################
#                       CMAP AND TMS Customization
tms = tms.register([custom_tms.EPSG3413, custom_tms.EPSG6933])

cmap = cmap.register({"above": custom_colormap.above_cmap})

################################################################################
# DO NOT UPDATE
# Create ENUMS with all CMAP and TMS for documentation and validation.
ColorMapNames = Enum(  # type: ignore
    "ColorMapNames", [(a, a) for a in sorted(cmap.list())]
)
ResamplingNames = Enum(  # type: ignore
    "ResamplingNames", [(r.name, r.name) for r in Resampling]
)
WebMercatorTileMatrixSetName = Enum(  # type: ignore
    "WebMercatorTileMatrixSetName", [("WebMercatorQuad", "WebMercatorQuad")]
)
TileMatrixSetNames = Enum(  # type: ignore
    "TileMatrixSetNames", [(a, a) for a in sorted(tms.list())]
)


async def request_hash(request: Request) -> str:
    """Create SHA224 id from reuqest."""
    return get_hash(**dict(request.query_params), **request.path_params)


def WebMercatorTMSParams(
    TileMatrixSetId: WebMercatorTileMatrixSetName = Query(
        WebMercatorTileMatrixSetName.WebMercatorQuad,  # type: ignore
        description="TileMatrixSet Name (default: 'WebMercatorQuad')",
    )
) -> TileMatrixSet:
    """TileMatrixSet Dependency."""
    return tms.get(TileMatrixSetId.name)


def TMSParams(
    TileMatrixSetId: TileMatrixSetNames = Query(
        TileMatrixSetNames.WebMercatorQuad,  # type: ignore
        description="TileMatrixSet Name (default: 'WebMercatorQuad')",
    )
) -> TileMatrixSet:
    """TileMatrixSet Dependency."""
    return tms.get(TileMatrixSetId.name)


@dataclass
class DefaultDependency:
    """Dependency Base Class"""

    kwargs: dict = field(init=False, default_factory=dict)


@dataclass
class PathParams:
    """Create dataset path from args"""

    url: str = Query(..., description="Dataset URL")


@dataclass
class BidxParams(DefaultDependency):
    """Band Indexes parameters."""

    bidx: Optional[str] = Query(
        None, title="Band indexes", description="comma (',') delimited band indexes",
    )

    def __post_init__(self):
        """Post Init."""
        if self.bidx is not None:
            self.kwargs["indexes"] = tuple(
                int(s) for s in re.findall(r"\d+", self.bidx)
            )


@dataclass
class BidxExprParams(DefaultDependency):
    """Band Indexes and Expression parameters."""

    bidx: Optional[str] = Query(
        None, title="Band indexes", description="comma (',') delimited band indexes",
    )
    expression: Optional[str] = Query(
        None,
        title="Band Math expression",
        description="rio-tiler's band math expression (e.g B1/B2)",
    )

    def __post_init__(self):
        """Post Init."""
        if self.bidx is not None:
            self.kwargs["indexes"] = tuple(
                int(s) for s in re.findall(r"\d+", self.bidx)
            )

        if self.expression is not None:
            self.kwargs["expression"] = self.expression


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

        if self.width is not None:
            self.kwargs["width"] = self.width

        if self.height is not None:
            self.kwargs["height"] = self.height

        if self.max_size is not None:
            self.kwargs["max_size"] = self.max_size


@dataclass
class DatasetParams(DefaultDependency):
    """Low level WarpedVRT Optional parameters."""

    nodata: Optional[Union[str, int, float]] = Query(
        None, title="Nodata value", description="Overwrite internal Nodata value"
    )
    unscale: Optional[bool] = Query(
        None,
        title="Apply internal Scale/Offset",
        description="Apply internal Scale/Offset",
    )
    resampling_method: ResamplingNames = Query(
        ResamplingNames.nearest, description="Resampling method."  # type: ignore
    )

    def __post_init__(self):
        """Post Init."""
        if self.nodata is not None:
            self.kwargs["nodata"] = (
                numpy.nan if self.nodata == "nan" else float(self.nodata)
            )

        if self.unscale is not None:
            self.kwargs["unscale"] = self.unscale

        if self.resampling_method is not None:
            self.kwargs["resampling_method"] = self.resampling_method.name


@dataclass
class RenderParams(DefaultDependency):
    """Image Rendering options."""

    rescale: Optional[str] = Query(
        None,
        title="Min/Max data Rescaling",
        description="comma (',') delimited Min,Max bounds",
    )
    color_formula: Optional[str] = Query(
        None,
        title="Color Formula",
        description="rio-color formula (info: https://github.com/mapbox/rio-color)",
    )
    color_map: Optional[ColorMapNames] = Query(
        None, description="rio-tiler's colormap name"
    )
    return_mask: bool = Query(True, description="Add mask to the output data.")

    colormap: Optional[Dict[int, Tuple[int, int, int, int]]] = field(init=False)
    rescale_range: Optional[List[Union[float, int]]] = field(init=False)

    def __post_init__(self):
        """Post Init."""
        self.colormap = cmap.get(self.color_map.value) if self.color_map else None
        self.rescale_range = (
            list(map(float, self.rescale.split(","))) if self.rescale else None
        )
