"""app settings"""

from starlette.config import Config

PROJECT_NAME = "titiler"
config = Config(".env")


BACKEND_CORS_ORIGINS = config("BACKEND_CORS_ORIGINS", cast=str, default="*")
DEFAULT_CACHECONTROL = config(
    "DEFAULT_CACHECONTROL", cast=str, default="public, max-age=3600"
)


DISABLE_CACHE = config("DISABLE_CACHE", cast=str, default=None)
MEMCACHE_HOST = config("MEMCACHE_HOST", cast=str, default=None)
MEMCACHE_PORT = config("MEMCACHE_PORT", cast=int, default=11211)
MEMCACHE_USERNAME = config("MEMCACHE_USERNAME", cast=str, default=None)
MEMCACHE_PASSWORD = config("MEMCACHE_PASSWORD", cast=str, default=None)


DEFAULT_MOSAIC_BACKEND = config("DEFAULT_MOSAIC_BACKEND", cast=str, default="s3://")
DEFAULT_MOSAIC_HOST = config("DEFAULT_MOSAIC_HOST", cast=str, default="")
