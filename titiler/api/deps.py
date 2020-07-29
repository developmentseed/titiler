"""Common dependency."""

import re
from enum import Enum
from typing import Any, Dict, Optional, Union
from urllib.parse import urlparse

import morecantile
import numpy
from rasterio.enums import Resampling
from rio_tiler.colormap import cmap

from titiler import settings
from titiler.api.utils import get_hash
from titiler.custom import cmap as custom_colormap
from titiler.custom import tms as custom_tms

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
ColorMapNames = Enum("ColorMapNames", [(a, a) for a in sorted(cmap.list())])  # type: ignore
TileMatrixSetNames = Enum("TileMatrixSetNames", [(a, a) for a in sorted(morecantile.tms.list())])  # type: ignore
ResamplingNames = Enum("ResamplingNames", [(r.name, r.name) for r in Resampling])  # type: ignore


async def request_hash(request: Request) -> str:
    """Create SHA224 id from reuqest."""
    return get_hash(**dict(request.query_params), **request.path_params)


class CommonTileParams:
    """Common Tile parameters."""

    def __init__(
        self,
        request: Request,
        bidx: Optional[str] = Query(
            None,
            title="Band indexes",
            description="comma (',') delimited band indexes",
        ),
        expression: Optional[str] = Query(
            None,
            title="Band Math expression",
            description="rio-tiler's band math expression (e.g B1/B2)",
        ),
        nodata: Optional[Union[str, int, float]] = Query(
            None, title="Nodata value", description="Overwrite internal Nodata value"
        ),
        rescale: Optional[str] = Query(
            None,
            title="Min/Max data Rescaling",
            description="comma (',') delimited Min,Max bounds",
        ),
        color_formula: Optional[str] = Query(
            None,
            title="Color Formula",
            description="rio-color formula (info: https://github.com/mapbox/rio-color)",
        ),
        color_map: Optional[ColorMapNames] = Query(
            None, description="rio-tiler's colormap name"
        ),
        resampling_method: ResamplingNames = Query(
            ResamplingNames.nearest, description="Resampling method."  # type: ignore
        ),
    ):
        """Populate Imager Params."""
        self.indexes = tuple(int(s) for s in re.findall(r"\d+", bidx)) if bidx else None
        self.expression = expression
        if nodata is not None:
            nodata = numpy.nan if nodata == "nan" else float(nodata)
        self.nodata = nodata
        self.rescale = rescale
        self.color_formula = color_formula
        self.color_map = cmap.get(color_map.value) if color_map else None
        kwargs = dict(request.query_params)
        kwargs.pop("TileMatrixSetId", None)
        kwargs.pop("url", None)
        kwargs.pop("scale", None)
        kwargs.pop("format", None)
        kwargs.pop("bidx", None)
        kwargs.pop("expression", None)
        kwargs.pop("nodata", None)
        kwargs.pop("rescale", None)
        kwargs.pop("color_formula", None)
        kwargs.pop("color_map", None)
        kwargs.pop("assets", None)  # For STAC
        self.kwargs = kwargs


