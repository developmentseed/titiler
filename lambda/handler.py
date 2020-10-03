"""AWS Lambda handler."""

from mangum import Mangum

from titiler.main import app

handler = Mangum(app, lifespan="auto", log_level="error")
