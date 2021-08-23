"""TiTiler demo custon dependencies."""

import json
from enum import Enum
from typing import Dict, Optional

import morecantile
from morecantile import tms
from morecantile.models import TileMatrixSet
from rasterio.crs import CRS
from rio_tiler.colormap import cmap, parse_color

from fastapi import HTTPException, Query

from starlette.templating import Jinja2Templates

try:
    from importlib.resources import files as resources_files  # type: ignore
except ImportError:
    # Try backported to PY<39 `importlib_resources`.
    from importlib_resources import files as resources_files  # type: ignore


templates = Jinja2Templates(directory=str(resources_files(__package__) / "templates"))


# colors from https://daac.ornl.gov/ABOVE/guides/Annual_Landcover_ABoVE.html
above_cmap = {
    1: [58, 102, 24, 255],  # Evergreen Forest
    2: [100, 177, 41, 255],  # Deciduous Forest
    3: [177, 177, 41, 255],  # Shrubland
    4: [221, 203, 154, 255],  # Herbaceous
    5: [218, 203, 47, 255],  # Sparely Vegetated
    6: [177, 177, 177, 255],  # Barren
    7: [175, 255, 205, 255],  # Fen
    8: [239, 255, 192, 255],  # Bog
    9: [144, 255, 255, 255],  # Shallows/Littoral
    10: [29, 0, 250, 255],  # Water
}
cmap = cmap.register({"above": above_cmap})

ColorMapName = Enum(  # type: ignore
    "ColorMapName", [(a, a) for a in sorted(cmap.list())]
)

# CUSTOM TMS for EPSG:3413
EPSG3413 = morecantile.TileMatrixSet.custom(
    [-4194300, -4194300, 4194300, 4194300],
    CRS.from_epsg(3413),
    identifier="EPSG3413",
    matrix_scale=[2, 2],
)

# CUSTOM TMS for EPSG:6933
# info from https://epsg.io/6933
EPSG6933 = morecantile.TileMatrixSet.custom(
    [-17357881.81713629, -7324184.56362408, 17357881.81713629, 7324184.56362408],
    CRS.from_epsg(6933),
    identifier="EPSG6933",
    matrix_scale=[1, 1],
)
tms = tms.register([EPSG3413, EPSG6933])

TileMatrixSetName = Enum(  # type: ignore
    "TileMatrixSetName", [(a, a) for a in sorted(tms.list())]
)


def ColorMapParams(
    colormap_name: ColorMapName = Query(None, description="Colormap name"),
    colormap: str = Query(None, description="JSON encoded custom Colormap"),
) -> Optional[Dict]:
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


def TMSParams(
    TileMatrixSetId: TileMatrixSetName = Query(
        TileMatrixSetName.WebMercatorQuad,  # type: ignore
        description="TileMatrixSet Name (default: 'WebMercatorQuad')",
    )
) -> TileMatrixSet:
    """TileMatrixSet Dependency."""
    return tms.get(TileMatrixSetId.name)
