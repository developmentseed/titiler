"""AWS Lambda handler."""

from mangum import Mangum
from titiler.main import app

handler = Mangum(app, enable_lifespan=False)