class CommonImageParams:
    """Common Image parameters."""

    def __init__(
        self,
        request: Request,
        bidx: Optional[str] = Query(
            None,
            title="Band indexes",
            description="comma (',') delimited band indexes",
        ),
        expression: Optional[str] = Query(
            None,
            title="Band Math expression",
            description="rio-tiler's band math expression (e.g B1/B2)",
        ),
        max_size: Optional[int] = Query(
            1024, description="Maximum image size to read onto."
        ),
        height: Optional[int] = Query(None, description="Force output image height."),
        width: Optional[int] = Query(None, description="Force output image width."),
        nodata: Optional[Union[str, int, float]] = Query(
            None, title="Nodata value", description="Overwrite internal Nodata value"
        ),
        rescale: Optional[str] = Query(
            None,
            title="Min/Max data Rescaling",
            description="comma (',') delimited Min,Max bounds",
        ),
        color_formula: Optional[str] = Query(
            None,
            title="Color Formula",
            description="rio-color formula (info: https://github.com/mapbox/rio-color)",
        ),
        color_map: Optional[ColorMapNames] = Query(
            None, description="rio-tiler's colormap name"
        ),
        resampling_method: ResamplingNames = Query(
            ResamplingNames.nearest, description="Resampling method."  # type: ignore
        ),
    ):
        """Populate Imager Params."""
        self.indexes = tuple(int(s) for s in re.findall(r"\d+", bidx)) if bidx else None
        self.expression = expression
        self.max_size = max_size
        self.height = height
        self.width = width
        if self.width and self.height:
            self.max_size = None
        if nodata is not None:
            nodata = numpy.nan if nodata == "nan" else float(nodata)
        self.nodata = nodata
        self.rescale = rescale
        self.color_formula = color_formula
        self.color_map = cmap.get(color_map.value) if color_map else None
        kwargs = dict(request.query_params)
        kwargs.pop("url", None)
        kwargs.pop("format", None)
        kwargs.pop("bidx", None)
        kwargs.pop("expression", None)
        kwargs.pop("nodata", None)
        kwargs.pop("rescale", None)
        kwargs.pop("color_formula", None)
        kwargs.pop("color_map", None)
        kwargs.pop("height", None)
        kwargs.pop("width", None)
        kwargs.pop("max_size", None)
        kwargs.pop("assets", None)  # For STAC
        self.kwargs = kwargs


class CommonMetadataParams:
    """Common Metadada parameters."""

    def __init__(
        self,
        request: Request,
        bidx: Optional[str] = Query(
            None,
            title="Band indexes",
            description="comma (',') delimited band indexes",
        ),
        nodata: Optional[Union[str, int, float]] = Query(
            None, title="Nodata value", description="Overwrite internal Nodata value"
        ),
        pmin: float = Query(2.0, description="Minimum percentile"),
        pmax: float = Query(98.0, description="Maximum percentile"),
        max_size: int = Query(1024, description="Maximum image size to read onto."),
        histogram_bins: Optional[int] = Query(None, description="Histogram bins."),
        histogram_range: Optional[str] = Query(
            None, description="comma (',') delimited Min,Max histogram bounds"
        ),
        bounds: Optional[str] = Query(
            None,
            descriptions="comma (',') delimited Bounding box coordinates from which to calculate image statistics.",
        ),
        resampling_method: ResamplingNames = Query(
            ResamplingNames.nearest, description="Resampling method."  # type: ignore
        ),
    ):
        """Populate Imager Params."""
        self.indexes = tuple(int(s) for s in re.findall(r"\d+", bidx)) if bidx else None
        if nodata is not None:
            nodata = numpy.nan if nodata == "nan" else float(nodata)
        self.nodata = nodata
        self.pmin = pmin
        self.pmax = pmax
        self.max_size = max_size
        self.hist_options: Dict[str, Any] = dict()
        if histogram_bins:
            self.hist_options.update(dict(bins=histogram_bins))
        if histogram_range:
            self.hist_options.update(
                dict(range=list(map(float, histogram_range.split(","))))
            )
        self.bounds = tuple(map(float, bounds.split(","))) if bounds else None
        kwargs = dict(request.query_params)
        kwargs.pop("url", None)
        kwargs.pop("bidx", None)
        kwargs.pop("nodata", None)
        kwargs.pop("pmin", None)
        kwargs.pop("pmax", None)
        kwargs.pop("max_size", None)
        kwargs.pop("histogram_bins", None)
        kwargs.pop("histogram_range", None)
        kwargs.pop("bounds", None)
        kwargs.pop("assets", None)  # For STAC
        self.kwargs = kwargs


def MosaicPath(url: str = Query(..., description="MosaicJSON URL")) -> str:
    """Create mosaic path from args"""
    parsed = urlparse(url)
    if parsed.scheme == "mosaicid":
        # by default we store the mosaicjson as a GZ compressed json (.json.gz) file
        return f"{settings.DEFAULT_MOSAIC_BACKEND}{settings.DEFAULT_MOSAIC_HOST}/{parsed.netloc}.json.gz"
    else:
        return url
