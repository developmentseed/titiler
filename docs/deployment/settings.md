# Configuration/Settings

Deployment settings are managed via [pydantic.BaseSettings](https://pydantic-docs.helpmanual.io/usage/settings/) and stored in [stack.config.py](https://github.com/developmentseed/titiler/blob/master/stack/config.py). Pydantic BaseSettings can receive input to overwrite the default value from `.env` file or from environment variables.

Variables in `.env` or in environment variable need to be prefixed with `STACK_`:


```bash
STACK_NAME="my_tiler"
STACK_STAGE="dev"

STACK_BUCKETS='["my-bucket*", "*"]'
STACK_MOSAIC_HOST="my-bucket/mosaics"

STACK_MEMORY=3008
```

Default values from [stack.config.py](https://github.com/developmentseed/titiler/blob/master/stack/config.py):
```python
name: str = "titiler"
stage: str = "production"

owner: Optional[str]
client: Optional[str]

additional_env: Dict = {}

buckets: List = []

## ECS
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

## LAMBDA
timeout: int = 10
memory: int = 1536

# The maximum of concurrent executions you want to reserve for the function.
# Default: - No specific limit - account limit.
max_concurrent: Optional[int]
```
