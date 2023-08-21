"""Titiler API settings."""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiSettings(BaseSettings):
    """FASTAPI application settings."""

    name: str = "TiTiler"
    cors_origins: str = "*"
    cors_allow_methods: str = "GET"
    cachecontrol: str = "public, max-age=3600"
    root_path: str = ""
    debug: bool = False

    disable_cog: bool = False
    disable_stac: bool = False
    disable_mosaic: bool = False

    lower_case_query_parameters: bool = False

    model_config = SettingsConfigDict(env_prefix="TITILER_API_", env_file=".env")

    @field_validator("cors_origins")
    def parse_cors_origin(cls, v):
        """Parse CORS origins."""
        return [origin.strip() for origin in v.split(",")]

    @field_validator("cors_allow_methods")
    def parse_cors_allow_methods(cls, v):
        """Parse CORS allowed methods."""
        return [method.strip().upper() for method in v.split(",")]
