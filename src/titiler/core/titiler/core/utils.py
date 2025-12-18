"""titiler.core utilities."""

from __future__ import annotations

import re
import warnings
from collections.abc import Callable, Sequence
from typing import Any, TypeVar, cast
from urllib.parse import urlencode

import numpy
from fastapi import FastAPI
from fastapi.datastructures import QueryParams
from fastapi.dependencies.utils import get_dependant, request_params_to_args
from geojson_pydantic.geometries import MultiPolygon, Polygon
from morecantile import TileMatrixSet
from rasterio.dtypes import dtype_ranges
from rio_tiler.colormap import apply_cmap
from rio_tiler.errors import InvalidDatatypeWarning
from rio_tiler.models import ImageData
from rio_tiler.types import BBox, ColorMapType, IntervalTuple
from rio_tiler.utils import linear_rescale, render
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route, request_response
from starlette.templating import Jinja2Templates, _TemplateResponse

from titiler.core.resources.enums import ImageType, MediaType


def rescale_array(
    array: numpy.ndarray,
    mask: numpy.ndarray,
    in_range: Sequence[IntervalTuple],
    out_range: Sequence[IntervalTuple] = ((0, 255),),
    out_dtype: str | numpy.number = "uint8",
) -> numpy.ndarray:
    """Rescale data array"""
    if len(array.shape) < 3:
        array = numpy.expand_dims(array, axis=0)

    nbands = array.shape[0]
    if len(in_range) != nbands:
        in_range = ((in_range[0]),) * nbands

    if len(out_range) != nbands:
        out_range = ((out_range[0]),) * nbands

    for bdx in range(nbands):
        array[bdx] = numpy.where(
            mask[bdx],
            linear_rescale(
                array[bdx], in_range=in_range[bdx], out_range=out_range[bdx]
            ),
            0,
        )

    return array.astype(out_dtype)


def render_image(  # noqa: C901
    image: ImageData,
    colormap: ColorMapType | None = None,
    output_format: ImageType | None = None,
    add_mask: bool = True,
    rescale: Sequence[IntervalTuple] | None = None,
    color_formula: str | None = None,
    **kwargs: Any,
) -> tuple[bytes, str]:
    """convert image data to file.

    This is adapted from https://github.com/cogeotiff/rio-tiler/blob/066878704f841a332a53027b74f7e0a97f10f4b2/rio_tiler/models.py#L698-L764
    """
    if rescale:
        image.rescale(rescale)

    if color_formula:
        image.apply_color_formula(color_formula)

    data, mask = image.data.copy(), image.mask.copy()
    input_range = dtype_ranges[str(data.dtype)]
    output_range = image.dataset_statistics or (input_range,)

    if colormap:
        data, alpha_from_cmap = apply_cmap(data, colormap)
        output_range = (dtype_ranges[str(data.dtype)],)
        # Combine both Mask from dataset and Alpha band from Colormap
        mask = numpy.where(
            mask != input_range[0], alpha_from_cmap, output_range[0][0]
        ).astype(data.dtype)

    # format-specific valid dtypes
    format_dtypes = {
        ImageType.png: ["uint8", "uint16"],
        ImageType.jpeg: ["uint8"],
        ImageType.jpg: ["uint8"],
        ImageType.webp: ["uint8"],
        ImageType.jp2: ["uint8", "int16", "uint16"],
    }

    # If output_format is not set, we choose between JPEG and PNG
    if not output_format:
        # Check if any alpha value == min datatype value (== Masked)
        is_masked = (mask == dtype_ranges[str(mask.dtype)][0]).any()
        output_format = ImageType.png if is_masked else ImageType.jpeg
        # For automatic format we make sure the output datatype
        # will be the same for both JPEG and PNG
        format_dtypes[ImageType.png] = ["uint8"]

    valid_dtypes = format_dtypes.get(output_format, [])
    if valid_dtypes and data.dtype not in valid_dtypes:
        warnings.warn(
            f"Invalid type: `{data.dtype}` for the `{output_format}` driver. "
            "Data will be rescaled using min/max type bounds or dataset_statistics.",
            InvalidDatatypeWarning,
            stacklevel=1,
        )
        data = rescale_array(data, mask, in_range=output_range)

    creation_options = {**kwargs, **output_format.profile}
    if output_format.driver == "GTiff":
        if "transform" not in creation_options:
            creation_options.update({"transform": image.transform})
        if "crs" not in creation_options and image.crs:
            creation_options.update({"crs": image.crs})

    if add_mask:
        content = render(
            data,
            mask,
            img_format=output_format.driver,
            **creation_options,
        )
    else:
        content = render(
            data,
            img_format=output_format.driver,
            **creation_options,
        )

    return content, output_format.mediatype


