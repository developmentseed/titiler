"""Common dependency."""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Tuple, Type, Union

import morecantile
import numpy
from rasterio.enums import Resampling
from rio_tiler.colormap import cmap
from rio_tiler.io import BaseReader

from .custom import cmap as custom_colormap
from .custom import tms as custom_tms
from .utils import get_hash

from fastapi import Query

from starlette.requests import Request

################################################################################
#                       CMAP AND TMS Customization
morecantile.tms.register(custom_tms.EPSG3413)
# REGISTER CUSTOM TMS
#
# e.g morecantile.tms.register(custom_tms.my_custom_tms)

cmap.register("above", custom_colormap.above_cmap)
# REGISTER CUSTOM COLORMAP HERE
#
# e.g cmap.register("customRed", custom_colormap.custom_red)

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
    "TileMatrixSetNames", [(a, a) for a in sorted(morecantile.tms.list())]
)


async def request_hash(request: Request) -> str:
    """Create SHA224 id from reuqest."""
    return get_hash(**dict(request.query_params), **request.path_params)


def WebMercatorTMSParams(
    TileMatrixSetId: WebMercatorTileMatrixSetName = Query(
        WebMercatorTileMatrixSetName.WebMercatorQuad,  # type: ignore
        description="TileMatrixSet Name (default: 'WebMercatorQuad')",
    )
) -> morecantile.TileMatrixSet:
    """TileMatrixSet Dependency."""
    return morecantile.tms.get(TileMatrixSetId.name)


def TMSParams(
    TileMatrixSetId: TileMatrixSetNames = Query(
        TileMatrixSetNames.WebMercatorQuad,  # type: ignore
        description="TileMatrixSet Name (default: 'WebMercatorQuad')",
    )
) -> morecantile.TileMatrixSet:
    """TileMatrixSet Dependency."""
    return morecantile.tms.get(TileMatrixSetId.name)


@dataclass
class DefaultDependency:
    """Dependency Base Class"""

    kwargs: dict = field(init=False, default_factory=dict)


@dataclass
class PathParams(DefaultDependency):
    """Create dataset path from args"""

    url: str = Query(..., description="Dataset URL")

    # Placeholder
    # Factory can accept a reader defined in the PathParams.
    # This is for case where a user would want to indicate in the input url what
    # reader to use:
    # landsat+{landsat scene id}
    # sentinel+{sentinel scene id}
    # ...
    reader: Optional[Type[BaseReader]] = field(init=False, default=None)


@dataclass
class AssetsParams(DefaultDependency):
    """Create dataset path from args"""

    assets: Optional[str] = Query(
        None,
        title="Asset indexes",
        description="comma (',') delimited asset names (might not be an available options of some readers)",
    )

    def __post_init__(self):
        """Post Init."""
        if self.assets is not None:
            self.kwargs["assets"] = self.assets.split(",")


@dataclass
class BandsParams(DefaultDependency):
    """Create dataset Bands from args"""

    bands: Optional[str] = Query(
        None,
        title="Bands indexes",
        description="comma (',') delimited band names (might not be an available options of some readers)",
    )

    def __post_init__(self):
        """Post Init."""
        if self.bands is not None:
            self.kwargs["bands"] = self.bands.split(",")


@dataclass
class CommonParams(DefaultDependency):
    """Common Reader params."""

    bidx: Optional[str] = Query(
        None, title="Band indexes", description="comma (',') delimited band indexes",
    )
    nodata: Optional[Union[str, int, float]] = Query(
        None, title="Nodata value", description="Overwrite internal Nodata value"
    )
    resampling_method: ResamplingNames = Query(
        ResamplingNames.nearest, description="Resampling method."  # type: ignore
    )

    def __post_init__(self):
        """Post Init."""
        self.indexes = (
            tuple(int(s) for s in re.findall(r"\d+", self.bidx)) if self.bidx else None
        )
        if self.nodata is not None:
            self.nodata = numpy.nan if self.nodata == "nan" else float(self.nodata)


@dataclass
class MetadataParams(CommonParams):
    """Common Metadada parameters."""

    pmin: float = Query(2.0, description="Minimum percentile")
    pmax: float = Query(98.0, description="Maximum percentile")
    max_size: int = Query(1024, description="Maximum image size to read onto.")
    histogram_bins: Optional[int] = Query(None, description="Histogram bins.")
    histogram_range: Optional[str] = Query(
        None, description="comma (',') delimited Min,Max histogram bounds"
    )
    bounds: Optional[str] = Query(
        None,
        descriptions="comma (',') delimited Bounding box coordinates from which to calculate image statistics.",
    )
    hist_options: dict = field(init=False, default_factory=dict)

    def __post_init__(self):
        """Post Init."""
        super().__post_init__()

        if self.histogram_bins:
            self.hist_options.update(dict(bins=self.histogram_bins))
        if self.histogram_range:
            self.hist_options.update(
                dict(range=list(map(float, self.histogram_range.split(","))))
            )
        if self.bounds:
            self.bounds = tuple(map(float, self.bounds.split(",")))


@dataclass
class PointParams(DefaultDependency):
    """Point Parameters."""

    bidx: Optional[str] = Query(
        None, title="Band indexes", description="comma (',') delimited band indexes",
    )
    nodata: Optional[Union[str, int, float]] = Query(
        None, title="Nodata value", description="Overwrite internal Nodata value"
    )
    expression: Optional[str] = Query(
        None,
        title="Band Math expression",
        description="rio-tiler's band math expression (e.g B1/B2)",
    )

    def __post_init__(self):
        """Post Init."""
        self.indexes = (
            tuple(int(s) for s in re.findall(r"\d+", self.bidx)) if self.bidx else None
        )
        if self.nodata is not None:
            self.nodata = numpy.nan if self.nodata == "nan" else float(self.nodata)


@dataclass
class TileParams(CommonParams):
    """Common Tile parameters."""

    expression: Optional[str] = Query(
        None,
        title="Band Math expression",
        description="rio-tiler's band math expression (e.g B1/B2)",
    )
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
    colormap: Optional[Dict[int, Tuple[int, int, int, int]]] = field(init=False)

    def __post_init__(self):
        """Post Init."""
        super().__post_init__()

        self.colormap = cmap.get(self.color_map.value) if self.color_map else None


@dataclass
class ImageParams(TileParams):
    """Common Image parameters."""

    max_size: Optional[int] = Query(
        1024, description="Maximum image size to read onto."
    )
    height: Optional[int] = Query(None, description="Force output image height.")
    width: Optional[int] = Query(None, description="Force output image width.")

    def __post_init__(self):
        """Post Init."""
        super().__post_init__()

        if self.width and self.height:
            self.max_size = None
