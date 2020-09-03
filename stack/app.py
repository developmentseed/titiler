"""Construct App."""

import os
from typing import Any, List, Optional, Union

import docker
from aws_cdk import aws_apigatewayv2 as apigw
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda, core
from config import StackSettings

settings = StackSettings()


DEFAULT_ENV = dict(
    CPL_TMPDIR="/tmp",
    CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
    GDAL_CACHEMAX="75%",
    GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
    GDAL_HTTP_MERGE_CONSECUTIVE_RANGES="YES",
    GDAL_HTTP_MULTIPLEX="YES",
    GDAL_HTTP_VERSION="2",
    PYTHONWARNINGS="ignore",
    VSI_CACHE="TRUE",
    VSI_CACHE_SIZE="1000000",
)


class titilerLambdaStack(core.Stack):
    """
    Titiler Lambda Stack

    This code is freely adapted from
    - https://github.com/leothomas/titiler/blob/10df64fbbdd342a0762444eceebaac18d8867365/stack/app.py author: @leothomas
    - https://github.com/ciaranevans/titiler/blob/3a4e04cec2bd9b90e6f80decc49dc3229b6ef569/stack/app.py author: @ciaranevans

    """

    def __init__(
        self,
        scope: core.Construct,
        id: str,
        memory: int = 1024,
        timeout: int = 30,
        concurrent: Optional[int] = None,
        permissions: Optional[List[iam.PolicyStatement]] = None,
        layer_arn: Optional[str] = None,
        env: dict = {},
        code_dir: str = "./",
        **kwargs: Any,
    ) -> None:
        """Define stack."""
        super().__init__(scope, id, *kwargs)

        permissions = permissions or []

        lambda_env = DEFAULT_ENV.copy()
        lambda_env.update(env)

        lambda_function = aws_lambda.Function(
            self,
            f"{id}-lambda",
            runtime=aws_lambda.Runtime.PYTHON_3_7,
            code=self.create_package(code_dir),
            handler="handler.handler",
            memory_size=memory,
            reserved_concurrent_executions=concurrent,
            timeout=core.Duration.seconds(timeout),
            environment=lambda_env,
        )

        # # If you use dynamodb mosaic backend you should add IAM roles to read/put Item and maybe create Table
        # permissions.append(
        #     iam.PolicyStatement(
        #         actions=[
        #             "dynamodb:GetItem",
        #             "dynamodb:PutItem",
        #             "dynamodb:CreateTable",
        #             "dynamodb:Scan",
        #             "dynamodb:BatchWriteItem",
        #         ],
        #         resources=[f"arn:aws:dynamodb:{self.region}:{self.account}:table/*"],
        #     )
        # )

        for perm in permissions:
            lambda_function.add_to_role_policy(perm)

        if layer_arn:
            lambda_function.add_layers(
                aws_lambda.LayerVersion.from_layer_version_arn(
                    self, layer_arn.split(":")[-2], layer_arn
                )
            )

        # defines an API Gateway Http API resource backed by our "dynamoLambda" function.
        api = apigw.HttpApi(
            self,
            f"{id}-endpoint",
            default_integration=apigw.LambdaProxyIntegration(handler=lambda_function),
        )
        core.CfnOutput(self, "Endpoint", value=api.url)

    def create_package(self, code_dir: str) -> aws_lambda.Code:
        """Build docker image and create package."""
        print("Creating lambda package [running in Docker]...")
        client = docker.from_env()

        print("Building docker image...")
        client.images.build(
            path=code_dir,
            dockerfile="Dockerfiles/lambda/Dockerfile",
            tag="lambda:latest",
        )

        print("Copying package.zip ...")
        client.containers.run(
            image="lambda:latest",
            command="/bin/sh -c 'cp /tmp/package.zip /local/package.zip'",
            remove=True,
            volumes={os.path.abspath(code_dir): {"bind": "/local/", "mode": "rw"}},
            user=0,
        )

        return aws_lambda.Code.asset(os.path.join(code_dir, "package.zip"))


class titilerECSStack(core.Stack):
    """Titiler ECS Fargate Stack."""

    def __init__(
        self,
        scope: core.Construct,
        id: str,
        cpu: Union[int, float] = 256,
        memory: Union[int, float] = 512,
        mincount: int = 1,
        maxcount: int = 50,
        permissions: Optional[List[iam.PolicyStatement]] = None,
        env: dict = {},
        code_dir: str = "./",
        **kwargs: Any,
    ) -> None:
        """Define stack."""
        super().__init__(scope, id, *kwargs)

        permissions = permissions or []

        vpc = ec2.Vpc(self, f"{id}-vpc", max_azs=2)

        cluster = ecs.Cluster(self, f"{id}-cluster", vpc=vpc)

        task_env = DEFAULT_ENV.copy()
        task_env.update(
            dict(
                MODULE_NAME="titiler.main",
                VARIABLE_NAME="app",
                WORKERS_PER_CORE="1",
                LOG_LEVEL="error",
            )
        )
        task_env.update(env)

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
                    code_dir,
                    exclude=["cdk.out", ".git"],
                    file="Dockerfiles/ecs/Dockerfile",
                ),
                container_port=80,
                environment=task_env,
            ),
        )

        # # If you use dynamodb mosaic backend you should add IAM roles to read/put Item and maybe create Table
        # permissions.append(
        #     iam.PolicyStatement(
        #         actions=[
        #             "dynamodb:GetItem",
        #             "dynamodb:PutItem",
        #             "dynamodb:CreateTable",
        #             "dynamodb:Scan",
        #             "dynamodb:BatchWriteItem",
        #         ],
        #         resources=[f"arn:aws:dynamodb:{self.region}:{self.account}:table/*"],
        #     )
        # )

        for perm in permissions:
            fargate_service.task_definition.task_role.add_to_policy(perm)

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


app = core.App()

perms = []
if settings.buckets:
    perms.append(
        iam.PolicyStatement(
            actions=["s3:GetObject", "s3:HeadObject"],
            resources=[f"arn:aws:s3:::{bucket}" for bucket in settings.buckets],
        )
    )

# Tag infrastructure
for key, value in {
    "Project": settings.name,
    "Stack": settings.stage,
    "Owner": settings.owner,
    "Client": settings.client,
}.items():
    if value:
        core.Tag.add(app, key, value)

ecs_stackname = f"{settings.name}-ecs-{settings.stage}"
titilerECSStack(
    app,
    ecs_stackname,
    cpu=settings.task_cpu,
    memory=settings.task_memory,
    mincount=settings.min_ecs_instances,
    maxcount=settings.max_ecs_instances,
    permissions=perms,
    env=settings.additional_env,
)

lambda_stackname = f"{settings.name}-lambda-{settings.stage}"
titilerLambdaStack(
    app,
    lambda_stackname,
    memory=settings.memory,
    timeout=settings.timeout,
    concurrent=settings.max_concurrent,
    permissions=perms,
    env=settings.additional_env,
)

app.synth()
