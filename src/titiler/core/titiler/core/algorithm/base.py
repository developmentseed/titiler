"""Algorithm base class."""

import abc
from collections.abc import Sequence

from pydantic import BaseModel
from rio_tiler.models import ImageData

from titiler.core.models.common import Link


class BaseAlgorithm(BaseModel, metaclass=abc.ABCMeta):
    """Algorithm baseclass.

    Note: attribute starting with `input_` or `output_` are considered as metadata

    """

    # metadata
    input_nbands: int | None = None
    output_nbands: int | None = None
    output_dtype: str | None = None
    output_min: Sequence | None = None
    output_max: Sequence | None = None

    model_config = {"extra": "allow"}

    @abc.abstractmethod
    def __call__(self, img: ImageData) -> ImageData:
        """Apply algorithm"""
        ...


class AlgorithmMetadata(BaseModel):
    """Algorithm metadata."""

    title: str | None = None
    description: str | None = None

    inputs: dict
    outputs: dict
    parameters: dict


class AlgorithmRef(BaseModel):
    """AlgorithmRef model."""

    id: str
    title: str | None = None
    links: list[Link]


class AlgorithmtList(BaseModel):
    """AlgorithmList model."""

    algorithms: list[AlgorithmRef]
