"""TiTiler GIS tools."""

from typing import Dict, Optional, Type, Union

import rasterio
from geojson_pydantic.features import Feature, FeatureCollection
from geojson_pydantic.geometries import Polygon
from morecantile import TileMatrixSet
from rio_tiler.io import BaseReader
from rio_tiler.models import BandStatistics, Bounds, Info
from rio_tiler.utils import get_array_statistics

from titiler.core.resources.enums import ImageType, MediaType
from titiler.core.utils import Timer

from starlette.requests import Request
from starlette.templating import Jinja2Templates

try:
    from importlib.resources import files as resources_files  # type: ignore
except ImportError:
    # Try backported to PY<39 `importlib_resources`.
    from importlib_resources import files as resources_files  # type: ignore

# TODO: mypy fails in python 3.9, we need to find a proper way to do this
templates = Jinja2Templates(directory=str(resources_files(__package__) / "templates"))  # type: ignore


def info_geojson(
    reader: Type[BaseReader],
    env: Dict,
    src_path: str,
    reader_params: Dict,
    info_params: Dict = {},
) -> Feature:
    """Return dataset's basic info as a GeoJSON feature."""
    with rasterio.Env(**env):
        with reader(src_path, **reader_params) as src_dst:
            return Feature(
                geometry=Polygon.from_bounds(*src_dst.geographic_bounds),
                properties=src_dst.info(**info_params),
            )


def info_geojson_multi(
    reader: Type[BaseReader],
    env: Dict,
    src_path: str,
    reader_params: Dict,
    asset_params: Dict,
) -> Feature:
    """Return dataset's basic info as a GeoJSON feature."""
    with rasterio.Env(**env):
        with reader(src_path, **reader_params) as src_dst:
            return Feature(
                geometry=Polygon.from_bounds(*src_dst.geographic_bounds),
                properties={
                    asset: asset_info
                    for asset, asset_info in src_dst.info(**asset_params).items()
                },
            )


def info(
    reader: Type[BaseReader],
    env: Dict,
    src_path: str,
    reader_params: Dict,
    info_params={},
) -> Info:
    """Return dataset's basic info."""
    with rasterio.Env(**env):
        with reader(src_path, **reader_params) as src_dst:
            return src_dst.info(**info_params)


def assets(reader: Type[BaseReader], env: Dict, src_path: str, reader_params) -> Info:
    """Return a list of supported assets."""
    with rasterio.Env(**env):
        with reader(src_path, **reader_params) as src_dst:
            return src_dst.assets


def bands(reader: Type[BaseReader], env: Dict, src_path: str, reader_params) -> Info:
    """Return a list of supported bands."""
    with rasterio.Env(**env):
        with reader(src_path, **reader_params) as src_dst:
            return src_dst.bands


def bounds(reader: Type[BaseReader], env: Dict, src_path: str, reader_params) -> Bounds:
    """Return the bounds of the COG."""
    with rasterio.Env(**env):
        with reader(src_path, **reader_params) as src_dst:
            return {"bounds": src_dst.geographic_bounds}


def statistics(
    reader: Type[BaseReader],
    env: Dict,
    src_path: str,
    reader_params: Dict,
    stats_params,
    histogram_params,
    layer_params=None,
) -> Dict[str, BandStatistics]:
    """Get Dataset statistics."""
    with rasterio.Env(**env):
        with reader(src_path, **reader_params) as src_dst:
            # Default to all available assets
            if layer_params:
                if not layer_params.assets and not layer_params.expression:
                    layer_params.assets = src_dst.assets
                stats_params = {**stats_params, **layer_params}

                return src_dst.merged_statistics(
                    **stats_params,
                    hist_options={**histogram_params},
                )
            else:
                return src_dst.statistics(
                    **stats_params,
                    hist_options={**histogram_params},
                )


