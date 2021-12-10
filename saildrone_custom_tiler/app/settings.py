"""settings.

app/settings.py

"""

from pydantic import BaseSettings
from typing import Optional


class CacheSettings(BaseSettings):
    """Cache settings"""

    endpoint: Optional[str] = None
    ttl: int = 3600

    class Config:
        """model config"""

        env_file = ".env"
        env_prefix = "CACHE_"


cache_settings = CacheSettings()
