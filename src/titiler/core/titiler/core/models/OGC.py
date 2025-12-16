"""OGC models."""

from datetime import datetime
from typing import Annotated, Literal

from morecantile.models import CRSType
from pydantic import AnyUrl, BaseModel, Field, RootModel

from titiler.core.models.common import Link


class TileMatrixSetRef(BaseModel):
    """
    TileMatrixSetRef model.

    Based on http://docs.opengeospatial.org/per/19-069.html#_tilematrixsets
    """

    id: str
    title: str | None = None
    links: list[Link]


class TileMatrixSetList(BaseModel):
    """
    TileMatrixSetList model.

    Based on http://docs.opengeospatial.org/per/19-069.html#_tilematrixsets
    """

    tileMatrixSets: list[TileMatrixSetRef]


class TimeStamp(RootModel):
    """TimeStamp model.

    Ref: https://github.com/opengeospatial/ogcapi-tiles/blob/master/openapi/schemas/common-geodata/timeStamp.yaml

    Code generated using https://github.com/koxudaxi/datamodel-code-generator/
    """

    root: Annotated[
        datetime,
        Field(
            json_schema_extra={
                "description": "This property indicates the time and date when the response was generated using RFC 3339 notation.",
                "examples": ["2017-08-17T08:05:32Z"],
            }
        ),
    ]


class BoundingBox(BaseModel):
    """BoundingBox model.

    Ref: https://github.com/opengeospatial/ogcapi-tiles/blob/master/openapi/schemas/tms/2DBoundingBox.yaml

    Code generated using https://github.com/koxudaxi/datamodel-code-generator/
    """

    lowerLeft: Annotated[
        list[float],
        Field(
            max_length=2,
            min_length=2,
            json_schema_extra={
                "description": "A 2D Point in the CRS indicated elsewhere",
            },
        ),
    ]
    upperRight: Annotated[
        list[float],
        Field(
            max_length=2,
            min_length=2,
            json_schema_extra={
                "description": "A 2D Point in the CRS indicated elsewhere",
            },
        ),
    ]
    crs: Annotated[CRSType | None, Field(json_schema_extra={"title": "CRS"})] = None
    orderedAxes: Annotated[list[str] | None, Field(max_length=2, min_length=2)] = None


# Ref: https://github.com/opengeospatial/ogcapi-tiles/blob/master/openapi/schemas/tms/propertiesSchema.yaml
Type = Literal["array", "boolean", "integer", "null", "number", "object", "string"]

# Ref: https://github.com/opengeospatial/ogcapi-tiles/blob/master/openapi/schemas/tms/propertiesSchema.yaml
AccessConstraints = Literal[
    "unclassified", "restricted", "confidential", "secret", "topSecret"
]


class Properties(BaseModel):
    """Properties model.

    Ref: https://github.com/opengeospatial/ogcapi-tiles/blob/master/openapi/schemas/tms/propertiesSchema.yaml

    Code generated using https://github.com/koxudaxi/datamodel-code-generator/
    """

    title: str | None = None
    description: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "description": "Implements 'description'",
            }
        ),
    ] = None
    type: Type | None = None
    enum: Annotated[
        set | None,
        Field(
            min_length=1,
            json_schema_extra={
                "description": "Implements 'acceptedValues'",
            },
        ),
    ] = None
    format: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "description": "Complements implementation of 'type'",
            }
        ),
    ] = None
    contentMediaType: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "description": "Implements 'mediaType'",
            }
        ),
    ] = None
    maximum: Annotated[
        float | None,
        Field(
            json_schema_extra={
                "description": "Implements 'range'",
            }
        ),
    ] = None
    exclusiveMaximum: Annotated[
        float | None,
        Field(
            json_schema_extra={
                "description": "Implements 'range'",
            }
        ),
    ] = None
    minimum: Annotated[
        float | None,
        Field(
            json_schema_extra={
                "description": "Implements 'range'",
            }
        ),
    ] = None
    exclusiveMinimum: Annotated[
        float | None,
        Field(
            json_schema_extra={
                "description": "Implements 'range'",
            }
        ),
    ] = None
    pattern: str | None = None
    maxItems: Annotated[
        int | None,
        Field(
            ge=0,
            json_schema_extra={
                "description": "Implements 'upperMultiplicity'",
            },
        ),
    ] = None
    minItems: Annotated[
        int | None,
        Field(
            ge=0,
            json_schema_extra={
                "description": "Implements 'lowerMultiplicity'",
            },
        ),
    ] = 0
    observedProperty: str | None = None
    observedPropertyURI: AnyUrl | None = None
    uom: str | None = None
    uomURI: AnyUrl | None = None


class PropertiesSchema(BaseModel):
    """PropertiesSchema model.

    Ref: https://github.com/opengeospatial/ogcapi-tiles/blob/master/openapi/schemas/tms/propertiesSchema.yaml

    Code generated using https://github.com/koxudaxi/datamodel-code-generator/
    """

    type: Literal["object"]
    required: Annotated[
        list[str] | None,
        Field(
            min_length=1,
            json_schema_extra={
                "description": "Implements 'multiplicity' by citing property 'name' defined as 'additionalProperties'",
            },
        ),
    ] = None
    properties: dict[str, Properties]


