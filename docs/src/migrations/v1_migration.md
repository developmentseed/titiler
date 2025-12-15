# Migration Guide: TiTiler 0.26 to 1.0

This guide covers the breaking changes and new features when upgrading from TiTiler 0.26 to 1.0.

## Breaking Changes

### Data Type Changes

#### UINT8 Output for JPEG/PNG

**Impact:** High - Affects all automatic image format outputs

When no output format is explicitly specified, TiTiler now returns `UINT8` datatype for JPEG and PNG formats.

```python
# If your data needs specific datatypes, explicitly specify the format
# Example: Request with explicit format control
# In this case, if the input data is in uint16, the ouput png will be in UINT16
response = requests.get("/tiles/1/2/3.png?url=data_in_uint16.tif")
```

**Action Required:** Review your endpoints that rely on automatic format detection. If you need specific data type handling, consider explicitly specifying the output format and rescaling parameters.

### WMTS Changes

#### WMTS Endpoint Restructuring

**Impact:** High - Affects all WMTS usage

The `/{tileMatrixSetId}/WMTSCapabilities.xml` endpoints have been removed from the default factories. WMTS functionality is now provided through a dedicated extension.

```python
# Before (0.26)
# WMTS available at: /{tileMatrixSetId}/WMTSCapabilities.xml

# Now (1.0)
from titiler.extensions import wmtsExtension

# Add extension to factory
factory = TilerFactory(
    router_prefix="/cog",
    extensions=[wmtsExtension()]
)

# WMTS now available at: /WMTSCapabilities.xml
```

Additionally, the WMTS response now supports all TileMatrixSets as separate layers.

**Action Required:**
1. Add `wmtsExtension` to your factory configurations
2. Update client applications to use the new `/WMTSCapabilities.xml` endpoint path
3. Update any code that expects a single layer to handle multiple TileMatrixSets

### titiler.core Changes

#### Point Endpoint Response Model

**Impact:** Medium - Affects `/point` endpoint consumers

The `/point` endpoint now includes a `band_description` attribute in its response model.

```python
# Before (0.26)
class Point(BaseModel):
    coordinates: List[float]
    values: List[Optional[float]]
    # ... other fields

# Now (1.0)
class Point(BaseModel):
    coordinates: List[float]
    values: List[Optional[float]]
    band_description: List[str] | None  # New field
    # ... other fields
```

**Action Required:** Update client code that parses `/point` responses to handle the new `band_description` field.

### titiler.mosaic Changes

#### Point Endpoint Response Restructuring

**Impact:** High - Affects mosaic `/point` endpoint consumers

The response model for the mosaic `/point` endpoint has been completely restructured for better clarity.

```python
# Before (0.26)
class Point(BaseModel):
    coordinates: List[float]
    values: List[Tuple[str, List[Optional[float]], List[str]]]

# Now (1.0)
class AssetPoint(BaseModel):
    name: str
    values: list[float | None]
    band_names: list[str]
    band_descriptions: list[str] | None = None

class Point(BaseModel):
    coordinates: list[float]
    assets: list[AssetPoint]
```

**Migration Example:**
```python
# Before (0.26)
response = {
    "coordinates": [-122.5, 37.5],
    "values": [
        ("asset1", [100.0, 200.0], ["B1", "B2"]),
        ("asset2", [150.0, 250.0], ["B1", "B2"])
    ]
}

# Now (1.0)
response = {
    "coordinates": [-122.5, 37.5],
    "assets": [
        {
            "name": "asset1",
            "values": [100.0, 200.0],
            "band_names": ["B1", "B2"],
            "band_descriptions": None
        },
        {
            "name": "asset2",
            "values": [150.0, 250.0],
            "band_names": ["B1", "B2"],
            "band_descriptions": None
        }
    ]
}
```

**Action Required:** Update all client code that parses mosaic `/point` responses to use the new structure.

#### MosaicJSON Dependency Now Optional

**Impact:** Medium - Affects installations and imports

The `cogeo-mosaic` package is now an optional dependency.

