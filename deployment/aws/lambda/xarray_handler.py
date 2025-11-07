"""AWS Lambda handler."""

import logging

from mangum import Mangum

from titiler.xarray.main import api_settings, app

logging.getLogger("mangum.lifespan").setLevel(logging.ERROR)
logging.getLogger("mangum.http").setLevel(logging.ERROR)

handler = Mangum(app, api_gateway_base_path=api_settings.root_path, lifespan="auto")
