"""Titiler API settings."""

import pydantic


class ApiSettings(pydantic.BaseSettings):
    """FASTAPI application settings."""

    name: str = "titiler"
    backend_cors_origins: str = "*"
    cachecontrol: str = "public, max-age=3600"

    @pydantic.validator("backend_cors_origins")
    def parse_cors_origin(cls, v):
        """Parse CORS origins."""
        return [origin.strip() for origin in v.split(",")]

    class Config:
        """model config"""

        env_file = ".env"
        env_prefix = "API_"