def bounds_to_geometry(bounds: BBox) -> Polygon | MultiPolygon:
    """Convert bounds to geometry.

    Note: if bounds are crossing the dateline separation line, a MultiPolygon geometry will be returned.

    """
    if bounds[0] > bounds[2]:
        pl = Polygon.from_bounds(-180, bounds[1], bounds[2], bounds[3])
        pr = Polygon.from_bounds(bounds[0], bounds[1], 180, bounds[3])
        return MultiPolygon(
            type="MultiPolygon",
            coordinates=[pl.coordinates, pr.coordinates],
        )
    return Polygon.from_bounds(*bounds)


T = TypeVar("T")

ValidParams = dict[str, Any]
Errors = list[Any]


def get_dependency_query_params(
    dependency: Callable,
    params: QueryParams | dict,
) -> tuple[ValidParams, Errors]:
    """Check QueryParams for Query dependency.

    1. `get_dependant` is used to get the query-parameters required by the `callable`
    2. we use `request_params_to_args` to construct arguments needed to call the `callable`
    3. we call the `callable` and catch any errors

    Important: We assume the `callable` in not a co-routine.
    """
    dep = get_dependant(path="", call=dependency)

    qp = (
        QueryParams(urlencode(params, doseq=True))
        if isinstance(params, dict)
        else params
    )
    return request_params_to_args(dep.query_params, qp)


def deserialize_query_params(
    dependency: Callable[..., T], params: QueryParams | dict
) -> tuple[T, Errors]:
    """Deserialize QueryParams for given dependency.

    Parse params as query params and deserialize with dependency.

    Important: We assume the `callable` in not a co-routine.
    """
    values, errors = get_dependency_query_params(dependency, params)
    return dependency(**values), errors


def extract_query_params(
    dependencies: list[Callable],
    params: QueryParams | dict,
) -> tuple[ValidParams, Errors]:
    """Extract query params given list of dependencies."""
    values = {}
    errors = []
    for dep in dependencies:
        query_params, dep_errors = get_dependency_query_params(dep, params)
        if query_params:
            values.update(query_params)
        errors += dep_errors
    return values, errors


def check_query_params(
    dependencies: list[Callable], params: QueryParams | dict
) -> bool:
    """Check QueryParams for Query dependency.

    1. `get_dependant` is used to get the query-parameters required by the `callable`
    2. we use `request_params_to_args` to construct arguments needed to call the `callable`
    3. we call the `callable` and catch any errors

    Important: We assume the `callable` in not a co-routine

    """
    qp = (
        QueryParams(urlencode(params, doseq=True))
        if isinstance(params, dict)
        else params
    )

    for dependency in dependencies:
        try:
            dep = get_dependant(path="", call=dependency)
            if dep.query_params:
                # call the dependency with the query-parameters values
                query_values, errors = request_params_to_args(dep.query_params, qp)
                if errors:
                    return False

                _ = dependency(**query_values)

        except Exception:
            return False

    return True


def accept_media_type(accept: str, mediatypes: list[MediaType]) -> MediaType | None:
    """Return MediaType based on accept header and available mediatype.

    Links:
    - https://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html
    - https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Accept

    """
    accept_values = {}
    for m in accept.replace(" ", "").split(","):
        values = m.split(";")
        if len(values) == 1:
            name = values[0]
            quality = 1.0
        else:
            name = values[0]
            groups = dict([param.split("=") for param in values[1:]])  # type: ignore
            try:
                q = groups.get("q")
                quality = float(q) if q else 1.0
            except ValueError:
                quality = 0

        # if quality is 0 we ignore encoding
        if quality:
            accept_values[name] = quality

    # Create Preference matrix
    media_preference = {
        v: [n for (n, q) in accept_values.items() if q == v]
        for v in sorted(set(accept_values.values()), reverse=True)
    }

    # Loop through available compression and encoding preference
    for _, pref in media_preference.items():
        for media in mediatypes:
            if media.value in pref:
                return media

    # If no specified encoding is supported but "*" is accepted,
    # take one of the available compressions.
    if "*" in accept_values and mediatypes:
        return mediatypes[0]

    return None


