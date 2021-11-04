"""TiTiler response models."""

from typing import Dict, List, Union

from geojson_pydantic.features import Feature, FeatureCollection
from geojson_pydantic.geometries import Geometry
from pydantic import BaseModel
from rio_tiler.models import BandStatistics, Info


class Point(BaseModel):
    """
    Point model.

    response model for `/point` endpoints

    """

    coordinates: List[float]
    values: List[float]


InfoGeoJSON = Feature[Geometry, Info]

Statistics = Dict[str, BandStatistics]


class StatisticsInGeoJSON(BaseModel):
    """Statistics model in geojson response."""

    statistics: Statistics

    class Config:
        """Config for model."""

        extra = "allow"


StatisticsGeoJSON = Union[
    FeatureCollection[Geometry, StatisticsInGeoJSON],
    Feature[Geometry, StatisticsInGeoJSON],
]

# MultiBase Models
MultiBaseInfo = Dict[str, Info]
MultiBaseInfoGeoJSON = Feature[Geometry, MultiBaseInfo]

MultiBaseStatistics = Dict[str, Statistics]
MultiBaseStatisticsGeoJSON = Union[
    FeatureCollection[Geometry, StatisticsInGeoJSON],
    Feature[Geometry, StatisticsInGeoJSON],
]
