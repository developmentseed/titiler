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
async def tms_list(request: Request):
    """
    Return list of supported TileMatrixSets.

    Specs: http://docs.opengeospatial.org/per/19-069.html#_tilematrixsets
    """
    scheme = request.url.scheme
    host = request.headers["host"]

    tms_list = morecantile.tms.list()
    return {
        "tileMatrixSets": [
            {
                "id": tms,
                "title": morecantile.tms.get(tms).title,
                "links": [
                    {
                        "href": f"{scheme}://{host}/tileMatrixSets/{tms}",
                        "rel": "item",
                        "type": "application/json",
                    }
                ],
            }
            for tms in tms_list
        ]
    }


@router.get(
    r"/tileMatrixSets/{TileMatrixSetId}",
    response_model=TileMatrixSet,
    response_model_exclude_none=True,
    tags=["TileMatrixSets"],
)
async def tms_info(
    TileMatrixSetId: TileMatrixSetNames = Query(..., description="TileMatrixSet Name")
):
    """Return TileMatrixSet JSON document."""
    tms = morecantile.tms.get(TileMatrixSetId.name)
    return json.loads(tms.json(exclude_none=True))
