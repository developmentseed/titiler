"""Algorithm base class."""

import abc
from typing import Dict, Optional, Sequence

from pydantic import BaseModel
from rio_tiler.models import ImageData


class BaseAlgorithm(BaseModel, metaclass=abc.ABCMeta):
    """Algorithm baseclass.

    Note: attribute starting with `input_` or `output_` are considered as metadata

    """

    # metadata
    input_nbands: int
    output_nbands: int
    output_dtype: str
    output_min: Optional[Sequence]
    output_max: Optional[Sequence]

    @abc.abstractmethod
    def apply(self, img: ImageData) -> ImageData:
        """Apply algorithm"""
        ...

    class Config:
        """Config for model."""

        extra = "allow"


class AlgorithmMetadata(BaseModel):
    """Algorithm metadata."""

    inputs: Dict
    outputs: Dict
    parameters: Dict
