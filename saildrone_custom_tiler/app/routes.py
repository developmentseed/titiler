"""routes.

app/routes.py
"""

import os
import re

import json
import boto3

import rasterio

from dataclasses import dataclass
from typing import Callable, Dict, Type
from urllib.parse import urlencode

from fastapi import Depends, Path
from starlette.requests import Request
from starlette.responses import Response

from morecantile import TileMatrixSet
from rio_tiler.io import BaseReader, COGReader
from rio_tiler.constants import MAX_THREADS
from rio_tiler.models import ImageData
from rio_tiler.errors import EmptyMosaicError

import numpy

from titiler.core.factory import BaseTilerFactory, img_endpoint_params
#from titiler.core.dependencies import ImageParams, MetadataParams, TMSParams
from titiler.core.dependencies import ImageParams, TMSParams, DefaultDependency
from titiler.core.models.mapbox import TileJSON
from titiler.core.resources.enums import ImageType, MediaType, OptionalHeader
from titiler.core.utils import Timer

from titiler.mosaic.factory import MosaicTilerFactory
from titiler.mosaic.resources.enums import PixelSelectionMethod
from fastapi import Query

from .cache import cached

from cogeo_mosaic.errors import (
    MosaicAuthError,
    MosaicError,
    MosaicNotFoundError,
    NoAssetFoundError,
)

MOSAIC_BACKEND = os.getenv("TITILER_MOSAIC_BACKEND", default="")
MOSAIC_HOST = os.getenv("TITILER_MOSAIC_HOST", default="")
DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", default="us-west-2")


@dataclass
class TilerFactory(BaseTilerFactory):

    # Default reader is set to COGReader
    reader: Type[BaseReader] = COGReader

    # Endpoint Dependencies
    img_dependency: Type[DefaultDependency] = ImageParams

    # TileMatrixSet dependency
    tms_dependency: Callable[..., TileMatrixSet] = TMSParams

    def register_routes(self):
        """This Method register routes to the router."""
        self.tile()
        self.tilejson()

    def tile(self):
        """Register /tiles endpoint."""

        @self.router.get(r"/tiles/{z}/{x}/{y}", **img_endpoint_params)
        @self.router.get(r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}", **img_endpoint_params)
        @cached()
        def tile(
            z: int = Path(..., ge=0, le=30, description="TMS tiles's zoom level"),
            x: int = Path(..., description="TMS tiles's column"),
            y: int = Path(..., description="TMS tiles's row"),
            tms: TileMatrixSet = Depends(self.tms_dependency),
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            render_params=Depends(self.render_dependency),
            postprocess_params=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
        ):
            """Create map tile from a dataset."""
            with self.reader(src_path, tms=tms) as src_dst:
                data = src_dst.tile(
                    x,
                    y,
                    z,
                    **layer_params,
                    **dataset_params,
                )
                dst_colormap = getattr(src_dst, "colormap", None)

            format = ImageType.jpeg if data.mask.all() else ImageType.png

            image = data.post_process(**postprocess_params)

            content = image.render(
                img_format=format.driver,
                colormap=colormap or dst_colormap,
                **format.profile,
                **render_params,
            )

            return Response(content, media_type=format.mediatype)

    def tilejson(self):
        """Register /tilejson.json endpoint."""

        @self.router.get(
            "/tilejson.json",
            response_model=TileJSON,
            responses={200: {"description": "Return a tilejson"}},
            response_model_exclude_none=True,
        )
        @self.router.get(
            "/{TileMatrixSetId}/tilejson.json",
            response_model=TileJSON,
            responses={200: {"description": "Return a tilejson"}},
            response_model_exclude_none=True,
        )
        @cached()
        def tilejson(
            request: Request,
            tms: TileMatrixSet = Depends(self.tms_dependency),
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            render_params=Depends(self.render_dependency),
            postprocess_params=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
        ):
            """Return TileJSON document for a dataset."""
            route_params = {
                "z": "{z}",
                "x": "{x}",
                "y": "{y}",
                "TileMatrixSetId": tms.identifier,
            }
            tiles_url = self.url_for(request, "tile", **route_params)

            qs_key_to_remove = [
                "tilematrixsetid",
                "tile_format",
                "tile_scale",
                "minzoom",
                "maxzoom",
            ]
            qs = [
                (key, value)
                for (key, value) in request.query_params._list
                if key.lower() not in qs_key_to_remove
            ]
            if qs:
                tiles_url += f"?{urlencode(qs)}"

            with self.reader(src_path, tms=tms) as src_dst:
                return {
                    "bounds": src_dst.geographic_bounds,
                    "minzoom": src_dst.minzoom,
                    "maxzoom": src_dst.maxzoom,
                    "name": "cogeotif",
                    "tiles": [tiles_url],
                }


sd_cog = TilerFactory()


def MosaicPathParams(
    mosaic: str = Query(..., description="mosaic name")
) -> str:
    """Create dataset path from args"""
    return f"{MOSAIC_BACKEND}{MOSAIC_HOST}{mosaic}.json"

