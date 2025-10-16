"""Common response models."""

from typing import Annotated, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, Field, model_validator


class LayerJSON(BaseModel):
    """
    https://github.com/mapbox/tilejson-spec/tree/master/3.0.0#33-vector_layers
    """

    id: str
    fields: Annotated[Dict, Field(default_factory=dict)]
    description: Optional[str] = None
    minzoom: Optional[int] = None
    maxzoom: Optional[int] = None


class TileJSON(BaseModel, extra="allow"):
    """
    TileJSON model.

    Based on https://github.com/mapbox/tilejson-spec/tree/master/3.0.0

    """

    tilejson: str = "3.0.0"
    name: Optional[str] = None
    description: Optional[str] = None
    version: str = "1.0.0"
    attribution: Optional[str] = None
    template: Optional[str] = None
    legend: Optional[str] = None
    scheme: Literal["xyz", "tms"] = "xyz"
    tiles: List[str]
    vector_layers: Optional[List[LayerJSON]] = None
    grids: Optional[List[str]] = None
    data: Optional[List[str]] = None
    minzoom: int = Field(0)
    maxzoom: int = Field(30)
    fillzoom: Optional[int] = None
    bounds: List[float] = [-180, -85.0511287798066, 180, 85.0511287798066]
    center: Optional[Tuple[float, float, int]] = None

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
