"""Construct App."""

import os
from typing import Any, Dict, List, Optional

from aws_cdk import App, CfnOutput, Duration, Stack, Tags
from aws_cdk import aws_apigatewayv2 as apigw
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda
from aws_cdk import aws_logs as logs
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration
from constructs import Construct
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
    # AWS LAMBDA
    # The following settings only apply to AWS Lambda deployment
    # more about lambda config: https://www.sentiatechblog.com/aws-re-invent-2020-day-3-optimizing-lambda-cost-with-multi-threading
    timeout: int = 10
    memory: int = 1536

    # The maximum of concurrent executions you want to reserve for the function.
    # Default: - No specific limit - account limit.
    max_concurrent: Optional[int] = None

    model_config = SettingsConfigDict(env_prefix="TITILER_STACK_", env_file=".env")


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
        runtime: aws_lambda.Runtime = aws_lambda.Runtime.PYTHON_3_14,
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

        # COG / STAC / MosaicJSON / Zarr endpoints
        lambda_function = aws_lambda.Function(
            self,
            f"{id}-lambda",
            runtime=runtime,
            code=aws_lambda.Code.from_docker_build(
                path=os.path.abspath(code_dir),
                file="lambda/Dockerfile",
                platform="linux/amd64",
                build_args={
                    "PYTHON_VERSION": "3.14",
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


app = App()
settings = StackSettings()

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
