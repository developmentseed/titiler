# AWS Lambda

TiTiler is built on top of [FastAPI](https://github.com/tiangolo/fastapi), a modern, fast, Python web framework for building APIs. It doesn't work natively with AWS Lambda and API Gateway because FastAPI understands HTTP requests, not API Gateway's `event` and `context` JSON objects. However, we can make our FastAPI application work on Lambda by wrapping it with the awesome [`mangum`](https://github.com/erm/mangum) module, which translates API Gateway events into HTTP requests.

```python
from mangum import Mangum
from titiler.main import app

handler = Mangum(app, enable_lifespan=False)
```

## Deploy

The Lambda stack is also deployed by the [AWS CDK](https://aws.amazon.com/cdk/) utility. Under the hood, CDK will create the deployment package required for AWS Lambda, upload it to AWS, and handle the creation of the Lambda and API Gateway resources.

1. Install CDK and connect to your AWS account. This step is only necessary once per AWS account.

    ```bash
    # Download titiler repo
    $ git clone https://github.com/developmentseed/titiler.git

    # install cdk dependencies
    $ cd titiler/deployment/aws && pip install -r requirements.txt
    $ npm install aws-cdk@1.76.0 -g

    $ cdk bootstrap # Deploys the CDK toolkit stack into an AWS environment

    # in specific region
    $ cdk bootstrap aws://${AWS_ACCOUNT_ID}/eu-central-1
    ```

2. Pre-Generate CFN template

    ```bash
    $ cdk synth  # Synthesizes and prints the CloudFormation template for this stack
    ```

3. Update settings (see [intro.md](intro.md))

    ```bash
    export TITILER_PROJECT="mytiler"
    export TITILER_STAGE="dev"
    export TITILER_MEMORY=512
    ```

    Available settings for AWS Lambda:

    ```python
    timeout: int = 10
    memory: int = 1536

    # The maximum of concurrent executions you want to reserve for the function.
    # Default: - No specific limit - account limit.
    max_concurrent: Optional[int]
    ```

4. Deploy

    ```bash
    $ cdk deploy mytiler-lambda-dev # Deploys the stack(s) titiler-lambda-dev in cdk/app.py

    # Deploy in specific region
    $ AWS_DEFAULT_REGION=eu-central-1 AWS_REGION=eu-central-1 cdk deploy mytiler-lambda-dev
    ```
