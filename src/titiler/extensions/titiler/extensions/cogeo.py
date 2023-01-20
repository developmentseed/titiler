"""rio-cogeo Extension."""

from dataclasses import dataclass

from titiler.core.factory import BaseTilerFactory, FactoryExtension

from fastapi import Depends, Query

try:
    from rio_cogeo.cogeo import cog_info
    from rio_cogeo.models import Info
except ImportError:  # pragma: nocover
    cog_info = None  # type: ignore
    Info = None


@dataclass
class cogValidateExtension(FactoryExtension):
    """Add /validate endpoint to a COG TilerFactory."""

    def register(self, factory: BaseTilerFactory):
        """Register endpoint to the tiler factory."""

        assert (
            cog_info is not None
        ), "'rio_cogeo' must be installed to use CogValidateExtension"

        @factory.router.get("/validate", response_model=Info)
        def validate(
            src_path: str = Depends(factory.path_dependency),
            strict: bool = Query(False, description="Treat warnings as errors"),
        ):
            """Validate a COG"""
            return cog_info(src_path, strict=strict)
