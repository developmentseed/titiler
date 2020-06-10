"""Common dependency."""

import re
from enum import Enum
from typing import Any, Dict, Optional, Union

import morecantile
import numpy
from rio_tiler.colormap import cmap

from titiler.custom import cmap as custom_colormap
from titiler.custom import tms as custom_tms

from fastapi import Query

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
ColorMapName = Enum("ColorMapNames", [(a, a) for a in sorted(cmap.list())])  # type: ignore
TileMatrixSetNames = Enum("TileMatrixSetNames", [(a, a) for a in sorted(morecantile.tms.list())])  # type: ignore


class CommonImageParams:
    """Common Image parameters."""

    def __init__(
        self,
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
        color_map: Optional[ColorMapName] = Query(
            None, description="rio-tiler's colormap name"
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


class CommonMetadataParams:
    """Common Metadada parameters."""

    def __init__(
        self,
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
