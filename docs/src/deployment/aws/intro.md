# Amazon Web Services deployments

Examples of AWS deployments can be found in https://github.com/developmentseed/titiler/tree/main/deployment/aws. Those examples use [AWS Cloud Development Kit](https://aws.amazon.com/cdk/) to define stacks using python code.

# Configuration/Settings

Deployment settings are managed via [pydantic.BaseSettings](https://pydantic-docs.helpmanual.io/usage/settings/) and stored in [config.py](https://github.com/developmentseed/titiler/blob/main/deployment/aws/cdk/config.py). Pydantic BaseSettings can receive input to overwrite the default value from a `.env` file or from environment variables.

Variables in `.env` or in environment variable need to be prefixed with `TITILER_STACK_`:


```bash
TITILER_STACK_NAME="my-tiler"
TITILER_STACK_STAGE="dev"

TITILER_STACK_BUCKETS='["my-bucket*", "*"]'

TITILER_STACK_MEMORY=3008

# Uncomment to allow lambda to access content on requester-payer buckets
# TITILER_STACK_ENV='{"AWS_REQUEST_PAYER":"requester"}'

# Uncomment if you only on the /cog endpoint
# TITILER_STACK_ENV='{"TITILER_API_DISABLE_STAC": "TRUE", "TITILER_API_DISABLE_MOSAIC": "TRUE"}'
```

Default values from [config.py](https://github.com/developmentseed/titiler/blob/main/deployment/aws/cdk/config.py):
```python
name: str = "titiler"
stage: str = "production"

owner: Optional[str]
client: Optional[str]

# Default options are optimized for CloudOptimized GeoTIFF
# For more information on GDAL env see: https://gdal.org/user/configoptions.html
env: Dict = {
    "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif,.TIF,.tiff",
    "GDAL_CACHEMAX": "200" # 200 mb
    "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
    "GDAL_HTTP_MERGE_CONSECUTIVE_RANGES": "YES",
    "GDAL_HTTP_MULTIPLEX": "YES",
    "GDAL_HTTP_VERSION": "2",
    "PYTHONWARNINGS": "ignore",
    "VSI_CACHE": "TRUE",
    "VSI_CACHE_SIZE": "5000000" # 5 MB (per file-handle)
}

# add S3 bucket where TiTiler could do HEAD and GET Requests
buckets: List = []

###########################################################################
# AWS LAMBDA
# The following settings only apply to AWS Lambda deployment
timeout: int = 10
memory: int = 1536
# more about lambda config: https://www.sentiatechblog.com/aws-re-invent-2020-day-3-optimizing-lambda-cost-with-multi-threading

# The maximum of concurrent executions you want to reserve for the function.
# Default: - No specific limit - account limit.
max_concurrent: Optional[int]
```
