"""TiTiler response models."""

from geojson_pydantic.features import Feature, FeatureCollection
from geojson_pydantic.geometries import Geometry, MultiPolygon, Polygon
from pydantic import BaseModel
from rio_tiler.models import BandStatistics, Info

from titiler.core.models.common import Link


class Point(BaseModel):
    """
    Point model.

    response model for `/point` endpoints

    """

    coordinates: list[float]
    values: list[float | None]
    band_names: list[str]
    band_descriptions: list[str] | None = None


InfoGeoJSON = Feature[Polygon | MultiPolygon, Info]
Statistics = dict[str, BandStatistics]


class StatisticsInGeoJSON(BaseModel):
    """Statistics model in geojson response."""

    statistics: Statistics

    model_config = {"extra": "allow"}


StatisticsGeoJSON = (
    FeatureCollection[Feature[Geometry, StatisticsInGeoJSON]]
    | Feature[Geometry, StatisticsInGeoJSON]
)

# MultiBase Models
MultiBaseInfo = dict[str, Info]
MultiBaseInfoGeoJSON = Feature[Polygon | MultiPolygon, MultiBaseInfo]

MultiBaseStatistics = dict[str, Statistics]
MultiBaseStatisticsGeoJSON = StatisticsGeoJSON


class ColorMapRef(BaseModel):
    """ColorMapRef model."""

    id: str
    title: str | None = None
    links: list[Link]


class ColorMapList(BaseModel):
    """Model for colormap list."""

    colormaps: list[ColorMapRef]
