"""app settings"""

from starlette.config import Config

PROJECT_NAME = "titiler"
config = Config(".env")


BACKEND_CORS_ORIGINS = config("BACKEND_CORS_ORIGINS", cast=str, default="*")
DEFAULT_CACHECONTROL = config(
    "DEFAULT_CACHECONTROL", cast=str, default="public, max-age=3600"
)

DEFAULT_MOSAIC_BACKEND = config("DEFAULT_MOSAIC_BACKEND", cast=str, default="s3://")
DEFAULT_MOSAIC_HOST = config("DEFAULT_MOSAIC_HOST", cast=str, default="")
