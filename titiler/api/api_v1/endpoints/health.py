"""API /health."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/ping", description="Health Check")
def ping():
    """Health check."""
    return "I'm all good, give me some COGs now."
