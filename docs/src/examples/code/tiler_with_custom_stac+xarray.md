
**Goal**: Create a custom STAC Reader supporting both COG and NetCDF/Zarr dataset

**requirements**:
- `titiler.core`
- `titiler.xarray`
- `fsspec`
- `zarr`
- `h5netcdf`
- `aiohttp` (optional)
- `s3fs` (optional)

**links**:

- https://cogeotiff.github.io/rio-tiler/examples/STAC_datacube_support/


#### 1. Custom STACReader

First, we need to create a custom `STACReader` which will support both COG and NetCDF/Zarr dataset. The custom parts will be:

- add `netcdf` and `zarr` as valid asset media types
- introduce a new `md://` prefixed asset form, so users can pass `assets=md://{netcdf asset name}?variable={variable name}` as we do for the `GDAL vrt string connection` support.

```python title="stac.py"
from typing import Set, Type, Tuple, Dict, Optional

import attr
from urllib.parse import urlparse, parse_qsl
from rio_tiler.types import AssetInfo
from rio_tiler.io import BaseReader, Reader
from rio_tiler.io import stac

from titiler.xarray.io import Reader as XarrayReader

valid_types = {
    *stac.DEFAULT_VALID_TYPE,
    "application/x-netcdf",
    "application/vnd+zarr",
}


@attr.s
class STACReader(stac.STACReader):
    """Custom STACReader which adds support for `md://` prefixed assets.

    Example:
    >>> with STACReader("https://raw.githubusercontent.com/cogeotiff/rio-tiler/refs/heads/main/tests/fixtures/stac_netcdf.json") as src:
            print(src.assets)
            print(src._get_asset_info("md://netcdf?variable=dataset"))

        ['geotiff', 'netcdf']
        {'url': 'https://raw.githubusercontent.com/cogeotiff/rio-tiler/refs/heads/main/tests/fixtures/dataset_2d.nc', 'metadata': {}, 'reader_options': {'variable': 'dataset'}, 'media_type': 'application/x-netcdf'}

    """
    include_asset_types: Set[str] = attr.ib(default=valid_types)

    def _get_reader(self, asset_info: AssetInfo) -> Tuple[Type[BaseReader], Dict]:
        """Get Asset Reader."""
        asset_type = asset_info.get("media_type", None)
        if asset_type and asset_type in [
            "application/x-netcdf",
            "application/vnd+zarr",
            "application/x-hdf5",
            "application/x-hdf",
        ]:
            return XarrayReader, asset_info.get("reader_options", {})

        return Reader, asset_info.get("reader_options", {})

    def _parse_md_asset(self, asset: str) -> Tuple[str, Optional[Dict]]:
        """Parse md:// asset string and return both asset name and reader options"""
        if asset.startswith("md://") and asset not in self.assets:
            parsed = urlparse(asset)
            if not parsed.netloc or parsed.netloc not in self.assets:
                raise InvalidAssetName(
                    f"'{parsed.netloc}' is not valid, should be one of {self.assets}"
                )

            # NOTE: by using `parse_qsl` we assume the
            # reader_options are in form of `key=single_value`
            # reader_options for XarrayReader are:
            # - variable: str
            # - group: Optional[str]
            # - decode_times: bool = True
            # - datetime: Optional[str]
            # - drop_dim: Optional[str]
            return parsed.netloc, dict(parse_qsl(parsed.query))

        return asset, None

    def _get_asset_info(self, asset: str) -> AssetInfo:
        """Validate asset names and return asset's info.

        Args:
            asset (str): STAC asset name.

        Returns:
            AssetInfo: STAC asset info.

        """
        vrt_options = None
        reader_options = None
        if asset.startswith("vrt://"):
            asset, vrt_options = self._parse_vrt_asset(asset)

        # not part of the original STACReader
        elif asset.startswith("md://"):
            asset, reader_options = self._parse_md_asset(asset)

        if asset not in self.assets:
            raise InvalidAssetName(
                f"'{asset}' is not valid, should be one of {self.assets}"
            )

        asset_info = self.item.assets[asset]
        extras = asset_info.extra_fields

        info = AssetInfo(
            url=asset_info.get_absolute_href() or asset_info.href,
            metadata=extras if not vrt_options else None,
            reader_options=reader_options or {}
        )

        if stac.STAC_ALTERNATE_KEY and extras.get("alternate"):
            if alternate := extras["alternate"].get(stac.STAC_ALTERNATE_KEY):
                info["url"] = alternate["href"]

        if asset_info.media_type:
            info["media_type"] = asset_info.media_type

        # https://github.com/stac-extensions/file
        if head := extras.get("file:header_size"):
            info["env"] = {"GDAL_INGESTED_BYTES_AT_OPEN": head}

        # https://github.com/stac-extensions/raster
        if extras.get("raster:bands") and not vrt_options:
            bands = extras.get("raster:bands")
            stats = [
                (b["statistics"]["minimum"], b["statistics"]["maximum"])
                for b in bands
                if {"minimum", "maximum"}.issubset(b.get("statistics", {}))
            ]
            # check that stats data are all double and make warning if not
            if (
                stats
                and all(isinstance(v, (int, float)) for stat in stats for v in stat)
                and len(stats) == len(bands)
            ):
                info["dataset_statistics"] = stats
            else:
                warnings.warn(
                    "Some statistics data in STAC are invalid, they will be ignored."
                )

        if vrt_options:
            info["url"] = f"vrt://{info['url']}?{vrt_options}"

        return info
