"""TiTiler response models."""

from typing import Dict, List, Union

from geojson_pydantic.features import Feature, FeatureCollection
from geojson_pydantic.geometries import Geometry, Polygon
from pydantic import BaseModel
from rio_tiler.models import BandStatistics, Info


class Point(BaseModel):
    """
    Point model.

    response model for `/point` endpoints

    """

    coordinates: List[float]
    values: List[float]


class MultiBasePoint(BaseModel):
    """Point model for MultiBaseReader."""

    coordinates: List[float]
    values: List[List[float]]


InfoGeoJSON = Feature[Polygon, Info]
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
MultiBaseInfoGeoJSON = Feature[Polygon, MultiBaseInfo]

MultiBaseStatistics = Dict[str, Statistics]
MultiBaseStatisticsGeoJSON = Union[
    FeatureCollection[Geometry, StatisticsInGeoJSON],
    Feature[Geometry, StatisticsInGeoJSON],
]
