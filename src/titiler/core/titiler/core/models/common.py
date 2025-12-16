"""titiler.core.models.common"""

from typing import Annotated

from pydantic import AnyUrl, BaseModel, Field


class Link(BaseModel):
    """Link model.

    Ref: https://github.com/opengeospatial/ogcapi-tiles/blob/master/openapi/schemas/common-core/link.yaml

    Code generated using https://github.com/koxudaxi/datamodel-code-generator/
    """

    href: Annotated[
        AnyUrl,
        Field(
            json_schema_extra={
                "description": "Supplies the URI to a remote resource (or resource fragment).",
                "examples": ["http://data.example.com/buildings/123"],
            }
        ),
    ]
    rel: Annotated[
        str,
        Field(
            json_schema_extra={
                "description": "The type or semantics of the relation.",
                "examples": ["alternate"],
            }
        ),
    ]
    type: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "description": "A hint indicating what the media type of the result of dereferencing the link should be.",
                "examples": ["application/geo+json"],
            }
        ),
    ] = None
    templated: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "description": "This flag set to true if the link is a URL template.",
            }
        ),
    ] = None
    varBase: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "description": "A base path to retrieve semantic information about the variables used in URL template.",
                "examples": ["/ogcapi/vars/"],
            }
        ),
    ] = None
    hreflang: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "description": "A hint indicating what the language of the result of dereferencing the link should be.",
                "examples": ["en"],
            }
        ),
    ] = None
    title: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "description": "Used to label the destination of a link such that it can be used as a human-readable identifier.",
                "examples": ["Trierer Strasse 70, 53115 Bonn"],
            }
        ),
    ] = None
    length: int | None = None

    model_config = {"use_enum_values": True}
