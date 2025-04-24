"""titiler.core.algorithm Math."""

import numpy
from rio_tiler.models import ImageData

from titiler.core.algorithm.base import BaseAlgorithm

__all__ = ["_Min", "_Max", "_Median", "_Mean", "_Std", "_Var"]


class _Min(BaseAlgorithm):
    """Return Min values along the `bands` axis."""

    title: str = "Min"
    description: str = "Return Min values along the `bands` axis."

    output_nbands: int = 1

    def __call__(self, img: ImageData) -> ImageData:
        """Return Min."""
        return ImageData(
            numpy.ma.min(img.array, axis=0, keepdims=True),
            assets=img.assets,
            crs=img.crs,
            bounds=img.bounds,
            band_names=["min"],
            metadata=img.metadata,
            cutline_mask=img.cutline_mask,
        )


class _Max(BaseAlgorithm):
    """Return Max values along the `bands` axis."""

    title: str = "Max"
    description: str = "Return Max values along the `bands` axis."

    output_nbands: int = 1

    def __call__(self, img: ImageData) -> ImageData:
        """Return Max."""
        return ImageData(
            numpy.ma.max(img.array, axis=0, keepdims=True),
            assets=img.assets,
            crs=img.crs,
            bounds=img.bounds,
            band_names=["max"],
            metadata=img.metadata,
            cutline_mask=img.cutline_mask,
        )


class _Median(BaseAlgorithm):
    """Return Median values along the `bands` axis."""

    title: str = "Median"
    description: str = "Return Median values along the `bands` axis."

    output_nbands: int = 1
    output_dtype: str = "float64"

    def __call__(self, img: ImageData) -> ImageData:
        """Return Median."""
        return ImageData(
            numpy.ma.median(img.array, axis=0, keepdims=True),
            assets=img.assets,
            crs=img.crs,
            bounds=img.bounds,
            band_names=["median"],
            metadata=img.metadata,
            cutline_mask=img.cutline_mask,
        )


class _Mean(BaseAlgorithm):
    """Return Mean values along the `bands` axis."""

    title: str = "Mean"
    description: str = "Return Mean values."

    output_nbands: int = 1
    output_dtype: str = "float64"

    def __call__(self, img: ImageData) -> ImageData:
        """Return Mean."""
        return ImageData(
            numpy.ma.mean(img.array, axis=0, keepdims=True),
            assets=img.assets,
            crs=img.crs,
            bounds=img.bounds,
            band_names=["mean"],
            metadata=img.metadata,
            cutline_mask=img.cutline_mask,
        )


class _Std(BaseAlgorithm):
    """Return the standard deviation along the `bands` axis."""

    title: str = "Standard deviation"
    description: str = "Return the Standard Deviation along the `bands` axis."

    output_nbands: int = 1
    output_dtype: str = "float64"

    def __call__(self, img: ImageData) -> ImageData:
        """Return Stddev."""
        return ImageData(
            numpy.ma.std(img.array, axis=0, keepdims=True, ddof=1),
            assets=img.assets,
            crs=img.crs,
            bounds=img.bounds,
            band_names=["std"],
            metadata=img.metadata,
            cutline_mask=img.cutline_mask,
        )


class _Var(BaseAlgorithm):
    """Return Variance values along the `bands` axis."""

    title: str = "Variance"
    description: str = "Return Variance along the `bands` axis."

    output_nbands: int = 1
    output_dtype: str = "float64"

    def __call__(self, img: ImageData) -> ImageData:
        """Return Variance."""
        return ImageData(
            numpy.ma.var(img.array, axis=0, keepdims=True, ddof=1),
            assets=img.assets,
            crs=img.crs,
            bounds=img.bounds,
            band_names=["std"],
            metadata=img.metadata,
            cutline_mask=img.cutline_mask,
        )
