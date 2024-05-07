"""TiTiler response models."""

from typing import Dict, List, Union

from geojson_pydantic.features import Feature, FeatureCollection
from geojson_pydantic.geometries import Geometry, Polygon
from pydantic import BaseModel
from rio_tiler.models import BandStatistics, Info

from titiler.core.models.OGC import Link


class Point(BaseModel):
    """
    Point model.

    response model for `/point` endpoints

    """

    coordinates: List[float]
    values: List[float]
    band_names: List[str]


InfoGeoJSON = Feature[Polygon, Info]
Statistics = Dict[str, BandStatistics]


class StatisticsInGeoJSON(BaseModel):
    """Statistics model in geojson response."""

    statistics: Statistics

    model_config = {"extra": "allow"}


StatisticsGeoJSON = Union[
    FeatureCollection[Feature[Geometry, StatisticsInGeoJSON]],
    Feature[Geometry, StatisticsInGeoJSON],
]

# MultiBase Models
MultiBaseInfo = Dict[str, Info]
MultiBaseInfoGeoJSON = Feature[Polygon, MultiBaseInfo]

MultiBaseStatistics = Dict[str, Statistics]
MultiBaseStatisticsGeoJSON = StatisticsGeoJSON


class ColorMapsList(BaseModel):
    """Model for colormap list."""

    colorMaps: List[str]
    links: List[Link]
