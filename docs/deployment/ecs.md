# AWS ECS (Fargate) + ALB (Application Load Balancer)

!!! warning
        When using Fargate or vanilla ECS, you should set the number of worker carefully. Setting too high a number of workers could lead to extra charges due to a bug in fastapi (https://github.com/developmentseed/titiler/issues/119, https://github.com/tiangolo/fastapi/issues/253).

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

3. Update settings (see [settings.md](settings.md))

    ```bash
    export TITILER_PROJECT="mytiler"
    export TITILER_STAGE="dev"
    export TITILER_MIN_ECS_INSTANCES=10
    ```

    Available settings for ECS:

    ```python
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
    ```

4. Deploy

    ```bash
    # Deploys the stack(s) titiler-ecs-dev in stack/app.py
    $ cdk deploy titiler-ecs-dev
    ```
