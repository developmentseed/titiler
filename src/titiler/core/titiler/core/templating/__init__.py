"""titiler.core HTML templating."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import jinja2
from starlette.templating import Jinja2Templates

if TYPE_CHECKING:
    from typing import Any

    from starlette.requests import Request
    from starlette.templating import _TemplateResponse


jinja2_env = jinja2.Environment(
    loader=jinja2.ChoiceLoader([jinja2.PackageLoader(__package__, "html")])
)
DEFAULT_TEMPLATES = Jinja2Templates(env=jinja2_env)


def create_html_response(
    request: Request,
    data: Any,
    template_name: str,
    templates: Jinja2Templates | None = None,
    title: str | None = None,
    router_prefix: str | None = None,
    **kwargs: Any,
) -> _TemplateResponse:
    """Create Template response."""

    templates = templates or DEFAULT_TEMPLATES

    urlpath = request.url.path
    if root_path := request.scope.get("root_path"):
        urlpath = re.sub(r"^" + root_path, "", urlpath)

    if router_prefix:
        urlpath = re.sub(r"^" + router_prefix, "", urlpath)

    crumbs = []
    baseurl = str(request.base_url).rstrip("/")

    if router_prefix:
        baseurl += router_prefix

    crumbpath = str(baseurl)
    if urlpath == "/":
        urlpath = ""

    for crumb in urlpath.split("/"):
        crumbpath = crumbpath.rstrip("/")
        part = crumb
        if part is None or part == "":
            part = "Home"
        crumbpath += f"/{crumb}"
        crumbs.append({"url": crumbpath.rstrip("/"), "part": part.capitalize()})

    return templates.TemplateResponse(
        request,
        name=f"{template_name}.html",
        context={
            "response": data,
            "template": {
                "api_root": baseurl,
                "params": request.query_params,
                "title": title or template_name,
            },
            "crumbs": crumbs,
            "url": baseurl + urlpath,
            "params": str(request.url.query),
            **kwargs,
        },
    )
