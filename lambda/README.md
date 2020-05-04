
# Titiler in AWS Lambda

Titiler is built on top of [FastAPI](https://github.com/tiangolo/fastapi) which *is a modern, fast (high-performance), web framework for building APIs*. It doesn't work natively with AWS Lambda and API Gateway because it needs a way to handler `event` and `context` instead of raw HTML requests. This is possible by wrapping the FastAPI app with the awesome [mangum](https://github.com/erm/mangum).

```python
from mangum import Mangum
from titiler.main import app

handler = Mangum(app, enable_lifespan=False)
```

## Deployment

Firstly, get titiler
```bash
git clone https://github.com/developmentseed/titiler.git
```

### Serverless

1. Build Docker image and save package
    ```bash
    cd titiler/lambda
    docker build --tag lambda:latest .
    docker run --name lambda -itd lambda:latest /bin/bash
    docker cp lambda:/tmp/package.zip package.zip
    docker stop lambda
    docker rm lambda
    ```

1. Install Serverless
    ```bash
    npm install -g serverless`
    ```
1. Create the following `serverless.yml`:
    ```yml
    # serverless.yml
    service: titiler
    
    provider:
      name: aws
      runtime: python3.7
      stage: ${opt:stage, 'production'}
      region: ${opt:region, 'us-east-1'}
    
    package:
      artifact: package.zip
    
    functions:
      app:
        handler: handler.handler
        memorySize: 2048
        timeout: 10
        environment:
          CPL_TMPDIR: /tmp
          GDAL_CACHEMAX: 25%
          GDAL_DISABLE_READDIR_ON_OPEN: EMPTY_DIR
          GDAL_HTTP_MERGE_CONSECUTIVE_RANGES: YES
          GDAL_HTTP_MULTIPLEX: YES
          GDAL_HTTP_VERSION: 2
          PYTHONWARNINGS: ignore
          VSI_CACHE: TRUE
          VSI_CACHE_SIZE: 1000000
        events:
          - httpApi:
              path: /{proxy+}
              method: '*'
              cors: true
    ```

1. Deploy with:
    ```bash
    sls deploy --bucket <my-bucket>
    ```
### CDK

Titiler is deployed with CDK as part of the main stack in `stack/app.py`.

1. Ensure you're in the root of the project

1. Check that CDK can synthesise:
    ```bash
    cdk synth
    ```
   
1. **Optional** - Check difference after running deploy
    ```bash
    cdk diff
    ```

1. Deploy with CDK
    ```bash
    cdk deploy
    # You may be asked for confirmation
    # You will see the following whilst the Lambda package is retrieved:
    Building image and retrieving container
    Extracting function package from container
    ```

1. Grab the API Gateway url, which will look like:
   ```bash
   titiler-lambda-dev.titilerlambdadevlambdaapigatewayEndpoint493715FB = https://<a_value>.execute-api.<a_region>.amazonaws.com/prod/
   ```

1. Navigate to the url and this will take you to titiler
