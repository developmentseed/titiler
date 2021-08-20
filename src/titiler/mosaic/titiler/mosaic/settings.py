"""app settings"""

from typing import Optional

import pydantic


class MosaicSettings(pydantic.BaseSettings):
    """Application settings"""

    backend: Optional[str]
    host: Optional[str]
    format: str = ".json.gz"  # format will be ignored for dynamodb backend

    class Config:
        """model config"""

        env_prefix = "MOSAIC_"
        env_file = ".env"


mosaic_config = MosaicSettings()
