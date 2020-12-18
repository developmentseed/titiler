# Amazon Web Services deployments

Example of of AWS deployments can be found in https://github.com/developmentseed/titiler/tree/master/deployment/AWS. Those examples use [AWS Cloud Development Kit](https://aws.amazon.com/cdk/) to define stacks using python code.

# Configuration/Settings

Deployment settings are managed via [pydantic.BaseSettings](https://pydantic-docs.helpmanual.io/usage/settings/) and stored in [config.py](https://github.com/developmentseed/titiler/blob/master/stack/config.py). Pydantic BaseSettings can receive input to overwrite the default value from `.env` file or from environment variables.

Variables in `.env` or in environment variable need to be prefixed with `STACK_`:


```bash
STACK_NAME="my-tiler"
STACK_STAGE="dev"

STACK_BUCKETS='["my-bucket*", "*"]'
STACK_MOSAIC_HOST="my-bucket/mosaics"

STACK_MEMORY=3008

# Uncomment to allow lambda to access content on requester-payer buckets
# STACK_ADDITIONAL_ENV='{"AWS_REQUEST_PAYER":"requester"}'

# Uncomment if you only on the /cog endpoint
# STACK_ADDITIONAL_ENV='{"API_DISABLE_STAC": "TRUE", "API_DISABLE_MOSAIC": "TRUE"}'
```

Default values from [config.py](https://github.com/developmentseed/titiler/blob/master/deployment/aws/cdk/config.py):
```python
name: str = "titiler"
stage: str = "production"

owner: Optional[str]
client: Optional[str]

additional_env: Dict = {}

# add S3 bucket where TiTiler could do HEAD and GET Requests
buckets: List = []

#########
# AWS ECS
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
web_concurrency: Optional[int]

image_version: str = "latest"

############
# AWS LAMBDA
timeout: int = 10
memory: int = 1536
# more about lambda config: https://www.sentiatechblog.com/aws-re-invent-2020-day-3-optimizing-lambda-cost-with-multi-threading

# The maximum of concurrent executions you want to reserve for the function.
# Default: - No specific limit - account limit.
max_concurrent: Optional[int]
```