def geojson_statistics(
    reader: Type[BaseReader],
    env: Dict,
    src_path: str,
    reader_params: Dict,
    geojson: Union[FeatureCollection, Feature],
    feature_params,
    stats_params,
    layer_params=None,
    bands_params=None,
):
    """Get Statistics from a geojson feature or featureCollection."""
    with rasterio.Env(**env):
        with reader(src_path, **reader_params) as src_dst:
            # Default to all available assets
            if layer_params:
                if not layer_params.assets and not layer_params.expression:
                    layer_params.assets = src_dst.assets
                feature_params = {**feature_params, **layer_params}

            # Default to all available bands
            if bands_params:
                if not bands_params.bands and not bands_params.expression:
                    bands_params.bands = src_dst.bands
                feature_params = {**feature_params, **bands_params}

            # TODO: stream features for FeatureCollection
            if isinstance(geojson, FeatureCollection):
                for feature in geojson:
                    data = src_dst.feature(
                        feature.dict(exclude_none=True),
                        **feature_params,
                    )
                    stats = get_array_statistics(
                        data.as_masked(),
                        **stats_params,
                    )

                feature.properties = feature.properties or {}
                feature.properties.update(
                    {
                        # NOTE: because we use `src_dst.feature` the statistics will be in form of
                        # `Dict[str, BandStatistics]` and not `Dict[str, Dict[str, BandStatistics]]`
                        "statistics": {
                            f"{data.band_names[ix]}": BandStatistics(**stats[ix])
                            for ix in range(len(stats))
                        }
                    }
                )

            else:  # simple feature
                data = src_dst.feature(
                    geojson.dict(exclude_none=True),
                    **feature_params,
                )
                stats = get_array_statistics(
                    data.as_masked(),
                    **stats_params,
                )

                geojson.properties = geojson.properties or {}
                geojson.properties.update(
                    {
                        "statistics": {
                            f"{data.band_names[ix]}": BandStatistics(**stats[ix])
                            for ix in range(len(stats))
                        }
                    }
                )

            return geojson


def tile(
    reader: Type[BaseReader],
    env: Dict,
    src_path: str,
    reader_params: Dict,
    z: int,
    x: int,
    y: int,
    tms: TileMatrixSet,
    scale: int,
    format: ImageType,
    tile_params: Dict,
    postprocess_params: Dict,
    colormap,
    render_params,
    tile_buffer: Optional[float],
):
    """Create map tile from a dataset."""
    timings = []

    tilesize = scale * 256

    with Timer() as t:
        with rasterio.Env(**env):
            with reader(src_path, tms=tms, **reader_params) as src_dst:
                data = src_dst.tile(
                    x, y, z, tilesize=tilesize, tile_buffer=tile_buffer, **tile_params
                )
                dst_colormap = getattr(src_dst, "colormap", None)
    timings.append(("dataread", round(t.elapsed * 1000, 2)))

    if not format:
        format = ImageType.jpeg if data.mask.all() else ImageType.png

    with Timer() as t:
        image = data.post_process(**postprocess_params)
    timings.append(("postprocess", round(t.elapsed * 1000, 2)))

    with Timer() as t:
        content = image.render(
            img_format=format.driver,
            colormap=colormap or dst_colormap,
            **format.profile,
            **render_params,
        )
    timings.append(("format", round(t.elapsed * 1000, 2)))

    return content, timings, format


def tilejson(
    reader: Type[BaseReader],
    env: Dict,
    src_path: str,
    reader_params: Dict,
    tiles_url: str,
    minzoom: Optional[int],
    maxzoom: Optional[int],
    tms: TileMatrixSet,
) -> Dict:
    """Return TileJSON document for a dataset."""
    with rasterio.Env(**env):
        with reader(src_path, tms=tms, **reader_params) as src_dst:
            return {
                "bounds": src_dst.geographic_bounds,
                "minzoom": minzoom if minzoom is not None else src_dst.minzoom,
                "maxzoom": maxzoom if maxzoom is not None else src_dst.maxzoom,
                "tiles": [tiles_url],
            }


def wmts(
    reader: Type[BaseReader],
    env: Dict,
    src_path: str,
    reader_params: Dict,
    request: Request,
    tile_format: ImageType,
    tms: TileMatrixSet,
    tiles_url: str,
    minzoom: Optional[int] = None,
    maxzoom: Optional[int] = None,
):
    """Returns a WMTS xml document."""
    with rasterio.Env(**env):
        with reader(src_path, tms=tms, **reader_params) as src_dst:
            bounds = src_dst.geographic_bounds
            minzoom = minzoom if minzoom is not None else src_dst.minzoom
            maxzoom = maxzoom if maxzoom is not None else src_dst.maxzoom

    tileMatrix = []
    for zoom in range(minzoom, maxzoom + 1):
        matrix = tms.matrix(zoom)
        tm = f"""
                <TileMatrix>
                    <ows:Identifier>{matrix.identifier}</ows:Identifier>
                    <ScaleDenominator>{matrix.scaleDenominator}</ScaleDenominator>
                    <TopLeftCorner>{matrix.topLeftCorner[0]} {matrix.topLeftCorner[1]}</TopLeftCorner>
                    <TileWidth>{matrix.tileWidth}</TileWidth>
                    <TileHeight>{matrix.tileHeight}</TileHeight>
                    <MatrixWidth>{matrix.matrixWidth}</MatrixWidth>
                    <MatrixHeight>{matrix.matrixHeight}</MatrixHeight>
                </TileMatrix>"""
        tileMatrix.append(tm)

    return templates.TemplateResponse(
        "wmts.xml",
        {
            "request": request,
            "tiles_endpoint": tiles_url,
            "bounds": bounds,
            "tileMatrix": tileMatrix,
            "tms": tms,
            "title": "Cloud Optimized GeoTIFF",
            "layer_name": "cogeo",
            "media_type": tile_format.mediatype,
        },
        media_type=MediaType.xml.value,
    )


