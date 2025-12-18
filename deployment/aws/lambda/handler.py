"""AWS Lambda handler."""

import asyncio
import logging

from mangum import Mangum

from titiler.application.main import app
from titiler.application.settings import ApiSettings

try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

logging.getLogger("mangum.lifespan").setLevel(logging.ERROR)
logging.getLogger("mangum.http").setLevel(logging.ERROR)

api_settings = ApiSettings()

handler = Mangum(app, api_gateway_base_path=api_settings.root_path, lifespan="auto")
