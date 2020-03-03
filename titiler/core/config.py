"""Config."""

import os


API_V1_STR = "/v1"

PROJECT_NAME = "titiler"

SERVER_NAME = os.getenv("SERVER_NAME")
SERVER_HOST = os.getenv("SERVER_HOST")
BACKEND_CORS_ORIGINS = os.getenv(
    "BACKEND_CORS_ORIGINS"
)  # a string of origins separated by commas, e.g: "http://localhost, http://localhost:4200, http://localhost:3000, http://localhost:8080, http://local.dockertoolbox.tiangolo.com"

DISABLE_CACHE = os.getenv("DISABLE_CACHE")
MEMCACHE_HOST = os.environ.get("MEMCACHE_HOST")
MEMCACHE_USERNAME = os.environ.get("MEMCACHE_USERNAME")
MEMCACHE_PASSWORD = os.environ.get("MEMCACHE_PASSWORD")
MEMCACHE_PORT = os.environ.get("MEMCACHE_PORT", "11211")