@dataclass
class MosaicTiler(MosaicTilerFactory):
    """Custom MosaicTilerFactory.

    Note this is a really simple MosaicTiler Factory with only few endpoints.
    end points are cached
    and TITILER_MOSAIC_BACKEND is added to path if it exists
    """


    def register_routes(self):
        """This Method register routes to the router. """

        self.tile()
        self.tilejson()

    ############################################################################
    # /tiles
    ############################################################################
    def tile(self):  # noqa: C901
        """Register /tiles endpoints."""

        @self.router.get(r"/tiles/{z}/{x}/{y}", **img_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}.{format}", **img_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}@{scale}x", **img_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}@{scale}x.{format}", **img_endpoint_params)
        @self.router.get(r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}", **img_endpoint_params)
        @self.router.get(
            r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}.{format}", **img_endpoint_params
        )
        @self.router.get(
            r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}@{scale}x", **img_endpoint_params
        )
        @self.router.get(
            r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}@{scale}x.{format}",
            **img_endpoint_params,
        )
        @cached()
        def tile(
            z: int = Path(..., ge=0, le=30, description="Mercator tiles's zoom level"),
            x: int = Path(..., description="Mercator tiles's column"),
            y: int = Path(..., description="Mercator tiles's row"),
            tms: TileMatrixSet = Depends(self.tms_dependency),
            scale: int = Query(
                1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
            ),
            format: ImageType = Query(
                None, description="Output image type. Default is auto."
            ),
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            pixel_selection: PixelSelectionMethod = Query(
                PixelSelectionMethod.first, description="Pixel selection method."
            ),
            postprocess_params=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            cache_action: str = Query(
                "cache_read", description="Read from cache or overwrite"
            ),
        ):

            """Create map tile from a COG."""
            timings = []
            headers: Dict[str, str] = {}

            tilesize = scale * 256

            threads = int(os.getenv("MOSAIC_CONCURRENCY", MAX_THREADS))
            with Timer() as t:
                with rasterio.Env(**self.gdal_config):
                    with self.reader(
                        src_path,
                        reader=self.dataset_reader,
                        **self.backend_options,
                    ) as src_dst:
                        mosaic_read = t.from_start
                        timings.append(("mosaicread", round(mosaic_read * 1000, 2)))

                        try:
                            data, _ = src_dst.tile(
                                x,
                                y,
                                z,
                                pixel_selection=pixel_selection.method(),
                                tilesize=tilesize,
                                threads=threads,
                                **layer_params,
                                **dataset_params,
                            )
                        except (NoAssetFoundError, MosaicError, EmptyMosaicError) as e:
                            d = numpy.zeros((3, 256, 256))
                            m = numpy.zeros((256, 256)) + 256
                            data = ImageData(d, m)
            timings.append(("dataread", round((t.elapsed - mosaic_read) * 1000, 2)))

            if not format:
                format = ImageType.jpeg if data.mask.all() else ImageType.png

            with Timer() as t:
                image = data.post_process(**postprocess_params)
            timings.append(("postprocess", round(t.elapsed * 1000, 2)))

            with Timer() as t:
                content = image.render(
                    img_format=format.driver,
                    colormap=colormap,
                    **format.profile,
                    **render_params,
                )
            timings.append(("format", round(t.elapsed * 1000, 2)))

            if OptionalHeader.server_timing in self.optional_headers:
                headers["Server-Timing"] = ", ".join(
                    [f"{name};dur={time}" for (name, time) in timings]
                )

            if OptionalHeader.x_assets in self.optional_headers:
                headers["X-Assets"] = ",".join(data.assets)

            return Response(content, media_type=format.mediatype, headers=headers)

sd_mosaic = MosaicTiler(path_dependency=MosaicPathParams)



@dataclass
class S3Proxy(BaseTilerFactory):
    # Default reader is set to COGReader
    reader: Type[BaseReader] = COGReader

    # Endpoint Dependencies
    img_dependency: Type[DefaultDependency] = ImageParams
    """

    Note this is a really simple s3 proxy with only few endpoints.
    end points are cached
    and TITILER_MOSAIC_BACKEND is added to path if it exists
    """

    def register_routes(self):
        """This Method register routes to the router. """

        self.proxy()

    def proxy(self):

        @self.router.get(r"/list/{list_id}")
        @self.router.get(r"/geotiff/{drone_id}/{deployment_id}/{filename}")

        @cached(ttl=60)
        def list(
            list_id: str = Path(..., description="name of the list in s3"),
            cache_action: str = Query(
                "cache_read", description="Read from cache or overwrite"
            ),
        ):

            headers: Dict[str, str] = {}
            content: Dict[str, str] = {}

            client_kwargs = {}
            client_kwargs['region_name'] = DEFAULT_REGION

            s3 = boto3.client('s3', **client_kwargs)

            # need to remove the leading s3:// from the bucketname
            bucket = MOSAIC_BACKEND.split('/')[2]
              
            # and force the list to the right location
            key = "mosaic_maps/nrt/" + list_id
            response = s3.get_object(
              Bucket=bucket,
              Key=key
            )
            
            content = response['Body'].read()

            content = json.dumps(content, indent=4, sort_keys=True, default=str)

            if OptionalHeader.x_assets in self.optional_headers:
                headers["X-Assets"] = ",".join(data.assets)

            return Response(content, media_type="application/json", headers=headers)

        # cache for 24 hrs
        @cached(ttl=86400)
        def geotiff(
            drone_id: str = Path(..., description="drone id"),
            deployment_id: str = Path(..., description="deployment id"),
            filename: str = Path(..., description="filename for the geotiff to fetch"),
            cache_action: str = Query(
                "cache_read", description="Read from cache or overwrite"
            ),
        ):

            headers: Dict[str, str] = {}

            client_kwargs = {}
            client_kwargs['region_name'] = DEFAULT_REGION

            s3 = boto3.client('s3', **client_kwargs)

            # need to remove the leading s3:// from the bucketname
            bucket = MOSAIC_BACKEND.split('/')[2]
              
            # and force the list to the right location
            key = "geotiffs/nrt/" + drone_id + "/" + deployment_id + "/" + filename
            response = s3.get_object(
              Bucket=bucket,
              Key=key
            )

            content = response['Body'].read()

            if OptionalHeader.x_assets in self.optional_headers:
                headers["X-Assets"] = ",".join(data.assets)

            return Response(content, media_type=MediaType.tif.value, headers=headers)

sd_s3_proxy = S3Proxy()
