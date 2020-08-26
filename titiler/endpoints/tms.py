"""TMS Api."""

import json

from morecantile.models import TileMatrixSet

from titiler.dependencies import TileMatrixSetNames, morecantile
from titiler.models.OGC import TileMatrixSetList

from fastapi import APIRouter, Query

from starlette.requests import Request

router = APIRouter()


@router.get(
    r"/tileMatrixSets",
    response_model=TileMatrixSetList,
    response_model_exclude_none=True,
    tags=["TileMatrixSets"],
)
async def TileMatrixSet_list(request: Request):
    """
    Return list of supported TileMatrixSets.

    Specs: http://docs.opengeospatial.org/per/19-069.html#_tilematrixsets
    """
    return {
        "tileMatrixSets": [
            {
                "id": tms.name,
                "title": morecantile.tms.get(tms.name).title,
                "links": [
                    {
                        "href": request.url_for(
                            "TileMatrixSet_info", TileMatrixSetId=tms.name
                        ),
                        "rel": "item",
                        "type": "application/json",
                    }
                ],
            }
            for tms in TileMatrixSetNames
        ]
    }


@router.get(
    r"/tileMatrixSets/{TileMatrixSetId}",
    response_model=TileMatrixSet,
    response_model_exclude_none=True,
    tags=["TileMatrixSets"],
)
async def TileMatrixSet_info(
    TileMatrixSetId: TileMatrixSetNames = Query(..., description="TileMatrixSet Name")
):
    """Return TileMatrixSet JSON document."""
    tms = morecantile.tms.get(TileMatrixSetId.name)
    return json.loads(tms.json(exclude_none=True))
