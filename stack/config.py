"""STACK Configs."""

from typing import Dict, List, Optional

import os

PROJECT_NAME = "titiler"
STAGE = os.environ.get("STAGE", "dev")

# Additional environement variable to set in the task/lambda
ENV: Dict = {}

# Add bucket where titiler can s3:GetObject/s3:HeadObject
BUCKET: List = ["ds-satellite"]

################################################################################
#                                                                              #
#                                   ECS                                        #
#                                                                              #
################################################################################
# Min/Max Number of ECS images
MIN_ECS_INSTANCES: int = 5
MAX_ECS_INSTANCES: int = 50

# CPU value      |   Memory value
# 256 (.25 vCPU) | 0.5 GB, 1 GB, 2 GB
# 512 (.5 vCPU)  | 1 GB, 2 GB, 3 GB, 4 GB
# 1024 (1 vCPU)  | 2 GB, 3 GB, 4 GB, 5 GB, 6 GB, 7 GB, 8 GB
# 2048 (2 vCPU)  | Between 4 GB and 16 GB in 1-GB increments
# 4096 (4 vCPU)  | Between 8 GB and 30 GB in 1-GB increments
TASK_CPU: int = 256
TASK_MEMORY: int = 512

################################################################################
#                                                                              #
#                                 LAMBDA                                       #
#                                                                              #
################################################################################
TIMEOUT: int = 10
MEMORY: int = 1536

# The maximum of concurrent executions you want to reserve for the function.
# Default: - No specific limit - account limit.
MAX_CONCURRENT: Optional[int] = None
