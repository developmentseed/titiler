"""Application environment variables"""

from starlette.config import Config

config = Config()

DEFAULT_MOSAIC_BACKEND = config("DEFAULT_MOSAIC_BACKEND", cast=str, default="s3://")

# TODO: Remove default (default is currently set to pass tests)
DEFAULT_MOSAIC_HOST = config("DEFAULT_MOSAIC_HOST", cast=str, default="placeholder")
