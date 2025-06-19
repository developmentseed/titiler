"""Construct App."""

import os
from typing import Any, Dict, List, Optional

from aws_cdk import App, CfnOutput, Duration, Stack, Tags
from aws_cdk import aws_apigatewayv2 as apigw
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda
from aws_cdk import aws_logs as logs
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration
from config import StackSettings
from constructs import Construct

settings = StackSettings()


class titilerLambdaStack(Stack):
    """
    Titiler Lambda Stack

    This code is freely adapted from
    - https://github.com/leothomas/titiler/blob/10df64fbbdd342a0762444eceebaac18d8867365/stack/app.py author: @leothomas
    - https://github.com/ciaranevans/titiler/blob/3a4e04cec2bd9b90e6f80decc49dc3229b6ef569/stack/app.py author: @ciaranevans

    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        memory: int = 1024,
        timeout: int = 30,
        runtime: aws_lambda.Runtime = aws_lambda.Runtime.PYTHON_3_12,
        concurrent: Optional[int] = None,
        permissions: Optional[List[iam.PolicyStatement]] = None,
        environment: Optional[Dict] = None,
        code_dir: str = "./",
        **kwargs: Any,
    ) -> None:
        """Define stack."""
        super().__init__(scope, id, **kwargs)

        permissions = permissions or []
        environment = environment or {}

        # COG / STAC / MosaicJSON
        lambda_function = aws_lambda.Function(
            self,
            f"{id}-lambda",
            runtime=runtime,
            code=aws_lambda.Code.from_docker_build(
                path=os.path.abspath(code_dir),
                file="lambda/Dockerfile",
                platform="linux/amd64",
                build_args={
                    "PYTHON_VERSION": "3.12",
                },
            ),
            handler="handler.handler",
            memory_size=memory,
            reserved_concurrent_executions=concurrent,
            timeout=Duration.seconds(timeout),
            environment=environment,
            log_retention=logs.RetentionDays.ONE_WEEK,
        )

        for perm in permissions:
            lambda_function.add_to_role_policy(perm)

        api = apigw.HttpApi(
            self,
            f"{id}-endpoint",
            default_integration=HttpLambdaIntegration(
                f"{id}-integration", handler=lambda_function
            ),
        )
        CfnOutput(self, "Endpoint", value=api.url)

        # Xarray
        xarray_lambda_function = aws_lambda.Function(
            self,
            f"{id}-xarray-lambda",
            runtime=runtime,
            code=aws_lambda.Code.from_docker_build(
                path=os.path.abspath(code_dir),
                file="lambda/Dockerfile.xarray",
                platform="linux/amd64",
                build_args={
                    "PYTHON_VERSION": "3.12",
                },
            ),
            handler="handler.handler",
            memory_size=memory,
            reserved_concurrent_executions=concurrent,
            timeout=Duration.seconds(timeout),
            environment=environment,
            log_retention=logs.RetentionDays.ONE_WEEK,
        )

        for perm in permissions:
            xarray_lambda_function.add_to_role_policy(perm)

        xarray_api = apigw.HttpApi(
            self,
            f"{id}-xarray-endpoint",
            default_integration=HttpLambdaIntegration(
                f"{id}-xarray-integration", handler=xarray_lambda_function
            ),
        )
        CfnOutput(self, "Xarray-Endpoint", value=xarray_api.url)


app = App()

perms = []
if settings.buckets:
    perms.append(
        iam.PolicyStatement(
            actions=["s3:GetObject"],
            resources=[
                f"arn:aws:s3:::{bucket}/{settings.key}" for bucket in settings.buckets
            ],
        )
    )

lambda_stack = titilerLambdaStack(
    app,
    f"{settings.name}-lambda-{settings.stage}",
    memory=settings.memory,
    timeout=settings.timeout,
    concurrent=settings.max_concurrent,
    permissions=perms,
    environment=settings.env,
)

# Tag infrastructure
for key, value in {
    "Project": settings.name,
    "Stack": settings.stage,
    "Owner": settings.owner,
    "Client": settings.client,
}.items():
    if value:
        Tags.of(lambda_stack).add(key, value)


app.synth()
