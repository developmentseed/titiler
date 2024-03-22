"""titiler Viewer Extensions."""

from dataclasses import dataclass

import jinja2
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from titiler.core.factory import BaseTilerFactory, FactoryExtension

jinja2_env = jinja2.Environment(
    loader=jinja2.ChoiceLoader([jinja2.PackageLoader(__package__, "templates")])
)
DEFAULT_TEMPLATES = Jinja2Templates(env=jinja2_env)


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
                request,
                name="cog_viewer.html",
                context={
                    "tilejson_endpoint": factory.url_for(
                        request, "tilejson", tileMatrixSetId="WebMercatorQuad"
                    ),
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
                request,
                name="stac_viewer.html",
                context={
                    "tilejson_endpoint": factory.url_for(
                        request, "tilejson", tileMatrixSetId="WebMercatorQuad"
                    ),
                    "info_endpoint": factory.url_for(request, "info"),
                    "statistics_endpoint": factory.url_for(request, "asset_statistics"),
                },
                media_type="text/html",
            )
