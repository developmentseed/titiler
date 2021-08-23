"""Common dependency."""

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Sequence, Tuple, Union

import numpy
from morecantile import tms
from morecantile.models import TileMatrixSet
from rasterio.enums import Resampling
from rio_tiler.colormap import cmap, parse_color
from rio_tiler.constants import NumType
from rio_tiler.errors import MissingAssets, MissingBands

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


def DatasetPathParams(url: str = Query(..., description="Dataset URL")) -> str:
    """Create dataset path from args"""
    return url


@dataclass
class DefaultDependency:
    """Dependency Base Class"""

    kwargs: Dict = field(init=False, default_factory=dict)


# Dependencies for simple BaseReader (e.g COGReader)
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


# Dependencies for  MultiBaseReader (e.g STACReader)
@dataclass
class AssetsBidxParams(DefaultDependency):
    """Asset and Band indexes parameters."""

    assets: Optional[str] = Query(
        ..., title="Asset indexes", description="comma (',') delimited asset names.",
    )
    bidx: Optional[str] = Query(
        None, title="Band indexes", description="comma (',') delimited band indexes",
    )

    def __post_init__(self):
        """Post Init."""
        if self.assets is not None:
            self.kwargs["assets"] = self.assets.split(",")
        if self.bidx is not None:
            self.kwargs["indexes"] = tuple(
                int(s) for s in re.findall(r"\d+", self.bidx)
            )


@dataclass
class AssetsBidxExprParams(DefaultDependency):
    """Assets, Band Indexes and Expression parameters."""

    assets: Optional[str] = Query(
        None, title="Asset indexes", description="comma (',') delimited asset names.",
    )
    expression: Optional[str] = Query(
        None,
        title="Band Math expression",
        description="rio-tiler's band math expression (e.g B1/B2)",
    )
    bidx: Optional[str] = Query(
        None, title="Band indexes", description="comma (',') delimited band indexes",
    )

    def __post_init__(self):
        """Post Init."""
        if not self.assets and not self.expression:
            raise MissingAssets(
                "assets must be defined either via expression or assets options."
            )

        if self.assets is not None:
            self.kwargs["assets"] = self.assets.split(",")
        if self.expression is not None:
            self.kwargs["expression"] = self.expression
        if self.bidx is not None:
            self.kwargs["indexes"] = tuple(
                int(s) for s in re.findall(r"\d+", self.bidx)
            )


# Dependencies for  MultiBandReader
@dataclass
class BandsParams(DefaultDependency):
    """Band names parameters."""

    bands: str = Query(
        ..., title="bands names", description="comma (',') delimited bands names.",
    )

    def __post_init__(self):
        """Post Init."""
        self.kwargs["bands"] = self.bands.split(",")


@dataclass
class BandsExprParams(DefaultDependency):
    """Band names and Expression parameters."""

    bands: Optional[str] = Query(
        None, title="bands names", description="comma (',') delimited bands names.",
    )
    expression: Optional[str] = Query(
        None,
        title="Band Math expression",
        description="rio-tiler's band math expression.",
    )

    def __post_init__(self):
        """Post Init."""
        if not self.bands and not self.expression:
            raise MissingBands(
                "bands must be defined either via expression or bands options."
            )

        if self.bands is not None:
            self.kwargs["bands"] = self.bands.split(",")
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
    histogram_bins: Optional[str] = Query(None, description="Histogram bins.")
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
        if self.histogram_bins is not None:
            bins = self.histogram_bins.split(",")
            if len(bins) == 1:
                hist_options.update(dict(bins=int(bins[0])))
            else:
                hist_options.update(dict(bins=list(map(float, bins))))

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
    resampling_method: ResamplingName = Query(
        ResamplingName.nearest, description="Resampling method."  # type: ignore
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

    rescale: Optional[List[str]] = Query(
        None,
        title="Min/Max data Rescaling",
        description="comma (',') delimited Min,Max bounds. Can set multiple time for multiple bands.",
    )
    color_formula: Optional[str] = Query(
        None,
        title="Color Formula",
        description="rio-color formula (info: https://github.com/mapbox/rio-color)",
    )
    return_mask: bool = Query(True, description="Add mask to the output data.")

    rescale_range: Optional[Sequence[Tuple[NumType, NumType]]] = field(init=False)

    def __post_init__(self):
        """Post Init."""
        self.rescale_range = (
            [tuple(map(float, r.replace(" ", "").split(","))) for r in self.rescale]
            if self.rescale
            else None
        )
