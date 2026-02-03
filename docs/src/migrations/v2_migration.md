# Migrating from TiTiler 1.x to 2.0

!!! note

    This migration guide was generated with the help of Claude AI and may require review.


This document describes the breaking changes and migration steps required when upgrading from TiTiler 1.1.1 to 2.0.0.

## Overview

TiTiler 2.0.0 introduces several breaking changes primarily focused on:

1. **Tile sizing**: Replaced `tile_scale` with direct `tilesize` parameter
2. **Dependency simplification**: Removed per-asset band indexes (`bidx`) support for multi-asset readers
3. **rio-tiler 9.0 compatibility**: Removed `MultiBandTilerFactory` and related classes

## Breaking Changes

### 1. Tile Size Parameter Changes

#### Removed: `tile_scale` and `@{scale}x` suffix

The `tile_scale` parameter and `@{scale}x` URL suffix have been removed from all endpoints.

**Before (1.x):**
```
GET /tiles/WebMercatorQuad/10/512/384@2x.png?url=...
GET /tilejson.json?url=...&tile_scale=2
GET /map.html?url=...&tile_scale=2
GET /WMTSCapabilities.xml?url=...&tile_scale=2
```

**After (2.0):**
```
GET /tiles/WebMercatorQuad/10/512/384.png?url=...&tilesize=512
GET /tilejson.json?url=...&tilesize=512
GET /map.html?url=...&tilesize=256
GET /WMTSCapabilities.xml?url=...  # can't overwrite tilesize anymore
```

#### New: `tilesize` query parameter

A new `tilesize` query parameter is available for tile and tilejson endpoints:

| Endpoint | Old Default | New Default |
|----------|-------------|-------------|
| `/tiles/{tms}/{z}/{x}/{y}` | 256x256 (scale=1) | TileMatrix's `tileHeight x tileWidth` |
| `/tilejson.json` | 256 | 512 |
| `/map.html` | 256 | 256 |

**Migration Steps:**
1. Replace `@2x` suffix with `tilesize=512` query parameter
2. Replace `@4x` suffix with `tilesize=1024` query parameter
3. Replace `tile_scale=N` with `tilesize=N*256` query parameter
4. Update any client code that constructs tile URLs with scale suffix

### 2. Dependency Class Renames

Several dependency classes have been renamed to reflect their simplified functionality.

#### Renamed Classes

| Old Name (1.x) | New Name (2.0) |
|----------------|----------------|
| `AssetsBidxExprParamsOptional` | `AssetsExprParamsOptional` |
| `AssetsBidxExprParams` | `AssetsExprParams` |

**Migration Steps:**
```python
# Before (1.x)
from titiler.core.dependencies import AssetsBidxExprParams, AssetsBidxExprParamsOptional

# After (2.0)
from titiler.core.dependencies import AssetsExprParams, AssetsExprParamsOptional
```

#### Removed Classes

The following classes have been removed entirely:

- `titiler.core.dependencies.AssetsBidxParams`
- `titiler.core.dependencies.BandsParams`
- `titiler.core.dependencies.BandsExprParamsOptional`
- `titiler.core.dependencies.BandsExprParams`

**Migration Steps:**

If you were using `BandsParams` or `BandsExprParams` with a custom `MultiBandReader`:
- Consider migrating to a `MultiBaseReader` approach with assets
- Or use expressions to select specific bands

### 3. Removed Functions

The following functions have been removed:

- `titiler.core.dependencies.parse_asset_indexes()`
- `titiler.core.dependencies.parse_asset_expression()`

These were used internally for parsing `asset_indexes` and `asset_expression` query parameters.

### 4. Removed: `MultiBandTilerFactory`

The `MultiBandTilerFactory` class has been completely removed because `MultiBandReader` is no longer available in rio-tiler 9.0.

**Before (1.x):**
```python
from titiler.core.factory import MultiBandTilerFactory
from rio_tiler.io import MultiBandReader

class MyBandReader(MultiBandReader):
    ...

tiler = MultiBandTilerFactory(reader=MyBandReader)
```

