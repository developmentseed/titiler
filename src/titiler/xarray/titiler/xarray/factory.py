"""TiTiler.xarray factory."""

from dataclasses import dataclass
from typing import Dict, List, Literal, Optional, Type, Union
from urllib.parse import urlencode

import jinja2
import numpy as np
from fastapi import Depends, Path, Query
from pydantic import conint
from rio_tiler.models import Info
from starlette.requests import Request
from starlette.responses import HTMLResponse, Response
from starlette.templating import Jinja2Templates
from typing_extensions import Annotated

from titiler.core.dependencies import ColorFormulaParams
from titiler.core.factory import BaseTilerFactory, img_endpoint_params
from titiler.core.models.mapbox import TileJSON
from titiler.core.resources.enums import ImageType
from titiler.core.resources.responses import JSONResponse
from titiler.core.utils import render_image
from titiler.xarray.reader import ZarrReader


def nodata_dependency(
    nodata: Annotated[
        Optional[Union[str, int, float]],
        Query(
            title="Nodata value",
            description="Overwrite internal Nodata value",
        ),
    ] = None,
) -> Optional[float]:
    """Nodata dependency."""
    if nodata is not None:
        nodata = np.nan if nodata == "nan" else float(nodata)

    return None


@dataclass
class ZarrTilerFactory(BaseTilerFactory):
    """Zarr Tiler Factory."""

    reader: Type[ZarrReader] = ZarrReader

    def register_routes(self) -> None:  # noqa: C901
        """Register Info / Tiles / TileJSON endoints."""

        @self.router.get(
            "/variables",
            response_class=JSONResponse,
            responses={200: {"description": "Return dataset's Variables."}},
        )
        def variable_endpoint(
            url: Annotated[str, Query(description="Dataset URL")],
            group: Annotated[
                Optional[int],
                Query(
                    description="Select a specific zarr group from a zarr hierarchy. Could be associated with a zoom level or dataset."
                ),
            ] = None,
            reference: Annotated[
                Optional[bool],
                Query(
                    title="reference",
                    description="Whether the dataset is a kerchunk reference",
                ),
            ] = False,
            decode_times: Annotated[
                Optional[bool],
                Query(
                    title="decode_times",
                    description="Whether to decode times",
                ),
            ] = True,
            consolidated: Annotated[
                Optional[bool],
                Query(
                    title="consolidated",
                    description="Whether to expect and open zarr store with consolidated metadata",
                ),
            ] = True,
        ) -> List[str]:
            """return available variables."""
            return self.reader.list_variables(
                url, group=group, reference=reference, consolidated=consolidated
            )

        @self.router.get(
            "/info",
            response_model=Info,
            response_model_exclude_none=True,
            response_class=JSONResponse,
            responses={200: {"description": "Return dataset's basic info."}},
        )
        def info_endpoint(
            url: Annotated[str, Query(description="Dataset URL")],
            variable: Annotated[
                str,
                Query(description="Xarray Variable"),
            ],
            group: Annotated[
                Optional[int],
                Query(
                    description="Select a specific zarr group from a zarr hierarchy, can be for pyramids or datasets. Can be used to open a dataset in HDF5 files."
                ),
            ] = None,
            reference: Annotated[
                bool,
                Query(
                    title="reference",
                    description="Whether the dataset is a kerchunk reference",
                ),
            ] = False,
            decode_times: Annotated[
                bool,
                Query(
                    title="decode_times",
                    description="Whether to decode times",
                ),
            ] = True,
            drop_dim: Annotated[
                Optional[str],
                Query(description="Dimension to drop"),
            ] = None,
            show_times: Annotated[
                Optional[bool],
                Query(description="Show info about the time dimension"),
            ] = None,
            consolidated: Annotated[
                Optional[bool],
                Query(
                    title="consolidated",
                    description="Whether to expect and open zarr store with consolidated metadata",
                ),
            ] = True,
        ) -> Info:
            """Return dataset's basic info."""
            with self.reader(
                url,
                variable=variable,
                group=group,
                reference=reference,
                decode_times=decode_times,
                drop_dim=drop_dim,
                consolidated=consolidated,
            ) as src_dst:
                info = src_dst.info().model_dump()
                if show_times and "time" in src_dst.input.dims:
                    times = [str(x.data) for x in src_dst.input.time]
                    info["count"] = len(times)
                    info["times"] = times

            return Info(**info)

        @self.router.get(r"/tiles/{z}/{x}/{y}", **img_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}.{format}", **img_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}@{scale}x", **img_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}@{scale}x.{format}", **img_endpoint_params)
        @self.router.get(r"/tiles/{tileMatrixSetId}/{z}/{x}/{y}", **img_endpoint_params)
        @self.router.get(
            r"/tiles/{tileMatrixSetId}/{z}/{x}/{y}.{format}", **img_endpoint_params
        )
        @self.router.get(
            r"/tiles/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x", **img_endpoint_params
        )
        @self.router.get(
            r"/tiles/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x.{format}",
            **img_endpoint_params,
        )
        def tiles_endpoint(  # type: ignore
            z: Annotated[
                int,
                Path(
                    description="Identifier (Z) selecting one of the scales defined in the TileMatrixSet and representing the scaleDenominator the tile.",
                ),
            ],
            x: Annotated[
                int,
                Path(
                    description="Column (X) index of the tile on the selected TileMatrix. It cannot exceed the MatrixHeight-1 for the selected TileMatrix.",
                ),
            ],
            y: Annotated[
                int,
                Path(
                    description="Row (Y) index of the tile on the selected TileMatrix. It cannot exceed the MatrixWidth-1 for the selected TileMatrix.",
                ),
            ],
            url: Annotated[str, Query(description="Dataset URL")],
            variable: Annotated[
                str,
                Query(description="Xarray Variable"),
            ],
            tileMatrixSetId: Annotated[  # type: ignore
                Literal[tuple(self.supported_tms.list())],
                f"Identifier selecting one of the TileMatrixSetId supported (default: '{self.default_tms}')",
            ] = self.default_tms,
            scale: Annotated[  # type: ignore
                conint(gt=0, le=4), "Tile size scale. 1=256x256, 2=512x512..."
            ] = 1,
            format: Annotated[
                ImageType,
                "Default will be automatically defined if the output image needs a mask (png) or not (jpeg).",
            ] = None,
            multiscale: Annotated[
                bool,
                Query(
                    title="multiscale",
                    description="Whether the dataset has multiscale groups (Zoom levels)",
                ),
            ] = False,
            reference: Annotated[
                bool,
                Query(
                    title="reference",
                    description="Whether the dataset is a kerchunk reference",
                ),
            ] = False,
            decode_times: Annotated[
                bool,
                Query(
                    title="decode_times",
                    description="Whether to decode times",
                ),
            ] = True,
            drop_dim: Annotated[
                Optional[str],
                Query(description="Dimension to drop"),
            ] = None,
            datetime: Annotated[
                Optional[str], Query(description="Slice of time to read (if available)")
            ] = None,
            post_process=Depends(self.process_dependency),
            rescale=Depends(self.rescale_dependency),
            color_formula=Depends(ColorFormulaParams),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            consolidated: Annotated[
                Optional[bool],
                Query(
                    title="consolidated",
                    description="Whether to expect and open zarr store with consolidated metadata",
                ),
            ] = True,
            nodata=Depends(nodata_dependency),
        ) -> Response:
            """Create map tile from a dataset."""
            tms = self.supported_tms.get(tileMatrixSetId)
            with self.reader(
                url,
                variable=variable,
                group=z if multiscale else None,
                reference=reference,
                decode_times=decode_times,
                drop_dim=drop_dim,
                datetime=datetime,
                tms=tms,
                consolidated=consolidated,
            ) as src_dst:
                image = src_dst.tile(
                    x,
                    y,
                    z,
                    tilesize=scale * 256,
                    nodata=nodata if nodata is not None else src_dst.input.rio.nodata,
                )

            if post_process:
                image = post_process(image)

            if rescale:
                image.rescale(rescale)

            if color_formula:
                image.apply_color_formula(color_formula)

            content, media_type = render_image(
                image,
                output_format=format,
                colormap=colormap,
                **render_params,
            )

            return Response(content, media_type=media_type)

        @self.router.get(
            "/tilejson.json",
            response_model=TileJSON,
            responses={200: {"description": "Return a tilejson"}},
            response_model_exclude_none=True,
        )
        @self.router.get(
            "/{tileMatrixSetId}/tilejson.json",
            response_model=TileJSON,
            responses={200: {"description": "Return a tilejson"}},
            response_model_exclude_none=True,
        )
        def tilejson_endpoint(  # type: ignore
            request: Request,
            url: Annotated[str, Query(description="Dataset URL")],
            variable: Annotated[
                str,
                Query(description="Xarray Variable"),
            ],
            tileMatrixSetId: Annotated[  # type: ignore
                Literal[tuple(self.supported_tms.list())],
                f"Identifier selecting one of the TileMatrixSetId supported (default: '{self.default_tms}')",
            ] = self.default_tms,
            group: Annotated[
                Optional[int],
                Query(
                    description="Select a specific zarr group from a zarr hierarchy, can be for pyramids or datasets. Can be used to open a dataset in HDF5 files."
                ),
            ] = None,
            reference: Annotated[
                bool,
                Query(
                    title="reference",
                    description="Whether the dataset is a kerchunk reference",
                ),
            ] = False,
            decode_times: Annotated[
                bool,
                Query(
                    title="decode_times",
                    description="Whether to decode times",
                ),
            ] = True,
            drop_dim: Annotated[
                Optional[str],
                Query(description="Dimension to drop"),
            ] = None,
            datetime: Annotated[
                Optional[str], Query(description="Slice of time to read (if available)")
            ] = None,
            tile_format: Annotated[
                Optional[ImageType],
                Query(
                    description="Default will be automatically defined if the output image needs a mask (png) or not (jpeg).",
                ),
            ] = None,
            tile_scale: Annotated[
                int,
                Query(
                    gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
                ),
            ] = 1,
            minzoom: Annotated[
                Optional[int],
                Query(description="Overwrite default minzoom."),
            ] = None,
            maxzoom: Annotated[
                Optional[int],
                Query(description="Overwrite default maxzoom."),
            ] = None,
            post_process=Depends(self.process_dependency),
            rescale=Depends(self.rescale_dependency),
            color_formula=Depends(ColorFormulaParams),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            consolidated: Annotated[
                Optional[bool],
                Query(
                    title="consolidated",
                    description="Whether to expect and open zarr store with consolidated metadata",
                ),
            ] = True,
            nodata=Depends(nodata_dependency),
        ) -> Dict:
            """Return TileJSON document for a dataset."""
            route_params = {
                "z": "{z}",
                "x": "{x}",
                "y": "{y}",
                "scale": tile_scale,
                "tileMatrixSetId": tileMatrixSetId,
            }
            if tile_format:
                route_params["format"] = tile_format.value
            tiles_url = self.url_for(request, "tiles_endpoint", **route_params)

            qs_key_to_remove = [
                "tilematrixsetid",
                "tile_format",
                "tile_scale",
                "minzoom",
                "maxzoom",
                "group",
            ]
            qs = [
                (key, value)
                for (key, value) in request.query_params._list
                if key.lower() not in qs_key_to_remove
            ]
            if qs:
                tiles_url += f"?{urlencode(qs)}"

            tms = self.supported_tms.get(tileMatrixSetId)

            with self.reader(
                url,
                variable=variable,
                group=group,
                reference=reference,
                decode_times=decode_times,
                tms=tms,
                consolidated=consolidated,
            ) as src_dst:
                # see https://github.com/corteva/rioxarray/issues/645
                minx, miny, maxx, maxy = zip(
                    [-180, -90, 180, 90], list(src_dst.geographic_bounds)
                )
                bounds = [max(minx), max(miny), min(maxx), min(maxy)]

                return {
                    "bounds": bounds,
                    "minzoom": minzoom if minzoom is not None else src_dst.minzoom,
                    "maxzoom": maxzoom if maxzoom is not None else src_dst.maxzoom,
                    "tiles": [tiles_url],
                }

        @self.router.get(
            "/histogram",
            response_class=JSONResponse,
            responses={200: {"description": "Return histogram for this data variable"}},
            response_model_exclude_none=True,
        )
        def histogram(
            url: Annotated[str, Query(description="Dataset URL")],
            variable: Annotated[
                str,
                Query(description="Xarray Variable"),
            ],
            reference: Annotated[
                bool,
                Query(
                    title="reference",
                    description="Whether the dataset is a kerchunk reference",
                ),
            ] = False,
            consolidated: Annotated[
                bool,
                Query(
                    title="consolidated",
                    description="Whether to expect a consolidated dataset",
                ),
            ] = True,
            group: Annotated[
                Optional[int],
                Query(
                    description="Select a specific zarr group from a zarr hierarchy, can be for pyramids or datasets. Can be used to open a dataset in HDF5 files."
                ),
            ] = None,
        ):
            with self.reader(
                url,
                variable=variable,
                reference=reference,
                consolidated=consolidated,
                group=group,
            ) as src_dst:
                boolean_mask = ~np.isnan(src_dst.input)
                data_values = src_dst.input.values[boolean_mask]
                counts, values = np.histogram(data_values, bins=10)
                counts, values = counts.tolist(), values.tolist()
                buckets = list(
                    zip(values, [values[i + 1] for i in range(len(values) - 1)])
                )
                hist_dict = []
                for idx, bucket in enumerate(buckets):
                    hist_dict.append({"bucket": bucket, "value": counts[idx]})
                return hist_dict

        @self.router.get("/map", response_class=HTMLResponse)
        @self.router.get("/{tileMatrixSetId}/map", response_class=HTMLResponse)
        def map_viewer(
            request: Request,
            url: Annotated[Optional[str], Query(description="Dataset URL")] = None,
            tileMatrixSetId: Annotated[  # type: ignore
                Literal[tuple(self.supported_tms.list())],
                f"Identifier selecting one of the TileMatrixSetId supported (default: '{self.default_tms}')",
            ] = self.default_tms,
            variable: Annotated[
                Optional[str],
                Query(description="Xarray Variable"),
            ] = None,
            group: Annotated[
                Optional[int],
                Query(
                    description="Select a specific zarr group from a zarr hierarchy, can be for pyramids or datasets. Can be used to open a dataset in HDF5 files."
                ),
            ] = None,
            reference: Annotated[
                bool,
                Query(
                    title="reference",
                    description="Whether the dataset is a kerchunk reference",
                ),
            ] = False,
            decode_times: Annotated[
                bool,
                Query(
                    title="decode_times",
                    description="Whether to decode times",
                ),
            ] = True,
            drop_dim: Annotated[
                Optional[str],
                Query(description="Dimension to drop"),
            ] = None,
            datetime: Annotated[
                Optional[str], Query(description="Slice of time to read (if available)")
            ] = None,
            tile_format: Annotated[
                Optional[ImageType],
                Query(
                    description="Default will be automatically defined if the output image needs a mask (png) or not (jpeg).",
                ),
            ] = None,
            tile_scale: Annotated[
                int,
                Query(
                    gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
                ),
            ] = 1,
            minzoom: Annotated[
                Optional[int],
                Query(description="Overwrite default minzoom."),
            ] = None,
            maxzoom: Annotated[
                Optional[int],
                Query(description="Overwrite default maxzoom."),
            ] = None,
            post_process=Depends(self.process_dependency),
            rescale=Depends(self.rescale_dependency),
            color_formula=Depends(ColorFormulaParams),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            nodata=Depends(nodata_dependency),
        ):
            """Return map Viewer."""
            templates = Jinja2Templates(
                directory="",
                loader=jinja2.ChoiceLoader([jinja2.PackageLoader(__package__, ".")]),
            )
            if url:
                tilejson_url = self.url_for(
                    request, "tilejson_endpoint", tileMatrixSetId=tileMatrixSetId
                )
                if request.query_params._list:
                    tilejson_url += f"?{urlencode(request.query_params._list)}"

                tms = self.supported_tms.get(tileMatrixSetId)
                return templates.TemplateResponse(
                    name="map.html",
                    context={
                        "request": request,
                        "tilejson_endpoint": tilejson_url,
                        "tms": tms,
                        "resolutions": [matrix.cellSize for matrix in tms],
                    },
                    media_type="text/html",
                )
            else:
                return templates.TemplateResponse(
                    name="map-form.html",
                    context={
                        "request": request,
                    },
                    media_type="text/html",
                )
