"""Microsoft Azure Function."""

import azure.functions as func
from titiler.application.main import app


async def main(
    req: func.HttpRequest,
    context: func.Context,
) -> func.HttpResponse:
    """Run App in AsgiMiddleware."""
    return await func.AsgiMiddleware(app).handle_async(req, context)