def update_openapi(app: FastAPI) -> FastAPI:
    """Update OpenAPI response content-type.

    This function modifies the openapi route to comply with the STAC API spec's required
    content-type response header.

    Copied from https://github.com/stac-utils/stac-fastapi/blob/main/stac_fastapi/api/stac_fastapi/api/openapi.py

    MIT License

    Copyright (c) 2020 Arturo AI

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
    """
    # Find the route for the openapi_url in the app
    openapi_route: Route = next(
        cast(Route, route)
        for route in app.router.routes
        if route.path == app.openapi_url  # type: ignore
    )
    # Store the old endpoint function so we can call it from the patched function
    old_endpoint = openapi_route.endpoint

    # Create a patched endpoint function that modifies the content type of the response
    async def patched_openapi_endpoint(req: Request) -> Response:
        # Get the response from the old endpoint function
        response = await old_endpoint(req)
        # Update the content type header in place
        response.headers["content-type"] = (
            "application/vnd.oai.openapi+json;version=3.0"
        )
        # Return the updated response
        return response

    # When a Route is accessed the `handle` function calls `self.app`. Which is
    # the endpoint function wrapped with `request_response`. So we need to wrap
    # our patched function and replace the existing app with it.
    openapi_route.app = request_response(patched_openapi_endpoint)

    # return the patched app
    return app


def create_html_response(
    request: Request,
    data: Any,
    template_name: str,
    templates: Jinja2Templates,
    title: str | None = None,
    router_prefix: str | None = None,
    **kwargs: Any,
) -> _TemplateResponse:
    """Create Template response."""
    urlpath = request.url.path
    if root_path := request.scope.get("root_path"):
        urlpath = re.sub(r"^" + root_path, "", urlpath)

    if router_prefix:
        urlpath = re.sub(r"^" + router_prefix, "", urlpath)

    crumbs = []
    baseurl = str(request.base_url).rstrip("/")

    if router_prefix:
        baseurl += router_prefix

    crumbpath = str(baseurl)
    if urlpath == "/":
        urlpath = ""

    for crumb in urlpath.split("/"):
        crumbpath = crumbpath.rstrip("/")
        part = crumb
        if part is None or part == "":
            part = "Home"
        crumbpath += f"/{crumb}"
        crumbs.append({"url": crumbpath.rstrip("/"), "part": part.capitalize()})

    return templates.TemplateResponse(
        request,
        name=f"{template_name}.html",
        context={
            "response": data,
            "template": {
                "api_root": baseurl,
                "params": request.query_params,
                "title": title or template_name,
            },
            "crumbs": crumbs,
            "url": baseurl + urlpath,
            "params": str(request.url.query),
            **kwargs,
        },
    )


def tms_limits(
    tms: TileMatrixSet,
    bounds: tuple[float, float, float, float],
    zooms: tuple[int, int] | None = None,
) -> list[dict[str, Any]]:
    """Generate TileMatrixSet limits for given bounds and zoom levels."""
    if zooms:
        minzoom, maxzoom = zooms
    else:
        minzoom, maxzoom = tms.minzoom, tms.maxzoom

    tilematrix_limits: list[dict[str, Any]] = []
    for zoom in range(minzoom, maxzoom + 1):
        matrix = tms.matrix(zoom)
        ulTile = tms.tile(bounds[0], bounds[3], zoom)
        lrTile = tms.tile(bounds[2], bounds[1], zoom)
        minx, maxx = (min(ulTile.x, lrTile.x), max(ulTile.x, lrTile.x))
        miny, maxy = (min(ulTile.y, lrTile.y), max(ulTile.y, lrTile.y))
        tilematrix_limits.append(
            {
                "tileMatrix": matrix.id,
                "minTileRow": max(miny, 0),
                "maxTileRow": min(maxy, matrix.matrixHeight),
                "minTileCol": max(minx, 0),
                "maxTileCol": min(maxx, matrix.matrixWidth),
            }
        )

    return tilematrix_limits