class Style(BaseModel):
    """Style model.

    Ref: https://github.com/opengeospatial/ogcapi-tiles/blob/master/openapi/schemas/tms/style.yaml

    Code generated using https://github.com/koxudaxi/datamodel-code-generator/
    """

    id: Annotated[
        str,
        Field(
            json_schema_extra={
                "description": "An identifier for this style. Implementation of 'identifier'",
            }
        ),
    ]
    title: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "description": "A title for this style",
            }
        ),
    ] = None
    description: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "description": "Brief narrative description of this style",
            }
        ),
    ] = None
    keywords: Annotated[
        list[str] | None,
        Field(
            json_schema_extra={
                "description": "keywords about this style",
            }
        ),
    ] = None
    links: Annotated[
        list[Link] | None,
        Field(
            min_length=1,
            json_schema_extra={
                "description": "Links to style related resources. Possible link 'rel' values are: 'style' for a URL pointing to the style description, 'styleSpec' for a URL pointing to the specification or standard used to define the style.",
            },
        ),
    ] = None


class GeospatialData(BaseModel):
    """Geospatial model.

    Ref: https://github.com/opengeospatial/ogcapi-tiles/blob/master/openapi/schemas/tms/geospatialData.yaml

    Code generated using https://github.com/koxudaxi/datamodel-code-generator/
    """

    title: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "description": "Title of this tile matrix set, normally used for display to a human",
            }
        ),
    ] = None
    description: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "description": "Brief narrative description of this tile matrix set, normally available for display to a human",
            }
        ),
    ] = None
    keywords: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "description": "Unordered list of one or more commonly used or formalized word(s) or phrase(s) used to describe this layer",
            }
        ),
    ] = None
    id: Annotated[
        str,
        Field(
            json_schema_extra={
                "description": "Unique identifier of the Layer. Implementation of 'identifier'",
            }
        ),
    ]
    dataType: Annotated[
        Literal["map", "vector", "coverage"],
        Field(
            json_schema_extra={
                "description": "Type of data represented in the tileset",
            }
        ),
    ]
    geometryDimension: Annotated[
        int | None,
        Field(  # type: ignore
            ge=0,
            le=3,
            json_schema_extra={
                "description": "The geometry dimension of the features shown in this layer (0: points, 1: curves, 2: surfaces, 3: solids), unspecified: mixed or unknown",
            },
        ),
    ] = None
    featureType: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "description": "Feature type identifier. Only applicable to layers of datatype 'geometries'",
            }
        ),
    ] = None
    attribution: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "description": "Short reference to recognize the author or provider",
            }
        ),
    ] = None
    license: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "description": "License applicable to the tiles",
            }
        ),
    ] = None
    pointOfContact: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "description": "Useful information to contact the authors or custodians for the layer (e.g. e-mail address, a physical address,  phone numbers, etc)",
            }
        ),
    ] = None
    publisher: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "description": "Organization or individual responsible for making the layer available",
            }
        ),
    ] = None
    theme: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "description": "Category where the layer can be grouped",
            }
        ),
    ] = None
    crs: Annotated[CRSType | None, Field(json_schema_extra={"title": "CRS"})] = None
    epoch: Annotated[
        float | None,
        Field(
            json_schema_extra={
                "description": "Epoch of the Coordinate Reference System (CRS)",
            }
        ),
    ] = None
    minScaleDenominator: Annotated[
        float | None,
        Field(
            json_schema_extra={
                "description": "Minimum scale denominator for usage of the layer",
            }
        ),
    ] = None
    maxScaleDenominator: Annotated[
        float | None,
        Field(
            json_schema_extra={
                "description": "Maximum scale denominator for usage of the layer",
            }
        ),
    ] = None
    minCellSize: Annotated[
        float | None,
        Field(
            json_schema_extra={
                "description": "Minimum cell size for usage of the layer",
            }
        ),
    ] = None
    maxCellSize: Annotated[
        float | None,
        Field(
            json_schema_extra={
                "description": "Maximum cell size for usage of the layer",
            }
        ),
    ] = None
    maxTileMatrix: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "description": "TileMatrix identifier associated with the minScaleDenominator",
            }
        ),
    ] = None
    minTileMatrix: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "description": "TileMatrix identifier associated with the maxScaleDenominator",
            }
        ),
    ] = None
    boundingBox: BoundingBox | None = None
    created: TimeStamp | None = None
    updated: TimeStamp | None = None
    style: Style | None = None
    geoDataClasses: Annotated[
        list[str] | None,
        Field(
            json_schema_extra={
                "description": "URI identifying a class of data contained in this layer (useful to determine compatibility with styles or processes)",
            }
        ),
    ] = None
    propertiesSchema: PropertiesSchema | None = None
    links: Annotated[
        list[Link] | None,
        Field(
            min_length=1,
            json_schema_extra={
                "description": "Links related to this layer. Possible link 'rel' values are: 'geodata' for a URL pointing to the collection of geospatial data.",
            },
        ),
    ] = None


