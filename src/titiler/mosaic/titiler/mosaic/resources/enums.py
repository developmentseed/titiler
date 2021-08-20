"""Titiler.mosaic Enums."""

from enum import Enum
from types import DynamicClassAttribute

from rio_tiler.mosaic.methods import defaults


class PixelSelectionMethod(str, Enum):
    """rio-tiler.mosaic pixel selection methods"""

    first = "first"
    highest = "highest"
    lowest = "lowest"
    mean = "mean"
    median = "median"
    stdev = "stdev"

    @DynamicClassAttribute
    def method(self):
        """Return rio-tiler-mosaic pixel selection class"""
        return getattr(defaults, f"{self._value_.title()}Method")
