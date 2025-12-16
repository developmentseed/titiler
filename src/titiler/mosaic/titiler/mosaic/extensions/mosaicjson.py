"""titiler.mosaic extensions."""

import logging

import rasterio
from attrs import define
from fastapi import Depends

from titiler.core.factory import FactoryExtension
from titiler.mosaic.factory import MosaicTilerFactory

logger = logging.getLogger(__name__)

try:
    from cogeo_mosaic.mosaic import MosaicJSON
except ImportError:  # pragma: nocover
    MosaicJSON = None  # type: ignore


@define
class MosaicJSONExtension(FactoryExtension):
    """Add MosaicJSON specific endpoints"""

    def register(self, factory: MosaicTilerFactory):  # type: ignore [override] # noqa: C901
        """Register endpoint to the tiler factory."""

        ############################################################################
        # /read
        ############################################################################

        @factory.router.get(
            "/",
            response_model=MosaicJSON,
            response_model_exclude_none=True,
            responses={200: {"description": "Return MosaicJSON definition"}},
            operation_id=f"{factory.operation_prefix}getMosaicJSON",
        )
        def read(
            src_path=Depends(factory.path_dependency),
            backend_params=Depends(factory.backend_dependency),
            reader_params=Depends(factory.reader_dependency),
            env=Depends(factory.environment_dependency),
        ):
            """Read a MosaicJSON"""
            with rasterio.Env(**env):
                logger.info(
                    f"opening data with backend: {factory.backend} and reader {factory.dataset_reader}"
                )
                with factory.backend(
                    src_path,
                    reader=factory.dataset_reader,
                    reader_options=reader_params.as_dict(),
                    **backend_params.as_dict(),
                ) as src_dst:
                    return src_dst.mosaic_def

        @factory.router.post(
            "/validate",
            operation_id=f"{factory.operation_prefix}validate",
        )
        def validate(body: MosaicJSON):
            """Validate a MosaicJSON"""
            return True
