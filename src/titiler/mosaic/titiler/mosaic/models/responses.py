"""TiTiler.mosaic response models."""

from pydantic import BaseModel


class AssetPoint(BaseModel):
    """Model for Point value per asset"""

    name: str
    values: list[float | None]
    band_names: list[str]
    band_descriptions: list[str] | None = None


class Point(BaseModel):
    """
    Point model.

    response model for `/point` endpoints

    """

    coordinates: list[float]
    assets: list[AssetPoint]
