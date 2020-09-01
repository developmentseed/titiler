# AWS ECS (Fargate) + ALB (Application Load Balancer)

The TiTiler [repository](https://github.com/developmentseed/titiler) includes an example that uses [AWS CDK](https://aws.amazon.com/cdk/) to deploy TiTiler on AWS' Elastic Container Service (ECS).

The example handles tasks such as generating a docker image and setting up an application load balancer (ALB) and ECS services.

1. Install CDK and connect to your AWS account. This step is only necessary once per AWS account.

    ```bash

    $ git clone https://github.com/developmentseed/titiler.git
    $ cd titiler && pip install -e .["deploy"]

    $ npm install cdk -g

    $ cdk bootstrap # Deploys the CDK toolkit stack into an AWS environment

    # in specific region
    $ cdk bootstrap aws://${AWS_ACCOUNT_ID}/eu-central-1
    ```

2. Generate CloudFormation template

    ```bash
    $ cdk synth  # Synthesizes and prints the CloudFormation template for this stack
    ```

3. Edit [stack/config.py](stack/config.py)

    ```python
    PROJECT_NAME = os.environ.get("PROJECT", "titiler")
    STAGE = os.environ.get("STAGE", "dev")

    # // Service config
    # Min/Max Number of ECS images
    MIN_ECS_INSTANCES = 2
    MAX_ECS_INSTANCES = 50

    # CPU value      |   Memory value
    # 256 (.25 vCPU) | 0.5 GB, 1 GB, 2 GB
    # 512 (.5 vCPU)  | 1 GB, 2 GB, 3 GB, 4 GB
    # 1024 (1 vCPU)  | 2 GB, 3 GB, 4 GB, 5 GB, 6 GB, 7 GB, 8 GB
    # 2048 (2 vCPU)  | Between 4 GB and 16 GB in 1-GB increments
    # 4096 (4 vCPU)  | Between 8 GB and 30 GB in 1-GB increments
    TASK_CPU = 1024
    TASK_MEMORY = 2048
    ```

4. Deploy

    ```bash
    $ cdk deploy titiler-ecs-dev # Deploys the stack(s) titiler-ecs-dev in stack/app.py
    ```
