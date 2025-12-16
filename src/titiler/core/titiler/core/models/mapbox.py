"""Common response models."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator


class LayerJSON(BaseModel):
    """
    https://github.com/mapbox/tilejson-spec/tree/master/3.0.0#33-vector_layers
    """

    id: str
    fields: Annotated[dict, Field(default_factory=dict)]
    description: str | None = None
    minzoom: int | None = None
    maxzoom: int | None = None


class TileJSON(BaseModel, extra="allow"):
    """
    TileJSON model.

    Based on https://github.com/mapbox/tilejson-spec/tree/master/3.0.0

    """

    tilejson: str = "3.0.0"
    name: str | None = None
    description: str | None = None
    version: str = "1.0.0"
    attribution: str | None = None
    template: str | None = None
    legend: str | None = None
    scheme: Literal["xyz", "tms"] = "xyz"
    tiles: list[str]
    vector_layers: list[LayerJSON] | None = None
    grids: list[str] | None = None
    data: list[str] | None = None
    minzoom: int = Field(0)
    maxzoom: int = Field(30)
    fillzoom: int | None = None
    bounds: list[float] = [-180, -85.0511287798066, 180, 85.0511287798066]
    center: tuple[float, float, int] | None = None

    @model_validator(mode="after")
    def compute_center(self):
        """Compute center if it does not exist."""
        bounds = self.bounds
        if not self.center:
            self.center = (
                (bounds[0] + bounds[2]) / 2,
                (bounds[1] + bounds[3]) / 2,
                self.minzoom,
            )
        return self
