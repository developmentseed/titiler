"""test titiler.models."""

import pytest
from pydantic import ValidationError

from titiler.core.models.mapbox import TileJSON


def test_tilejson_model():
    """Make sure TileJSON model validates input and return default."""
    tj = TileJSON(tiles=["https://something.xyz/{x}/{y}/{z}"])
    assert list(map(round, tj.center)) == [0.0, 0.0, 0]
    assert tj.bounds == [-180, -85.0511287798066, 180, 85.0511287798066]
    assert tj.minzoom == 0
    assert tj.maxzoom == 30
    assert tj.scheme == "xyz"

    tj = TileJSON(
        tiles=["https://something.xyz/{x}/{y}/{z}"], center=(10, 10, 4), scheme="tms"
    )
    assert tj.center == (10.0, 10.0, 4)
    assert tj.bounds == [-180, -85.0511287798066, 180, 85.0511287798066]
    assert tj.scheme == "tms"

    with pytest.raises(ValidationError):
        TileJSON(tiles=["https://something.xyz/{x}/{y}/{z}"], scheme="abc")

    # Check extra fields are allowed
    tj = TileJSON(tiles=["https://something.xyz/{x}/{y}/{z}"], dtype="uint8")
    assert tj.dtype == "uint8"
