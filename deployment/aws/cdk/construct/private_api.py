"""Private API Construct"""

import os
from typing import Any, Dict, List, Optional, cast

from aws_cdk import CfnOutput, Duration, Stack
from aws_cdk.aws_apigateway import (
    EndpointConfiguration,
    EndpointType,
    LambdaIntegration,
    RestApi,
)
from aws_cdk.aws_iam import AnyPrincipal, Effect, PolicyDocument, PolicyStatement
from aws_cdk.aws_lambda import Code, Function, IFunction, Runtime
from aws_cdk.aws_logs import RetentionDays
from constructs import Construct


class TitilerPrivateApiStack(Stack):
    """
    Titiler Private API Stack

    Private api configuration for titiler.

    author: @jeandsmith
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc_endpoint_id: None | str,
        memory: int = 1024,
        timeout: int = 30,
        runtime: Runtime = Runtime.PYTHON_3_11,
        code_dir: str = "./",
        concurrent: Optional[int] = None,
        permissions: Optional[List[PolicyStatement]] = None,
        environment: Optional[Dict] = None,
        **kwargs: Any,
    ) -> None:
        """Define the stack"""
        super().__init__(scope, id, **kwargs)

        permissions = permissions or []
        environment = environment or {}

        lambda_function = Function(
            self,
            f"{id}-lambda",
            runtime=runtime,
            code=Code.from_docker_build(
                path=os.path.abspath(code_dir),
                file="lambda/Dockerfile",
            ),
            handler="handler.handler",
            memory_size=memory,
            reserved_concurrent_executions=concurrent,
            timeout=Duration.seconds(timeout),
            environment=environment,
            log_retention=RetentionDays.ONE_WEEK,
        )

        for perm in permissions:
            lambda_function.add_to_role_policy(perm)

        policy = (
            PolicyDocument(
                statements=[
                    PolicyStatement(
                        principals=[AnyPrincipal()],
                        effect=Effect.DENY,
                        actions=["execute-api:Invoke"],
                        resources=[
                            Stack.of(self).format_arn(
                                service="execute-api", resource="*"
                            )
                        ],
                        conditions={
                            "StringNotEquals": {"aws:SourceVpce": vpc_endpoint_id}
                        },
                    ),
                    PolicyStatement(
                        principals=[AnyPrincipal()],
                        effect=Effect.ALLOW,
                        actions=["execute-api:Invoke"],
                        resources=[
                            Stack.of(self).format_arn(
                                service="execute-api", resource="*"
                            )
                        ],
                    ),
                ]
            )
            if vpc_endpoint_id
            else None
        )

        endpoint_config = (
            EndpointConfiguration(types=[EndpointType.PRIVATE])
            if vpc_endpoint_id
            else EndpointConfiguration(types=[EndpointType.REGIONAL])
        )

        api = RestApi(
            self,
            f"{id}-endpoint",
            default_integration=LambdaIntegration(
                handler=cast(IFunction, lambda_function)
            ),
            policy=policy,
            endpoint_configuration=endpoint_config,
        )
        api.root.add_proxy()

        CfnOutput(self, "Endpoint", value=api.url)