**Migration Steps:**

1. Convert your `MultiBandReader` to a `MultiBaseReader` that exposes bands as assets
2. Use `MultiBaseTilerFactory` instead

```python
# After (2.0)
from titiler.core.factory import MultiBaseTilerFactory
from rio_tiler.io import MultiBaseReader

class MyAssetReader(MultiBaseReader):
    # Expose bands as assets
    ...

tiler = MultiBaseTilerFactory(reader=MyAssetReader)
```

### 5. `bidx` Parameter Ignored for MultiBaseReader

The `bidx` (band index) parameter is now **ignored** by `MultiBaseTilerFactory` endpoints. Previously, you could use `bidx` to select bands across all assets.

**Before (1.x):**
```
GET /stac/tiles/WebMercatorQuad/10/512/384.png?url=...&assets=B02&assets=B03&bidx=1
```

**After (2.0):**

Use new `asset` notation: `assets={AssetName}|indexes=1,2,3`

```
GET /stac/tiles/WebMercatorQuad/10/512/384.png?url=...&assets=B02|indexes=1&assets=B03|indexes=1
```

### 6. Removed: `asset_indexes` and `asset_expression` Options

The `asset_indexes` and `asset_expression` query parameters have been removed from `dependencies.py`.

**Before (1.x):**
```
GET /stac/preview.png?url=...&asset_indexes=data|1,2,3
GET /stac/preview.png?url=...&asset_expression=data|b1*b2
```

**After (2.0):**

Use new `asset` notation: `assets={AssetName}|indexes=1,2,3` or `assets={AssetName}|expression=b1*2`

```
GET /stac/preview.png?url=...&assets=B01|indexes=1,2,3
GET /stac/preview.png?url=...&assets=B01|expression=b1*2
```

### 7. Extension Changes

#### COG and STAC Viewers

The `cogViewerExtension` and `stacViewerExtension` now force `tilesize=256` in their tile requests.

#### WMTS Capabilities

The `tile_scale` parameter has been removed from `/WMTSCapabilities.xml` endpoints in both `titiler.extensions` and `titiler.mosaic`.

## API Endpoint Changes Summary

| Endpoint Pattern | Change |
|-----------------|--------|
| `/tiles/{tms}/{z}/{x}/{y}@{scale}x` | **Removed** - Use `tilesize` query param |
| `/tiles/{tms}/{z}/{x}/{y}@{scale}x.{format}` | **Removed** - Use `tilesize` query param |
| `/tilejson.json?tile_scale=N` | **Removed** - Use `tilesize=N*256` |
| `/map.html?tile_scale=N` | **Removed** - Use `tilesize=N*256` |
| `/WMTSCapabilities.xml?tile_scale=N` | **Removed** |

## Code Migration Checklist

- [ ] Replace all `@{scale}x` tile URL suffixes with `tilesize` parameter
- [ ] Replace `tile_scale` query parameter with `tilesize`
- [ ] Update imports: `AssetsBidxExprParams` → `AssetsExprParams`
- [ ] Update imports: `AssetsBidxExprParamsOptional` → `AssetsExprParamsOptional`
- [ ] Remove usage of `AssetsBidxParams`, `BandsParams`, `BandsExprParams`, `BandsExprParamsOptional`
- [ ] Migrate `MultiBandTilerFactory` usage to `MultiBaseTilerFactory`
- [ ] Remove `bidx` parameter from multi-asset requests (use `expression` instead)
- [ ] Remove `asset_indexes` and `asset_expression` parameters

## Dependency Updates

TiTiler 2.0 requires:
- rio-tiler >= 9.0

Make sure to update your `pyproject.toml` accordingly.

## Need Help?

If you encounter issues during migration:
- Check the [CHANGES.md](https://github.com/developmentseed/titiler/blob/main/CHANGES.md) for detailed release notes
- Open an issue at [https://github.com/developmentseed/titiler/issues](https://github.com/developmentseed/titiler/issues)
