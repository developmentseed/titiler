"""TITILER_STACK Configs."""

from typing import Dict, List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class StackSettings(BaseSettings):
    """Application settings"""

    name: str = "titiler"
    stage: str = "production"

    owner: Optional[str] = None
    client: Optional[str] = None

    # Default options are optimized for CloudOptimized GeoTIFF
    # For more information on GDAL env see: https://gdal.org/user/configoptions.html
    # or https://developmentseed.org/titiler/advanced/performance_tuning/
    env: Dict = {
        "GDAL_CACHEMAX": "200",  # 200 mb
        "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
        "GDAL_INGESTED_BYTES_AT_OPEN": "32768",  # get more bytes when opening the files.
        "GDAL_HTTP_MERGE_CONSECUTIVE_RANGES": "YES",
        "GDAL_HTTP_MULTIPLEX": "YES",
        "GDAL_HTTP_VERSION": "2",
        "PYTHONWARNINGS": "ignore",
        "VSI_CACHE": "TRUE",
        "VSI_CACHE_SIZE": "5000000",  # 5 MB (per file-handle)
    }

    # S3 bucket names where TiTiler could do HEAD and GET Requests
    # specific private and public buckets MUST be added if you want to use s3:// urls
    # You can whitelist all bucket by setting `*`.
    # ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-arn-format.html
    buckets: List = []

    # S3 key pattern to limit the access to specific items (e.g: "my_data/*.tif")
    key: str = "*"

    ###########################################################################
    # AWS LAMBDA
    # The following settings only apply to AWS Lambda deployment
    # more about lambda config: https://www.sentiatechblog.com/aws-re-invent-2020-day-3-optimizing-lambda-cost-with-multi-threading
    timeout: int = 10
    memory: int = 1536

    # The maximum of concurrent executions you want to reserve for the function.
    # Default: - No specific limit - account limit.
    max_concurrent: Optional[int] = None

    model_config = SettingsConfigDict(env_prefix="TITILER_STACK_", env_file=".env")
