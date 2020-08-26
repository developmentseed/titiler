# AWS Lambda

Titiler is built on top of [FastAPI](https://github.com/tiangolo/fastapi) which *is a modern, fast (high-performance), web framework for building APIs*. It doesn't work natively with AWS Lambda and API Gateway because it needs a way to handler `event` and `context` instead of raw HTML requests. This is possible by wrapping the FastAPI app with the awesome [mangum](https://github.com/erm/mangum) module.


```python
from mangum import Mangum
from titiler.main import app

handler = Mangum(app, enable_lifespan=False)
```

The Lambda stack is also deployed by the [aws cdk](https://aws.amazon.com/cdk/) utility. It will create the `package.zip` and handle the creation of the lambda function and the API Gateway HTTP endpoint.

1. Instal cdk and set up CDK in your AWS account - Only need once per account

    ```bash
    $ git clone https://github.com/developmentseed/titiler.git
    $ cd titiler && pip install -e .["deploy"]

    $ npm install cdk -g

    $ cdk bootstrap # Deploys the CDK toolkit stack into an AWS environment

    # in specific region
    $ cdk bootstrap aws://${AWS_ACCOUNT_ID}/eu-central-1
    ```

2. Pre-Generate CFN template

    ```bash
    $ cdk synth  # Synthesizes and prints the CloudFormation template for this stack
    ```

3. Edit [stack/config.py](stack/config.py)

    ```python
    PROJECT_NAME = "titiler"
    PROJECT_NAME = os.environ.get("PROJECT", "titiler")
    ...
    TIMEOUT: int = 10
    MEMORY: int = 512
    MAX_CONCURRENT: int = 500
    ```

4. Deploy

    ```bash
    $ cdk deploy titiler-lambda-dev # Deploys the stack(s) titiler-lambda-dev in stack/app.py

    # in specific region
    $ AWS_DEFAULT_REGION=eu-central-1 AWS_REGION=eu-central-1 cdk deploy titiler-lambda-dev 
    ```
