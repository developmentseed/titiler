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
    input_nbands: Optional[int] = None
    output_nbands: Optional[int] = None
    output_dtype: Optional[str] = None
    output_min: Optional[Sequence] = None
    output_max: Optional[Sequence] = None

    model_config = {"extra": "allow"}

    @abc.abstractmethod
    def __call__(self, img: ImageData) -> ImageData:
        """Apply algorithm"""
        ...


class AlgorithmMetadata(BaseModel):
    """Algorithm metadata."""

    title: Optional[str] = None
    description: Optional[str] = None

    inputs: Dict
    outputs: Dict
    parameters: Dict
