"""titiler: Template Factory."""

import os
from typing import Callable

from starlette.requests import Request
from starlette.templating import Jinja2Templates, _TemplateResponse

html_templates = Jinja2Templates(directory=os.path.dirname(__file__))


def web_template() -> Callable[[Request, str, str, str], _TemplateResponse]:
    """Create a dependency which may be injected into a FastAPI app."""

    def _template(
        request: Request, page: str, tilejson: str, metadata: str
    ) -> _TemplateResponse:
        """Create a template from a request"""
        return html_templates.TemplateResponse(
            name=page,
            context={
                "request": request,
                "tilejson_endpoint": request.url_for(tilejson),
                "metadata_endpoint": request.url_for(metadata),
            },
            media_type="text/html",
        )

    return _template