```

#### 2. Endpoint Factory

Custom `MultiBaseTilerFactory` which removes some endpoints (`/preview`) and adapt dependencies to work with both COG and Xarray Datasets.

```python title="factory.py"
"""Custom MultiBaseTilerFactory."""
from dataclasses import dataclass
from typing import Type, Union, Optional, List
from typing_extensions import Annotated
from attrs import define, field
from geojson_pydantic.features import Feature, FeatureCollection
from fastapi import Body, Depends, Query
from titiler.core import factory
from titiler.core.dependencies import (
    DefaultDependency,
    BidxParams,
    AssetsParams,
    AssetsBidxExprParamsOptional,
    CoordCRSParams,
    DstCRSParams,
)
from titiler.core.models.responses import MultiBaseStatisticsGeoJSON
from titiler.core.resources.responses import GeoJSONResponse
from rio_tiler.constants import WGS84_CRS
from rio_tiler.io import MultiBaseReader

from stac import STACReader


# Simple Asset dependency (1 asset, no expression)
@dataclass
class SingleAssetsParams(DefaultDependency):
    """Custom Assets parameters which only accept ONE asset and make it required."""

    assets: Annotated[
        str,
        Query(title="Asset names", description="Asset's name."),
    ]

    indexes: Annotated[
        Optional[List[int]],
        Query(
            title="Band indexes",
            alias="bidx",
            description="Dataset band indexes",
            openapi_examples={
                "one-band": {"value": [1]},
                "multi-bands": {"value": [1, 2, 3]},
            },
        ),
    ] = None


