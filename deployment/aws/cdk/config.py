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
    # AWS ECS
    # The following settings only apply to AWS ECS deployment
    min_ecs_instances: int = 5
    max_ecs_instances: int = 50

    # CPU value      |   Memory value
    # 256 (.25 vCPU) | 0.5 GB, 1 GB, 2 GB
    # 512 (.5 vCPU)  | 1 GB, 2 GB, 3 GB, 4 GB
    # 1024 (1 vCPU)  | 2 GB, 3 GB, 4 GB, 5 GB, 6 GB, 7 GB, 8 GB
    # 2048 (2 vCPU)  | Between 4 GB and 16 GB in 1-GB increments
    # 4096 (4 vCPU)  | Between 8 GB and 30 GB in 1-GB increments
    task_cpu: int = 256
    task_memory: int = 512

    # GUNICORN configuration
    # Ref: https://github.com/developmentseed/titiler/issues/119

    # WORKERS_PER_CORE
    # This image will check how many CPU cores are available in the current server running your container.
    # It will set the number of workers to the number of CPU cores multiplied by this value.
    workers_per_core: int = 1

    # MAX_WORKERS
    # You can use it to let the image compute the number of workers automatically but making sure it's limited to a maximum.
    # should depends on `task_cpu`
    max_workers: int = 1

    # WEB_CONCURRENCY
    # Override the automatic definition of number of workers.
    # Set to the number of CPU cores in the current server multiplied by the environment variable WORKERS_PER_CORE.
    # So, in a server with 2 cores, by default it will be set to 2.
    web_concurrency: Optional[int] = None

    image_version: str = "latest"

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
