from dataclasses import dataclass

from titiler.core import BaseTilerFactory
from titiler.core.factory import FactoryExtension


@dataclass
class wmtsTitleExtension(FactoryExtension):
    """fix /cog/WMTSCapabilities.xml title to url name without extension"""
    def register(self, factory: "BaseTilerFactory"):
        template_response = factory.templates.TemplateResponse
        import typing
        from starlette.requests import Request
        import os

        def proxy_template_response(name: str, context: dict, *args, **kwargs):
            if context["title"]:
                request = typing.cast(Request, context["request"])
                url = request.query_params["url"]
                filename = os.path.splitext(url.split("/")[-1])[0]
                context["title"] = filename
            return template_response(name, context, *args, **kwargs)
        factory.templates.TemplateResponse = proxy_template_response