@define(kw_only=True)
class MultiBaseTilerFactory(factory.MultiBaseTilerFactory):

    reader: Type[MultiBaseReader] = STACReader

    # Assets/Indexes/Expression dependency
    layer_dependency: Type[DefaultDependency] = SingleAssetsParams

    # Assets dependency (for /info endpoints)
    assets_dependency: Type[DefaultDependency] = AssetsParams

    # remove preview endpoints
    img_preview_dependency: Type[DefaultDependency] = field(init=False)
    add_preview: bool = field(init=False, default=False)

    # Overwrite the `/statistics` endpoint to remove `full` dataset statistics (which could be unusable for NetCDF dataset)
    def statistics(self):  # noqa: C901
        """Register /statistics endpoint."""

        @self.router.post(
            "/statistics",
            response_model=MultiBaseStatisticsGeoJSON,
            response_model_exclude_none=True,
            response_class=GeoJSONResponse,
            responses={
                200: {
                    "content": {"application/geo+json": {}},
                    "description": "Return dataset's statistics from feature or featureCollection.",
                }
            },
        )
        def geojson_statistics(
            geojson: Annotated[
                Union[FeatureCollection, Feature],
                Body(description="GeoJSON Feature or FeatureCollection."),
            ],
            src_path=Depends(self.path_dependency),
            reader_params=Depends(self.reader_dependency),
            layer_params=Depends(AssetsBidxExprParamsOptional),
            dataset_params=Depends(self.dataset_dependency),
            coord_crs=Depends(CoordCRSParams),
            dst_crs=Depends(DstCRSParams),
            post_process=Depends(self.process_dependency),
            image_params=Depends(self.img_part_dependency),
            stats_params=Depends(self.stats_dependency),
            histogram_params=Depends(self.histogram_dependency),
            env=Depends(self.environment_dependency),
        ):
            """Get Statistics from a geojson feature or featureCollection."""
            fc = geojson
            if isinstance(fc, Feature):
                fc = FeatureCollection(type="FeatureCollection", features=[geojson])

            with rasterio.Env(**env):
                with self.reader(src_path, **reader_params.as_dict()) as src_dst:
                    # Default to all available assets
                    if not layer_params.assets and not layer_params.expression:
                        layer_params.assets = src_dst.assets

                    for feature in fc:
                        image = src_dst.feature(
                            feature.model_dump(exclude_none=True),
                            shape_crs=coord_crs or WGS84_CRS,
                            dst_crs=dst_crs,
                            align_bounds_with_dataset=True,
                            **layer_params.as_dict(),
                            **image_params.as_dict(),
                            **dataset_params.as_dict(),
                        )

                        if post_process:
                            image = post_process(image)

                        stats = image.statistics(
                            **stats_params.as_dict(),
                            hist_options=histogram_params.as_dict(),
                        )

                    feature.properties = feature.properties or {}
                    # NOTE: because we use `src_dst.feature` the statistics will be in form of
                    # `Dict[str, BandStatistics]` and not `Dict[str, Dict[str, BandStatistics]]`
                    feature.properties.update({"statistics": stats})

            return fc.features[0] if isinstance(geojson, Feature) else fc
```

#### 3. Application

```python title="main.py"
"""FastAPI application."""

from fastapi import FastAPI

from titiler.core.dependencies import DatasetPathParams
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers

from factory import MultiBaseTilerFactory

# STAC uses MultiBaseReader so we use MultiBaseTilerFactory to built the default endpoints
stac = MultiBaseTilerFactory(router_prefix="stac")

# Create FastAPI application
app = FastAPI()
app.include_router(stac.router, tags=["STAC"])
add_exception_handlers(app, DEFAULT_STATUS_CODES)
```

```
uvicorn app:app --port 8080 --reload
```

<img width="800" alt="Screenshot 2024-11-07 at 4 42 21 PM" src="https://github.com/user-attachments/assets/2b68500e-c1a7-4461-90bd-67bb492e6057">


```bash
curl http://127.0.0.1:8080/assets\?url\=https%3A%2F%2Fraw.githubusercontent.com%2Fcogeotiff%2Frio-tiler%2Frefs%2Fheads%2Fmain%2Ftests%2Ffixtures%2Fstac_netcdf.json | jq

[
  "geotiff",
  "netcdf"
]
```

```bash
curl http://127.0.0.1:8080/info?url=https://raw.githubusercontent.com/cogeotiff/rio-tiler/refs/heads/main/tests/fixtures/stac_netcdf.json&assets=md://netcdf?variable=dataset  | jq
{
  "md://netcdf?variable=dataset": {
    "bounds": [
      -170.085,
      -80.08,
      169.914999999975,
      79.91999999999659
    ],
    "crs": "http://www.opengis.net/def/crs/EPSG/0/4326",
    "band_metadata": [
      [
        "b1",
        {}
      ]
    ],
    "band_descriptions": [
      [
        "b1",
        "value"
      ]
    ],
    "dtype": "float64",
    "nodata_type": "Nodata",
    "name": "dataset",
    "count": 1,
    "width": 2000,
    "height": 1000,
    "attrs": {
      "valid_min": 1.0,
      "valid_max": 1000.0,
      "fill_value": 0
    }
  }
}
```

```bash
curl http://127.0.0.1:8080/tiles/WebMercatorQuad/1/0/0?url=https://raw.githubusercontent.com/cogeotiff/rio-tiler/refs/heads/main/tests/fixtures/stac_netcdf.json&assets=md://netcdf?variable=dataset&rescale=0,1000
```
