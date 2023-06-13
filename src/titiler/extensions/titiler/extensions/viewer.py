"""titiler Viewer Extensions."""

from dataclasses import dataclass

import jinja2
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from titiler.core.factory import BaseTilerFactory, FactoryExtension

DEFAULT_TEMPLATES = Jinja2Templates(
    directory="",
    loader=jinja2.ChoiceLoader([jinja2.PackageLoader(__package__, "templates")]),
)  # type:ignore


@dataclass
class cogViewerExtension(FactoryExtension):
    """Add /viewer endpoint to the TilerFactory."""

    templates: Jinja2Templates = DEFAULT_TEMPLATES

    def register(self, factory: BaseTilerFactory):
        """Register endpoint to the tiler factory."""

        @factory.router.get("/viewer", response_class=HTMLResponse)
        def cog_viewer(request: Request):
            """COG Viewer."""
            return self.templates.TemplateResponse(
                name="cog_viewer.html",
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

    templates: Jinja2Templates = DEFAULT_TEMPLATES

    def register(self, factory: BaseTilerFactory):
        """Register endpoint to the tiler factory."""

        @factory.router.get("/viewer", response_class=HTMLResponse)
        def stac_viewer(request: Request):
            """STAC Viewer."""
            return self.templates.TemplateResponse(
                name="stac_viewer.html",
                context={
                    "request": request,
                    "tilejson_endpoint": factory.url_for(request, "tilejson"),
                    "info_endpoint": factory.url_for(request, "info"),
                    "statistics_endpoint": factory.url_for(request, "asset_statistics"),
                },
                media_type="text/html",
            )
