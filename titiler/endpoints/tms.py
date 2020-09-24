"""TMS Api."""

import json

from morecantile.models import TileMatrixSet

from titiler.dependencies import TileMatrixSetNames, TMSParams
from titiler.models.OGC import TileMatrixSetList

from fastapi import APIRouter, Depends

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
                "title": tms.name,
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
async def TileMatrixSet_info(tms=Depends(TMSParams)):
    """Return TileMatrixSet JSON document."""
    return json.loads(tms.json(exclude_none=True))
