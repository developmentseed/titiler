"""api clients."""

import abc
from typing import Dict, Generator

from cogeo_mosaic.backends import BaseBackend as CogeoMosaicBackend
from cogeo_mosaic.backends import MosaicBackend
from rio_tiler.io import COGReader, STACReader

from starlette.requests import Request


class BaseTiler(abc.ABC):
    """
    Base class
    """

    @abc.abstractmethod
    def get_bounds(self) -> Dict:
        """Create /bounds API response"""
        ...


class Tiler(COGReader, BaseTiler):
    """
    COG tiler
    """

    @classmethod
    def create_from_request(
        cls, request: Request
    ) -> Generator["StacTiler", Request, None]:
        """
        Create an instance of the class from a starlette request, used for dependency injection
        """
        with cls(filepath=request.query_params["url"]) as tiler:
            yield tiler

    def get_bounds(self) -> Dict:
        """Create /bounds API response"""
        return {"bounds": self.bounds}


class StacTiler(STACReader, BaseTiler):
    """
    STAC tiler
    """

    @classmethod
    def create_from_request(
        cls, request: Request
    ) -> Generator["StacTiler", Request, None]:
        """
        Create an instance of the class from a starlette request, used for dependency injection
        """
        with cls(filepath=request.query_params["url"]) as tiler:
            yield tiler

    def get_bounds(self) -> Dict:
        """Create /bounds API response"""
        return {"bounds": self.bounds}


class MosaicTiler(CogeoMosaicBackend, BaseTiler):
    """
    Mosaic tiler
    """

    @classmethod
    def create_from_request(
        cls, request: Request
    ) -> Generator["MosaicTiler", Request, None]:
        """
        Create an instance of the class from a starlette request, used for dependency injection
        """
        with MosaicBackend(url=request.query_params["url"]) as mosaic:
            yield mosaic

    def get_bounds(self) -> Dict:
        """Create /bounds API response"""
        return {"bounds": self.mosaic_def.bounds}
