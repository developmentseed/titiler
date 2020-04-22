
# Titiler in AWS Lambda

Titiler is built on top of [FastAPI](https://github.com/tiangolo/fastapi) which *is a modern, fast (high-performance), web framework for building APIs*. It doesn't work natively with AWS Lambda and API Gateway because it needs a way to handler `event` and `context` instead of raw HTTL requests. This is handled by the awesome [mangum](https://github.com/erm/mangum).


```python
from mangum import Mangum
from titiler.main import app

handler = Mangum(app, enable_lifespan=False)
```

## Deployement

1. Get titiler

```bash
$ git clone https://github.com/developmentseed/titiler.git
$ cd titiler/lambda
```

2. Build Docker image and save package

```bash
docker build --tag lambda:latest .
docker run --name lambda -itd lambda:latest /bin/bash
docker cp lambda:/tmp/package.zip package.zip
docker stop lambda
docker rm lambda
```

3. Deploy

3.1. Using Serverless

`npm install -g serverless`

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

`sls deploy --bucket <my-bucket>`

3.2. Using CDK
    
**TODO**