class TilePoint(BaseModel):
    """TilePoint model.

    Ref: https://github.com/opengeospatial/ogcapi-tiles/blob/master/openapi/schemas/tms/tilePoint.yaml

    Code generated using https://github.com/koxudaxi/datamodel-code-generator/
    """

    coordinates: Annotated[list[float], Field(max_length=2, min_length=2)]
    crs: Annotated[CRSType | None, Field(json_schema_extra={"title": "CRS"})]
    tileMatrix: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "description": "TileMatrix identifier associated with the scaleDenominator",
            }
        ),
    ] = None
    scaleDenominator: Annotated[
        float | None,
        Field(
            json_schema_extra={
                "description": "Scale denominator of the tile matrix selected",
            }
        ),
    ] = None
    cellSize: Annotated[
        float | None,
        Field(
            json_schema_extra={
                "description": "Cell size of the tile matrix selected",
            }
        ),
    ] = None


class TileMatrixLimits(BaseModel):
    """
    The limits for an individual tile matrix of a TileSet's TileMatrixSet, as defined in the OGC 2D TileMatrixSet and TileSet Metadata Standard

    Based on https://github.com/opengeospatial/ogcapi-tiles/blob/master/openapi/schemas/tms/tileMatrixLimits.yaml
    """

    tileMatrix: str
    minTileRow: Annotated[int, Field(ge=0)]
    maxTileRow: Annotated[int, Field(ge=0)]
    minTileCol: Annotated[int, Field(ge=0)]
    maxTileCol: Annotated[int, Field(ge=0)]


class TileSet(BaseModel):
    """
    TileSet model.

    Based on https://github.com/opengeospatial/ogcapi-tiles/blob/master/openapi/schemas/tms/tileSet.yaml
    """

    title: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "description": "A title for this tileset",
            }
        ),
    ] = None
    description: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "description": "Brief narrative description of this tile set",
            }
        ),
    ] = None
    dataType: Annotated[
        Literal["map", "vector", "coverage"],
        Field(
            json_schema_extra={
                "description": "Type of data represented in the tileset",
            }
        ),
    ]
    crs: Annotated[CRSType, Field(json_schema_extra={"title": "CRS"})]
    tileMatrixSetURI: Annotated[
        AnyUrl | None,
        Field(
            json_schema_extra={
                "description": "Reference to a Tile Matrix Set on an official source for Tile Matrix Sets",
            }
        ),
    ] = None
    links: Annotated[
        list[Link],
        Field(
            json_schema_extra={
                "description": "Links to related resources",
            }
        ),
    ]
    tileMatrixSetLimits: Annotated[
        list[TileMatrixLimits] | None,
        Field(
            json_schema_extra={
                "description": "Limits for the TileRow and TileCol values for each TileMatrix in the tileMatrixSet. If missing, there are no limits other that the ones imposed by the TileMatrixSet. If present the TileMatrices listed are limited and the rest not available at all",
            }
        ),
    ] = None
    epoch: Annotated[
        float | int | None,
        Field(
            json_schema_extra={
                "description": "Epoch of the Coordinate Reference System (CRS)",
            }
        ),
    ] = None
    layers: Annotated[
        list[GeospatialData] | None,
        Field(min_length=1),
    ] = None
    boundingBox: BoundingBox | None = None
    centerPoint: TilePoint | None = None
    style: Style | None = None
    attribution: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "description": "Short reference to recognize the author or provider",
            }
        ),
    ] = None
    license: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "description": "License applicable to the tiles",
            }
        ),
    ] = None
    accessConstraints: Annotated[
        AccessConstraints | None,
        Field(
            json_schema_extra={
                "description": "Restrictions on the availability of the Tile Set that the user needs to be aware of before using or redistributing the Tile Set",
            }
        ),
    ] = "unclassified"
    keywords: Annotated[
        list[str] | None,
        Field(
            json_schema_extra={
                "description": "keywords about this tileset",
            }
        ),
    ] = None
    version: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "description": "Version of the Tile Set. Changes if the data behind the tiles has been changed",
            }
        ),
    ] = None
    created: TimeStamp | None = None
    updated: TimeStamp | None = None
    pointOfContact: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "description": "Useful information to contact the authors or custodians for the Tile Set",
            }
        ),
    ] = None
    mediaTypes: Annotated[
        list[str] | None,
        Field(
            json_schema_extra={
                "description": "Media types available for the tiles",
            }
        ),
    ] = None


class TileSetList(BaseModel):
    """
    TileSetList model.

    Based on https://docs.ogc.org/is/20-057/20-057.html#toc34
    """

    tilesets: list[TileSet]


class Conformance(BaseModel):
    """Conformance model.

    Ref: http://schemas.opengis.net/ogcapi/features/part1/1.0/openapi/schemas/confClasses.yaml

    """

    conformsTo: list[str]


class Landing(BaseModel):
    """Landing page model.

    Ref: http://schemas.opengis.net/ogcapi/features/part1/1.0/openapi/schemas/landingPage.yaml

    """

    title: str | None = None
    description: str | None = None
    links: list[Link]
