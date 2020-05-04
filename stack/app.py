"""Construct App."""

from typing import Any, Union

import os

from aws_cdk import (
    aws_apigateway as apigw,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_lambda as _lambda,
    core
)

import config


class titilerStack(core.Stack):
    """Titiler ECS Fargate Stack."""

    def __init__(
        self,
        scope: core.Construct,
        id: str,
        cpu: Union[int, float] = 256,
        memory: Union[int, float] = 512,
        mincount: int = 1,
        maxcount: int = 50,
        code_dir: str = "./",
        **kwargs: Any,
    ) -> None:
        """Define stack."""
        super().__init__(scope, id, *kwargs)

        vpc = ec2.Vpc(self, f"{id}-vpc", max_azs=2)

        cluster = ecs.Cluster(self, f"{id}-cluster", vpc=vpc)

        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            f"{id}-service",
            cluster=cluster,
            cpu=cpu,
            memory_limit_mib=memory,
            desired_count=mincount,
            public_load_balancer=True,
            listener_port=80,
            task_image_options=dict(
                image=ecs.ContainerImage.from_asset(
                    code_dir, exclude=["cdk.out", ".git"]
                ),
                container_port=80,
                environment=dict(
                    CPL_TMPDIR="/tmp",
                    GDAL_CACHEMAX="75%",
                    GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                    GDAL_HTTP_MERGE_CONSECUTIVE_RANGES="YES",
                    GDAL_HTTP_MULTIPLEX="YES",
                    GDAL_HTTP_VERSION="2",
                    MODULE_NAME="titiler.main",
                    PYTHONWARNINGS="ignore",
                    VARIABLE_NAME="app",
                    VSI_CACHE="TRUE",
                    VSI_CACHE_SIZE="1000000",
                    WORKERS_PER_CORE="1",
                    LOG_LEVEL="error",
                ),
            ),
        )

        scalable_target = fargate_service.service.auto_scale_task_count(
            min_capacity=mincount, max_capacity=maxcount
        )

        # https://github.com/awslabs/aws-rails-provisioner/blob/263782a4250ca1820082bfb059b163a0f2130d02/lib/aws-rails-provisioner/scaling.rb#L343-L387
        scalable_target.scale_on_request_count(
            "RequestScaling",
            requests_per_target=50,
            scale_in_cooldown=core.Duration.seconds(240),
            scale_out_cooldown=core.Duration.seconds(30),
            target_group=fargate_service.target_group,
        )

        # scalable_target.scale_on_cpu_utilization(
        #     "CpuScaling", target_utilization_percent=70,
        # )

        fargate_service.service.connections.allow_from_any_ipv4(
            port_range=ec2.Port(
                protocol=ec2.Protocol.ALL,
                string_representation="All port 80",
                from_port=80,
            ),
            description="Allows traffic on port 80 from NLB",
        )


class titilerLambdaStack(core.Stack):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        code_dir: str = "./",
        **kwargs: Any,
    ) -> None:
        """Define stack."""
        super().__init__(scope, id, *kwargs)

        titiler_lambda = _lambda.Function(
            self,
            'TestLambda',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda/lambda.zip'),
            handler='lambda.handler'
        )

        apigw.LambdaRestApi(
            self,
            'TestGateway',
            handler=titiler_lambda
        )

app = core.App()

# Tag infrastructure
for key, value in {
    "Project": config.PROJECT_NAME,
    "Stack": config.STAGE,
    "Owner": os.environ.get("OWNER"),
    "Client": os.environ.get("CLIENT"),
}.items():
    if value:
        core.Tag.add(app, key, value)

stackname = f"{config.PROJECT_NAME}-{config.STAGE}"
# titilerStack(
#     app,
#     stackname,
#     cpu=config.TASK_CPU,
#     memory=config.TASK_MEMORY,
#     mincount=config.MIN_ECS_INSTANCES,
#     maxcount=config.MAX_ECS_INSTANCES,
# )
titilerLambdaStack(
    app,
    stackname
)
app.synth()