def point(
    reader: Type[BaseReader],
    env: Dict,
    src_path: str,
    reader_params: Dict,
    lon: float,
    lat: float,
    layer_params,
    dataset_params,
):
    """Get Point value for a dataset."""
    with rasterio.Env(**env):
        with reader(src_path, **reader_params) as src_dst:
            values = src_dst.point(
                lon,
                lat,
                **layer_params,
                **dataset_params,
            )
            return {"coordinates": [lon, lat], "values": values}


def preview(
    reader: Type[BaseReader],
    env: Dict,
    src_path,
    reader_params,
    format: ImageType,
    preview_params,
    postprocess_params,
    colormap,
    render_params,
):
    """Create preview of a dataset."""
    timings = []

    with Timer() as t:
        with rasterio.Env(**env):
            with reader(src_path, **reader_params) as src_dst:
                data = src_dst.preview(**preview_params)
                dst_colormap = getattr(src_dst, "colormap", None)
    timings.append(("dataread", round(t.elapsed * 1000, 2)))

    if not format:
        format = ImageType.jpeg if data.mask.all() else ImageType.png

    with Timer() as t:
        image = data.post_process(**postprocess_params)
    timings.append(("postprocess", round(t.elapsed * 1000, 2)))

    with Timer() as t:
        content = image.render(
            img_format=format.driver,
            colormap=colormap or dst_colormap,
            **format.profile,
            **render_params,
        )
    timings.append(("format", round(t.elapsed * 1000, 2)))

    return content, timings, format


def part(
    reader: Type[BaseReader],
    env: Dict,
    src_path: str,
    reader_params: Dict,
    minx: float,
    miny: float,
    maxx: float,
    maxy: float,
    format: ImageType,
    part_params,
    postprocess_params,
    colormap,
    render_params,
):
    """Create image from part of a dataset."""
    timings = []

    with Timer() as t:
        with rasterio.Env(**env):
            with reader(src_path, **reader_params) as src_dst:
                data = src_dst.part([minx, miny, maxx, maxy], **part_params)
                dst_colormap = getattr(src_dst, "colormap", None)
    timings.append(("dataread", round(t.elapsed * 1000, 2)))

    with Timer() as t:
        image = data.post_process(**postprocess_params)
    timings.append(("postprocess", round(t.elapsed * 1000, 2)))

    with Timer() as t:
        content = image.render(
            img_format=format.driver,
            colormap=colormap or dst_colormap,
            **format.profile,
            **render_params,
        )
    timings.append(("format", round(t.elapsed * 1000, 2)))

    return timings, content


def geojson_crop(
    reader: Type[BaseReader],
    env: Dict,
    src_path: str,
    reader_params: Dict,
    geojson: Feature,
    format: ImageType,
    feature_params,
    postprocess_params,
    colormap,
    render_params,
):
    """Create image from a geojson feature."""
    timings = []

    with Timer() as t:
        with rasterio.Env(**env):
            with reader(src_path, **reader_params) as src_dst:
                data = src_dst.feature(
                    geojson.dict(exclude_none=True),
                    **feature_params,
                )
                dst_colormap = getattr(src_dst, "colormap", None)
    timings.append(("dataread", round(t.elapsed * 1000, 2)))

    with Timer() as t:
        image = data.post_process(**postprocess_params)
    timings.append(("postprocess", round(t.elapsed * 1000, 2)))

    if not format:
        format = ImageType.jpeg if data.mask.all() else ImageType.png

    with Timer() as t:
        content = image.render(
            img_format=format.driver,
            colormap=colormap or dst_colormap,
            **format.profile,
            **render_params,
        )
    timings.append(("format", round(t.elapsed * 1000, 2)))
    return timings, content, format