```bash
# Before (0.26)
pip install titiler.mosaic

# Now (1.0) - Install with MosaicJSON support
pip install "titiler.mosaic[mosaicjson]"
```

**Action Required:** Update your installation commands if you use MosaicJSON functionality.

#### Backend Attribute No Longer Has Default

**Impact:** High - Affects custom mosaic implementations

The `MosaicTilerFactory.backend` attribute no longer has a default value and must be explicitly specified.

```python
# Before (0.26)
# Backend had a default value
factory = MosaicTilerFactory()

# Now (1.0)
# Must explicitly set backend
from titiler.mosaic.backends import MosaicBackend

factory = MosaicTilerFactory(
    backend=MosaicBackend
)
```

**Action Required:** Explicitly set the `backend` attribute when creating `MosaicTilerFactory` instances.

#### MosaicJSON Endpoints Moved to Extension

**Impact:** Medium - Affects mosaic endpoint structure

The `/` and `/validate` endpoints are now provided by the `MosaicJSONExtension` instead of being included by default.

```python
# Before (0.26)
# Endpoints available by default
factory = MosaicTilerFactory()

# Now (1.0)
from titiler.mosaic.extensions import MosaicJSONExtension

factory = MosaicTilerFactory(
    extensions=[MosaicJSONExtension()]
)
```

**Action Required:** Add `MosaicJSONExtension` to your factory if you need the `/` and `/validate` endpoints.

### titiler.extensions Changes

#### rio-cogeo Version Update

**Impact:** Low - Dependency version change

The `rio-cogeo` requirement has been updated to `7.0,<8.0`.

**Action Required:** Review the [rio-cogeo changelog](https://github.com/cogeotiff/rio-cogeo/blob/main/CHANGES.md) for any breaking changes that might affect your usage.

## New Features

### titiler.mosaic

#### New Optional Endpoints

Three new optional endpoints are available for mosaic operations:

- `/feature` - Feature-based queries
- `/bbox` - Bounding box queries
- `/statistics` - Statistical analysis

```python
# Enable in your factory
factory = MosaicTilerFactory(
    add_feature=True,  # Enables /feature endpoint
    add_bbox=True,     # Enables /bbox endpoint
    add_statistics=True # Enables /statistics endpoint
)
```

#### WMTS Extension for Mosaics

A dedicated WMTS extension is now available for mosaic factories:

```python
from titiler.mosaic.extensions import wmtsExtension

factory = MosaicTilerFactory(
    extensions=[wmtsExtension()]
)
```

#### OGC Maps API Support

Optional OGC Maps API `/map` endpoint is now available:

```python
factory = MosaicTilerFactory(
    add_map=True  # Enables /map endpoint
)
```

## Dependency Updates

### Core Dependencies

- `rio-tiler`: Updated to `>=8.0,<9.0`
- `rio-cogeo`: Updated to `7.0,<8.0`

**Action Required:** Test your application with the new versions and review their respective changelogs for any behavioral changes.

## Migration Checklist

Use this checklist to ensure a smooth migration:

- [ ] Update WMTS usage to use the new `wmtsExtension`
- [ ] Update client code parsing `/point` responses (both core and mosaic)
- [ ] Explicitly set `backend` attribute for `MosaicTilerFactory`
- [ ] Add `MosaicJSONExtension` if using MosaicJSON endpoints
- [ ] Update installation to include `[mosaicjson]` extra if needed
- [ ] Review and test automatic image format outputs (UINT8 behavior)
- [ ] Update dependency versions: `rio-tiler` and `rio-cogeo`
- [ ] Test with new Python 3.11+ requirement (from 0.25)
- [ ] Update any hardcoded WMTS endpoint paths in client applications
- [ ] Consider adopting new optional endpoints (`/feature`, `/bbox`, `/statistics`)
- [ ] Review OGC Maps API support for your use cases

## Getting Help

If you encounter issues during migration:

1. Check the [GitHub Issues](https://github.com/developmentseed/titiler/issues)
2. Review the [full CHANGELOG](https://github.com/developmentseed/titiler/blob/main/CHANGES.md)
3. Join the discussions in the [TiTiler repository](https://github.com/developmentseed/titiler)
