"""Common dependency."""

from typing import Union, Optional
from enum import Enum

import re
from fastapi import Query
import numpy

from titiler.custom import cmap as custom_colormap
from rio_tiler.colormap import cmap

cmap.register("above", custom_colormap.above_cmap)

ColorMapName = Enum("ColorMapNames", [(a, a) for a in sorted(cmap.list())])  # type: ignore


class CommonImageParams:
    """Common Image parameters."""

    def __init__(
        self,
        bidx: Optional[str] = Query(
            None, title="Band indexes", description="Coma (',') delimited band indexes",
        ),
        nodata: Optional[Union[str, int, float]] = Query(
            None, title="Nodata value", description="Overwrite internal Nodata value"
        ),
        rescale: Optional[str] = Query(
            None,
            title="Min/Max data Rescaling",
            description="Coma (',') delimited Min,Max bounds",
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

        if nodata is not None:
            nodata = numpy.nan if nodata == "nan" else float(nodata)

        self.nodata = nodata

        self.rescale = rescale
        self.color_formula = color_formula
        self.color_map = cmap.get(color_map.value) if color_map else None
