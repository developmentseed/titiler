"""titiler Viewer Extensions."""

from dataclasses import dataclass

from titiler.core.factory import BaseTilerFactory, FactoryExtension

from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

try:
    from importlib.resources import files as resources_files  # type: ignore
except ImportError:
    # Try backported to PY<39 `importlib_resources`.
    from importlib_resources import files as resources_files  # type: ignore

# TODO: mypy fails in python 3.9, we need to find a proper way to do this
templates = Jinja2Templates(directory=str(resources_files(__package__) / "templates"))  # type: ignore


@dataclass
class cogViewerExtension(FactoryExtension):
    """Add /viewer endpoint to the TilerFactory."""

    def register(self, factory: BaseTilerFactory):
        """Register endpoint to the tiler factory."""

        @factory.router.get("/viewer", response_class=HTMLResponse)
        def cog_viewer(request: Request):
            """COG Viewer."""
            return templates.TemplateResponse(
                name="cog_index.html",
                context={
                    "request": request,
                    "tilejson_endpoint": factory.url_for(request, "tilejson"),
                    "info_endpoint": factory.url_for(request, "info"),
                    "statistics_endpoint": factory.url_for(request, "statistics"),
                },
                media_type="text/html",
            )


@dataclass
class stacViewerExtension(FactoryExtension):
    """Add /viewer endpoint to the TilerFactory."""

    def register(self, factory: BaseTilerFactory):
        """Register endpoint to the tiler factory."""

        @factory.router.get("/viewer", response_class=HTMLResponse)
        def stac_viewer(request: Request):
            """STAC Viewer."""
            return templates.TemplateResponse(
                name="stac_index.html",
                context={
                    "request": request,
                    "tilejson_endpoint": factory.url_for(request, "tilejson"),
                    "info_endpoint": factory.url_for(request, "info"),
                    "statistics_endpoint": factory.url_for(request, "asset_statistics"),
                },
                media_type="text/html",
            )
