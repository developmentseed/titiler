"""TileMatrixSet Extension."""

import math
from typing import Annotated, Any, Literal

import pyproj
import rasterio
from attrs import define
from fastapi import Depends, Query
from morecantile import TileMatrixSet
from morecantile.models import CRS_to_uri, TileMatrix, TMSBoundingBox, crs_axis_inverted
from morecantile.utils import meters_per_unit
from pyproj.exceptions import CRSError
from starlette.requests import Request

from titiler.core.factory import FactoryExtension, TilerFactory
from titiler.core.resources.enums import MediaType
from titiler.core.utils import (
    accept_media_type,
    create_html_response,
    rio_crs_to_pyproj,
)


@define
class tmsExtension(FactoryExtension):
    """Add /tms endpoint to a TilerFactory."""

    def register(self, factory: TilerFactory):  # type: ignore [override]  # noqa: C901
        """Register endpoint to the tiler factory."""

        @factory.router.get(
            "/tms",
            response_model=TileMatrixSet,
            response_model_exclude_none=True,
            name="Create TileMatrixSet from Dataset",
            operation_id=f"{factory.operation_prefix}createTMS",
        )
        def create_tilematrixset(
            request: Request,
            src_path=Depends(factory.path_dependency),
            f: Annotated[
                Literal["html", "json"] | None,
                Query(
                    description="Response MediaType. Defaults to endpoint's default or value defined in `accept` header."
                ),
            ] = None,
        ):
            """Create TileMatrixSet document."""
            tile_matrices: list[TileMatrix] = []

            with rasterio.open(src_path) as src_dst:
                bbox = src_dst.bounds
                blockxsize, blockysize = src_dst.block_shapes[0]
                width = src_dst.width
                height = src_dst.height

                try:
                    overviews = src_dst.overviews(1)
                except Exception:
                    overviews = []

                crs = rio_crs_to_pyproj(src_dst.crs)
                mpu = meters_per_unit(crs)
                screen_pixel_size = 0.28e-3

                is_inverted = crs_axis_inverted(crs)
                # TODO: check this, some image might have different origin
                corner_of_origin = "topLeft"
                if corner_of_origin == "topLeft":
                    x_origin = bbox.left if not is_inverted else bbox.top
                    y_origin = bbox.top if not is_inverted else bbox.left
                    point_of_origin = [x_origin, y_origin]
                elif corner_of_origin == "bottomLeft":
                    x_origin = bbox.left if not is_inverted else bbox.bottom
                    y_origin = bbox.bottom if not is_inverted else bbox.left
                    point_of_origin = [x_origin, y_origin]

                res = max(src_dst.res)
                base_level = TileMatrix(
                    id=str(len(overviews)),  # Last TileMatrix
                    scaleDenominator=res * mpu / screen_pixel_size,
                    cellSize=res,
                    cornerOfOrigin=corner_of_origin,
                    pointOfOrigin=point_of_origin,
                    tileWidth=blockxsize,
                    tileHeight=blockysize,
                    matrixWidth=math.ceil(width / blockxsize),
                    matrixHeight=math.ceil(height / blockysize),
                )

            for ix, ovr in enumerate(reversed(range(len(overviews)))):
                with rasterio.open(src_path, OVERVIEW_LEVEL=ovr) as src_dst:
                    res = max(src_dst.res)
                    try:
                        blocksize = src_dst.block_shapes[0]
                    except Exception:
                        blocksize = (src_dst.width, 1)

                    width = src_dst.width
                    height = src_dst.height

                    # add tile matrix for highest resolution (base level)
                    tile_matrices.append(
                        TileMatrix(
                            id=str(ix),
                            scaleDenominator=res * mpu / 0.28e-3,
                            cellSize=res,
                            cornerOfOrigin=corner_of_origin,
                            pointOfOrigin=point_of_origin,
                            tileWidth=blocksize[1],
                            tileHeight=blocksize[0],
                            matrixWidth=math.ceil(width / blocksize[1]),
                            matrixHeight=math.ceil(height / blocksize[0]),
                        )
                    )

            tile_matrices.append(base_level)

            if crs.to_authority(min_confidence=20):
                crs_data: Any = CRS_to_uri(crs)

                # Some old Proj version might not support URI
                # so we fall back to wkt
                try:
                    pyproj.CRS.from_user_input(crs_data)
                except CRSError:
                    crs_data = {"wkt": crs.to_json_dict()}

            else:
                crs_data = {"wkt": crs.to_json_dict()}

            tms = TileMatrixSet(
                description=f"TileMatrixSet document for {src_path}",
                crs=crs_data,
                tileMatrices=tile_matrices,
                boundingBox=TMSBoundingBox(
                    lowerLeft=[bbox.left, bbox.bottom],
                    upperRight=[bbox.right, bbox.top],
                    crs=crs_data,
                ),
            )

            if f:
                output_type = MediaType[f]
            else:
                accepted_media = [MediaType.html, MediaType.json]
                output_type = (
                    accept_media_type(request.headers.get("accept", ""), accepted_media)
                    or MediaType.json
                )

            if output_type == MediaType.html:
                return create_html_response(
                    request,
                    {
                        **tms.model_dump(exclude_none=True, mode="json"),
                        # For visualization purpose we add the tms bbox
                        "bbox": list(tms.bbox),
                    },
                    title="TileMatrixSet",
                    template_name="tilematrixset",
                    templates=factory.templates,
                )

            return tms
